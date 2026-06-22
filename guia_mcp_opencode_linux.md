# Guía: Crear y conectar un servidor MCP local con opencode (Linux)

> Adaptación del laboratorio original (Windows + VS Code + GitHub Copilot) al stack **Linux + opencode**.

---

## 1. Meta y requisitos

**Meta:** Construir un servidor MCP en Python, registrarlo en `opencode.json` y ejecutar sus herramientas desde el chat de opencode en modo agente.

**Resultado esperado:** Crear tools con `FastMCP`, registrarlas por stdio y ejecutarlas desde opencode.

**Requisitos (Linux):**
- Terminal (bash/zsh) con acceso a la carpeta del proyecto.
- Python 3 instalado: `python3 --version`.
- Módulo `venv` disponible: `python3 -m venv --help` (en Debian/Ubuntu/Mint puede requerir `sudo apt install python3-venv`).
- [opencode](https://opencode.ai) instalado y autenticado con un proveedor de modelo.

**Estructura final:**
```
qaLabMcp/
├── opencode.json
├── server.py
└── datos_prueba.json   (si se hace el reto 4)
```

---

## 2. Preparar el proyecto

```bash
mkdir -p ~/qaLabMcp && cd ~/qaLabMcp

# Validar Python
python3 --version
python3 -m pip --version

# Crear entorno virtual (recomendado en Linux: evita tocar el Python del sistema)
python3 -m venv .venv
source .venv/bin/activate

# Instalar MCP
pip install "mcp[cli]"

# Verificar
pip show mcp
```

> **Nota Linux:** si `python3 -m venv` falla con `ensurepip is not available`, falta el paquete del sistema: `sudo apt install python3-venv python3-pip`. Esto **no ocurre en Windows**, donde `venv` viene incluido con el instalador oficial de Python.

---

## 3. Crear `server.py`

En la raíz de `qaLabMcp`, crea `server.py`:

```python
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
        "pasos": ["Preparar datos", "Enviar la petición", "Validar código y respuesta"],
    }

@mcp.tool()
def calcular_percentil_simple(valores: list[float], percentil: float) -> dict:
    """Calcula un percentil simple."""
    if not valores or not 0 <= percentil <= 100:
        return {"error": "Datos inválidos"}
    ordenados = sorted(valores)
    indice = round((percentil / 100) * (len(ordenados) - 1))
    return {"percentil": percentil, "valor": ordenados[indice]}

if __name__ == "__main__":
    mcp.run()
```

Comprobación de sintaxis:
```bash
python -m py_compile server.py
```

---

## 4. Registrar el servidor en opencode

A diferencia de VS Code (`.vscode/mcp.json` con `${workspaceFolder}`), opencode usa **`opencode.json`** y no tiene una variable de "carpeta del proyecto" — las rutas deben ser absolutas, o relativas al directorio desde el que se lanza `opencode`.

```bash
pwd   # confirma tu ruta absoluta, ej. /home/awong/qaLabMcp
```

`opencode.json` (ruta absoluta, opción más estable):
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "qaLabMcp": {
      "type": "local",
      "command": ["/home/awong/qaLabMcp/.venv/bin/python", "/home/awong/qaLabMcp/server.py"],
      "enabled": true
    }
  }
}
```

Alternativa con ruta relativa (solo funciona si siempre ejecutas `opencode` desde dentro de `qaLabMcp`):
```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "qaLabMcp": {
      "type": "local",
      "command": [".venv/bin/python", "server.py"],
      "enabled": true
    }
  }
}
```

> **Importante:** opencode resuelve rutas relativas contra el directorio de trabajo del proceso (tu `pwd` al momento de lanzar `opencode`), no contra la ubicación del archivo `opencode.json`. Si tienes configs en carpetas padre/hijas anidadas, esto puede causar errores `ENOENT` — usa rutas absolutas si no estás seguro.

---

## 5. Iniciar y verificar

```bash
cd ~/qaLabMcp
opencode mcp list
```

Salida esperada:
```
┌  MCP Servers
│
●  ✓ qaLabMcp connected
│      /home/awong/qaLabMcp/.venv/bin/python /home/awong/qaLabMcp/server.py
│
└  1 server(s)
```

Si dice `failed`, revisa el mensaje de error que acompaña — normalmente apunta a una ruta inexistente (venv no creado, `mcp` no instalado, o variable sin resolver).

---

## 6. Probar desde el chat de opencode

```bash
opencode
```

Prompts de prueba:
- *"Usa validar_cliente con CIP 12345, teléfono 6677-8899 y correo prueba@demo.com"*
- *"Usa generar_caso_prueba para POST /api/login con credenciales inválidas"*
- *"Calcula el percentil 95 de [120, 130, 150, 300, 90, 100, 500, 220]"*

opencode debería listar las tools de `qaLabMcp` y devolver una respuesta estructurada al invocarlas.

---

## 7. Retos prácticos

Agrega cada función antes de `if __name__ == "__main__":`, guarda, y vuelve a abrir `opencode` (o usa `opencode mcp list` para confirmar que sigue conectado) para que recargue el servidor.

| Reto | Función | Prueba |
|---|---|---|
| 1 · Básico | `clasificar_error_http(status_code)` | 500 → "Error del servidor" |
| 2 · Intermedio | `evaluar_sla(p95_ms, limite_ms)` | 480, 500 → cumple: true |
| 3 · Intermedio | `validar_respuesta_api(status_code, tiempo_ms, limite_ms, tiene_token)` | 200, 350, 500, true → válido |
| 4 · Avanzado | `buscar_cliente(cip)` + `datos_prueba.json` | lectura desde archivo local |

Para el Reto 4, usa rutas absolutas dentro del propio script con `os.path.dirname(os.path.abspath(__file__))`, así la tool encuentra el JSON sin depender de desde dónde se lanzó `opencode`.

---

## 8. Configuración global vs. local

El laboratorio original usa configuración **local de proyecto** (`.vscode/mcp.json` dentro de la carpeta), no global. El equivalente correcto en opencode es mantener `opencode.json` dentro de `qaLabMcp/`, no en `~/.config/opencode/opencode.json`. La config global es útil para tools de uso general en todos tus proyectos, pero no es lo que pide esta asignación.

---

## 9. ¿Qué cambiaría si el ecosistema fuera opencode + Windows?

Todo lo anterior funciona igual en concepto; estas son las diferencias concretas:

| Aspecto | Linux | Windows |
|---|---|---|
| **Terminal** | bash/zsh | PowerShell o CMD |
| **Crear venv** | `python3 -m venv .venv` | `python -m venv .venv` (el comando es `python`, no `python3`) |
| **Activar venv** | `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` (PowerShell) o `.venv\Scripts\activate.bat` (CMD) |
| **Ruta del intérprete** | `.venv/bin/python` | `.venv\Scripts\python.exe` |
| **Separador de rutas** | `/` | `\` (pero en JSON casi siempre se recomienda usar `/` para evitar escapar barras invertidas: `"C:/Users/usuario/qaLabMcp/.venv/Scripts/python.exe"`) |
| **Dependencia `venv`** | A veces falta el paquete del sistema (`python3-venv`) y hay que instalarlo con `apt` | Viene incluido con el instalador oficial de Python; no requiere paso adicional |
| **Permisos de ejecución** | No suele requerir `chmod`, los scripts del venv ya son ejecutables | No aplica el concepto de bit de ejecución; Windows resuelve por extensión `.exe`/`.bat` |
| **Política de ejecución de scripts** | No aplica | PowerShell puede bloquear `Activate.ps1` por la *Execution Policy*; puede requerir `Set-ExecutionPolicy -Scope Process Bypass` |
| **Ruta de config global de opencode** | `~/.config/opencode/opencode.json` | Generalmente `%USERPROFILE%\.config\opencode\opencode.json` (confirma esto en la documentación oficial, ya que puede variar según versión) |
| **Variables de entorno** | `$HOME`, `export VAR=valor` | `%USERPROFILE%`, `$env:VAR` (PowerShell) o `set VAR=valor` (CMD) |
| **`{env:VAR}` en opencode.json** | Mismo comportamiento | Mismo comportamiento — la sintaxis del config es multiplataforma, solo cambia cómo defines la variable en tu shell |

**En resumen:** la estructura del `opencode.json`, las tools de `server.py`, y la lógica de MCP no cambian en absoluto entre sistemas — opencode abstrae eso. Lo único que varía es **cómo se crea/activa el entorno virtual de Python** y **el formato de las rutas** que apuntan al intérprete dentro de ese entorno.

---

## 10. Checklist final

- [ ] Python responde desde la terminal.
- [ ] `mcp[cli]` está instalado dentro del venv.
- [ ] `server.py` compila sin errores (`python -m py_compile server.py`).
- [ ] `opencode.json` está en la raíz del proyecto, con rutas correctas.
- [ ] `opencode mcp list` muestra `qaLabMcp` como `connected`.
- [ ] Las tres tools base funcionan desde el chat.
- [ ] Los cuatro retos fueron implementados y probados.
