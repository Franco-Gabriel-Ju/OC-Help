function byId(id) {
  return document.getElementById(id);
}

function showOutput(id, data) {
  const out = byId(id);
  if (data.ok) {
    out.classList.remove("error");
    out.textContent = typeof data.resultado === "string" ? data.resultado : JSON.stringify(data.resultado, null, 2);
    if (data.explicito) {
      out.textContent += `\n(explicito: ${data.explicito})`;
    }
  } else {
    out.classList.add("error");
    out.textContent = data.error || "Error desconocido";
  }
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

const BASES = {
  DEC: 10,
  BIN: 2,
  HEX: 16,
  OCT: 8,
};

const OUTPUT_IDS = {
  DEC: "out-dec",
  BIN: "out-bin",
  HEX: "out-hex",
  OCT: "out-oct",
};

let calcStatusTimer = null;
let calcLayoutRaf = null;

function getOuterHeight(element) {
  if (!element) {
    return 0;
  }

  const rect = element.getBoundingClientRect();
  const styles = window.getComputedStyle(element);
  const marginTop = Number.parseFloat(styles.marginTop) || 0;
  const marginBottom = Number.parseFloat(styles.marginBottom) || 0;
  return rect.height + marginTop + marginBottom;
}

function getViewportHeight() {
  return Math.round(window.visualViewport?.height || window.innerHeight || 0);
}

function updateCalcLayout() {
  const panel = byId("panel-calc");
  const mainGrid = document.querySelector("#panel-calc .calc-main-grid");
  if (!panel || !mainGrid || !panel.classList.contains("active")) {
    if (mainGrid) {
      mainGrid.style.height = "";
    }
    return;
  }

  const isMobile = window.matchMedia("(max-width: 700px)").matches;
  if (!isMobile) {
    mainGrid.style.height = "";
    return;
  }

  const panelHeight = panel.getBoundingClientRect().height || getViewportHeight();
  const gap = Number.parseFloat(window.getComputedStyle(panel).rowGap || window.getComputedStyle(panel).gap || "0") || 0;
  const visibleItems = Array.from(panel.children).filter((element) => {
    if (element === mainGrid || element.getClientRects().length === 0) {
      return false;
    }

    // Dialogs y elementos fijos/absolutos no deben influir en la altura disponible del teclado.
    if (element.tagName === "DIALOG") {
      return false;
    }

    const position = window.getComputedStyle(element).position;
    if (position === "fixed" || position === "absolute") {
      return false;
    }

    return true;
  });
  const otherHeight = visibleItems.reduce((total, element) => total + getOuterHeight(element), 0);
  const remainingHeight = Math.max(0, Math.floor(panelHeight - otherHeight - (gap * visibleItems.length)));

  mainGrid.style.height = `${remainingHeight}px`;
}

function scheduleCalcLayoutUpdate() {
  if (calcLayoutRaf) {
    cancelAnimationFrame(calcLayoutRaf);
  }

  calcLayoutRaf = requestAnimationFrame(() => {
    calcLayoutRaf = null;
    updateCalcLayout();
  });
}

function setCalcStatus(text, isError = false) {
  const status = byId("calc-status");
  if (!status) {
    return;
  }

  const quietInfo = !isError && (
    text.startsWith("Listo.") ||
    text.startsWith("Conversion actualizada")
  );

  if (quietInfo || !text) {
    status.classList.remove("is-visible", "error");
    status.textContent = "";
    if (calcStatusTimer) {
      clearTimeout(calcStatusTimer);
      calcStatusTimer = null;
    }
    return;
  }

  status.classList.toggle("error", isError);
  status.textContent = text;
  status.classList.add("is-visible");

  if (calcStatusTimer) {
    clearTimeout(calcStatusTimer);
  }

  const duration = isError ? 3200 : 1800;
  calcStatusTimer = setTimeout(() => {
    status.classList.remove("is-visible", "error");
    status.textContent = "";
    calcStatusTimer = null;
  }, duration);
}

function getBaseName(baseNumber) {
  const entries = Object.entries(BASES);
  const found = entries.find(([, value]) => value === baseNumber);
  return found ? found[0] : "DEC";
}

function clearCalcOutputs() {
  Object.values(OUTPUT_IDS).forEach((id) => {
    byId(id).value = "";
  });
}

function syncToggleButtonsState() {
  document.querySelectorAll(".toggle-btn").forEach((label) => {
    const checkbox = label.querySelector('input[type="checkbox"]');
    if (!checkbox) {
      return;
    }

    label.classList.toggle("is-on", checkbox.checked);
  });
}

function resetCalcOptions() {
  const checkboxDefaults = {
    "calc-redondear": true,
    "calc-entrada-comp": false,
    "calc-nc-fijo": false,
    "calc-complemento": false,
  };

  Object.entries(checkboxDefaults).forEach(([id, value]) => {
    const element = byId(id);
    if (element) {
      element.checked = value;
    }
  });

  const selectDefaults = {
    "calc-separador": ",",
    "calc-base-nc": "10",
  };

  Object.entries(selectDefaults).forEach(([id, value]) => {
    const element = byId(id);
    if (element) {
      element.value = value;
    }
  });

  const numberDefaults = {
    "calc-e": "5",
    "calc-f": "2",
    "calc-precision": "4",
  };

  Object.entries(numberDefaults).forEach(([id, value]) => {
    const element = byId(id);
    if (element) {
      element.value = value;
    }
  });

  syncToggleButtonsState();
  updateOptionsIndicator();
}


function getAllowedDigits(baseNumber) {
  if (baseNumber === 2) {
    return "01";
  }
  if (baseNumber === 8) {
    return "01234567";
  }
  if (baseNumber === 10) {
    return "0123456789";
  }
  return "0123456789ABCDEF";
}

function refreshKeypadByBase() {
  const base = Number(byId("calc-base-origen").value);
  const allowed = getAllowedDigits(base);
  document.querySelectorAll(".key[data-key]").forEach((button) => {
    const key = button.dataset.key;
    if (key.length === 1 && /^[0-9A-F]$/.test(key)) {
      button.disabled = !allowed.includes(key);
      return;
    }
    button.disabled = false;
  });
}

function appendCalcToken(token) {
  const input = byId("calc-numero");
  const current = input.value;
  const base = Number(byId("calc-base-origen").value);
  const allowed = getAllowedDigits(base);

  if (/^[0-9A-F]$/.test(token) && !allowed.includes(token)) {
    return;
  }
  if (token === "." || token === ",") {
    const lastOpIndex = Math.max(
      current.lastIndexOf("+"),
      current.lastIndexOf("-"),
      current.lastIndexOf("*"),
      current.lastIndexOf("/"),
      current.lastIndexOf("("),
      current.lastIndexOf(")")
    );
    const tail = current.slice(lastOpIndex + 1);
    if (tail.includes(".") || tail.includes(",")) {
      return;
    }
    input.value = `${current}${token}`;
    return;
  }

  if (token === "+" || token === "-" || token === "*" || token === "/") {
    if (!current && token !== "-") {
      return;
    }
    const last = current.slice(-1);
    if (["+", "-", "*", "/"].includes(last) && token !== "-") {
      input.value = `${current.slice(0, -1)}${token}`;
      return;
    }
    input.value = `${current}${token}`;
    return;
  }

  input.value = `${current}${token}`;
}

function toggleSign() {
  const input = byId("calc-numero");
  if (!input.value) {
    input.value = "-";
    return;
  }
  input.value = input.value.startsWith("-") ? input.value.slice(1) : `-${input.value}`;
}

function isExpression(text) {
  const t = String(text || "").trim();
  if (!t) {
    return false;
  }
  if (/[+*/xX÷()]/.test(t)) {
    return true;
  }
  for (let i = 1; i < t.length; i += 1) {
    if (t[i] === "-" && /[0-9A-F),.]/i.test(t[i - 1])) {
      return true;
    }
  }
  return false;
}

