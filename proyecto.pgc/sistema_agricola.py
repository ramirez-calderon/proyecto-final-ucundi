import random
from datetime import datetime

# esta es la alerta
class Alerta:
    contador = 0  

    def __init__(self, tipo, mensaje):
        Alerta.contador += 1
        self.id = Alerta.contador
        self.tipo = tipo          # "RIEGO", "ANTRACNOSIS", "PLAGA", etc.
        self.mensaje = mensaje
        self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    def enviar_notificacion(self):
        # Por ahora solo imprime. Luego podría enviar un SMS o WhatsApp.
        print(f"  [ALERTA #{self.id} - {self.tipo}] {self.mensaje}")

# la clase sensor

class Sensor:
    def __init__(self, id, tipo, nivel_critico, nivel_maximo):
        self.id = id
        self.tipo = tipo                   
        self.valor = 0.0                    
        self.nivel_critico = nivel_critico  
        self.nivel_maximo = nivel_maximo    

    def leer_valor(self):
        # Simulamos la lectura del sensor con un número aleatorio
        self.valor = round(random.uniform(10, 95), 1)
        return self.valor

    def enviar_datos(self):
        return {"sensor": self.id, "tipo": self.tipo, "valor": self.valor}


# la clase condicion climatica

class CondicionClimatica:
    def __init__(self):
        self.temperatura = 0.0   
        self.humedad = 0.0        
        self.precipitacion = 0.0  

    def obtener_pronostico(self):
        self.temperatura = round(random.uniform(24, 37), 1)
        self.humedad = round(random.uniform(40, 95), 1)
        self.precipitacion = round(random.uniform(0, 30), 1)

    def analizar_riesgos(self, humedad_suelo):
        """Devuelve una lista de alertas según clima y humedad del suelo.
        OJO: las reglas son de ejemplo. Deben validarse con datos
        de AGROSAVIA / ICA o con un ingeniero agrónomo."""
        alertas = []


        if humedad_suelo > 80 or (self.humedad > 80 and self.precipitacion > 10):
            alertas.append(Alerta(
                "ANTRACNOSIS",
                "Riesgo ALTO de antracnosis: mucha humedad. "
                "Evite regar y revise el drenaje del suelo."))


        if 25 <= self.temperatura <= 32 and 60 <= self.humedad <= 85:
            alertas.append(Alerta(
                "MOSCA DE LA FRUTA",
                "Condiciones favorables para la mosca de la fruta. "
                "Instale trampas y recoja la fruta caída."))


        if self.temperatura > 32 and self.humedad < 55:
            alertas.append(Alerta(
                "ACAROS",
                "Calor y ambiente seco: posible aparición de ácaros. "
                "Revise el envés de las hojas."))

        return alertas

# la clase cultivo

class Cultivo:
    def __init__(self, id, tipo, ubicacion, area):
        self.id = id
        self.tipo = tipo            
        self.ubicacion = ubicacion
        self.area = area            
        self.sensores = []
        self.observaciones = []     
        self.clima = CondicionClimatica()

    def agregar_sensor(self, sensor):
        self.sensores.append(sensor)

    def obtener_resultados(self):
        """Lee los sensores y devuelve las alertas de riego."""
        alertas = []
        for sensor in self.sensores:
            valor = sensor.leer_valor()
            print(f"  Sensor {sensor.id} ({sensor.tipo}): {valor}%")

            if valor < sensor.nivel_critico:
                alertas.append(Alerta(
                    "RIEGO",
                    f"Suelo muy seco ({valor}%) en {self.tipo} '{self.ubicacion}'. "
                    "Se recomienda regar."))
            elif valor > sensor.nivel_maximo:
                alertas.append(Alerta(
                    "EXCESO DE AGUA",
                    f"Suelo saturado ({valor}%) en {self.tipo} '{self.ubicacion}'. "
                    "Suspenda el riego."))
        return alertas

    def agregar_observacion(self, texto):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.observaciones.append(f"{fecha} - {texto}")

    def generar_reporte(self):
        print("-" * 50)
        print(f"REPORTE DEL CULTIVO #{self.id}")
        print(f"Tipo: {self.tipo} | Ubicación: {self.ubicacion} | Área: {self.area} ha")
        print(f"Sensores instalados: {len(self.sensores)}")
        for sensor in self.sensores:
            print(f"  - Sensor {sensor.id}: último valor {sensor.valor}%")
        print("Observaciones del agricultor:")
        if len(self.observaciones) == 0:
            print("  (sin observaciones)")
        for obs in self.observaciones:
            print(f"  * {obs}")
        print("-" * 50)


# la clase agricultor

class Agricultor:
    def __init__(self, id, nombre, telefono):
        self.id = id
        self.nombre = nombre
        self.telefono = telefono
        self.cultivos = []
        self.alertas = []

    def registrar(self):
        print(f"Agricultor registrado: {self.nombre} (tel. {self.telefono})")

    def agregar_cultivo(self, cultivo):
        self.cultivos.append(cultivo)

    def ver_reportes(self):
        if len(self.cultivos) == 0:
            print("Aún no tiene cultivos registrados.")
        for cultivo in self.cultivos:
            cultivo.generar_reporte()


# funciones de ayudapara el menu

