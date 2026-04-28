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

function setCalcStatus(text, isError = false) {
  const status = byId("calc-status");
  status.classList.toggle("error", isError);
  status.textContent = text;
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
  byId("calc-abrev").textContent = "";
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
  if (token === "." || token === ",") {
    if (current.includes(".") || current.includes(",")) {
      return;
    }
    input.value = `${current}${token}`;
    return;
  }

  if (token === "-") {
    if (current.startsWith("-")) {
      return;
    }
    input.value = `-${current}`;
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

function useOutputAsInput(baseName) {
  const value = byId(OUTPUT_IDS[baseName]).value;
  if (!value) {
    setCalcStatus("No hay resultado en esa base.", true);
    return;
  }
  byId("calc-base-origen").value = String(BASES[baseName]);
  byId("calc-numero").value = value;
  refreshKeypadByBase();
  setCalcStatus(`Tomando ${baseName} como nueva entrada.`);
}

async function runCalcAll() {
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
  byId("calc-abrev").textContent = data.abreviacion || "";
  setCalcStatus("Conversion actualizada en DEC, BIN, HEX y OCT.");
}

function initCalculator() {
  byId("calc-run").addEventListener("click", runCalcAll);

  byId("calc-base-origen").addEventListener("change", () => {
    refreshKeypadByBase();
    runCalcAll();
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
    byId(id).addEventListener("input", runCalcAll);
    byId(id).addEventListener("change", runCalcAll);
  });

  document.querySelectorAll(".usar-btn").forEach((btn) => {
    btn.addEventListener("click", () => useOutputAsInput(btn.dataset.out));
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
        runCalcAll();
        return;
      }
      if (key === "+/-") {
        toggleSign();
        runCalcAll();
        return;
      }
      if (key === "CPBIN") {
        const value = byId("out-bin").value;
        if (value) {
          await copyText(value);
          setCalcStatus(`Copiado BIN: ${value}`);
        } else {
          setCalcStatus("No hay valor BIN para copiar.", true);
        }
        return;
      }
      if (key === "CPDEC") {
        const value = byId("out-dec").value;
        if (value) {
          await copyText(value);
          setCalcStatus(`Copiado DEC: ${value}`);
        } else {
          setCalcStatus("No hay valor DEC para copiar.", true);
        }
        return;
      }

      appendCalcToken(key);
      runCalcAll();
    });
  });

  byId("calc-numero").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      runCalcAll();
    }
  });

  refreshKeypadByBase();
  setCalcStatus("Listo. Escribe un numero y se convierte a todas las bases.");
}

function initTabs() {
  const tabs = document.querySelectorAll(".tab");
  const panels = {
    calc: byId("panel-calc"),
    nc2nc: byId("panel-nc2nc"),
    nc2cs: byId("panel-nc2cs"),
    suma: byId("panel-suma"),
    manual: byId("panel-manual"),
  };

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      Object.values(panels).forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      panels[tab.dataset.tab].classList.add("active");
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
    sync();
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

  byId("manual-run").addEventListener("click", async () => {
    const payload = {
      numero: byId("manual-numero").value,
      base_origen: Number(byId("manual-bo").value),
      base_destino: Number(byId("manual-bd").value),
      precision: Number(byId("manual-precision").value),
      separador: byId("manual-sep").value,
      redondear: byId("manual-redondear").checked,
      entrada_complementada: byId("manual-entrada-comp").checked,
      complemento: byId("manual-complemento").checked,
      nc_fijo: byId("manual-nc-fijo").checked,
      base_nc: Number(byId("manual-bnc").value),
      e: Number(byId("manual-e").value),
      f: Number(byId("manual-f").value),
    };
    const data = await postJson("/api/manual", payload);
    if (data.ok) {
      showOutput("manual-out", { ok: true, resultado: `${data.resultado}\n\n${data.detalle}` });
      return;
    }
    showOutput("manual-out", data);
  });
}

initTabs();
initToggleButtons();
initCalculator();
initActions();
