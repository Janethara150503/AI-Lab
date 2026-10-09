document.addEventListener("DOMContentLoaded", () => {
  // -------------------------------------------------------------
  // Modal: nuevo hábito
  // -------------------------------------------------------------
  const newModal = document.getElementById("modal-overlay");
  const openBtns = [
    document.getElementById("open-modal-btn"),
    document.getElementById("open-modal-btn-empty"),
  ].filter(Boolean);
  const cancelNewBtn = document.getElementById("cancel-modal-btn");
  const newForm = document.getElementById("nuevo-habito-form");

  function openModal(overlay) {
    overlay.classList.add("is-open");
    const firstInput = overlay.querySelector("input, textarea");
    if (firstInput) firstInput.focus();
  }

  function closeModal(overlay) {
    overlay.classList.remove("is-open");
  }

  openBtns.forEach((btn) => {
    btn.addEventListener("click", () => openModal(newModal));
  });

  if (cancelNewBtn) {
    cancelNewBtn.addEventListener("click", () => {
      newForm.reset();
      closeModal(newModal);
    });
  }

  newModal.addEventListener("click", (e) => {
    if (e.target === newModal) closeModal(newModal);
  });

  // -------------------------------------------------------------
  // Modal: confirmar eliminación
  // -------------------------------------------------------------
  const deleteModal = document.getElementById("delete-modal-overlay");
  const deleteForm = document.getElementById("delete-habito-form");
  const deleteNombreEl = document.getElementById("delete-habito-nombre");
  const cancelDeleteBtn = document.getElementById("cancel-delete-btn");

  document.querySelectorAll(".btn--delete-trigger").forEach((btn) => {
    btn.addEventListener("click", () => {
      const habitoId = btn.dataset.habitoId;
      const habitoNombre = btn.dataset.habitoNombre;

      deleteForm.action = `/habitos/${habitoId}/eliminar`;
      deleteNombreEl.textContent = habitoNombre;

      openModal(deleteModal);
    });
  });

  if (cancelDeleteBtn) {
    cancelDeleteBtn.addEventListener("click", () => closeModal(deleteModal));
  }

  deleteModal.addEventListener("click", (e) => {
    if (e.target === deleteModal) closeModal(deleteModal);
  });

  // -------------------------------------------------------------
  // Modal: sugerencias de hábitos con IA
  // -------------------------------------------------------------
  const suggestModal = document.getElementById("suggest-modal-overlay");
  const suggestOpenBtn = document.getElementById("open-suggest-btn");
  const suggestList = document.getElementById("suggest-list");
  const suggestStatus = document.getElementById("suggest-status");
  const suggestRetryBtn = document.getElementById("suggest-retry-btn");
  const suggestCloseBtn = document.getElementById("suggest-close-btn");

  function hiddenInput(name, value) {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = name;
    input.value = value;
    return input;
  }

  // Cada sugerencia es un formulario POST a /habitos/nuevo (ruta existente).
  // Se usa textContent / value, nunca innerHTML, porque el texto viene de la IA.
  function renderSugerencia(s) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/habitos/nuevo";
    form.className = "suggest-item";

    const info = document.createElement("div");
    const nombre = document.createElement("strong");
    nombre.textContent = s.nombre;
    const desc = document.createElement("p");
    desc.className = "suggest-item__desc";
    desc.textContent = s.descripcion || "";
    info.append(nombre, desc);

    const btn = document.createElement("button");
    btn.type = "submit";
    btn.className = "btn btn--complete";
    btn.textContent = "Agregar";

    form.append(hiddenInput("nombre", s.nombre), hiddenInput("descripcion", s.descripcion || ""), info, btn);
    return form;
  }

  async function cargarSugerencias() {
    suggestList.replaceChildren();
    suggestStatus.textContent = "Pensando en hábitos para ti…";
    suggestRetryBtn.disabled = true;

    try {
      const resp = await fetch("/habitos/sugerencias", { method: "POST" });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || "Error inesperado.");

      suggestStatus.textContent = "Basado en tus hábitos actuales:";
      data.sugerencias.forEach((s) => suggestList.appendChild(renderSugerencia(s)));
    } catch (err) {
      suggestStatus.textContent =
        err instanceof TypeError
          ? "No hay conexión con el servidor. Intenta de nuevo."
          : err.message;
    } finally {
      suggestRetryBtn.disabled = false;
    }
  }

  if (suggestOpenBtn) {
    suggestOpenBtn.addEventListener("click", () => {
      openModal(suggestModal);
      cargarSugerencias();
    });
    suggestRetryBtn.addEventListener("click", cargarSugerencias);
    suggestCloseBtn.addEventListener("click", () => closeModal(suggestModal));
    suggestModal.addEventListener("click", (e) => {
      if (e.target === suggestModal) closeModal(suggestModal);
    });
  }

  // -------------------------------------------------------------
  // Cerrar modales con la tecla Escape
  // -------------------------------------------------------------
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeModal(newModal);
      closeModal(deleteModal);
      closeModal(suggestModal);
    }
  });

  // -------------------------------------------------------------
  // Quitar los toasts del DOM después de su animación
  // -------------------------------------------------------------
  document.querySelectorAll(".toast").forEach((toast) => {
    toast.addEventListener("animationend", (e) => {
      if (e.animationName === "toast-out") toast.remove();
    });
  });
});