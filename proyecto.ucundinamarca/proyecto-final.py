candidatos = {
    "ana": 0,
    "luis": 0,
    "maria": 0
}

votantes = []


def mostrar_candidatos():
    print("CANDIDATOS DISPONIBLES:")
    for nombre in candidatos:
        print(f" - {nombre}")


def votar():
    nombre_votante = input("Ingrese su nombre: ").lower()

    if nombre_votante in votantes:
        print("Usted ya ha votado. No puede hacerlo de nuevo.")
        return

    mostrar_candidatos()
    voto = input("Elija su candidato: ").lower()

    if voto in candidatos:
        candidatos[voto] += 1
        votantes.append(nombre_votante)
        print(f"Voto registrado para {voto}. ¡Gracias por participar!")
    else:
        print("Candidato no válido. Intente de nuevo.")


def mostrar_resultados():
    print("RESULTADOS ACTUALES")
    total_votos = sum(candidatos.values())
    if total_votos == 0:
        print("no hay resgistro de votos")
        return

    for nombre, voto in candidatos.items():
        porcrntaje = (voto / total_votos) * 100
        print(f"{nombre} tiene cantidad de votos {voto} el porcentaje es % {porcrntaje}")


def menu():
    while True:
        print("== VOTACION PARA EL CONSEJO ESTUDIANTIL, UCUNDUNAMARCA. ==")
        print("1. Votar")
        print("2. Ver resultados")
        print("3. salir")
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            votar()
        elif opcion == "2":
            mostrar_resultados()
        elif opcion == "3":
            print("Gracias por usar el sistema de votación.")
            break
        else:
            print("Opción inválida. Intente nuevamente.")


menu()

