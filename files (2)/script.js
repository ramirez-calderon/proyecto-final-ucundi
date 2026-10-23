// ==============================================================
// PARTE 1: CLASES (las mismas del diagrama de clases)
// Los datos de sensores y clima son SIMULADOS con Math.random()
// ==============================================================

class Alerta {
  static contador = 0;   // para darle un id único a cada alerta

  constructor(tipo, mensaje) {
    Alerta.contador++;
    this.id = Alerta.contador;
    this.tipo = tipo;
    this.mensaje = mensaje;
    this.fecha = new Date().toLocaleString("es-CO");
  }

  enviarNotificacion() {
    // Por ahora solo lo muestra en la consola (F12). Luego podría enviar un SMS.
    console.log("ALERTA #" + this.id + " [" + this.tipo + "]: " + this.mensaje);
  }
}

class Sensor {
  constructor(id, tipo, nivelCritico, nivelMaximo) {
    this.id = id;
    this.tipo = tipo;                  // "humedad_suelo"
    this.valor = 0;                    // última lectura (%)
    this.nivelCritico = nivelCritico;  // por debajo: falta de agua
    this.nivelMaximo = nivelMaximo;    // por encima: exceso de agua
  }

  leerValor() {
    // Número aleatorio entre 10 y 95 con un decimal
    this.valor = Math.round((10 + Math.random() * 85) * 10) / 10;
    return this.valor;
  }

  enviarDatos() {
    return { sensor: this.id, tipo: this.tipo, valor: this.valor };
  }
}

class CondicionClimatica {
  constructor() {
    this.temperatura = 0;
    this.humedad = 0;
    this.precipitacion = 0;
  }

  obtenerPronostico() {
    // Pronóstico simulado (en un proyecto real vendría de una API de clima)
    this.temperatura = Math.round((24 + Math.random() * 13) * 10) / 10;
    this.humedad = Math.round((40 + Math.random() * 55) * 10) / 10;
    this.precipitacion = Math.round(Math.random() * 30 * 10) / 10;
  }

  // Reglas de EJEMPLO: deben validarse con AGROSAVIA, el ICA o un agrónomo
  analizarRiesgos(humedadSuelo) {
    const alertas = [];

    if (humedadSuelo > 80 || (this.humedad > 80 && this.precipitacion > 10)) {
      alertas.push(new Alerta("ANTRACNOSIS",
        "Riesgo ALTO de antracnosis: mucha humedad. Evite regar y revise el drenaje."));
    }
    if (this.temperatura >= 25 && this.temperatura <= 32 &&
        this.humedad >= 60 && this.humedad <= 85) {
      alertas.push(new Alerta("MOSCA DE LA FRUTA",
        "Condiciones favorables para la mosca de la fruta. Instale trampas y recoja la fruta caída."));
    }
    if (this.temperatura > 32 && this.humedad < 55) {
      alertas.push(new Alerta("ÁCAROS",
        "Calor y ambiente seco: posibles ácaros. Revise el envés de las hojas."));
    }
    return alertas;
  }
}

class Cultivo {
  constructor(id, tipo, ubicacion, area) {
    this.id = id;
    this.tipo = tipo;
    this.ubicacion = ubicacion;
    this.area = area;
    this.sensores = [];
    this.observaciones = [];
    this.clima = new CondicionClimatica();
  }

  agregarSensor(sensor) {
    this.sensores.push(sensor);
  }

  // Lee los sensores y devuelve las alertas de riego
  obtenerResultados() {
    const alertas = [];
    for (const sensor of this.sensores) {
      const valor = sensor.leerValor();
      if (valor < sensor.nivelCritico) {
        alertas.push(new Alerta("RIEGO",
          "Suelo muy seco (" + valor + "%) en " + this.tipo + " " + this.ubicacion + ". Se recomienda regar."));
      } else if (valor > sensor.nivelMaximo) {
        alertas.push(new Alerta("EXCESO DE AGUA",
          "Suelo saturado (" + valor + "%) en " + this.tipo + " " + this.ubicacion + ". Suspenda el riego."));
      }
    }
    return alertas;
  }

