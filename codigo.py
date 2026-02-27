import json
import time
from datetime import datetime
import configparser

import requests
import ollama


# --- CONFIG DESDE .conf ---
def load_config(conf_path: str = "agent.conf"):
    cfg = configparser.ConfigParser()
    read_ok = cfg.read(conf_path, encoding="utf-8")
    if not read_ok:
        raise FileNotFoundError(
            f"No se pudo leer el archivo de configuración '{conf_path}'. "
            "Crea agent.conf en el mismo directorio."
        )

    scheme = cfg.get("server", "scheme", fallback="http").strip()
    host = cfg.get("server", "host").strip()
    port = cfg.getint("server", "port", fallback=8000)

    api_url = f"{scheme}://{host}:{port}"
    model = cfg.get("ollama", "model", fallback="qwen2.5-coder").strip()
    agent_name = cfg.get("agent", "name", fallback="Mapache_Diplomatico").strip()

    sleep_idle = cfg.getint("runtime", "sleep_idle_seconds", fallback=10)
    sleep_after_tools = cfg.getint("runtime", "sleep_after_tools_seconds", fallback=2)

    return api_url, model, agent_name, sleep_idle, sleep_after_tools


API_URL, MODELO_OLLAMA, MI_NOMBRE_AGENTE, SLEEP_IDLE, SLEEP_AFTER_TOOLS = load_config(
    "agent.conf"
)


# ====
# LOGS (MINIMAL)
# ====
def log_event(event: str, **fields):
    ts = datetime.now().strftime("%H:%M:%S")
    extras = " ".join([f"{k}={v!r}" for k, v in fields.items() if v is not None])
    print(f"[{ts}] {event} {extras}".rstrip())


def preview(text: str, n: int = 120):
    if text is None:
        return ""
    s = str(text).replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def safe_parse_tool_args(raw):
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        s = raw.strip()
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}
    return {}


# ====
# API CLIENT
# ====
class JuegoAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.mis_alias = []

    def registrar_si_es_necesario(self, nombre: str):
        info = self.get_info()
        alias = info.get("Alias")
        if not alias:
            try:
                requests.post(f"{self.base_url}/alias/{nombre}", timeout=10)
            except Exception:
                pass
            info = self.get_info()
            alias = info.get("Alias") or nombre

        if isinstance(alias, str):
            self.mis_alias = [alias]
        elif isinstance(alias, list) and alias:
            self.mis_alias = alias
        else:
            self.mis_alias = [nombre]

        log_event(
            "AGENT_READY",
            alias=self.mis_alias[0],
            api=self.base_url,
            model=MODELO_OLLAMA,
        )

    def get_info(self):
        try:
            return requests.get(f"{self.base_url}/info", timeout=10).json()
        except Exception:
            return {}

    def get_gente(self):
        try:
            return requests.get(f"{self.base_url}/gente", timeout=10).json()
        except Exception:
            return []

    def enviar_carta(self, destinatario: str, asunto: str, cuerpo: str):
        if not self.mis_alias:
            return "Error: Sin identidad"

        payload = {
            "remi": self.mis_alias[0],
            "dest": destinatario,
            "asunto": asunto,
            "cuerpo": cuerpo,
        }
        try:
            r = requests.post(f"{self.base_url}/carta", json=payload, timeout=10)
            if r.status_code >= 400:
                return f"Error HTTP {r.status_code}: {r.text}"
            log_event(
                "MESSAGE_SENT", to=destinatario, subject=asunto, body=preview(cuerpo)
            )
            return f"Carta enviada a {destinatario}."
        except Exception as e:
            return f"Error: {e}"

    def enviar_recursos(self, destinatario: str, madera: int = 0, oro: int = 0):
        payload = {"madera": int(madera), "oro": int(oro)}
        try:
            r = requests.post(
                f"{self.base_url}/paquete/{destinatario}", json=payload, timeout=10
            )
            if r.status_code >= 400:
                return f"Error HTTP {r.status_code}: {r.text}"
            log_event(
                "RESOURCES_SENT", to=destinatario, madera=int(madera), oro=int(oro)
            )
            return f"Enviado {madera} madera y {oro} oro a {destinatario}."
        except Exception as e:
            return f"Error: {e}"

    def borrar_carta(self, uid: str):
        try:
            r = requests.delete(f"{self.base_url}/mail/{uid}", timeout=10)
            if r.status_code >= 400:
                return f"Error HTTP {r.status_code}: {r.text}"
            log_event("MAIL_DELETED", uid=uid)
            return f"Carta {uid} borrada."
        except Exception as e:
            return f"Error: {e}"


