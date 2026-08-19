from datetime import datetime, timedelta
from config import RUTA_REPARACIONES, RUTA_HERRAMIENTAS, DIAS_REPARACION, ESTADO_ACTIVA, ESTADO_REPARACION, ESTADOS_REPARACION
from modulos import almacenamiento
from modulos import utilidades
from modulos import logs
from modulos import permisos



def registrar_reparacion(usuario):
    if not permisos.requiere_admin(usuario):
        return

    reparaciones = almacenamiento.cargar(RUTA_REPARACIONES)
    herramientas = almacenamiento.cargar(RUTA_HERRAMIENTAS)

    if len(herramientas) == 0:
        print("\nNo hay herramientas en reparacion.")
        return

    print("\n--- HERRAMIENTAS EN REPARACION ---")
    for h in herramientas:
        print(str(h["id"]) + ". " + h["nombre"] +
              " | cantidad: " + str(h["cantidad"]) +
              " | " + h["estado"])


    id_herramienta = utilidades.pedir_entero("\nId de la herramienta: ", 1)
    herramienta = utilidades.buscar_por_id(herramientas, id_herramienta)

    if herramienta is None:
        print("Herramienta no encontrada con ese id.")
        logs.error("Reparacion fallida: herramienta no encontrada con id: " + str(id_herramienta))
        return

    if herramienta["estado"] == ESTADO_REPARACION:
        print("La herramienta " + herramienta["nombre"] + " ya se encuentra en reparacion.")
        logs.advertencia("Reparacion duplicada: herramienta ya en reparacion: " + herramienta["nombre"])
        return

    dias = utilidades.pedir_entero("Dias estimados de reparacion " + str(DIAS_REPARACION) + " por defecto, 0 para usarlo: ", 0)

    if dias == 0:
        dias = DIAS_REPARACION

    observaciones = input("Observaciones de la reparacion: ").strip()
    if observaciones == "":
        observaciones = "Sin observaciones"


    hoy = datetime.now()
    fecha_inicio = hoy.strftime("%Y-%m-%d")
    fecha_estimada = (hoy + timedelta(days=dias)).strftime("%Y-%m-%d")

    reparacion = {
        "id": utilidades.generar_id(reparaciones),
        "herramienta_id": herramienta["id"],
        "nombre": herramienta["nombre"],
        "fecha_inicio": fecha_inicio,
        "fecha_estimada": fecha_estimada,
        "fecha_finalizacion": None,
        "estado": ESTADOS_REPARACION[0],
        "observaciones": observaciones
    }

    estado_anterior = herramienta["estado"]
    herramienta["estado"] = ESTADO_REPARACION

    reparaciones.append(reparacion)
    almacenamiento.guardar(RUTA_REPARACIONES, reparaciones)
    almacenamiento.guardar(RUTA_HERRAMIENTAS, herramientas)

    print("Reparacion #" + str(reparacion["id"]) + " registrada")
    print(herramienta["nombre"] + " ahora se encuentra en reparacion.")
    print("Fecha estimada de finalizacion: " + fecha_estimada)
    logs.info("Reparacion #" + str(reparacion["id"]) + " de '" + herramienta["nombre"] + "' iniciada, en reparacion hasta " + fecha_estimada, usuario=usuario["id"])



def ya_cumplio_plazo(reparacion):
    if reparacion["estado"] != ESTADOS_REPARACION[0]:
        return False

    hoy = datetime.now().strftime("%Y-%m-%d")
    return reparacion["fecha_estimada"] <= hoy



def mostrar_una(r):
    if r["fecha_finalizacion"] is None:
        cierre = "pendiente"
    else:
        cierre = "finalizada el " + r["fecha_finalizacion"]

    linea = ("#" + str(r["id"]) +
              " | " + r["nombre"] +
              " | id herramienta: " + str(r["herramienta_id"]) +
              " | inicio: " + r["fecha_inicio"] +
                " | estimada: " + r["fecha_estimada"] +
                " | " + cierre +
                " | obs: " + r["observaciones"])

    if r["estado"] == ESTADOS_REPARACION[0] and ya_cumplio_plazo(r):
        linea = linea + "## PLAZO CUMPLIDO ##"

    print(linea)