  agregarObservacion(texto) {
    this.observaciones.push(new Date().toLocaleString("es-CO") + " - " + texto);
  }

  generarReporte() {
    let texto = "REPORTE DEL CULTIVO #" + this.id + "\n";
    texto += "Tipo: " + this.tipo + "\n";
    texto += "Ubicación: " + this.ubicacion + "\n";
    texto += "Área: " + this.area + " ha\n";
    texto += "Último valor de humedad: " + this.sensores[0].valor + " %\n\n";
    texto += "Observaciones:\n";
    if (this.observaciones.length === 0) {
      texto += "  (sin observaciones)\n";
    }
    for (const obs of this.observaciones) {
      texto += "  * " + obs + "\n";
    }
    return texto;
  }
}

class Agricultor {
  constructor(id, nombre, telefono) {
    this.id = id;
    this.nombre = nombre;
    this.telefono = telefono;
    this.cultivos = [];
    this.alertas = [];
  }

  agregarCultivo(cultivo) {
    this.cultivos.push(cultivo);
  }
}


// ==============================================================
// PARTE 2: INTERFAZ (conecta las clases con la página HTML)
// ==============================================================

// Pedimos el nombre al abrir la página
let agricultor = null;   // se crea cuando el usuario inicia sesión

// Atajo para buscar elementos por su id
function $(id) { return document.getElementById(id); }

// ---------- Cambiar de pestaña ----------
const botones = document.querySelectorAll("#menu button");
for (const boton of botones) {
  boton.addEventListener("click", function () {
    for (const b of botones) { b.classList.remove("activa"); }
    for (const s of document.querySelectorAll("section")) { s.classList.remove("visible"); }
    boton.classList.add("activa");
    $(boton.dataset.tab).classList.add("visible");
  });
}

// ---------- Llenar listas desplegables de cultivos ----------
function actualizarSelects() {
  const ids = ["selHumedad", "selClima", "selReporte"];
  for (const id of ids) {
    const select = $(id);
    select.innerHTML = "";
    for (let i = 0; i < agricultor.cultivos.length; i++) {
      const c = agricultor.cultivos[i];
      const opcion = document.createElement("option");
      opcion.value = i;
      opcion.textContent = c.tipo + " - " + c.ubicacion;
      select.appendChild(opcion);
    }
  }
}

// Devuelve el cultivo elegido en un select (o null si no hay)
function obtenerCultivo(idSelect) {
  const select = $(idSelect);
  if (agricultor.cultivos.length === 0) {
    alert("Primero registre un cultivo.");
    return null;
  }
  return agricultor.cultivos[select.value];
}

// Muestra una lista de textos dentro de un <ul>
function llenarLista(idLista, textos) {
  const ul = $(idLista);
  ul.innerHTML = "";
  for (const t of textos) {
    const li = document.createElement("li");
    li.textContent = t;     // textContent es seguro: no interpreta HTML
    ul.appendChild(li);
  }
}

// ---------- 1. Registrar cultivo ----------
$("btnRegistrar").addEventListener("click", function () {
  const tipo = $("tipo").value;
  const ubicacion = $("ubicacion").value.trim();
  const area = parseFloat($("area").value.replace(",", "."));

  if (ubicacion === "") {
    alert("Escriba la ubicación del cultivo.");
    return;
  }
  if (isNaN(area) || area <= 0) {
    alert("El área debe ser un número mayor que 0.");
    return;
  }

  const id = agricultor.cultivos.length + 1;
  const cultivo = new Cultivo(id, tipo, ubicacion, area);
  cultivo.agregarSensor(new Sensor(id, "humedad_suelo", 30, 80));
  agricultor.agregarCultivo(cultivo);

  const textos = [];
  for (const c of agricultor.cultivos) {
    textos.push("#" + c.id + " " + c.tipo + " - " + c.ubicacion + " (" + c.area + " ha)");
  }
  llenarLista("listaCultivos", textos);
  actualizarSelects();

  $("ubicacion").value = "";
  $("area").value = "";
});

