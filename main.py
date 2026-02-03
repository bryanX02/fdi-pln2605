import requests
import ollama
import json
import time
import uuid
from datetime import datetime

# --- CONFIGURACIÓN ---
API_URL = "http://147.96.81.252:8000"
# Si va muy lento, prueba modelos más pequeños como "llama3.2:1b" o "qwen:1.8b"
MODELO_OLLAMA = "qwen3-vl:8b" # O el que estés usando (qwen3)
MI_NOMBRE_AGENTE = "Daddy Scammer" 

class JuegoAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.mis_alias = []

    def registrar_si_es_necesario(self, nombre):
        info = self.get_info()
        if not info.get("Alias"):
            print(f"⚠️ Intentando registrar: {nombre}...")
            try:
                requests.post(f"{self.base_url}/alias/{nombre}")
                self.mis_alias.append(nombre)
            except: pass
        else:
            self.mis_alias = info["Alias"]
            print(f"✅ Identidad confirmada: {self.mis_alias[0]}")

    def get_info(self):
        try: return requests.get(f"{self.base_url}/info").json()
        except: return {}

    def get_gente(self):
        try: return requests.get(f"{self.base_url}/gente").json()
        except: return []

    def enviar_carta(self, destinatario, asunto, cuerpo):
        if not self.mis_alias: return "Error: Sin identidad"
        payload = {
            "remi": self.mis_alias[0], "dest": destinatario,
            "asunto": asunto, "cuerpo": cuerpo,
            "id": str(uuid.uuid4()), "fecha": datetime.now().isoformat()
        }
        try:
            requests.post(f"{self.base_url}/carta", json=payload)
            return f"Carta enviada a {destinatario}."
        except Exception as e: return f"Error: {e}"

    def enviar_recursos(self, destinatario, madera, oro):
        payload = {"madera": int(madera), "oro": int(oro)}
        try:
            requests.post(f"{self.base_url}/paquete/{destinatario}", json=payload)
            return f"Enviado {madera} madera y {oro} oro a {destinatario}."
        except Exception as e: return f"Error: {e}"

    def borrar_carta(self, uid):
        try:
            requests.delete(f"{self.base_url}/mail/{uid}")
            return f"Carta {uid} borrada."
        except Exception as e: return f"Error: {e}"

# --- HERRAMIENTAS ---
tools_definition = [
    {
        'type': 'function',
        'function': {
            'name': 'check_population',
            'description': 'Ver quién está conectado para poder hablar con ellos.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []}
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'send_message',
            'description': 'Enviar propuesta de colaboración o saludo.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'target_agent': {'type': 'string'},
                    'subject': {'type': 'string'},
                    'body': {'type': 'string', 'description': 'Mensaje amable y colaborativo.'}
                },
                'required': ['target_agent', 'body']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'send_resources',
            'description': 'Enviar recursos para cumplir un trato.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'target_agent': {'type': 'string'},
                    'wood_amount': {'type': 'integer'},
                    'gold_amount': {'type': 'integer'}
                },
                'required': ['target_agent', 'wood_amount', 'gold_amount']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'delete_mail',
            'description': 'Borrar correo procesado.',
            'parameters': {
                'type': 'object', 
                'properties': {'mail_uid': {'type': 'string'}}, 
                'required': ['mail_uid']
            }
        }
    }
]

