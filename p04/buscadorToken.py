from pathlib import Path
from bs4 import BeautifulSoup
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

# --- 1. CARGA Y PREPROCESAMIENTO ---
def cargar_chunks(ruta):
    """Carga el HTML y extrae los párrafos como chunks."""
    html_crudo = Path(ruta).read_text(encoding="utf-8")
    soup = BeautifulSoup(html_crudo, "html.parser")
    # Filtramos párrafos muy cortos para evitar ruido
    return [p.get_text(separator=" ").strip() for p in soup.find_all('p') if len(p.get_text()) > 30]

def preprocesar_texto_clasico(texto, nlp):
    """
    Aplica PLN clásico: Tokeniza, elimina stopwords/puntuación y extrae el lema.
    Ej: "Los gatos corren" -> "gato correr"
    """
    doc = nlp(texto.lower())
    lemas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct and token.text.strip()]
    return " ".join(lemas)

# --- 2. MOTORES DE BÚSQUEDA ---
class BuscadorP4:
    def __init__(self, ruta_archivo):
        print("[*] Cargando corpus...")
        self.chunks_originales = cargar_chunks(ruta_archivo)
        
        print("[*] Cargando modelo lingüístico (spaCy) para Búsqueda Clásica...")
        self.nlp = spacy.load("es_core_news_sm")
        
        print("[*] Lematizando corpus... (esto puede tardar unos segundos)")
        self.chunks_lematizados = [preprocesar_texto_clasico(chunk, self.nlp) for chunk in self.chunks_originales]
        
        # Indice TF-IDF para la búsqueda clásica
        self.vectorizer_tfidf = TfidfVectorizer()
        self.matriz_tfidf = self.vectorizer_tfidf.fit_transform(self.chunks_lematizados)
        
        print("[*] Cargando modelo neuronal para Búsqueda Semántica...")
        # Usamos un modelo multilingüe ligero y rápido
        self.embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        print("[*] Calculando embeddings del corpus...")
        self.embeddings_corpus = self.embedder.encode(self.chunks_originales, show_progress_bar=True)
        print("[✓] ¡Sistema listo!\n")

    def mostrar_resultados(self, similitudes, top_k=3):
        """Función auxiliar para rankear y mostrar los mejores resultados."""
        indices_top = similitudes.argsort()[::-1][:top_k]
        encontrado = False
        
        for i, idx in enumerate(indices_top):
            score = similitudes[idx]
            if score > 0.05:  # Umbral de relevancia
                print(f"\n--- Resultado {i+1} (Score: {score:.4f}) ---")
                print(self.chunks_originales[idx])
                encontrado = True
                
        if not encontrado:
            print("\nNo se encontraron resultados relevantes.")

    def busqueda_clasica(self, consulta):
        """Búsqueda por lemas e índice TF-IDF."""
        consulta_procesada = preprocesar_texto_clasico(consulta, self.nlp)
        print(f"\n[Info] Consulta lematizada: '{consulta_procesada}'")
        
        vector_consulta = self.vectorizer_tfidf.transform([consulta_procesada])
        similitudes = cosine_similarity(vector_consulta, self.matriz_tfidf).flatten()
        self.mostrar_resultados(similitudes)

    def busqueda_semantica(self, consulta):
        """Búsqueda profunda usando Embeddings."""
        # Se codifica la consulta tal cual, sin quitar stopwords, para mantener el contexto
        embedding_consulta = self.embedder.encode([consulta])
        similitudes = cosine_similarity(embedding_consulta, self.embeddings_corpus).flatten()
        self.mostrar_resultados(similitudes)

# --- 3. MENÚ INTERACTIVO ---
def main():
    ruta = "2000-h.htm"
    buscador = BuscadorP4(ruta)
    
    while True:
        print("\n" + "="*40)
        print("   MOTOR DE BÚSQUEDA - EL QUIJOTE (P4)")
        print("="*40)
        print("1. Búsqueda Clásica (Lemas + TF-IDF)")
        print("2. Búsqueda Semántica (Embeddings)")
        print("3. Salir")
        
        opcion = input("Elige una opción: ")
        
        if opcion == '3':
            break
        elif opcion in ['1', '2']:
            consulta = input("\nIntroduce tu consulta: ")
            if not consulta.strip():
                continue
                
            if opcion == '1':
                buscador.busqueda_clasica(consulta)
            elif opcion == '2':
                buscador.busqueda_semantica(consulta)
        else:
            print("Opción inválida.")

if __name__ == "__main__":
    main()