// ---------- 2. Leer humedad ----------
$("btnLeer").addEventListener("click", function () {
  const cultivo = obtenerCultivo("selHumedad");
  if (cultivo === null) { return; }

  const alertas = cultivo.obtenerResultados();
  const sensor = cultivo.sensores[0];
  $("valorHumedad").textContent = sensor.valor + " %";

  const estado = $("estadoHumedad");
  estado.className = "estado";
  if (sensor.valor < sensor.nivelCritico) {
    estado.textContent = "SUELO SECO";
    estado.classList.add("seco");
  } else if (sensor.valor > sensor.nivelMaximo) {
    estado.textContent = "SUELO SATURADO";
    estado.classList.add("saturado");
  } else {
    estado.textContent = "HUMEDAD NORMAL";
    estado.classList.add("normal");
  }

  const mensajes = [];
  if (alertas.length === 0) { mensajes.push("Sin alertas. La humedad está en rango normal."); }
  for (const a of alertas) {
    agricultor.alertas.push(a);
    a.enviarNotificacion();
    mensajes.push(a.mensaje);
  }
  llenarLista("listaHumedad", mensajes);
  refrescarAlertas();
});

// ---------- 3. Clima y plagas ----------
$("btnClima").addEventListener("click", function () {
  const cultivo = obtenerCultivo("selClima");
  if (cultivo === null) { return; }

  const sensor = cultivo.sensores[0];
  if (sensor.valor === 0) { sensor.leerValor(); }

  const clima = cultivo.clima;
  clima.obtenerPronostico();
  $("datosClima").textContent =
    "Temperatura: " + clima.temperatura + " °C | " +
    "Humedad del aire: " + clima.humedad + " % | " +
    "Lluvia esperada: " + clima.precipitacion + " mm | " +
    "Humedad del suelo: " + sensor.valor + " %";

  const alertas = clima.analizarRiesgos(sensor.valor);
  const mensajes = [];
  if (alertas.length === 0) { mensajes.push("Sin riesgos detectados por ahora."); }
  for (const a of alertas) {
    agricultor.alertas.push(a);
    a.enviarNotificacion();
    mensajes.push(a.tipo + ": " + a.mensaje);
  }
  llenarLista("listaRiesgos", mensajes);
  refrescarAlertas();
});

// ---------- 4. Historial de alertas ----------
function refrescarAlertas() {
  const cuerpo = $("cuerpoAlertas");
  cuerpo.innerHTML = "";
  for (const a of agricultor.alertas) {
    const fila = document.createElement("tr");
    const datos = [a.id, a.fecha, a.tipo, a.mensaje];
    for (const dato of datos) {
      const celda = document.createElement("td");
      celda.textContent = dato;
      fila.appendChild(celda);
    }
    cuerpo.appendChild(fila);
  }
  $("sinAlertas").style.display = agricultor.alertas.length === 0 ? "block" : "none";
}

// ---------- 5. Observaciones y reporte ----------
$("btnGuardarObs").addEventListener("click", function () {
  const cultivo = obtenerCultivo("selReporte");
  if (cultivo === null) { return; }

  const texto = $("observacion").value.trim();
  if (texto === "") {
    alert("Escriba una observación.");
    return;
  }
  cultivo.agregarObservacion(texto);
  $("observacion").value = "";
  $("textoReporte").textContent = cultivo.generarReporte();
});

$("btnReporte").addEventListener("click", function () {
  const cultivo = obtenerCultivo("selReporte");
  if (cultivo === null) { return; }
  $("textoReporte").textContent = cultivo.generarReporte();
});

