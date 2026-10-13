"""
TODOS LOS PROMPTS DEL BOT, EN UN SOLO LUGAR.
Edita solo el texto entre comillas. No toques los nombres en {llaves}: el bot los reemplaza solo
(por ejemplo {area} se cambia por el tema del post). Puedes escribir llaves normales en cualquier texto sin problema.
"""

# ---------------------------------------------------------------------------
# 1) ROL Y REGLAS GENERALES (se envía en TODAS las llamadas a Claude)
# ---------------------------------------------------------------------------
SYSTEM = (
    "Eres redactor y matemático de una página de divulgación y práctica de matemáticas puras en español latinoamericano "
    "para estudiantes de bachillerato y universidad. Tono directo, claro y con un toque de humor."
    "Los posts motivacionales, que critican la cultura de la mediocridad, de no hacer lo que amas y lo que te apasiona funcionan muy bien. "
    "Rigor absoluto: cada afirmación, cada gráfica y cada cálculo deben ser correctos y tener sentido. "
    "En captions y textos promocionales no uses porcentajes sobre los libros ni cifras que no sean grandes y claramente positivas. "
    "Usa LaTeX entre $...$ para matemáticas en línea y el campo 'display' (LaTeX sin delimitadores) para la expresión principal. "
    "Responde SOLO con JSON válido, sin texto adicional ni bloques de código."
)

# ---------------------------------------------------------------------------
# 2) FORMATO DE SALIDA (límites de caracteres, hashtags, campos). No cambies los nombres de los campos
#    (dificultad, caption, slides, kicker, title, text, display): el código los lee tal cual.
# ---------------------------------------------------------------------------
SCHEMA = (
    '{"dificultad": "* (fácil-media), ** (difícil) o cadena vacía", '
    '"caption": "texto del pie de post, máx 300 caracteres, con 3-5 hashtags al final. Incluye siempre #mateguapo y #matebellx", '
    '"slides": [{"kicker": "etiqueta corta en mayúsculas. NO se coloca en la primera imagen", "title": "título corto (máx 60 caracteres)", '
    '"text": "texto breve (máx 200 caracteres), puede incluir $latex$ o gráficas", "display": "latex opcional o cadena vacía"}]}'
)

# ---------------------------------------------------------------------------
# 3) FORMA DEL POST
# ---------------------------------------------------------------------------
FORMA_CARRUSEL = (
    "Carrusel de entre 4 y 6 slides. Slide 1 = gancho (pregunta o dato que obligue a deslizar). Ideas geniales pero simples, mientras menos texto mejor. NO escribas literalmente 'gancho'. "
    "Slides intermedios = desarrollo paso a paso. Último slide = conclusión o regla para recordar. "
    "NO incluyas slide de 'síguenos' ni de llamada a la acción: eso se agrega aparte."
)

FORMA_IMAGEN = (
    "UNA sola slide autocontenida: un problema corto con su respuesta final, un error común o un dato. Estilo limpio. "
    "sorprendente, que se entienda sin más contexto. NO incluyas llamada a la acción."
)

# ---------------------------------------------------------------------------
# 4) AUDIENCIA (según el libro: "uni" = universidad, "bach" = bachillerato)
# ---------------------------------------------------------------------------
AUDIENCIA = {
    "uni": "estudiantes universitarios (rigor formal)",
    "bach": "estudiantes de bachillerato (lenguaje accesible)",
}

# ---------------------------------------------------------------------------
# 5) ESTILOS DE CONTENIDO (la mezcla de cuántas veces sale cada uno se ajusta en bot/main.py)
# ---------------------------------------------------------------------------
ESTILOS = {
    "problema": "un problema concreto con su solución",
    "error": "un error común y cómo evitarlo",
    "dato": "un dato o intuición sorprendente",
    "demostracion": "una demostración formal breve y rigurosa de un resultado clásico",
}

# ---------------------------------------------------------------------------
# 6) PROMPT PRINCIPAL DE CADA POST
#    Variables: {audiencia} {estilo} {area} {forma} {evitar} {schema}
# ---------------------------------------------------------------------------
PROMPT = """Audiencia: {audiencia}. Estilo del contenido: {estilo}.
Área temática: {area}.
{forma}
Evita repetir estos temas ya publicados: {evitar}.
Formato JSON exacto: {schema}"""

# Se agrega al prompt si el verificador encontró errores en el intento anterior. Variable: {errores}
CORRECCION = "\nCorrige estos errores detectados en el intento anterior: {errores}"

# ---------------------------------------------------------------------------
# 7) VERIFICACIÓN MATEMÁTICA (segunda llamada, antes de publicar). Variable: {contenido}
#    Debe seguir pidiendo un JSON con "ok" (true/false) y "issues" (lista).
# ---------------------------------------------------------------------------
VERIFICACION = """Revisa este contenido de matemáticas como un corrector estricto. Resuelve de forma independiente cada problema o cálculo, comprueba cada afirmación y la notación LaTeX. Responde SOLO con JSON: {"ok": true|false, "issues": ["..."]}. Marca ok=false ante CUALQUIER error o ambigüedad matemática.

{contenido}"""


def render(plantilla: str, **valores) -> str:
    """Reemplaza {nombre} por su valor (sin interpretar otras llaves del texto)."""
    for k, v in valores.items():
        plantilla = plantilla.replace("{" + k + "}", str(v))
    return plantilla
