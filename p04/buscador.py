from pathlib import Path
from bs4 import BeautifulSoup
from joblib import Parallel, delayed
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog

def buscar_palabra_en_linea(num_linea: int, texto_linea: str, palabra_objetivo: str):
    """
    Busca la palabra objetivo en una línea de texto.
    """
    if palabra_objetivo.lower() in texto_linea.lower():
        return num_linea, texto_linea.strip()
    return None

class BuscadorPLNApp(App):
    """Aplicación TUI para buscar texto en HTML del Quijote."""
    
    BINDINGS = [("q", "quit", "Salir")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(highlight=True, markup=True)
        yield Footer()

    def on_ready(self) -> None:
        self.ejecutar_busqueda()

    def ejecutar_busqueda(self) -> None:
        log = self.query_one(RichLog)
        
        palabra_objetivo = "dulcinea"
        ruta_archivo = Path("2000-h.htm")
        
        if not ruta_archivo.exists():
            log.write(f"[bold red]Error:[/bold red] No se encontró el archivo '{ruta_archivo}'.")
            return
            
        log.write("[bold cyan]1. Leyendo el fragmento HTML con Pathlib...[/bold cyan]")
        html_crudo = ruta_archivo.read_text(encoding="utf-8")
        
        log.write("[bold cyan]2. Extrayendo texto limpio con BeautifulSoup4...[/bold cyan]")
        soup = BeautifulSoup(html_crudo, "html.parser")
        texto_limpio = soup.get_text(separator="\n")
        
        lineas = [linea for linea in texto_limpio.split("\n") if linea.strip()]
        
        log.write(f"[bold cyan]3. Procesando {len(lineas)} líneas con Joblib (backend='threading')...[/bold cyan]\n")
        
        # ¡AQUÍ ESTÁ EL CAMBIO CLAVE! Añadimos backend="threading"
        resultados_crudos = Parallel(n_jobs=-1, backend="threading")(
            delayed(buscar_palabra_en_linea)(i + 1, linea, palabra_objetivo) 
            for i, linea in enumerate(lineas)
        )
        
        coincidencias = [res for res in resultados_crudos if res is not None]
        
        log.write(f"[bold green]¡Análisis Completado![/bold green]")
        log.write(f"La palabra [bold yellow]'{palabra_objetivo}'[/bold yellow] aparece en [bold red]{len(coincidencias)}[/bold red] líneas distintas.\n")
        log.write("-" * 50)
        
        for numero_linea, texto_linea in coincidencias:
            log.write(f"[dim]Línea {numero_linea}:[/dim] {texto_linea}")
            
        log.write("\n[italic]Presiona 'Q' para salir de la aplicación.[/italic]")

if __name__ == "__main__":
    app = BuscadorPLNApp()
    app.run()