function isValidNumberTokenForBase(token, base) {
  const raw = String(token || "").trim().toUpperCase();
  if (!raw) {
    return false;
  }

  const text = raw.startsWith("+") || raw.startsWith("-") ? raw.slice(1) : raw;
  if (!text) {
    return false;
  }

  const allowed = getAllowedDigits(base);
  let separators = 0;
  for (const ch of text) {
    if (ch === "." || ch === ",") {
      separators += 1;
      if (separators > 1) {
        return false;
      }
      continue;
    }
    if (!allowed.includes(ch)) {
      return false;
    }
  }

  if (text === "." || text === ",") {
    return false;
  }
  return true;
}

function validateInputByBase(text, base) {
  const t = String(text || "").trim();
  if (!t || t === "+" || t === "-") {
    return { ok: false, reason: "empty" };
  }

  if (/[+\-*/xX÷()]/.test(t)) {
    const expr = t.replace(/x|X/g, "*").replace(/÷/g, "/");
    if (/[+\-*/]$/.test(expr)) {
      return { ok: false, reason: "partial" };
    }

    const parts = expr.split(/[+\-*/()]/).map((p) => p.trim()).filter(Boolean);
    if (!parts.length) {
      return { ok: false, reason: "partial" };
    }
    for (const part of parts) {
      if (!isValidNumberTokenForBase(part, base)) {
        return { ok: false, reason: "invalid" };
      }
    }
    return { ok: true };
  }

  return isValidNumberTokenForBase(t, base) ? { ok: true } : { ok: false, reason: "invalid" };
}