# ====
# TEMPLATES
# ====
TEMPLATES = {
    "saludo": (
        "Hola {target_agent}!\n"
        "Soy {agent_name}. Estoy buscando colaboración e intercambios justos.\n"
        "¿Qué recurso te sobra y qué necesitas?"
    ),
    "intercambio": (
        "Hola {target_agent}, soy {agent_name}.\n"
        "Te propongo un intercambio:\n"
        "- Yo ofrezco: {offer}\n"
        "- Yo necesito: {request}\n"
        "Si te encaja, dime cantidades y lo hacemos."
    ),
    "respuesta_ayuda": (
        "Hola {target_agent}, soy {agent_name}.\n"
        "Puedo ayudarte con: {offer}\n"
        "A cambio, cuando puedas, me vendría bien: {request}\n"
        "Si confirmas, lo envío."
    ),
    "respuesta_generica": ("Hola {target_agent}, soy {agent_name}.\n{message}"),
}


def render_template(template_id: str, **kwargs) -> str:
    tpl = TEMPLATES.get(template_id, TEMPLATES["respuesta_generica"])
    safe = {
        "target_agent": kwargs.get("target_agent", ""),
        "agent_name": kwargs.get("agent_name", MI_NOMBRE_AGENTE),
        "offer": kwargs.get("offer", "algo de mis excedentes"),
        "request": kwargs.get("request", "algo que me falte"),
        "message": kwargs.get("message", ""),
    }
    safe.update(kwargs)
    return tpl.format(**safe)


# ====
# TOOLS
# ====
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "check_population",
            "description": "Ver quién está conectado para poder hablar con ellos.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Enviar propuesta de colaboración o saludo usando plantillas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_agent": {"type": "string"},
                    "subject": {"type": "string"},
                    "template_id": {"type": "string"},
                    "template_vars": {"type": "object"},
                    "body": {"type": "string"},
                },
                "required": ["target_agent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_resources",
            "description": "Enviar recursos. Solo madera y oro.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_agent": {"type": "string"},
                    "resources": {
                        "type": "object",
                        "additionalProperties": {"type": "integer"},
                    },
                },
                "required": ["target_agent", "resources"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_mail",
            "description": "Borrar una carta del buzón por ID.",
            "parameters": {
                "type": "object",
                "properties": {"mail_uid": {"type": "string"}},
                "required": ["mail_uid"],
            },
        },
    },
]


def pick_someone_else(gente, my_aliases):
    if not isinstance(gente, list):
        return None
    for g in gente:
        if isinstance(g, str) and g and g not in set(my_aliases or []):
            return g
    return None