def listar_reparaciones():
    reparaciones = almacenamiento.cargar(RUTA_REPARACIONES)

    if len(reparaciones) == 0:
        print("\nNo hay reparaciones registradas.")
        return

    abiertas = []
    cerradas = []
    for r in reparaciones:
        if r["estado"] == ESTADOS_REPARACION[0]:
            abiertas.append(r)
        else:
            cerradas.append(r)

    print("\n--- EN REPARACION (" + str(len(abiertas)) + ") ---")
    if len(abiertas) == 0:
        print("Ninguna.")
    else:
        for r in abiertas:
            mostrar_una(r)

    print("\n--- FINALIZADAS (" + str(len(cerradas)) + ") ---")
    if len(cerradas) == 0:
        print("Ninguna.")
    else:
        for r in cerradas:
            mostrar_una(r)



def cerrar_reparacion(reparacion, herramientas):
    reparacion["estado"] = ESTADOS_REPARACION[1]
    reparacion["fecha_finalizacion"] = datetime.now().strftime("%Y-%m-%d")

    herramienta = utilidades.buscar_por_id(herramientas, reparacion["herramienta_id"])

    if herramienta is None:
        logs.advertencia("Reparacion finalizada pero no se encontro la herramienta con id: " + str(reparacion["herramienta_id"]))
        return False

    herramienta["estado"] = ESTADO_ACTIVA
    return True


def finalizar_reparacion(usuario): #solo el admin puedfeee

    if not permisos.requiere_admin(usuario):
        return

    reparaciones = almacenamiento.cargar(RUTA_REPARACIONES)
    herramientas = almacenamiento.cargar(RUTA_HERRAMIENTAS)

    abiertas = []
    for r in reparaciones:
        if r["estado"] == ESTADOS_REPARACION[0]:
            abiertas.append(r)

    if len(abiertas) == 0:
        print("\nNo hay herramientas en reparacion.")
        return

    print("\n--- REPARACIONES ABIERTAS ---")
    for r in abiertas:
        mostrar_una(r)

    id_reparacion = utilidades.pedir_entero("\nId de la reparacion a finalizar: ", 1)
    reparacion = utilidades.buscar_por_id(reparaciones, id_reparacion)

    if reparacion is None:
        print("\U0000274C No existe una reparacion con ese id.")
        logs.error("Cierre fallido: reparacion inexistente id " + str(id_reparacion),
                   usuario=usuario["id"])
        return

    if reparacion["estado"] != ESTADOS_REPARACION[0]:
        print("Esa reparacion ya fue finalizada el " + str(reparacion["fecha_finalizacion"]) + ".")
        return

    nota = input("Observacion de cierre (opcional): ").strip()
    if nota != "":
        reparacion["observaciones"] = reparacion["observaciones"] + " | Cierre: " + nota

    encontrada = cerrar_reparacion(reparacion, herramientas)

    almacenamiento.guardar(RUTA_REPARACIONES, reparaciones)
    almacenamiento.guardar(RUTA_HERRAMIENTAS, herramientas)

    print("\n\U00002705 Reparacion #" + str(id_reparacion) + " finalizada.")
    if encontrada:
        print("'" + reparacion["nombre"] + "' vuelve a estar disponible (estado " +
              ESTADO_ACTIVA + ").")
    else:
        print("La herramienta asociada ya no existe en el inventario.")

    logs.info("Reparacion #" + str(id_reparacion) + " finalizada: '" +
              reparacion["nombre"] + "' vuelve a " + ESTADO_ACTIVA,
              usuario=usuario["id"])


def revisar_vencidas(silencioso=False):
    reparaciones = almacenamiento.cargar(RUTA_REPARACIONES)
    herramientas = almacenamiento.cargar(RUTA_HERRAMIENTAS)

    cerradas = 0
    for r in reparaciones:
        if ya_cumplio_plazo(r):
            cerrar_reparacion(r, herramientas)
            logs.info("Reparacion #" + str(r["id"]) + " finalizada automaticamente por vencimiento de plazo: '" + r["nombre"] + "' vuelve a " + ESTADO_ACTIVA)
            cerradas += 1

    if cerradas > 0:
        almacenamiento.guardar(RUTA_REPARACIONES, reparaciones)
        almacenamiento.guardar(RUTA_HERRAMIENTAS, herramientas)

    if not silencioso:
        if cerradas == 0:
            print("\nNo hay reparaciones vencidas.")
        else:
            print(str(cerradas) + " herramientas volvieron a estar disponibles.")

    return cerradas