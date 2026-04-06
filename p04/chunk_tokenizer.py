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
parrafos_lista = [p.get_text(separator=" ").strip() for p in soup.find_all('p') if p.get_text(strip=True)]

# 3️⃣ Master Structure with Embeddings for EVERYTHING
resultado = {
    "parrafos": [],
    "chunks": [],
    "frases": [],
    "lineas": []
}


def get_data(doc_or_span):
    """Helper to extract text, lemmas (no stops/punct) and aggregated embedding."""
    return {
        "texto": doc_or_span.text.strip(),
        "lemas": [t.lemma_.lower() for t in doc_or_span if not t.is_punct and not t.is_stop],
        "embedding": doc_or_span.vector.tolist()  # <--- Aggregated Embedding
    }


print("Procesando párrafos, frases y líneas...")
for doc_p in nlp.pipe(parrafos_lista):
    if len(doc_p.text.strip()) < 10: continue

    # A. Paragraphs
    resultado["parrafos"].append(get_data(doc_p))

    # B. Sentences (using spaCy sentence segmenter)
    for sent in doc_p.sents:
        if len(sent.text.strip()) > 15:
            resultado["frases"].append(get_data(sent))

    # C. Lines (defined by internal line breaks \n)
    for l in doc_p.text.split("\n"):
        l_strip = l.strip()
        if len(l_strip) > 10:
            resultado["lineas"].append(get_data(nlp.make_doc(l_strip)))

# 4️⃣ Chunks (500 words, 50 overlap) from the full text stream
print("Generando chunks de 500 palabras...")
texto_completo = " ".join(parrafos_lista)
doc_completo = nlp(texto_completo)
tokens_reales = [t for t in doc_completo if not t.is_space]

tamano_chunk = 500
overlap = 50

for i in range(0, len(tokens_reales), tamano_chunk - overlap):
    rango_chunk = tokens_reales[i: i + tamano_chunk]
    if len(rango_chunk) < 50: continue

    # Reprocess chunk slice to get clean normalized vector
    texto_chunk = "".join([t.text_with_ws for t in rango_chunk]).strip()
    doc_chunk = nlp(texto_chunk)
    resultado["chunks"].append(get_data(doc_chunk))

# 5️⃣ Save to JSON
print("Guardando estructura.json...")
with open("estructura.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False)

print(f"Éxito: {len(resultado['parrafos'])} párrafos, {len(resultado['chunks'])} chunks, "
      f"{len(resultado['frases'])} frases y {len(resultado['lineas'])} líneas vectorizadas.")