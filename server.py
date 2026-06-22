from typing import Any
import re
import json
import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("qaLabMcp")

@mcp.tool()
def validar_cliente(cip: str, telefono: str, email: str) -> dict[str, Any]:
    """Valida y normaliza datos básicos de un cliente."""
    errores = []
    telefono_limpio = re.sub(r"\D", "", telefono or "")

    if len((cip or "").strip()) < 3:
        errores.append("CIP inválido")
    if len(telefono_limpio) < 7:
        errores.append("Teléfono inválido")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""):
        errores.append("Correo inválido")

    return {
        "valido": not errores,
        "errores": errores,
        "datos": {
            "cip": (cip or "").strip(),
            "telefono": telefono_limpio,
            "email": (email or "").strip().lower(),
        },
    }

@mcp.tool()
def generar_caso_prueba(endpoint: str, metodo: str, escenario: str) -> dict:
    """Genera un caso de prueba funcional básico."""
    return {
        "titulo": f"Validar {metodo.upper()} {endpoint}",
        "escenario": escenario,
        "pasos": [
            "Preparar datos",
            "Enviar la petición",
            "Validar código y respuesta",
        ],
    }

@mcp.tool()
def calcular_percentil_simple(valores: list[float], percentil: float) -> dict:
    """Calcula un percentil simple."""
    if not valores or not 0 <= percentil <= 100:
        return {"error": "Datos inválidos"}
    ordenados = sorted(valores)
    indice = round((percentil / 100) * (len(ordenados) - 1))
    return {"percentil": percentil, "valor": ordenados[indice]}

@mcp.tool()
def clasificar_error_http(status_code: int) -> dict:
    """Clasifica un código HTTP en su categoría."""
    if 200 <= status_code < 300:
        categoria = "Éxito"
    elif 300 <= status_code < 400:
        categoria = "Redirección"
    elif 400 <= status_code < 500:
        categoria = "Error del cliente"
    elif 500 <= status_code < 600:
        categoria = "Error del servidor"
    else:
        categoria = "Código inválido"

    return {"status_code": status_code, "categoria": categoria}

@mcp.tool()
def evaluar_sla(p95_ms: float, limite_ms: float) -> dict:
    """Evalúa si un p95 cumple un límite de SLA."""
    diferencia = limite_ms - p95_ms
    return {
        "p95_ms": p95_ms,
        "limite_ms": limite_ms,
        "cumple": p95_ms <= limite_ms,
        "diferencia_ms": diferencia,
    }

@mcp.tool()
def validar_respuesta_api(
    status_code: int, tiempo_ms: float, limite_ms: float, tiene_token: bool
) -> dict:
    """Valida una respuesta de API según código, tiempo y token."""
    es_2xx = 200 <= status_code < 300
    cumple_tiempo = tiempo_ms <= limite_ms
    valido = es_2xx and cumple_tiempo and tiene_token

    return {
        "valido": valido,
        "detalles": {
            "codigo_2xx": es_2xx,
            "cumple_tiempo": cumple_tiempo,
            "tiene_token": tiene_token,
        },
    }

@mcp.tool()
def buscar_cliente(cip: str) -> dict:
    """Busca un cliente por CIP en datos_prueba.json."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos_prueba.json")

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except FileNotFoundError:
        return {"error": "Archivo datos_prueba.json no encontrado"}

    for cliente in datos.get("clientes", []):
        if cliente.get("cip") == cip:
            return {"encontrado": True, "cliente": cliente}

    return {"encontrado": False, "mensaje": f"No se encontró cliente con CIP {cip}"}

if __name__ == "__main__":
    mcp.run()
