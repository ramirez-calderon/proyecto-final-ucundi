# AgroGirardot — Prototipo funcional (avance)

Prototipo del **Sistema inteligente de monitoreo y control agrícola para los
cultivos de mango y limón en el municipio de Girardot**.

- **Backend:** Python + Flask (implementa las clases del diagrama: `Agricultor`,
  `Cultivo`, `Sensor`, `CondicionClimatica`, `Alerta`) y expone una API REST.
- **Frontend:** HTML + CSS + JavaScript (sin frameworks), consumiendo la API
  con `fetch`.

## Funcionalidades incluidas (mínimo 3 exigidas)

1. **Monitoreo de humedad del suelo en tiempo real**, con alertas automáticas
   cuando el valor está muy bajo (falta de riego) o muy alto (riesgo de
   hongos).
2. **Identificación de riesgo de plagas y enfermedades** (antracnosis, mosca
   de la fruta, ácaros) combinando la lectura del sensor con el clima.
3. **Pronóstico climático local** para Girardot, usando la API pública y
   gratuita [Open-Meteo](https://open-meteo.com/) (sin necesidad de API key).
   Si no hay conexión a internet, el sistema usa un modelo simulado de
   respaldo para que el prototipo nunca deje de funcionar.
4. **Panel de recomendaciones y registro de observaciones** del agricultor.

No usa hardware físico (Arduino/Raspberry Pi) todavía: el sensor de humedad
se **simula** en `app.py` (método `Sensor.leerValor()`), dejando ese punto
listo para conectarse a un sensor real más adelante si el proyecto lo requiere.

## Cómo ejecutarlo

Necesitas **Python 3.9+** instalado.

```bash
# 1. Entra a la carpeta del proyecto
cd prototipo

# 2. (Recomendado) crea un entorno virtual
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 3. Instala las dependencias
pip install -r requirements.txt

# 4. Ejecuta el servidor
python app.py
```

Luego abre tu navegador en **http://127.0.0.1:5000**

## Estructura del proyecto

```
prototipo/
├── app.py                  # Backend Flask + clases del diagrama + API REST
├── requirements.txt
├── templates/
│   └── index.html          # Estructura del panel web
└── static/
    ├── css/style.css       # Estilos del panel
    └── js/app.js           # Lógica del frontend (fetch a la API)
```

## Próximos pasos sugeridos

- Reemplazar el sensor simulado por uno físico (Arduino/Raspberry Pi) leyendo
  por serial o MQTT.
- Persistir los datos en una base de datos real (hoy están en memoria) y
  subir el repositorio a la nube (GitHub, por ejemplo).
- Afinar las reglas de `analizarRiesgos()` con datos históricos reales de
  Girardot en vez de los rangos usados en este avance.