def run_agent():
    api = JuegoAPI(API_URL)
    api.registrar_si_es_necesario(MI_NOMBRE_AGENTE)
    
    # --- PERSONALIDAD COLABORATIVA ---
    system_prompt = (
        f"Eres {MI_NOMBRE_AGENTE}, un diplomático que busca el beneficio mutuo.\n"
        "TU OBJETIVO FINAL: Conseguir los recursos de tu 'Objetivo', pero ayudando a otros.\n"
        "REGLAS DE CONDUCTA:\n"
        "1. NO seas codicioso. Prioriza formar alianzas.\n"
        "2. Sé BREVE y CONCISO en tus pensamientos. No divagues.\n"
        "3. Si ves gente nueva, saluda y propón intercambio.\n"
        "4. Si alguien te pide ayuda y te sobra recurso, dáselo (ganarás confianza).\n"
        "5. GESTIÓN DE BUZÓN: Lee mensaje -> Responde -> Borra (delete_mail).\n"
    )

    messages = [{'role': 'system', 'content': system_prompt}]
    print(f"🕊️ Agente {MI_NOMBRE_AGENTE} listo para colaborar.")

    while True:
        info = api.get_info()
        buzon = info.get("Buzon", {})
        
        # Formateo visual del estado para el log
        recursos_str = f"Madera: {info.get('Recursos', {}).get('madera',0)} | Oro: {info.get('Recursos', {}).get('oro',0)}"
        inbox_str = "VACÍO"
        buzon_prompt = "Buzón vacío."
        
        if buzon:
            inbox_str = f"{len(buzon)} mensajes"
            buzon_prompt = "TIENES MENSAJES (Procesa y BORRA):\n"
            for uid, c in buzon.items():
                buzon_prompt += f"- ID: {uid} | De: {c.get('remi')} | Dice: {c.get('cuerpo')}\n"

        print(f"\n--- 👁️ ESTADO: {recursos_str} | 📬 {inbox_str} ---")

        # Contexto para el LLM
        user_msg = (
            f"ESTADO: {recursos_str}\n"
            f"OBJETIVO: {info.get('Objetivo')}\n"
            f"{buzon_prompt}\n"
            "¿Qué hacemos? (Sé breve. Usa herramientas si es necesario)."
        )

        # Usamos historial corto para velocidad
        contexto_actual = [messages[0]] + messages[-4:] + [{'role': 'user', 'content': user_msg}]

        print("🧠 Pensando...")
        start = time.time()
        try:
            # stream=False para esperar toda la respuesta, pero print inmediato
            response = ollama.chat(model=MODELO_OLLAMA, messages=contexto_actual, tools=tools_definition)
        except Exception as e:
            print(f"❌ Error Ollama: {e}")
            time.sleep(5)
            continue
        
        duracion = time.time() - start
        
        # --- AQUÍ ESTÁ EL CAMBIO: Imprimimos lo que dice el modelo ---
        contenido_texto = response['message']['content']
        tool_calls = response['message'].get('tool_calls', [])

        if contenido_texto:
            print(f"💭 PENSAMIENTO ({duracion:.1f}s):\n{contenido_texto}")
        
        if not contenido_texto and not tool_calls:
            print(f"⚠️ El modelo devolvió vacío en {duracion:.1f}s. (Posible fallo de modelo)")

        # Ejecución de herramientas
        if tool_calls:
            print(f"🔥 EJECUTANDO {len(tool_calls)} ACCIONES:")
            for tool in tool_calls:
                fn = tool['function']['name']
                args = tool['function']['arguments']
                print(f"  👉 {fn} {args}")
                
                # Ejecutar en API
                res = "Error"
                if fn == 'check_population': res = str(api.get_gente())
                elif fn == 'send_message': res = api.enviar_carta(args.get('target_agent'), args.get('subject','Hola'), args.get('body'))
                elif fn == 'send_resources': res = api.enviar_recursos(args.get('target_agent'), args.get('wood_amount',0), args.get('gold_amount',0))
                elif fn == 'delete_mail': res = api.borrar_carta(args.get('mail_uid'))
                
                print(f"     ✅ Resultado: {res}")
                # Guardamos resultado en memoria
                messages.append(response['message']) # La decisión del asistente
                messages.append({'role': 'tool', 'content': str(res)}) # El resultado
        else:
            # Si no hubo herramientas, guardamos el pensamiento
            messages.append({'role': 'assistant', 'content': contenido_texto})

        # Dormir según actividad
        sleep_time = 2 if tool_calls else 10
        print(f"⏳ Esperando {sleep_time}s...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    run_agent()
