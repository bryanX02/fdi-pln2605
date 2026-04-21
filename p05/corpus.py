# Carga de corpus de texto
#
# PLN 2025/2026 (FDI UCM)

from pathlib import Path


def load_corpus(path="alicia"):
    """Carga todos los archivos .txt de un directorio y los concatena.

    Si `path` es un archivo, lo lee directamente.
    Si es un directorio, lee todos los .txt que contenga.
    """
    path = Path(path)

    if path.is_file():
        return path.read_text(encoding="utf-8")

    # Leemos todos los .txt del directorio y los unimos con doble salto
    textos = []
    for archivo in sorted(path.glob("*.txt")):
        textos.append(archivo.read_text(encoding="utf-8"))

    if not textos:
        raise FileNotFoundError(f"No se encontraron archivos .txt en {path}")

    return "\n\n".join(textos)


if __name__ == "__main__":
    import sys

    corpus_path = sys.argv[1] if len(sys.argv) > 1 else "alicia"
    text = load_corpus(corpus_path)
    print(f"Corpus cargado: {len(text):,} caracteres")
    print(f"Primeros 200 chars: {text[:200]}")
