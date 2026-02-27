import os

import httpx

# Lê a URL do servidor a partir da variável de ambiente obrigatória.
# Se não estiver definida, usa o valor local por defeito para desenvolvimento.
base_url = os.environ.get("FDI_PLN__BUTLER_ADDRESS", "http://127.0.0.1:7719").rstrip(
    "/"
)


def register_agent(name):
    endpoint = f"{base_url}/alias/{name}"
    payload = {"name": name}

    try:
        response = httpx.post(endpoint, json=payload)

        if response.status_code == 200:
            print("✅ Registro exitoso!")
            return response.json()
        else:
            print(f"❌ Error: {response.status_code}")
            print("Detalles:", response.text)
            return None

    except httpx.RequestError as e:
        print(f"❌ Error de conexión: {e}")
        return None


def get_info():
    endpoint = f"{base_url}/info"

    try:
        response = httpx.get(endpoint)

        if response.status_code == 200:
            data = response.json()
            return {
                "alias": data.get("Alias"),
                "recursos": data.get("Recursos", {}),
                "objetivo": data.get("Objetivo", {}),
                "buzon": data.get("Buzon", {}),
            }
        else:
            print(f"❌ Error: {response.status_code}")
            return None

    except httpx.RequestError as e:
        print(f"❌ Error de conexión: {e}")
        return None


def get_gente():
    endpoint = f"{base_url}/gente"

    try:
        response = httpx.get(endpoint)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.status_code}")
            return None

    except httpx.RequestError as e:
        print(f"❌ Error de conexión: {e}")
        return None


def send_paquete(dest, recursos: dict):
    endpoint = f"{base_url}/paquete/{dest}"

    try:
        response = httpx.post(endpoint, json=recursos)

        if response.status_code == 200:
            print("✅ Paquete enviado!")
            return response.json()
        else:
            print(f"❌ Error: {response.status_code}")
            print("Detalles:", response.text)
            return None

    except httpx.RequestError as e:
        print(f"❌ Error de conexión: {e}")
        return None


def get_dashboard():
    endpoint = f"{base_url}/dashboard"

    try:
        response = httpx.get(endpoint)

        if response.status_code == 200:
            return response.text  # Returns HTML content
        else:
            print(f"❌ Error: {response.status_code}")
            return None

    except httpx.RequestError as e:
        print(f"❌ Error de conexión: {e}")
        return None


def send_carta(asunto, cuerpo, dest, remi):
    endpoint = f"{base_url}/carta"
    payload = {"asunto": asunto, "cuerpo": cuerpo, "dest": dest, "remi": remi}

    try:
        response = httpx.post(endpoint, json=payload)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Carta enviada! UID: {data.get('uid')}")
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            print("Detalles:", response.text)
            return None

    except httpx.RequestError as e:
        print(f"❌ Error de conexión: {e}")
        return None


def delete_carta(uid: str):
    endpoint = f"{base_url}/mail/{uid}"

    try:
        response = httpx.delete(endpoint)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Carta eliminada! UID: {data.get('uid')}")
            return data
        elif response.status_code == 404:
            print(f"❌ Carta não encontrada (UID: {uid})")
            return None
        else:
            print(f"❌ Error: {response.status_code}")
            print("Detalles:", response.text)
            return None

    except httpx.RequestError as e:
        print(f"❌ Error de conexión: {e}")
        return None

    except httpx.RequestError as e:
        print(f"❌ Error de conexión: {e}")
        return None
