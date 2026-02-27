import time
import json
import string as _string
import ollama
from pathlib import Path
from api_functions import register_agent, get_info, get_gente, delete_carta
from tools import TOOLS_SCHEMA, TOOLS_IMPL
from memory import add_carta_to_memory, get_all_history, add_event_to_memory
from templates import render_template, TEMPLATES as _TEMPLATES

# Todas las herramientas disponibles para el modelo
ALL_TOOLS = TOOLS_SCHEMA


def load_config(conf_path: str = "agent.conf"):
    """Carga la configuración desde el archivo agent.conf."""
    path = Path(conf_path)
    if not path.exists():
        return {"model": "qwen2.5-coder", "sleep_idle_seconds": 10}

    config = {}
    current_section = None
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("#", ";")):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].strip()
                config[current_section] = {}
                continue
            if "=" in line and current_section:
                key, value = line.split("=", 1)
                config[current_section][key.strip()] = value.strip()

    ollama_conf = config.get("ollama", {})
    runtime_conf = config.get("runtime", {})

    return {
        "model": ollama_conf.get("model", "qwen2.5-coder").strip(),
        "sleep_idle_seconds": int(runtime_conf.get("sleep_idle_seconds", 10)),
    }


def run_agent_loop(butler_url: str):
    """
    Bucle principal del agente.
    Recibe la URL del butler (aunque api_functions ya la lea de la env var,
    es buena práctica tenerla aquí para logs o validaciones).
    """
    config = load_config()
    agent_name = "agente_fdi_26XX"  # REEMPLAZA XX POR TU EQUIPO
    model_name = config["model"]

    print(f"🤖 Agente '{agent_name}' activo usando modelo '{model_name}'")

    register_agent(agent_name)
    j = 0

    while True:
        print(f"\n{'=' * 20} Ciclo {j} {'=' * 20}")

        info = get_info()
        gente = get_gente()

        if info:
            # --- Lógica de Procesamiento de Mensajes ---
            mensagens_formatadas = []
            if info.get("buzon"):
                for msg_id, msg in info["buzon"].items():
                    carta = {
                        "uid": msg_id,
                        "asunto": msg["asunto"],
                        "cuerpo": msg["cuerpo"],
                    }
                    sender = msg["remi"]

                    add_carta_to_memory(
                        agent_name,
                        sender,
                        carta,
                        llm_choose_fn=lambda cartas: list(range(len(cartas)))[-3:],
                    )

                    mensagens_formatadas.append(
                        {
                            "de": sender,
                            "assunto": msg["asunto"],
                            "conteudo": msg["cuerpo"],
                        }
                    )

                    delete_carta(msg_id)
                    print(f"🗑️ Carta {msg_id} eliminada del buzón.")

            # --- Construcción del Contexto para el LLM ---
            historico_memoria = get_all_history(agent_name)
            contexto = {
                "tu_nombre": agent_name,
                "tu_objetivo": info.get("objetivo", "Sin objetivo"),
                "tus_recursos": info.get("recursos", {}),
                "personas_conocidas": [p["alias"] for p in gente] if gente else [],
                "tus_mensajes_buzon": mensagens_formatadas,
                "historial_mensajes_por_agente": historico_memoria,
            }

            prompt = (
                f"Eres {agent_name}. Tu objetivo es: {contexto['tu_objetivo']}.\n\n"
                f"Estado actual: {json.dumps(contexto, ensure_ascii=False)}\n\n"
                f"REGLAS DE DECISIÓN:\n"
                f"1. Prioriza cumplir acuerdos con send_paquete.\n"
                f"2. Responde mensajes usando send_carta y las plantillas adecuadas.\n"
                f"3. No envíes recursos que no tienes.\n"
                f"4. Habla siempre en español profesional.\n"
            )

            try:
                response = ollama.chat(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    tools=ALL_TOOLS,
                )

                if response.get("message", {}).get("tool_calls"):
                    for tool in response["message"]["tool_calls"]:
                        func_name = tool["function"]["name"]
                        args = tool["function"]["arguments"]

                        if func_name in TOOLS_IMPL:
                            # Lógica de ejecución de herramientas (send_carta, send_paquete, etc.)
                            # [Aquí va tu lógica de renderizado de templates y validación de stock]
                            print(f"🔧 Ejecutando '{func_name}'...")
                            resultado = TOOLS_IMPL[func_name](args)

                            # Registro de eventos en memoria
                            if func_name == "send_paquete" and resultado:
                                add_event_to_memory(
                                    agent_name,
                                    args.get("dest"),
                                    f"Enviado: {args.get('recursos')}",
                                )

                else:
                    print("ℹ️ El modelo no ha propuesto acciones en este ciclo.")

            except Exception as e:
                print(f"❌ Error en el razonamiento del LLM: {e}")

        time.sleep(config["sleep_idle_seconds"])
        j += 1
