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

function initActions() {
  byId("calc-run").addEventListener("click", async () => {
    const payload = {
      numero: byId("calc-numero").value,
      base_origen: Number(byId("calc-base-origen").value),
      base_destino: Number(byId("calc-base-destino").value),
      precision: Number(byId("calc-precision").value),
      separador: byId("calc-separador").value,
      complemento: byId("calc-complemento").checked,
      enteros_valor_fijos: byId("calc-enteros-fijos").value || null,
    };
    showOutput("calc-out", await postJson("/api/convert", payload));
  });

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
initActions();
