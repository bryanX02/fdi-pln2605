import spacy
import json
import numpy as np
from bs4 import BeautifulSoup
from pathlib import Path

# 1️⃣ Setup and Model Load (md/lg required for embeddings)
try:
    nlp = spacy.load("es_core_news_md")
except:
    print("Downloading medium model for embeddings...")
    spacy.cli.download("es_core_news_md")
    nlp = spacy.load("es_core_news_md")

nlp.max_length = 5_000_000

# 2️⃣ Extract Clean Text
ruta_archivo = "2000-h.htm"
html_crudo = Path(ruta_archivo).read_text(encoding="utf-8")
soup = BeautifulSoup(html_crudo, "html.parser")

# 2️⃣ Cargar spaCy y aumentar límite
nlp = spacy.load("es_core_news_sm")
nlp.max_length = 3_000_000  # suficiente para textos grandes

# 3️⃣ Estructura de resultados
resultado = {
    "parrafos": {},
    "lineas": {},
    "frases": {}
}

# 4️⃣ Extraer párrafos reales
parrafos = [p.get_text(separator="\n").strip() for p in soup.find_all('p') if p.get_text(strip=True)]

# 5️⃣ Procesar en batch con nlp.pipe
for doc_p in nlp.pipe(parrafos):
    p_text = doc_p.text
    tokens_p = [t.lemma_.lower() for t in doc_p if not t.is_punct]
    resultado["parrafos"][p_text] = tokens_p

    # 🔹 Líneas dentro del párrafo
    for l in p_text.split("\n"):
        l = l.strip()
        if not l:
            continue
        doc_l = nlp(l)
        tokens_l = [t.lemma_.lower() for t in doc_l if not t.is_punct]
        resultado["lineas"][l] = tokens_l

    # 🔹 Frases dentro del párrafo
    for sent in doc_p.sents:
        frase = sent.text.strip()
        if not frase:
            continue
        tokens_f = [t.lemma_.lower() for t in sent if not t.is_punct]
        resultado["frases"][frase] = tokens_f

# 6️⃣ Guardar JSON
with open("estructura.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)