def run_agent():
    api = JuegoAPI(API_URL)
    api.registrar_si_es_necesario(MI_NOMBRE_AGENTE)

    system_prompt = (
        f"Eres {MI_NOMBRE_AGENTE}, un diplomático que busca el beneficio mutuo.\n"
        "Prioriza: responder a mensajes, proponer intercambio, y ejecutar envíos.\n"
        "IMPORTANTE: Solo puedes enviar recursos por API: madera y oro.\n"
        "REGLA CRÍTICA: Debes responder SIEMPRE usando tool calls (function calls). "
        "No escribas texto normal.\n"
        "Buzón: responde y luego borra el mail (delete_mail).\n"
        "Si no hay mensajes, usa check_population y saluda a 1 agente.\n"
    )

    messages = [{"role": "system", "content": system_prompt}]
    last_seen_mail_ids = set()

    while True:
        info = api.get_info()
        buzon = info.get("Buzon", {}) or {}
        recursos = info.get("Recursos", {}) or {}
        objetivo = info.get("Objetivo", {}) or {}

        # Log apenas "mensagens recebidas novas"
        current_ids = set(buzon.keys())
        new_ids = [mid for mid in current_ids if mid not in last_seen_mail_ids]
        for mid in new_ids:
            c = buzon.get(mid, {})
            log_event(
                "MESSAGE_RECEIVED",
                id=mid,
                from_=c.get("remi"),
                subject=c.get("asunto"),
                body=preview(c.get("cuerpo", "")),
            )
        last_seen_mail_ids = current_ids

        buzon_prompt = "Buzón vacío."
        if buzon:
            buzon_prompt = "TIENES MENSAJES (responde y BORRA):\n"
            for uid, c in buzon.items():
                buzon_prompt += f"- ID:{uid} | De:{c.get('remi')} | Asunto:{c.get('asunto')} | {c.get('cuerpo')}\n"

        user_msg = (
            f"RECURSOS: {recursos}\n"
            f"OBJETIVO: {objetivo}\n"
            f"{buzon_prompt}\n"
            "Decide la siguiente acción. Responde SOLO con tool calls."
        )

        contexto_actual = (
            [messages[0]] + messages[-6:] + [{"role": "user", "content": user_msg}]
        )

        # --- call model (force tool calls with retries) ---
        try:
            response = ollama.chat(
                model=MODELO_OLLAMA,
                messages=contexto_actual,
                tools=tools_definition,
                think=False,
            )
        except Exception as e:
            log_event("OLLAMA_ERROR", error=str(e))
            time.sleep(5)
            continue

        msg = response.get("message", {}) or {}
        tool_calls = msg.get("tool_calls", []) or []

        retries = 0
        while not tool_calls and retries < 2:
            log_event("NO_TOOL_CALLS", retry=retries + 1)
            messages.append(msg)
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Respuesta inválida: debes usar UNA o MÁS tool calls ahora. "
                        "Elige una acción ejecutable (check_population, send_message, send_resources, delete_mail)."
                    ),
                }
            )
            try:
                response = ollama.chat(
                    model=MODELO_OLLAMA,
                    messages=[messages[0]] + messages[-8:],
                    tools=tools_definition,
                    think=False,
                )
            except Exception as e:
                log_event("OLLAMA_ERROR", error=str(e))
                break
            msg = response.get("message", {}) or {}
            tool_calls = msg.get("tool_calls", []) or []
            retries += 1

        # Fallback determinístico se sigue sin tool calls
        if not tool_calls:
            log_event("FALLBACK", action="greet_someone")
            gente = api.get_gente()
            target = pick_someone_else(gente, api.mis_alias)
            if target:
                api.enviar_carta(
                    target, "Hola", render_template("saludo", target_agent=target)
                )
                time.sleep(SLEEP_AFTER_TOOLS)
            else:
                time.sleep(SLEEP_IDLE)
            continue

        # normal path: execute tool calls
        messages.append(msg)

        for tool in tool_calls:
            fn = tool.get("function", {}).get("name")
            raw_args = tool.get("function", {}).get("arguments")
            args = safe_parse_tool_args(raw_args)

            res = "Error"
            if fn == "check_population":
                res = str(api.get_gente())

            elif fn == "send_message":
                target = args.get("target_agent", "")
                subject = args.get("subject", "Hola")
                template_id = args.get("template_id")
                template_vars = args.get("template_vars") or {}

                if template_id:
                    body = render_template(
                        template_id,
                        target_agent=target,
                        agent_name=MI_NOMBRE_AGENTE,
                        **template_vars,
                    )
                else:
                    body = args.get("body", "")

                res = api.enviar_carta(target, subject, body)

            elif fn == "send_resources":
                target = args.get("target_agent", "")
                resources = args.get("resources") or {}
                madera = int(resources.get("madera", 0) or 0)
                oro = int(resources.get("oro", 0) or 0)
                res = api.enviar_recursos(target, madera=madera, oro=oro)

            elif fn == "delete_mail":
                uid = args.get("mail_uid", "")
                res = api.borrar_carta(uid)

            messages.append({"role": "tool", "content": str(res)})

        time.sleep(SLEEP_AFTER_TOOLS)


if __name__ == "__main__":
    run_agent()