def pedir_numero(mensaje):
    """Pide un número y repite hasta que el usuario escriba uno válido."""
    while True:
        texto = input(mensaje).replace(",", ".")
        try:
            numero = float(texto)
            if numero > 0:
                return numero
            print("Escriba un número mayor que 0.")
        except ValueError:
            print("Eso no es un número. Intente de nuevo.")


def elegir_cultivo(agricultor):
    """Muestra los cultivos y devuelve el que elija el usuario."""
    if len(agricultor.cultivos) == 0:
        print("Primero debe registrar un cultivo (opción 1).")
        return None

    print("Sus cultivos:")
    for i, c in enumerate(agricultor.cultivos):
        print(f"  {i + 1}. {c.tipo} - {c.ubicacion}")

    opcion = input("Elija el número del cultivo: ")
    if opcion.isdigit() and 1 <= int(opcion) <= len(agricultor.cultivos):
        return agricultor.cultivos[int(opcion) - 1]

    print("Opción no válida.")
    return None


def registrar_cultivo(agricultor):
    print("\n--- REGISTRAR CULTIVO ---")
    tipo = ""
    while tipo not in ("mango", "limon"):
        tipo = input("Tipo de cultivo (mango / limon): ").lower().strip()
        tipo = tipo.replace("ó", "o")

    ubicacion = input("Ubicación o nombre de la finca/vereda: ")
    area = pedir_numero("Área en hectáreas: ")

    id_cultivo = len(agricultor.cultivos) + 1
    cultivo = Cultivo(id_cultivo, tipo, ubicacion, area)


    cultivo.agregar_sensor(Sensor(id_cultivo, "humedad_suelo", 30, 80))
    agricultor.agregar_cultivo(cultivo)
    print("Cultivo registrado con un sensor de humedad.")


def monitorear_humedad(agricultor):
    print("\n--- MONITOREO DE HUMEDAD ---")
    cultivo = elegir_cultivo(agricultor)
    if cultivo is None:
        return

    alertas = cultivo.obtener_resultados()
    if len(alertas) == 0:
        print("  Humedad en rango normal. No hay alertas de riego.")
    for alerta in alertas:
        agricultor.alertas.append(alerta)
        alerta.enviar_notificacion()


def ver_pronostico(agricultor):
    print("\n--- PRONÓSTICO Y RIESGO DE PLAGAS ---")
    cultivo = elegir_cultivo(agricultor)
    if cultivo is None:
        return

    sensor = cultivo.sensores[0]
    if sensor.valor == 0:
        sensor.leer_valor()

    clima = cultivo.clima
    clima.obtener_pronostico()
    print(f"  Temperatura: {clima.temperatura} °C")
    print(f"  Humedad del aire: {clima.humedad} %")
    print(f"  Lluvia esperada: {clima.precipitacion} mm")
    print(f"  Humedad del suelo: {sensor.valor} %")

    alertas = clima.analizar_riesgos(sensor.valor)
    if len(alertas) == 0:
        print("  Sin riesgos detectados por ahora.")
    for alerta in alertas:
        agricultor.alertas.append(alerta)
        alerta.enviar_notificacion()


def ver_alertas(agricultor):
    print("\n--- HISTORIAL DE ALERTAS ---")
    if len(agricultor.alertas) == 0:
        print("No hay alertas registradas.")
    for alerta in agricultor.alertas:
        print(f"  #{alerta.id} [{alerta.fecha}] {alerta.tipo}: {alerta.mensaje}")


def registrar_observacion(agricultor):
    print("\n--- REGISTRAR OBSERVACIÓN ---")
    cultivo = elegir_cultivo(agricultor)
    if cultivo is None:
        return
    texto = input("Escriba su observación: ")
    cultivo.agregar_observacion(texto)
    print("Observación guardada.")


# este es el programa principal

def main():
    print("=" * 50)
    print(" SISTEMA DE MONITOREO AGRÍCOLA - MANGO Y LIMÓN")
    print(" Girardot, Cundinamarca")
    print("=" * 50)

    nombre = input("Nombre del agricultor: ")
    telefono = input("Teléfono: ")
    agricultor = Agricultor(1, nombre, telefono)
    agricultor.registrar()

    while True:
        print("\n========== MENÚ ==========")
        print("1. Registrar cultivo")
        print("2. Monitorear humedad del suelo")
        print("3. Ver pronóstico y riesgo de plagas")
        print("4. Ver historial de alertas")
        print("5. Registrar observación")
        print("6. Ver reportes")
        print("0. Salir")
        opcion = input("Elija una opción: ")

        if opcion == "1":
            registrar_cultivo(agricultor)
        elif opcion == "2":
            monitorear_humedad(agricultor)
        elif opcion == "3":
            ver_pronostico(agricultor)
        elif opcion == "4":
            ver_alertas(agricultor)
        elif opcion == "5":
            registrar_observacion(agricultor)
        elif opcion == "6":
            agricultor.ver_reportes()
        elif opcion == "0":
            print("Hasta luego. ¡Buenas cosechas!")
            break
        else:
            print("Opción no válida.")


# Esto hace que main() se ejecute solo si corremos este archivo directamente
if __name__ == "__main__":
    main()
