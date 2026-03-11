# Documentación de la práctica 3

## Objetivo
El objetivo es realizar una búsqueda de un texto específico (el profe ha puesto el ejemplo de "dulcinea") dentro del libro *Don Quijote de la Mancha* en formato HTML, adjuntado, reportando el número de apariciones y la línea exacta.

## Limpieza Manual
Para evitar ruido en nuestro análisis, hemos decidido borrar manualmente todo el contenido que no pertenece al contenido del quijote, prologo, notas y etiquetas html incluidas.

**Pasos realizados para la limpieza:**
1. Abrir el archivo `2000-h.htm` con un editor de texto o código (ej. VS Code).
2. Localizar la etiqueta de inicio del libro: `<div class="chapter">`.
3. Localizar la etiqueta de fin del libro: `</div><!--end chapter-->`.
4. Seleccionar y **eliminar todo el texto y etiquetas HTML** comprendidos antes y despues esos dos puntos.
5. Guardar el archivo modificado para su posterior lectura con el script de Python.
