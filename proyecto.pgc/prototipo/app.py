"""
Sistema inteligente de monitoreo y control agrícola
Prototipo funcional - Prototipo de Escritorio/Web (backend en Python)

Este backend implementa, en código, las entidades del diagrama de clases
del anteproyecto: Agricultor, Cultivo, Sensor, CondicionClimatica y Alerta,
y expone una API REST que consume el frontend (HTML + JavaScript).

Funcionalidades prioritarias implementadas (mínimo 3 exigidas):
  1. Monitoreo en tiempo real de humedad del suelo con alertas automáticas.
  2. Identificación de riesgo de plagas y enfermedades (antracnosis, mosca
     de la fruta, ácaros) a partir de humedad, temperatura y precipitación.
  3. Pronóstico climático local (consume la API pública gratuita Open-Meteo
     para las coordenadas de Girardot; si no hay internet, usa un modelo
     simulado como respaldo).
  4. Panel de recomendaciones y registro de observaciones del agricultor.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Coordenadas del municipio de Girardot, Cundinamarca (usadas para el clima)
# ---------------------------------------------------------------------------
GIRARDOT_LAT = 4.305
GIRARDOT_LON = -74.803

_id_counter = itertools.count(1)


def next_id() -> int:
    return next(_id_counter)


# ---------------------------------------------------------------------------
# Entidades del diagrama de clases
# ---------------------------------------------------------------------------

@dataclass
class Alerta:
    id: int
    tipo: str            # "riego" | "plaga" | "enfermedad" | "clima"
    mensaje: str
    cultivo_id: int
    severidad: str = "media"   # "baja" | "media" | "alta"
    fecha: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    atendida: bool = False

    def enviarNotificacion(self) -> dict:
        """Simula el envío de la notificación al agricultor."""
        return {"enviado": True, "canal": "panel-web", "alerta": self.to_dict()}

    def marcarResultado(self, atendida: bool = True) -> None:
        self.atendida = atendida

    def to_dict(self) -> dict:
        return {
            "id": self.id, "tipo": self.tipo, "mensaje": self.mensaje,
            "cultivo_id": self.cultivo_id, "severidad": self.severidad,
            "fecha": self.fecha, "atendida": self.atendida,
        }


@dataclass
class Sensor:
    id: int
    cultivo_id: int
    tipo: str = "humedad_suelo"
    valor: float = 0.0
    nivel_critico_bajo: float = 30.0   # % por debajo -> falta de agua
    nivel_critico_alto: float = 85.0   # % por encima -> exceso de humedad
    historial: list = field(default_factory=list)

    def leerValor(self) -> float:
        """
        Simula la lectura de un sensor físico de humedad del suelo
        (en un despliegue real este método leería un Arduino/Raspberry Pi
        por puerto serie o MQTT). Se genera una variación suave alrededor
        del último valor para simular un sensor real.
        """
        base = self.valor if self.historial else random.uniform(45, 65)
        variacion = random.uniform(-6, 6)
        nuevo_valor = max(5.0, min(100.0, base + variacion))
        self.valor = round(nuevo_valor, 1)
        self.historial.append({
            "valor": self.valor,
            "fecha": datetime.now().isoformat(timespec="seconds"),
        })
        self.historial = self.historial[-30:]  # conserva las últimas 30 lecturas
        return self.valor

    def enviarDatos(self) -> dict:
        return {
            "id": self.id, "cultivo_id": self.cultivo_id, "tipo": self.tipo,
            "valor": self.valor, "nivel_critico_bajo": self.nivel_critico_bajo,
            "nivel_critico_alto": self.nivel_critico_alto,
            "historial": self.historial,
        }


@dataclass
class CondicionClimatica:
    temperatura: float = 0.0
    humedad: float = 0.0
    precipitacion: float = 0.0

    @staticmethod
    def obtenerPronostico(lat: float = GIRARDOT_LAT, lon: float = GIRARDOT_LON) -> list[dict]:
        """
        Obtiene el pronóstico climático local para los próximos 3 días
        usando la API pública y gratuita Open-Meteo (sin necesidad de
        API key). Si no hay conexión a internet, cae a un modelo simulado
        representativo del clima cálido y estacionalmente lluvioso de
        Girardot, para que el prototipo nunca deje de funcionar.
        """
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                "&hourly=temperature_2m,relative_humidity_2m,precipitation"
                "&forecast_days=3&timezone=America%2FBogota"
            )
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()["hourly"]

            por_dia: dict[str, dict] = {}
            for i, hora in enumerate(data["time"]):
                dia = hora[:10]
                registro = por_dia.setdefault(dia, {"temps": [], "hums": [], "precs": []})
                registro["temps"].append(data["temperature_2m"][i])
                registro["hums"].append(data["relative_humidity_2m"][i])
                registro["precs"].append(data["precipitation"][i])

            pronostico = []
            for dia, r in list(por_dia.items())[:3]:
                pronostico.append({
                    "fecha": dia,
                    "temperatura": round(sum(r["temps"]) / len(r["temps"]), 1),
                    "humedad": round(sum(r["hums"]) / len(r["hums"]), 1),
                    "precipitacion": round(sum(r["precs"]), 1),
                    "fuente": "open-meteo",
                })
            return pronostico
        except Exception:
            hoy = datetime.now()
            pronostico = []
            for i in range(3):
                fecha = (hoy + timedelta(days=i)).strftime("%Y-%m-%d")
                pronostico.append({
                    "fecha": fecha,
                    "temperatura": round(random.uniform(27, 34), 1),
                    "humedad": round(random.uniform(55, 85), 1),
                    "precipitacion": round(random.uniform(0, 15), 1),
                    "fuente": "simulado (sin conexión a internet)",
                })
            return pronostico

    @staticmethod
    def analizarRiesgos(humedad_suelo: float, clima: dict) -> list[dict]:
        """
        Reglas de negocio para identificar el riesgo de plagas y
        enfermedades a partir de la humedad del suelo (sensor) y las
        condiciones climáticas (temperatura, humedad ambiental,
        precipitación). Basado en las condiciones descritas en el
        anteproyecto para antracnosis, mosca de la fruta y ácaros.
        """
        riesgos = []
        temp = clima.get("temperatura", 0)
        hum_amb = clima.get("humedad", 0)
        precip = clima.get("precipitacion", 0)

        if hum_amb >= 75 and precip >= 4 and 20 <= temp <= 30 and humedad_suelo >= 70:
            riesgos.append({
                "tipo": "enfermedad", "nombre": "Antracnosis (Colletotrichum spp.)",
                "severidad": "alta",
                "recomendacion": "Reducir el riego, mejorar el drenaje y aplicar "
                                  "control preventivo; alta humedad y lluvias "
                                  "favorecen la aparición del hongo.",
            })
        if 24 <= temp <= 30 and 50 <= hum_amb <= 78:
            riesgos.append({
                "tipo": "plaga", "nombre": "Mosca de la fruta (Anastrepha obliqua)",
                "severidad": "media",
                "recomendacion": "Instalar trampas de monitoreo y revisar frutos "
                                  "en maduración; el rango de temperatura actual "
                                  "favorece su actividad.",
            })
        if temp >= 30 and hum_amb <= 45:
            riesgos.append({
                "tipo": "plaga", "nombre": "Ácaros",
                "severidad": "media",
                "recomendacion": "Vigilar el envés de las hojas; el calor y la "
                                  "baja humedad ambiental favorecen su proliferación.",
            })
        if not riesgos:
            riesgos.append({
                "tipo": "info", "nombre": "Sin riesgo relevante detectado",
                "severidad": "baja",
                "recomendacion": "Las condiciones actuales no coinciden con los "
                                  "patrones de riesgo conocidos. Continuar el "
                                  "monitoreo habitual.",
            })
        return riesgos


@dataclass
class Cultivo:
    id: int
    tipo: str            # "mango" | "limon"
    ubicacion: str
    area: float
    agricultor_id: int
    sensor: Sensor = None  # type: ignore
    alertas: list = field(default_factory=list)
    observaciones: list = field(default_factory=list)

    def obtenerResultados(self) -> dict:
        return {
            "cultivo": self.to_dict(),
            "sensor": self.sensor.enviarDatos() if self.sensor else None,
            "alertas": [a.to_dict() for a in self.alertas],
        }

    def generarReporte(self) -> dict:
        total_alertas = len(self.alertas)
        atendidas = sum(1 for a in self.alertas if a.atendida)
        return {
            "cultivo_id": self.id,
            "tipo": self.tipo,
            "total_lecturas": len(self.sensor.historial) if self.sensor else 0,
            "total_alertas": total_alertas,
            "alertas_atendidas": atendidas,
            "observaciones_registradas": len(self.observaciones),
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id, "tipo": self.tipo, "ubicacion": self.ubicacion,
            "area": self.area, "agricultor_id": self.agricultor_id,
        }


@dataclass
class Agricultor:
    id: int
    nombre: str
    telefono: str
    cultivos: list = field(default_factory=list)

    def registrar(self, cultivo: Cultivo) -> None:
        self.cultivos.append(cultivo)

    def verReportes(self) -> list[dict]:
        return [c.generarReporte() for c in self.cultivos]

    def to_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "telefono": self.telefono}


# ---------------------------------------------------------------------------
# "Base de datos" en memoria (suficiente para el prototipo del semestre;
# el repositorio en la nube / persistencia real es un entregable aparte).
# ---------------------------------------------------------------------------

agricultor = Agricultor(id=next_id(), nombre="Agricultor Girardot", telefono="3000000000")

_cultivos_semilla = [
    ("mango", "Vereda La Marina, Girardot", 1.5),
    ("limon", "Vereda Chicalá, Girardot", 0.8),
]
cultivos: dict[int, Cultivo] = {}
for tipo, ubicacion, area in _cultivos_semilla:
    cid = next_id()
    sensor = Sensor(id=next_id(), cultivo_id=cid)
    sensor.leerValor()
    cultivo = Cultivo(id=cid, tipo=tipo, ubicacion=ubicacion, area=area,
                       agricultor_id=agricultor.id, sensor=sensor)
    agricultor.registrar(cultivo)
    cultivos[cid] = cultivo


def get_cultivo_or_404(cultivo_id: int) -> Optional[Cultivo]:
    return cultivos.get(cultivo_id)


# ---------------------------------------------------------------------------
# Rutas de páginas
# ---------------------------------------------------------------------------

from flask import render_template  # noqa: E402


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# API REST
# ---------------------------------------------------------------------------

@app.route("/api/agricultor")
def api_agricultor():
    return jsonify(agricultor.to_dict())


@app.route("/api/cultivos", methods=["GET", "POST"])
def api_cultivos():
    if request.method == "POST":
        data = request.get_json(force=True)
        cid = next_id()
        sensor = Sensor(id=next_id(), cultivo_id=cid)
        sensor.leerValor()
        cultivo = Cultivo(
            id=cid,
            tipo=data.get("tipo", "mango"),
            ubicacion=data.get("ubicacion", "Girardot"),
            area=float(data.get("area", 0) or 0),
            agricultor_id=agricultor.id,
            sensor=sensor,
        )
        agricultor.registrar(cultivo)
        cultivos[cid] = cultivo
        return jsonify(cultivo.to_dict()), 201

    return jsonify([c.to_dict() for c in cultivos.values()])


@app.route("/api/cultivos/<int:cultivo_id>/sensor")
def api_sensor(cultivo_id: int):
    """Funcionalidad 1: monitoreo en tiempo real de humedad del suelo."""
    cultivo = get_cultivo_or_404(cultivo_id)
    if not cultivo:
        return jsonify({"error": "Cultivo no encontrado"}), 404

    valor = cultivo.sensor.leerValor()
    alerta_generada = None

    if valor < cultivo.sensor.nivel_critico_bajo:
        a = Alerta(id=next_id(), tipo="riego",
                    mensaje=f"Humedad del suelo baja ({valor}%). Se recomienda regar el cultivo.",
                    cultivo_id=cultivo_id, severidad="alta")
        a.enviarNotificacion()
        cultivo.alertas.append(a)
        alerta_generada = a.to_dict()
    elif valor > cultivo.sensor.nivel_critico_alto:
        a = Alerta(id=next_id(), tipo="riego",
                    mensaje=f"Exceso de humedad en el suelo ({valor}%). Reducir el riego para evitar hongos.",
                    cultivo_id=cultivo_id, severidad="alta")
        a.enviarNotificacion()
        cultivo.alertas.append(a)
        alerta_generada = a.to_dict()

    return jsonify({"sensor": cultivo.sensor.enviarDatos(), "alerta_generada": alerta_generada})


@app.route("/api/clima")
def api_clima():
    """Funcionalidad 3: pronóstico climático local (Girardot)."""
    pronostico = CondicionClimatica.obtenerPronostico()
    return jsonify(pronostico)


@app.route("/api/cultivos/<int:cultivo_id>/riesgo")
def api_riesgo(cultivo_id: int):
    """Funcionalidad 2: identificación de riesgo de plagas y enfermedades."""
    cultivo = get_cultivo_or_404(cultivo_id)
    if not cultivo:
        return jsonify({"error": "Cultivo no encontrado"}), 404

    pronostico = CondicionClimatica.obtenerPronostico()
    clima_hoy = pronostico[0] if pronostico else {"temperatura": 0, "humedad": 0, "precipitacion": 0}
    riesgos = CondicionClimatica.analizarRiesgos(cultivo.sensor.valor, clima_hoy)

    nuevas_alertas = []
    for riesgo in riesgos:
        if riesgo["severidad"] in ("alta", "media") and riesgo["tipo"] != "info":
            a = Alerta(id=next_id(), tipo=riesgo["tipo"],
                        mensaje=f"{riesgo['nombre']}: {riesgo['recomendacion']}",
                        cultivo_id=cultivo_id, severidad=riesgo["severidad"])
            a.enviarNotificacion()
            cultivo.alertas.append(a)
            nuevas_alertas.append(a.to_dict())

    return jsonify({"clima_usado": clima_hoy, "riesgos": riesgos, "nuevas_alertas": nuevas_alertas})


@app.route("/api/cultivos/<int:cultivo_id>/alertas")
def api_alertas(cultivo_id: int):
    cultivo = get_cultivo_or_404(cultivo_id)
    if not cultivo:
        return jsonify({"error": "Cultivo no encontrado"}), 404
    return jsonify([a.to_dict() for a in reversed(cultivo.alertas)])


@app.route("/api/alertas/<int:alerta_id>/marcar", methods=["POST"])
def api_marcar_alerta(alerta_id: int):
    for cultivo in cultivos.values():
        for a in cultivo.alertas:
            if a.id == alerta_id:
                a.marcarResultado(True)
                return jsonify(a.to_dict())
    return jsonify({"error": "Alerta no encontrada"}), 404


@app.route("/api/cultivos/<int:cultivo_id>/observaciones", methods=["GET", "POST"])
def api_observaciones(cultivo_id: int):
    cultivo = get_cultivo_or_404(cultivo_id)
    if not cultivo:
        return jsonify({"error": "Cultivo no encontrado"}), 404

    if request.method == "POST":
        data = request.get_json(force=True)
        obs = {
            "texto": data.get("texto", "").strip(),
            "fecha": datetime.now().isoformat(timespec="seconds"),
        }
        if obs["texto"]:
            cultivo.observaciones.append(obs)
        return jsonify(obs), 201

    return jsonify(list(reversed(cultivo.observaciones)))


@app.route("/api/cultivos/<int:cultivo_id>/reporte")
def api_reporte(cultivo_id: int):
    """Panel de recomendaciones: reporte consolidado de un cultivo."""
    cultivo = get_cultivo_or_404(cultivo_id)
    if not cultivo:
        return jsonify({"error": "Cultivo no encontrado"}), 404
    return jsonify(cultivo.obtenerResultados())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
