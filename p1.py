import httpx

# Configura la URL y los datos de registro
url = "http://147.96.81.252:8000/alias/g05"
payload = {"name": "g05"}  # Ajusta este campo según el esquema de tu API

try:
    # Realiza la solicitud POST
    response = httpx.post(url, json=payload)
    
    # Verifica el estado de la respuesta
    if response.status_code == 200:
        print("✅ Registro exitoso!")
        print("Respuesta:", response.json())
    else:
        print(f"❌ Error: {response.status_code}")
        print("Detalles:", response.text)
except httpx.RequestError as e:
    print(f"❌ Error de conexión: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")


