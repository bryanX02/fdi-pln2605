import json
import math
import numpy as np
import spacy
import typer
from rich.console import Console
from pathlib import Path
from bs4 import BeautifulSoup

app = typer.Typer()
console = Console()


def generar_datos(ruta_html, ruta_json):
    console.print("Generando datos...")
    html_crudo = Path(ruta_html).read_text(encoding="utf-8")
    soup = BeautifulSoup(html_crudo, "html.parser")

    try:
        nlp = spacy.load("es_core_news_md")
    except:
        spacy.cli.download("es_core_news_md")
        nlp = spacy.load("es_core_news_md")

    resultado = {"chunks": []}
    parrafos = [p.get_text(separator=" ").strip() for p in soup.find_all("p")]

    for p in parrafos:
        if len(p) > 30:
            doc = nlp(p)
            lemas = [t.lemma_.lower() for t in doc if not t.is_punct and not t.is_stop]
            resultado["chunks"].append(
                {"texto": p, "lemas": lemas, "embedding": doc.vector.tolist()}
            )

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resultado, f)
    return resultado


def cargar_datos(ruta_html, ruta_json):
    if not Path(ruta_json).exists():
        return generar_datos(ruta_html, ruta_json)
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)


def calcular_coseno(vec_a, matriz_b):
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(matriz_b, axis=1)
    norm_a = 1e-10 if norm_a == 0 else norm_a
    norm_b = np.where(norm_b == 0, 1e-10, norm_b)
    return np.dot(matriz_b, vec_a) / (norm_a * norm_b)


def procesar_consulta(consulta, nlp):
    doc = nlp(consulta.lower())
    lemas = [t.lemma_ for t in doc if not t.is_punct and not t.is_stop]
    return lemas, doc.vector


def busqueda_clasica(consulta, datos, nlp):
    lemas_consulta, _ = procesar_consulta(consulta, nlp)
    vocabulario = list(set(lemas_consulta))

    if not vocabulario:
        return []

    N = len(datos["chunks"])
    idf = {}
    for lema in vocabulario:
        docs_con_lema = sum(1 for c in datos["chunks"] if lema in c["lemas"])
        idf[lema] = math.log(N / (docs_con_lema + 1))

    similitudes = []
    for i, chunk in enumerate(datos["chunks"]):
        score = 0
        for lema in vocabulario:
            tf = chunk["lemas"].count(lema)
            score += tf * idf[lema]
        similitudes.append((i, score))

    similitudes.sort(key=lambda x: x[1], reverse=True)
    return similitudes[:3]


def busqueda_semantica(consulta, datos, nlp):
    _, vector_consulta = procesar_consulta(consulta, nlp)
    matriz_embeddings = np.array([c["embedding"] for c in datos["chunks"]])

    scores = calcular_coseno(np.array(vector_consulta), matriz_embeddings)
    similitudes = [(i, s) for i, s in enumerate(scores)]
    similitudes.sort(key=lambda x: x[1], reverse=True)
    return similitudes[:3]


@app.command()
def main():
    try:
        nlp = spacy.load("es_core_news_md")
    except:
        spacy.cli.download("es_core_news_md")
        nlp = spacy.load("es_core_news_md")

    datos = cargar_datos("2000-h.htm", "estructura.json")

    while True:
        console.print("\n1. Busqueda Clasica\n2. Busqueda Semantica\n3. Salir")
        opcion = typer.prompt("Opcion")

        if opcion == "3":
            break
        elif opcion in ["1", "2"]:
            consulta = typer.prompt("Consulta")

            if opcion == "1":
                resultados = busqueda_clasica(consulta, datos, nlp)
            else:
                resultados = busqueda_semantica(consulta, datos, nlp)

            for idx, score in resultados:
                if score > 0.05:
                    console.print(f"\nScore: {score:.4f}")
                    console.print(datos["chunks"][idx]["texto"])


if __name__ == "__main__":
    app()