// ==============================================================
// PARTE 3: REGISTRO E INICIO DE SESIÓN
// Los usuarios se guardan en el navegador con localStorage.
// OJO: es solo un prototipo. En un sistema real las contraseñas
// NO se guardan así: van cifradas en un servidor con base de datos.
// ==============================================================

function leerUsuarios() {
  try {
    return JSON.parse(localStorage.getItem("usuarios")) || [];
  } catch (e) {
    return [];
  }
}

function guardarUsuarios(lista) {
  try {
    localStorage.setItem("usuarios", JSON.stringify(lista));
    return true;
  } catch (e) {
    return false;
  }
}

function mostrarMensaje(idMensaje, texto, tipo) {
  const p = $(idMensaje);
  p.textContent = texto;
  p.className = "mensaje " + tipo;
}

// Cambiar entre formulario de login y de registro
$("irRegistro").addEventListener("click", function () {
  $("formLogin").style.display = "none";
  $("formRegistro").style.display = "block";
});
$("irLogin").addEventListener("click", function () {
  $("formRegistro").style.display = "none";
  $("formLogin").style.display = "block";
});

// ---------- Registrar usuario ----------
$("btnRegistroUsuario").addEventListener("click", function () {
  const nombre = $("regNombre").value.trim();
  const correo = $("regCorreo").value.trim().toLowerCase();
  const clave = $("regClave").value;
  const clave2 = $("regClave2").value;

  if (nombre === "" || correo === "" || clave === "") {
    mostrarMensaje("msgRegistro", "Complete todos los campos.", "error");
    return;
  }
  if (clave.length < 6) {
    mostrarMensaje("msgRegistro", "La contraseña debe tener mínimo 6 caracteres.", "error");
    return;
  }
  if (clave !== clave2) {
    mostrarMensaje("msgRegistro", "Las contraseñas no coinciden.", "error");
    return;
  }

  const usuarios = leerUsuarios();
  for (const u of usuarios) {
    if (u.correo === correo) {
      mostrarMensaje("msgRegistro", "Ese correo ya está registrado.", "error");
      return;
    }
  }

  usuarios.push({ id: usuarios.length + 1, nombre: nombre, correo: correo, clave: clave });
  if (!guardarUsuarios(usuarios)) {
    mostrarMensaje("msgRegistro", "No se pudo guardar el usuario en este navegador.", "error");
    return;
  }

  // Limpiamos el formulario y mandamos al login
  $("regNombre").value = "";
  $("regCorreo").value = "";
  $("regClave").value = "";
  $("regClave2").value = "";
  mostrarMensaje("msgRegistro", "", "ok");
  $("formRegistro").style.display = "none";
  $("formLogin").style.display = "block";
  mostrarMensaje("msgLogin", "Cuenta creada. Ahora inicie sesión.", "ok");
});

// ---------- Iniciar sesión ----------
$("btnLogin").addEventListener("click", function () {
  const correo = $("loginCorreo").value.trim().toLowerCase();
  const clave = $("loginClave").value;

  const usuarios = leerUsuarios();
  let encontrado = null;
  for (const u of usuarios) {
    if (u.correo === correo && u.clave === clave) {
      encontrado = u;
    }
  }

  if (encontrado === null) {
    mostrarMensaje("msgLogin", "Correo o contraseña incorrectos.", "error");
    return;
  }
  entrarAlSistema(encontrado);
});

function entrarAlSistema(usuario) {
  agricultor = new Agricultor(usuario.id, usuario.nombre, "");
  $("nombreAgricultor").textContent = "Agricultor: " + agricultor.nombre;
  $("pantallaAuth").style.display = "none";
  $("app").style.display = "block";   // aquí se muestran todas las herramientas
}

// ---------- Cerrar sesión ----------
$("btnSalir").addEventListener("click", function () {
  location.reload();   // recarga la página y vuelve al login
});
