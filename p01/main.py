import os
import sys
from brain import run_agent_loop


def main():
    """
    Punto de entrada principal exigido por el profesor.
    """
    # 1. Requisito: Leer la URL de la variable de entorno
    butler_address = os.environ.get("FDI_PLN__BUTLER_ADDRESS")

    if not butler_address:
        print("Error: La variable de entorno FDI_PLN__BUTLER_ADDRESS no está definida.")
        # Opcional: puedes poner una por defecto para desarrollo local,
        # pero para la entrega es mejor avisar.
        # butler_address = "http://127.0.0.1:7719"
        sys.exit(1)

    print(f"--- Agente FDI-PLN Equipo 26XX ---")
    print(f"Conectando a Butler en: {butler_address}")

    try:
        # 2. Lanzar el bucle del agente pasando la URL dinámica
        run_agent_loop(butler_address)
    except KeyboardInterrupt:
        print("\nAgente detenido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"Error crítico en la ejecución: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