async function resolveExpressionIfNeeded(forceResolve) {
  const raw = byId("calc-numero").value.trim();
  if (!isExpression(raw)) {
    return { ok: true, resolved: false };
  }

  if (!forceResolve) {
    clearCalcOutputs();
    setCalcStatus("Expresion detectada. Pulsa '=' para resolver.");
    return { ok: false, resolved: false, deferred: true };
  }

  const evalData = await postJson("/api/eval-expression", {
    expresion: raw,
    base_origen: Number(byId("calc-base-origen").value),
    precision: Number(byId("calc-precision").value),
    separador: byId("calc-separador").value,
  });

  if (!evalData.ok) {
    clearCalcOutputs();
    setCalcStatus(evalData.error || "Error al evaluar la expresion.", true);
    return { ok: false, resolved: false };
  }

  byId("calc-numero").value = evalData.resultado;
  return { ok: true, resolved: true };
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const temp = document.createElement("textarea");
    temp.value = text;
    document.body.appendChild(temp);
    temp.select();
    document.execCommand("copy");
    document.body.removeChild(temp);
  }
}

async function useOutputAsInput(baseName) {
  const value = byId(OUTPUT_IDS[baseName]).value;
  if (!value) {
    setCalcStatus("No hay resultado en esa base.", true);
    return;
  }
  byId("calc-base-origen").value = String(BASES[baseName]);
  byId("calc-numero").value = value;
  refreshKeypadByBase();
  scheduleCalcLayoutUpdate();
  resetCalcOptions();
  await runCalcAll(false);
  setCalcStatus("Opciones reseteadas.");
}

async function runCalcAll(forceResolveExpression = false) {
  const inputText = byId("calc-numero").value;
  const base = Number(byId("calc-base-origen").value);
  const validity = validateInputByBase(inputText, base);
  if (!validity.ok) {
    clearCalcOutputs();
    if (validity.reason === "empty") {
      setCalcStatus("Listo. Escribe un numero y se convierte a todas las bases.");
      return;
    }
    if (validity.reason === "partial") {
      setCalcStatus("Expresion incompleta. Continúa escribiendo o pulsa '=' al terminar.");
      return;
    }
    setCalcStatus("Entrada invalida para la base seleccionada.", true);
    return;
  }

  const resolvedInfo = await resolveExpressionIfNeeded(forceResolveExpression);
  if (!resolvedInfo.ok) {
    return;
  }

  const payload = {
    numero: byId("calc-numero").value,
    base_origen: Number(byId("calc-base-origen").value),
    precision: Number(byId("calc-precision").value),
    separador: byId("calc-separador").value,
    redondear: byId("calc-redondear").checked,
    entrada_complementada: byId("calc-entrada-comp").checked,
    nc_fijo: byId("calc-nc-fijo").checked,
    base_nc: Number(byId("calc-base-nc").value),
    e: Number(byId("calc-e").value),
    f: Number(byId("calc-f").value),
    complemento: byId("calc-complemento").checked,
  };

  const data = await postJson("/api/convert-all", payload);
  if (!data.ok) {
    clearCalcOutputs();
    setCalcStatus(data.error || "Error desconocido", true);
    return;
  }

  Object.entries(OUTPUT_IDS).forEach(([key, id]) => {
    byId(id).value = data.resultados[key] || "";
  });
  if (data.aviso) {
    setCalcStatus(data.aviso);
  } else {
    setCalcStatus("Conversion actualizada en DEC, BIN, HEX y OCT.");
  }
}


function updateOptionsIndicator() {
  const badge = byId("calc-options-badge");
  if (!badge) {
    return;
  }

  const activeOptions = [];

  if (byId("calc-entrada-comp").checked) {
    activeOptions.push("A");
  }
  if (byId("calc-nc-fijo").checked) {
    activeOptions.push("N");
  }
  if (byId("calc-complemento").checked) {
    activeOptions.push("C");
  }

  if (activeOptions.length > 0) {
    badge.classList.add("active");
    badge.textContent = activeOptions.length;
  } else {
    badge.classList.remove("active");
    badge.textContent = "";
  }
}

