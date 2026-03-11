TEMPLATES = {
    "presentacion": (
        "Hola {dest}, soy {remi}. "
        "Actualmente tengo los siguientes recursos: {tem}. "
        "Para cumplir mi objetivo, estoy buscando: {precisa}. "
        "¿Te interesa colaborar?"
    ),
    "negociacion": (
        "Propuesta de intercambio para {dest}: "
        "Ofrezco {ofrece} a cambio de {pede}. "
        "¿Qué te parece?"
    ),
    "aceptar_trato": (
        "¡Acepto tu propuesta, {dest}! Procederé al envío de los recursos ahora mismo."
    ),
    "confirmacion_envio": (
        "Te informo que ya te he enviado los siguientes recursos: {recursos_enviados}. "
        "Por favor, confirma la recepción en tu dashboard."
    ),
}


def render_template(template_name: str, data: dict) -> str:
    """
    Rellena la plantilla indicada con los datos proporcionados.

    Parámetros
    ----------
    template_name : str
        Uno de los valores válidos: "presentacion", "negociacion",
        "aceptar_trato", "confirmacion_envio".
    data : dict
        Diccionario con los campos necesarios para la plantilla elegida:
        - presentacion       : dest, remi, tem, precisa
        - negociacion        : dest, ofrece, pede
        - aceptar_trato      : dest
        - confirmacion_envio : dest, recursos_enviados

    Retorna
    -------
    str
        Mensaje final formateado en español.

    Lanza
    -----
    ValueError
        Si el template_name no es reconocido.
    KeyError
        Si algún campo obligatorio falta en data.
    """
    if template_name not in TEMPLATES:
        raise ValueError(
            f"Plantilla '{template_name}' no reconocida. "
            f"Opciones válidas: {list(TEMPLATES.keys())}"
        )

    def _fmt(value):
        """
        Formatea valores a lenguaje natural (español):
        - lista vacía      -> "recursos a convenir"
        - ['trigo']        -> "1 trigo"
        - ['trigo','vino'] -> "1 trigo o 1 vino"
        - "" / None        -> "recursos a convenir"
        """
        if isinstance(value, list):
            if len(value) == 0:
                return "recursos a convenir"
            if len(value) == 1:
                return f"1 {value[0]}"
            return " o ".join(f"1 {item}" for item in value)

        if value is None:
            return "recursos a convenir"

        # Cadenas vacías o solo espacios en blanco
        if isinstance(value, str) and value.strip() == "":
            return "recursos a convenir"

        return value

    formatted_data = {k: _fmt(v) for k, v in data.items()}

    try:
        return TEMPLATES[template_name].format(**formatted_data)
    except KeyError as e:
        raise KeyError(
            f"Campo obligatorio faltante para la plantilla '{template_name}': {e}"
        )
