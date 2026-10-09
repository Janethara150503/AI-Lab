"""
db.py
Módulo exclusivo para la conexión con PostgreSQL (Supabase).
No contiene lógica de rutas ni de negocio.
"""

import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL")

if not SUPABASE_DB_URL:
    raise RuntimeError(
        "No se encontró la variable de entorno SUPABASE_DB_URL. "
        "Revisa que exista un archivo .env con esa variable definida."
    )


def get_connection():
    """
    Abre y devuelve una nueva conexión a la base de datos.
    Usa dict_row para que las filas se devuelvan como diccionarios
    (más fácil de usar en las plantillas de Flask).
    """
    try:
        conn = psycopg.connect(SUPABASE_DB_URL, row_factory=dict_row)
        return conn
    except psycopg.OperationalError as e:
        raise RuntimeError(f"No se pudo conectar a la base de datos: {e}")


def close_connection(conn):
    """Cierra una conexión de forma segura si sigue abierta."""
    if conn is not None and not conn.closed:
        conn.close()


def execute_query(query, params=None, fetch=False, commit=False):
    """
    Ejecuta una consulta parametrizada.

    - query: sentencia SQL con placeholders %s
    - params: tupla con los valores para la consulta (evita SQL injection)
    - fetch: si True, devuelve todas las filas resultantes
    - commit: si True, confirma los cambios (INSERT/UPDATE/DELETE)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            result = cur.fetchall() if fetch else None
            if commit:
                conn.commit()
            return result
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Error al ejecutar la consulta: {e}")
    finally:
        close_connection(conn)