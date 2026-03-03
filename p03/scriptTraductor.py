def decodificar_y_limpiar(ruta_archivo, numero_magico):
    texto_bruto = ""

    try:
        # Leemos y aplicamos el desplazamiento
        with open(ruta_archivo, 'rb') as archivo:
            bytes_leidos = archivo.read()
            for byte in bytes_leidos:
                nuevo_valor = (byte + numero_magico) % 256
                texto_bruto += chr(nuevo_valor)

        # 2. Limpiamos los caracteres especiales del profesor
        texto_limpio = texto_bruto

        # Espacios y puntuación
        texto_limpio = texto_limpio.replace('8', ' ')  # El 8 es el espacio
        texto_limpio = texto_limpio.replace('s', '.')  # La 's' al final es el punto
        texto_limpio = texto_limpio.replace('7', '\n')  # El 7 es el salto de línea (Enter)
        texto_limpio = texto_limpio.replace('b', '')  # La 'b' parece ser un relleno invisible

        # Tildes y caracteres especiales
        texto_limpio = texto_limpio.replace('A_', 'Á')
        texto_limpio = texto_limpio.replace('E_', 'É')
        texto_limpio = texto_limpio.replace('I_', 'Í')
        texto_limpio = texto_limpio.replace('O_', 'Ó')
        texto_limpio = texto_limpio.replace('U_', 'Ú')
        texto_limpio = texto_limpio.replace('U`', 'Ü')  # Diéresis en cigüeña
        texto_limpio = texto_limpio.replace('Na', 'Ñ')  # La eñe

        return texto_limpio

    except FileNotFoundError:
        return "Error: No se ha encontrado el archivo. Comprueba la ruta."


nombre_archivo = "principal.bin"

print("=== Texto Final Descifrado y Limpio ===")
resultado_final = decodificar_y_limpiar(nombre_archivo, 45)
print(resultado_final)