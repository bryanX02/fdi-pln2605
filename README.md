# Agente Diplomático — README

Sistema de agente autónomo basado en LLM (Ollama) que participa en un entorno multiagente de intercambio de recursos. El agente percibe su entorno a través de una API REST, razona con un modelo de lenguaje local y actúa mediante *tool calls* estructuradas.

---

## Estructura del proyecto

```
.
├── agent.conf          # Configuración del servidor, modelo y tiempos de espera
├── brain.py            # Bucle principal del agente (percepción → razonamiento → acción)
├── api_functions.py    # Cliente HTTP para la API del servidor de juego
├── tools.py            # Registro de herramientas disponibles para el modelo
├── tools.json          # Esquema de herramientas en formato OpenAI/Ollama
├── templates.py        # Plantillas de mensajes y función de renderizado
├── memory.py           # Persistencia de historial de conversaciones por agente
└── codigo.py           # Implementación alternativa/standalone del agente
```

---

## Requisitos

- Python 3.10+
- [Ollama](https://ollama.com/) instalado y en ejecución local
- Servidor de juego corriendo en la dirección configurada en `agent.conf`

### Dependencias Python

```bash
pip install httpx requests ollama
```

---

## Configuración

Edita `agent.conf` antes de ejecutar:

```ini
[server]
host   = 127.0.0.1
port   = 7719
scheme = http

[ollama]
model = qwen2.5:7b

[runtime]
sleep_idle_seconds       = 4
sleep_after_tools_seconds = 1
```

| Parámetro | Descripción |
|---|---|
| `host` / `port` / `scheme` | Dirección del servidor de juego |
| `model` | Modelo Ollama a utilizar para el razonamiento |
| `sleep_idle_seconds` | Tiempo de espera entre ciclos sin actividad |
| `sleep_after_tools_seconds` | Tiempo de espera tras ejecutar herramientas |

---

## Ejecución

```bash
python brain.py
```

O con la implementación alternativa standalone:

```bash
python codigo.py
```

---

## Arquitectura

### Bucle principal (`brain.py`)

Cada ciclo el agente:

1. **Percibe** — Consulta la API para obtener su estado actual (recursos, objetivo, buzón).
2. **Memoriza** — Guarda los mensajes recibidos en memoria persistente y los elimina del buzón de la API.
3. **Razona** — Envía el contexto al modelo LLM local (Ollama) con las herramientas disponibles.
4. **Actúa** — Ejecuta las *tool calls* devueltas por el modelo (enviar carta, enviar recursos, etc.).

### Herramientas disponibles

| Herramienta | Descripción |
|---|---|
| `register_agent` | Registra el alias del agente en el servidor |
| `get_info` | Obtiene recursos, objetivo y buzón del agente |
| `get_gente` | Lista los agentes conectados |
| `send_carta` | Envía un mensaje a otro agente |
| `send_paquete` | Envía recursos (madera, oro) a otro agente |
| `get_dashboard` | Obtiene el HTML del dashboard de estado |
| `delete_carta` | Elimina una carta del buzón por UID |

### Plantillas de mensajes (`templates.py`)

Los mensajes se generan siempre a partir de plantillas predefinidas para garantizar coherencia:

| Plantilla | Campos requeridos | Uso |
|---|---|---|
| `presentacion` | `dest`, `remi`, `tem`, `precisa` | Primer contacto con otro agente |
| `negociacion` | `dest`, `ofrece`, `pede` | Propuesta de intercambio |
| `aceptar_trato` | `dest` | Confirmación de acuerdo |
| `confirmacion_envio` | `dest`, `recursos_enviados` | Notificación de envío de recursos |

### Memoria persistente (`memory.py`)

- El historial de conversaciones se almacena en archivos `memory_<agent_name>.txt` (JSON).
- Se mantienen como máximo **3 entradas por agente** (cartas o eventos del sistema).
- Los acuerdos cumplidos se registran como eventos especiales con `asunto: EVENTO_SISTEMA`.

---

## Reglas de decisión del agente

El modelo sigue este orden de prioridad en cada ciclo:

1. Si existe un acuerdo previo y hay recursos disponibles → **enviar recursos inmediatamente** (`send_paquete`).
2. Si hay mensajes en el buzón → **responder y eliminar** la carta (`send_carta` + `delete_carta`).
3. Si no hay actividad → **explorar** consultando agentes conectados y saludar a uno (`check_population` + `send_carta`).

> **Importante:** El agente solo puede enviar `madera` y `oro`. Nunca enviará más recursos de los que dispone.

---

## Notas adicionales

- Toda la comunicación entre agentes se realiza **en español**.
- El modelo debe responder **siempre mediante tool calls**. Si no lo hace, el sistema reintenta hasta 2 veces antes de aplicar un fallback determinístico.
- Los logs se emiten por consola con marca de tiempo en formato `[HH:MM:SS]`.
