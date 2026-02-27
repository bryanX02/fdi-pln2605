# tools.py
import json
from api_functions import (
    register_agent,
    get_info,
    get_gente,
    send_paquete,
    get_dashboard,
    send_carta,
    delete_carta,
)

# Carga el esquema de herramientas desde el archivo de definición JSON
with open("tools.json", "r", encoding="utf-8") as f:
    TOOLS_SCHEMA = json.load(f)

# Mapeo de nombres de herramientas a sus implementaciones correspondientes
TOOLS_IMPL = {
    "register_agent": lambda args: register_agent(args["name"]),
    "get_info": lambda args: get_info(),
    "get_gente": lambda args: get_gente(),
    "send_paquete": lambda args: send_paquete(
        dest=args["dest"],
        recursos=args["recursos"],
    ),
    "get_dashboard": lambda args: get_dashboard(),
    "send_carta": lambda args: send_carta(
        asunto=args["asunto"],
        cuerpo=args["cuerpo"],
        dest=args["dest"],
        remi=args["remi"],
    ),
    "delete_carta": lambda args: delete_carta(args["uid"]),
}
