import json
import os


# ---------------------------------------------------------------------------
# Funciones auxiliares internas
# ---------------------------------------------------------------------------


def _memory_file(agent_name: str) -> str:
    """Devuelve la ruta del archivo de memoria asociado al agente."""
    return f"memory_{agent_name}.txt"


def load_memory(agent_name: str) -> dict:
    """Carga la memoria completa del agente desde su archivo persistente."""
    path = _memory_file(agent_name)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(agent_name: str, memory: dict):
    """Persiste la memoria completa del agente en su archivo correspondiente."""
    path = _memory_file(agent_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def add_carta_to_memory(agent_name: str, sender: str, carta: dict, llm_choose_fn):
    """
    Añade una carta al historial del remitente indicado.

    Si el número de cartas almacenadas supera 3, invoca `llm_choose_fn`
    para determinar cuáles 3 conservar.

    Parámetros
    ----------
    agent_name    : alias del agente propietario de esta memoria
    sender        : alias del remitente de la carta
    carta         : dict con al menos {"uid", "asunto", "cuerpo"}
                    (puede incluir "data" u otros campos adicionales)
    llm_choose_fn : callable(cartas: list[dict]) -> list[int]
                    Recibe la lista de cartas y devuelve los índices (máx. 3) a conservar.
    """
    memory = load_memory(agent_name)
    cartas = memory.get(sender, [])

    # Añadir la nueva carta evitando duplicados por UID
    existing_uids = {c["uid"] for c in cartas}
    if carta["uid"] not in existing_uids:
        cartas.append(carta)

    # Si se supera el límite, delegar la selección al LLM
    if len(cartas) > 3:
        indices = llm_choose_fn(cartas)

        # Guardrails: asegurar índices válidos y un máximo de 3
        indices = [i for i in indices if isinstance(i, int) and 0 <= i < len(cartas)]
        indices = list(dict.fromkeys(indices))[:3]  # deduplicar y limitar a 3

        # Fallback: si el LLM devuelve algo inválido, conservar las 3 más recientes
        if len(indices) < 1:
            indices = list(range(len(cartas)))[-3:]

        cartas = [cartas[i] for i in indices]

    memory[sender] = cartas
    save_memory(agent_name, memory)


def get_history(agent_name: str, sender: str) -> list:
    """Devuelve las cartas almacenadas de un remitente específico."""
    return load_memory(agent_name).get(sender, [])


def get_all_history(agent_name: str) -> dict:
    """Devuelve toda la memoria del agente (todos los remitentes)."""
    return load_memory(agent_name)


def clear_sender_history(agent_name: str, sender: str):
    """Elimina el historial de un remitente específico."""
    memory = load_memory(agent_name)
    if sender in memory:
        del memory[sender]
        save_memory(agent_name, memory)


def clear_all_memory(agent_name: str):
    """Elimina toda la memoria del agente."""
    save_memory(agent_name, {})


def add_event_to_memory(agent_name: str, target: str, event_text: str):
    """
    Registra un evento del sistema (p. ej. acuerdo cumplido) en el historial de un agente.

    Genera un UID ficticio para evitar que el evento sea filtrado como duplicado.
    Mantiene un máximo de 3 entradas por agente (cartas o eventos).
    """
    memory = load_memory(agent_name)
    history = memory.get(target, [])

    import uuid

    event_entry = {
        "uid": f"event_{uuid.uuid4().hex[:8]}",
        "asunto": "EVENTO_SISTEMA",
        "cuerpo": event_text,
    }

    history.append(event_entry)

    # Conservar únicamente los últimos 3 registros
    if len(history) > 3:
        history = history[-3:]

    memory[target] = history
    save_memory(agent_name, memory)