function initCalculator() {
  byId("calc-base-origen").addEventListener("change", () => {
    refreshKeypadByBase();
    scheduleCalcLayoutUpdate();
    runCalcAll(false);
  });

  [
    "calc-numero",
    "calc-precision",
    "calc-separador",
    "calc-redondear",
    "calc-entrada-comp",
    "calc-nc-fijo",
    "calc-base-nc",
    "calc-e",
    "calc-f",
    "calc-complemento",
  ].forEach((id) => {
    byId(id).addEventListener("input", () => {
      updateOptionsIndicator();
      runCalcAll(false);
    });
    byId(id).addEventListener("change", () => {
      updateOptionsIndicator();
      runCalcAll(false);
    });
  });

  document.querySelectorAll(".key[data-key]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const key = btn.dataset.key;
      if (key === "AC") {
        byId("calc-numero").value = "";
        clearCalcOutputs();
        setCalcStatus("Listo.");
        return;
      }
      if (key === "DEL") {
        byId("calc-numero").value = byId("calc-numero").value.slice(0, -1);
        runCalcAll(false);
        return;
      }
      if (key === "+/-") {
        toggleSign();
        runCalcAll(false);
        return;
      }

      if (key === "=") {
        await runCalcAll(true);
        return;
      }

      appendCalcToken(key);
      runCalcAll(false);
    });
  });

  byId("calc-numero").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      runCalcAll(true);
      return;
    }

    const key = event.key.toUpperCase();
    const base = Number(byId("calc-base-origen").value);
    const allowed = getAllowedDigits(base);
    const controlKeys = [
      "BACKSPACE",
      "DELETE",
      "ARROWLEFT",
      "ARROWRIGHT",
      "HOME",
      "END",
      "TAB",
      "ENTER",
    ];

    if (controlKeys.includes(key)) {
      return;
    }

    if (event.ctrlKey || event.metaKey || event.altKey) {
      return;
    }

    if (["+", "-", "*", "/", "(", ")"].includes(key)) {
      return;
    }

    if (key.length === 1 && /[0-9A-F]/.test(key) && !allowed.includes(key)) {
      event.preventDefault();
      return;
    }

    if (key === "." || key === ",") {
      if (byId("calc-numero").value.includes(".") || byId("calc-numero").value.includes(",")) {
        event.preventDefault();
      }
    }
  });

  refreshKeypadByBase();
  setCalcStatus("Listo. Escribe un numero y se convierte a todas las bases.");
  updateOptionsIndicator();
  scheduleCalcLayoutUpdate();
}

function initTabs() {
  const tabs = document.querySelectorAll(".tab");
  const tabsShell = document.querySelector(".tabs-shell");
  const menuBtn = byId("tabs-menu-btn");
  const mobileQuery = window.matchMedia("(max-width: 700px)");
  const panels = {
    calc: byId("panel-calc"),
    nc2nc: byId("panel-nc2nc"),
    nc2cs: byId("panel-nc2cs"),
    suma: byId("panel-suma"),
  };

  const syncTabsMenuState = () => {
    if (!tabsShell || !menuBtn) {
      return;
    }

    if (mobileQuery.matches) {
      tabsShell.classList.remove("open");
      menuBtn.setAttribute("aria-expanded", "false");
      return;
    }

    tabsShell.classList.add("open");
    menuBtn.setAttribute("aria-expanded", "true");
  };

  if (tabsShell && menuBtn) {
    menuBtn.addEventListener("click", () => {
      if (!mobileQuery.matches) {
        return;
      }
      const willOpen = !tabsShell.classList.contains("open");
      tabsShell.classList.toggle("open", willOpen);
      menuBtn.setAttribute("aria-expanded", String(willOpen));
    });

    syncTabsMenuState();
    mobileQuery.addEventListener("change", syncTabsMenuState);
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      Object.values(panels).forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      panels[tab.dataset.tab].classList.add("active");

      if (tabsShell && menuBtn && mobileQuery.matches) {
        tabsShell.classList.remove("open");
        menuBtn.setAttribute("aria-expanded", "false");
      }

      scheduleCalcLayoutUpdate();
    });
  });
}

function initToggleButtons() {
  document.querySelectorAll(".toggle-btn").forEach((label) => {
    const checkbox = label.querySelector('input[type="checkbox"]');
    if (!checkbox) {
      return;
    }

    const sync = () => {
      label.classList.toggle("is-on", checkbox.checked);
    };

    checkbox.addEventListener("change", sync);
  });

  syncToggleButtonsState();
}

