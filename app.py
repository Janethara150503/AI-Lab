"""
app.py
Aplicación Flask: rutas para listar, crear, marcar como cumplido
y eliminar hábitos, con cálculo de racha e historial de 7 días.
"""

import os
from datetime import date, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from db import execute_query
from ai_service import sugerir_habitos, AIServiceError

load_dotenv()

app = Flask(__name__)
# Necesaria para flash(). Debe venir del entorno (.env / panel del hosting).
app.secret_key = os.environ.get("SECRET_KEY", "clave-solo-para-desarrollo-local")


# ---------------------------------------------------------------------
# Lógica de racha (independiente de Flask, fácil de probar por separado)
# ---------------------------------------------------------------------

def calcular_racha(fechas_registro):
    """
    Calcula la racha actual de días consecutivos hasta hoy.

    fechas_registro: set/list de objetos date en los que el hábito
                      fue marcado como cumplido.

    Reglas:
    - Si no hay registro de hoy, la racha actual es 0.
    - Si hay registro de hoy, se cuenta hacia atrás (ayer, anteayer...)
      mientras exista un registro para cada día consecutivo.
    - En cuanto falta un día, la racha se detiene ahí.
    """
    fechas = set(fechas_registro)
    hoy = date.today()

    if hoy not in fechas:
        return 0

    racha = 0
    dia_actual = hoy
    while dia_actual in fechas:
        racha += 1
        dia_actual -= timedelta(days=1)

    return racha


def historial_7_dias(fechas_registro):
    """
    Devuelve una lista de 7 elementos (hoy y los 6 días anteriores),
    ordenada cronológicamente (más antiguo primero), cada uno con
    su fecha y si hubo registro ese día.
    """
    fechas = set(fechas_registro)
    hoy = date.today()

    dias = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        dias.append({
            "fecha": dia,
            "cumplido": dia in fechas,
        })
    return dias


# ---------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------

def obtener_habitos_con_datos():
    """Lee habitos y registros de Supabase y calcula racha e historial."""
    habitos = execute_query(
        "SELECT id, nombre, descripcion, fecha_creacion FROM habitos ORDER BY fecha_creacion DESC",
        fetch=True,
    )

    habitos_con_datos = []
    for habito in habitos:
        registros = execute_query(
            "SELECT fecha FROM registros WHERE habito_id = %s",
            (habito["id"],),
            fetch=True,
        )
        fechas_registro = [r["fecha"] for r in registros]

        habitos_con_datos.append({
            **habito,
            "racha": calcular_racha(fechas_registro),
            "historial": historial_7_dias(fechas_registro),
            "cumplido_hoy": date.today() in fechas_registro,
        })
    return habitos_con_datos


@app.route("/")
def index():
    return render_template("index.html", habitos=obtener_habitos_con_datos())


@app.route("/habitos/sugerencias", methods=["POST"])
def sugerencias_habitos():
    """
    Devuelve JSON con 3 hábitos nuevos sugeridos por la IA.
    La llamada a OpenAI ocurre aquí en el servidor (ai_service.py);
    el navegador nunca ve la API key.
    """
    try:
        habitos = obtener_habitos_con_datos()
        sugerencias = sugerir_habitos(habitos)
        return jsonify({"sugerencias": sugerencias})
    except AIServiceError as e:
        return jsonify({"error": str(e)}), 502
    except RuntimeError:
        return jsonify({"error": "No pude leer tus hábitos. Intenta de nuevo."}), 500


@app.route("/habitos/nuevo", methods=["POST"])
def nuevo_habito():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip() or None

    if not nombre:
        flash("El nombre del hábito es obligatorio.", "error")
        return redirect(url_for("index"))

    try:
        execute_query(
            "INSERT INTO habitos (nombre, descripcion) VALUES (%s, %s)",
            (nombre, descripcion),
            commit=True,
        )
        flash(f'Hábito "{nombre}" creado correctamente.', "success")
    except RuntimeError:
        flash("Ocurrió un error al guardar el hábito. Intenta de nuevo.", "error")

    return redirect(url_for("index"))


@app.route("/habitos/<int:habito_id>/cumplir", methods=["POST"])
def cumplir_habito(habito_id):
    habito = execute_query(
        "SELECT id FROM habitos WHERE id = %s", (habito_id,), fetch=True
    )
    if not habito:
        flash("Ese hábito no existe.", "error")
        return redirect(url_for("index"))

    hoy = date.today()

    ya_marcado = execute_query(
        "SELECT id FROM registros WHERE habito_id = %s AND fecha = %s",
        (habito_id, hoy),
        fetch=True,
    )

    if ya_marcado:
        flash("Este hábito ya estaba marcado como cumplido hoy.", "info")
    else:
        execute_query(
            "INSERT INTO registros (habito_id, fecha) VALUES (%s, %s)",
            (habito_id, hoy),
            commit=True,
        )
        flash("¡Hábito marcado como cumplido hoy!", "success")

    return redirect(url_for("index"))


@app.route("/habitos/<int:habito_id>/eliminar", methods=["POST"])
def eliminar_habito(habito_id):
    habito = execute_query(
        "SELECT id, nombre FROM habitos WHERE id = %s", (habito_id,), fetch=True
    )
    if not habito:
        flash("Ese hábito no existe.", "error")
        return redirect(url_for("index"))

    # No se borran registros manualmente: la FK tiene ON DELETE CASCADE.
    execute_query(
        "DELETE FROM habitos WHERE id = %s", (habito_id,), commit=True
    )
    flash(f'Hábito "{habito[0]["nombre"]}" eliminado.', "success")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)