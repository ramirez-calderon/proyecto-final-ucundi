// ---------------------------------------------------------------------------
// AgroGirardot · lógica del panel (vanilla JavaScript, sin frameworks)
// Todo el estado real vive en el backend Flask; aquí solo se consume la API.
// ---------------------------------------------------------------------------

const state = {
  cultivos: [],
  cultivoActualId: null,
  chart: null,
};

const $ = (sel) => document.querySelector(sel);

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`Error en ${path}: ${res.status}`);
  return res.json();
}

const nombreTipo = (tipo) => (tipo === "mango" ? "Mango" : "Limón");

// ---------------------------------------------------------------------------
// Cultivos (sidebar)
// ---------------------------------------------------------------------------

async function cargarCultivos() {
  state.cultivos = await api("/api/cultivos");
  if (!state.cultivoActualId && state.cultivos.length) {
    state.cultivoActualId = state.cultivos[0].id;
  }
  renderListaCultivos();
  await seleccionarCultivo(state.cultivoActualId);
}

function renderListaCultivos() {
  const ul = $("#lista-cultivos");
  ul.innerHTML = "";
  state.cultivos.forEach((c) => {
    const li = document.createElement("li");
    li.className = c.id === state.cultivoActualId ? "active" : "";
    li.innerHTML = `<span>${nombreTipo(c.tipo)}</span><span class="crop-tag">${c.area} ha</span>`;
    li.addEventListener("click", () => seleccionarCultivo(c.id));
    ul.appendChild(li);
  });
}

async function seleccionarCultivo(id) {
  state.cultivoActualId = id;
  renderListaCultivos();
  const cultivo = state.cultivos.find((c) => c.id === id);
  if (!cultivo) return;

  $("#cultivo-titulo").textContent = `${nombreTipo(cultivo.tipo)} · ${cultivo.ubicacion}`;
  $("#riesgo-lista").innerHTML = `<p class="card__note">Presiona "Analizar riesgo" para evaluar este cultivo.</p>`;

  const reporte = await api(`/api/cultivos/${id}/reporte`);
  actualizarGauge(reporte.sensor.valor);
  actualizarHistorial(reporte.sensor.historial);
  renderAlertas(reporte.alertas);

  await cargarObservaciones(id);
}

// ---------------------------------------------------------------------------
// Funcionalidad 1: humedad del suelo
// ---------------------------------------------------------------------------

function actualizarGauge(valor) {
  const circunferencia = 251; // longitud del arco en el SVG
  const porcentaje = Math.max(0, Math.min(100, valor)) / 100;
  const offset = circunferencia - circunferencia * porcentaje;
  const fill = $("#gauge-fill");
  fill.style.strokeDashoffset = offset;

  let color = "var(--water)";
  let estado = "Humedad en rango saludable.";
  if (valor < 30) { color = "#e4572e"; estado = "Humedad baja: se recomienda regar."; }
  else if (valor > 85) { color = "#e8871e"; estado = "Exceso de humedad: reducir el riego."; }
  fill.style.stroke = color;

  $("#humedad-valor").textContent = valor.toFixed(1);
  $("#humedad-estado").textContent = estado;
}

function actualizarHistorial(historial) {
  const labels = historial.map((h) => h.fecha.split("T")[1]);
  const datos = historial.map((h) => h.valor);

  if (state.chart) {
    state.chart.data.labels = labels;
    state.chart.data.datasets[0].data = datos;
    state.chart.update();
    return;
  }

  const ctx = $("#chart-historial").getContext("2d");
  state.chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Humedad del suelo (%)",
        data: datos,
        borderColor: "#4fb8c4",
        backgroundColor: "rgba(79, 184, 196, 0.15)",
        tension: 0.35,
        fill: true,
        pointRadius: 2,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#9fb4a4", maxTicksLimit: 6 }, grid: { display: false } },
        y: { min: 0, max: 100, ticks: { color: "#9fb4a4" }, grid: { color: "#2c4b37" } },
      },
    },
  });
}

async function leerSensor() {
  const id = state.cultivoActualId;
  if (!id) return;
  const res = await api(`/api/cultivos/${id}/sensor`);
  actualizarGauge(res.sensor.valor);
  actualizarHistorial(res.sensor.historial);
  if (res.alerta_generada) {
    await refrescarAlertas(id);
  }
}

// ---------------------------------------------------------------------------
// Funcionalidad 3: clima local
// ---------------------------------------------------------------------------