function initRoundingModal() {
  const modal = byId("rounding-modal");
  const openButton = byId("rounding-modal-btn");
  const closeButton = byId("rounding-modal-close");

  if (!modal || !openButton || !closeButton) {
    return;
  }

  const closeModal = () => {
    if (modal.open) {
      modal.close();
    }
  };

  openButton.addEventListener("click", () => {
    if (modal.open) {
      modal.close();
      return;
    }
    modal.showModal();
  });

  closeButton.addEventListener("click", closeModal);

  modal.addEventListener("click", (event) => {
    const rect = modal.getBoundingClientRect();
    const clickedBackdrop = (
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom
    );

    if (clickedBackdrop) {
      closeModal();
    }
  });
}

function initCalcOptionsModal() {
  const modal = byId("calc-options-modal");
  const openButton = byId("calc-options-btn");
  const closeButton = byId("calc-options-close");

  if (!modal || !openButton || !closeButton) {
    return;
  }

  const closeModal = () => {
    if (modal.open) {
      modal.close();
      openButton.setAttribute("aria-expanded", "false");
    }
  };

  openButton.setAttribute("aria-expanded", "false");

  openButton.addEventListener("click", () => {
    if (modal.open) {
      closeModal();
      return;
    }

    modal.showModal();
    openButton.setAttribute("aria-expanded", "true");
  });

  closeButton.addEventListener("click", closeModal);

  modal.addEventListener("click", (event) => {
    const rect = modal.getBoundingClientRect();
    const clickedBackdrop = (
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom
    );

    if (clickedBackdrop) {
      closeModal();
    }
  });

  modal.addEventListener("close", () => {
    openButton.setAttribute("aria-expanded", "false");
  });
}

function initWelcomeModal() {
  const modal = byId("welcome-modal");
  const closeButton = byId("welcome-close");

  if (!modal || !closeButton) {
    return;
  }

  const closeModal = () => {
    if (modal.open) {
      modal.close();
    }
  };

  closeButton.addEventListener("click", closeModal);

  modal.addEventListener("click", (event) => {
    const rect = modal.getBoundingClientRect();
    const clickedBackdrop = (
      event.clientX < rect.left ||
      event.clientX > rect.right ||
      event.clientY < rect.top ||
      event.clientY > rect.bottom
    );

    if (clickedBackdrop) {
      closeModal();
    }
  });

  requestAnimationFrame(() => {
    modal.showModal();
  });
}

function initActions() {
  byId("nc2nc-run").addEventListener("click", async () => {
    const payload = {
      numero_comp: byId("nc2nc-numero").value,
      base_origen: Number(byId("nc2nc-bo").value),
      e_origen: Number(byId("nc2nc-eo").value),
      f_origen: Number(byId("nc2nc-fo").value),
      base_destino: Number(byId("nc2nc-bd").value),
      e_destino: Number(byId("nc2nc-ed").value),
      f_destino: Number(byId("nc2nc-fd").value),
      separador: byId("nc2nc-sep").value,
    };
    showOutput("nc2nc-out", await postJson("/api/nc2nc", payload));
  });

  document.querySelectorAll(".usar-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await useOutputAsInput(btn.dataset.out);
    });
  });

  byId("nc2cs-run").addEventListener("click", async () => {
    const payload = {
      numero_comp: byId("nc2cs-numero").value,
      base: Number(byId("nc2cs-base").value),
      e: Number(byId("nc2cs-e").value),
      f: Number(byId("nc2cs-f").value),
      separador: byId("nc2cs-sep").value,
    };
    showOutput("nc2cs-out", await postJson("/api/nc2cs", payload));
  });

  byId("suma-run").addEventListener("click", async () => {
    const payload = {
      n1: byId("suma-n1").value,
      n2: byId("suma-n2").value,
      base: Number(byId("suma-base").value),
      e: Number(byId("suma-e").value),
      f: Number(byId("suma-f").value),
      operacion: byId("suma-op").value,
      separador: byId("suma-sep").value,
    };
    showOutput("suma-out", await postJson("/api/suma-nc", payload));
  });

}

initTabs();
initToggleButtons();
initRoundingModal();
initCalcOptionsModal();
initWelcomeModal();
initCalculator();
initActions();

window.addEventListener("resize", scheduleCalcLayoutUpdate);
window.addEventListener("orientationchange", scheduleCalcLayoutUpdate);
window.visualViewport?.addEventListener("resize", scheduleCalcLayoutUpdate);
