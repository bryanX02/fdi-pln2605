from pathlib import Path
from bs4 import BeautifulSoup
import nltk
from nltk.stem import WordNetLemmatizer

# Descargar recursos necesarios de NLTK
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()

def cargar_y_limpiar_documento(ruta):
    """Carga el documento HTML y devuelve el objeto soup y el texto limpio."""
    html_crudo = Path(ruta).read_text(encoding="utf-8")
    soup = BeautifulSoup(html_crudo, "html.parser")
    texto_completo = soup.get_text(separator=" ")
    return soup, texto_completo

def buscar_por_lineas(texto, consulta):
    """Busca separando el texto por saltos de línea."""
    lineas = texto.split('\n')
    resultados = []
    for i, linea in enumerate(lineas):
        if consulta.lower() in linea.lower():
            resultados.append(f"Línea {i+1}: {linea.strip()}")
    return resultados

def buscar_por_oraciones(texto, consulta):
    """Busca separando por puntos (oraciones completas)."""
    # Un método simple: dividir por puntos
    oraciones = texto.split('.')
    resultados = []
    for oracion in oraciones:
        if consulta.lower() in oracion.lower():
            resultados.append(oracion.strip() + ".")
    return resultados

def buscar_por_parrafos(soup, consulta):
    """Usa las etiquetas <p> del HTML para extraer párrafos enteros."""
    parrafos = soup.find_all('p')
    resultados = []
    for p in parrafos:
        texto_p = p.get_text().strip()
        if consulta.lower() in texto_p.lower():
            resultados.append(texto_p)
    return resultados

def buscar_por_capitulos(soup, consulta):
    """Busca en bloques más grandes usando etiquetas <h3> (donde suelen ir los títulos).
    Asume que un capítulo es el texto entre un <h3> y el siguiente."""
    resultados = []
    
    # Encontramos todos los encabezados (pueden ser h2 o h3 según el libro)
    encabezados = soup.find_all(['h2', 'h3'])
    
    for i in range(len(encabezados)):
        titulo_capitulo = encabezados[i].get_text().strip()
        
        # Extraer el contenido hasta el siguiente encabezado
        nodo_actual = encabezados[i].find_next_sibling()
        contenido_capitulo = ""
        
        while nodo_actual and nodo_actual.name not in ['h2', 'h3']:
            if nodo_actual.name == 'p':
                contenido_capitulo += nodo_actual.get_text() + " "
            nodo_actual = nodo_actual.find_next_sibling()
            
        if consulta.lower() in contenido_capitulo.lower():
            resultados.append(f"Capítulo/Sección: {titulo_capitulo}\n{contenido_capitulo[:200]}... [Continúa]")
            
    return resultados

def buscar_contexto_palabras(texto, consulta, margen=30):
    """Busca la palabra (usando lematización) y devuelve N palabras antes y N palabras después."""
    palabras = texto.split()
    resultados = []
    
    # Lematizamos la consulta (asumiendo que es una sola palabra)
    consulta_lema = lemmatizer.lemmatize(consulta.lower())
    
    for i, palabra in enumerate(palabras):
        # Limpiamos signos de puntuación pegados a la palabra
        palabra_limpia = palabra.strip('.,;:"\'()!?').lower()
        
        # Lematizamos la palabra del texto para comparar
        if lemmatizer.lemmatize(palabra_limpia) == consulta_lema:
            inicio = max(0, i - margen)
            fin = min(len(palabras), i + margen + 1)
            
            fragmento = " ".join(palabras[inicio:fin])
            resultados.append(f"... {fragmento} ...")
            
    return resultados

def mostrar_menu():
    print("\n--- MENÚ DE BÚSQUEDA NLP ---")
    print("1. Búsqueda por Línea exacta")
    print("2. Búsqueda por Oración completa")
    print("3. Búsqueda por Párrafo completo")
    print("4. Búsqueda con Contexto (30 palabras antes y después)")
    print("5. Búsqueda por Capítulo (Aparición en sección)")
    print("6. Salir")
    opcion = input("Elige una opción (1-6): ")
    return opcion

def main():
    ruta_archivo = "2000-h.htm"
    print("Cargando y procesando el documento...")
    soup, texto_completo = cargar_y_limpiar_documento(ruta_archivo)
    
    while True:
        opcion = mostrar_menu()
        
        if opcion == '6':
            print("Saliendo del programa...")
            break
            
        if opcion not in ['1', '2', '3', '4', '5']:
            print("Opción no válida. Inténtalo de nuevo.")
            continue
            
        consulta = input("\nIntroduce el texto o palabra a buscar: ")
        
        # Ejecutamos la función correspondiente según la opción
        resultados = []
        if opcion == '1':
            resultados = buscar_por_lineas(texto_completo, consulta)
        elif opcion == '2':
            resultados = buscar_por_oraciones(texto_completo, consulta)
        elif opcion == '3':
            resultados = buscar_por_parrafos(soup, consulta)
        elif opcion == '4':
            resultados = buscar_contexto_palabras(texto_completo, consulta, margen=30)
        elif opcion == '5':
            resultados = buscar_por_capitulos(soup, consulta)
            
        # Mostrar los resultados
        print(f"\n--- Se encontraron {len(resultados)} coincidencias ---")
        # Mostramos máximo 5 para no saturar la pantalla
        for idx, res in enumerate(resultados[:10]):
            print(f"\nCoincidencia {idx + 1}:")
            print(res)
            
        if len(resultados) > 10:
            print(f"\n... y {len(resultados) - 5} coincidencias más ocultas.")

if __name__ == "__main__":
    main()