async function cargarClima() {
  const dias = await api("/api/clima");
  const cont = $("#clima-dias");
  cont.innerHTML = "";
  dias.forEach((d) => {
    const div = document.createElement("div");
    div.className = "climate-day";
    div.innerHTML = `
      <span class="climate-day__date">${d.fecha}</span>
      <span class="climate-day__metrics">
        <span>🌡️ ${d.temperatura}°C</span>
        <span>💧 ${d.humedad}%</span>
        <span>🌧️ ${d.precipitacion} mm</span>
      </span>`;
    cont.appendChild(div);
  });
  const nota = document.createElement("p");
  nota.className = "card__note";
  nota.textContent = `Fuente: ${dias[0]?.fuente ?? "desconocida"}`;
  cont.appendChild(nota);
}

// ---------------------------------------------------------------------------
// Funcionalidad 2: riesgo de plagas y enfermedades
// ---------------------------------------------------------------------------

async function analizarRiesgo() {
  const id = state.cultivoActualId;
  if (!id) return;
  const res = await api(`/api/cultivos/${id}/riesgo`);
  const cont = $("#riesgo-lista");
  cont.innerHTML = "";
  res.riesgos.forEach((r) => {
    const div = document.createElement("div");
    div.className = `risk-item sev-${r.severidad}`;
    div.innerHTML = `
      <div class="risk-item__title">${r.nombre}</div>
      <div class="risk-item__rec">${r.recomendacion}</div>`;
    cont.appendChild(div);
  });
  if (res.nuevas_alertas.length) {
    await refrescarAlertas(id);
  }
}

// ---------------------------------------------------------------------------
// Alertas
// ---------------------------------------------------------------------------

function renderAlertas(alertas) {
  const ul = $("#lista-alertas");
  ul.innerHTML = "";
  if (!alertas.length) {
    ul.innerHTML = `<li class="card__note">Sin alertas todavía.</li>`;
    return;
  }
  alertas.forEach((a) => {
    const li = document.createElement("li");
    li.className = `alert-item${a.atendida ? " atendida" : ""}`;
    li.innerHTML = `
      <div class="alert-item__text">
        ${a.mensaje}
        <div class="alert-item__meta">${a.tipo} · ${a.severidad} · ${a.fecha}</div>
      </div>
      ${a.atendida ? "" : '<button data-id="' + a.id + '">Marcar atendida</button>'}`;
    ul.appendChild(li);
  });
  ul.querySelectorAll("button[data-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await api(`/api/alertas/${btn.dataset.id}/marcar`, { method: "POST" });
      refrescarAlertas(state.cultivoActualId);
    });
  });
}

async function refrescarAlertas(cultivoId) {
  const alertas = await api(`/api/cultivos/${cultivoId}/alertas`);
  renderAlertas(alertas);
}

// ---------------------------------------------------------------------------
// Observaciones del agricultor
// ---------------------------------------------------------------------------

async function cargarObservaciones(cultivoId) {
  const obs = await api(`/api/cultivos/${cultivoId}/observaciones`);
  const ul = $("#lista-observaciones");
  ul.innerHTML = "";
  if (!obs.length) {
    ul.innerHTML = `<li class="card__note">Aún no hay observaciones registradas.</li>`;
    return;
  }
  obs.forEach((o) => {
    const li = document.createElement("li");
    li.innerHTML = `${o.texto}<time>${o.fecha}</time>`;
    ul.appendChild(li);
  });
}

// ---------------------------------------------------------------------------
// Eventos
// ---------------------------------------------------------------------------

$("#btn-leer-sensor").addEventListener("click", leerSensor);
$("#btn-analizar-riesgo").addEventListener("click", analizarRiesgo);

$("#form-nuevo-cultivo").addEventListener("submit", async (e) => {
  e.preventDefault();
  const tipo = $("#input-tipo").value;
  const ubicacion = $("#input-ubicacion").value.trim();
  const area = $("#input-area").value;
  if (!ubicacion || !area) return;

  const nuevo = await api("/api/cultivos", {
    method: "POST",
    body: JSON.stringify({ tipo, ubicacion, area }),
  });
  e.target.reset();
  await cargarCultivos();
  await seleccionarCultivo(nuevo.id);
});

$("#form-observacion").addEventListener("submit", async (e) => {
  e.preventDefault();
  const texto = $("#input-observacion").value.trim();
  if (!texto) return;
  await api(`/api/cultivos/${state.cultivoActualId}/observaciones`, {
    method: "POST",
    body: JSON.stringify({ texto }),
  });
  $("#input-observacion").value = "";
  await cargarObservaciones(state.cultivoActualId);
});

// ---------------------------------------------------------------------------
// Inicialización
// ---------------------------------------------------------------------------

(async function init() {
  const agricultor = await api("/api/agricultor");
  $("#farmer-name").textContent = `👤 ${agricultor.nombre}`;
  await cargarCultivos();
  await cargarClima();
})();
