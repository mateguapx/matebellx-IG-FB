"""Generación y verificación de contenido con la API de Claude. Solo texto/LaTeX: las imágenes se renderizan con código."""
import json
import re
import anthropic
from .config import MODEL

client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno

SYSTEM = (
    "Eres redactor y matemático de una página de divulgación y práctica de matemáticas en español latinoamericano "
    "para estudiantes de bachillerato y universidad. Tono directo, claro y con un toque de humor. "
    "Rigor absoluto: cada afirmación y cada cálculo deben ser correctos. "
    "En captions y textos promocionales no uses porcentajes sobre los libros ni cifras que no sean grandes y claramente positivas. "
    "Usa LaTeX entre $...$ para matemáticas en línea y el campo 'display' (LaTeX sin delimitadores) para la expresión principal. "
    "Responde SOLO con JSON válido, sin texto adicional ni bloques de código."
)

SCHEMA = (
    '{"dificultad": "* (fácil-media), ** (difícil) o cadena vacía", "caption": "texto del pie de post, máx 300 caracteres, con 3-5 hashtags al final", '
    '"slides": [{"kicker": "etiqueta corta en mayúsculas", "title": "título corto (máx 60 caracteres)", '
    '"text": "texto breve (máx 220 caracteres), puede incluir $latex$", "display": "latex opcional o cadena vacía"}]}'
)


def _ask(user: str, max_tokens: int = 8000) -> str:
    r = client.messages.create(
        model=MODEL, max_tokens=max_tokens, system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    # La respuesta puede traer bloques de razonamiento antes del texto: se concatenan solo los de tipo "text".
    text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    if not text.strip():
        raise RuntimeError(f"Respuesta sin texto (stop_reason={r.stop_reason}); sube max_tokens o baja el esfuerzo.")
    return text


def _json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def _prompt(kind: str, area: str, avoid: list[str], nivel: str = "uni", estilo: str = "problema") -> str:
    if kind == "carousel":
        shape = (
            "Carrusel de entre 4 y 6 slides. Slide 1 = gancho (pregunta o dato que obligue a deslizar). "
            "Slides intermedios = desarrollo paso a paso. Último slide = conclusión o regla para recordar. "
            "NO incluyas slide de 'síguenos' ni de llamada a la acción: eso se agrega aparte."
        )
    else:
        shape = (
            "UNA sola slide autocontenida: un problema corto con su respuesta final, un error común o un dato "
            "sorprendente, que se entienda sin más contexto. NO incluyas llamada a la acción."
        )
    avoid_txt = "; ".join(avoid[-40:]) or "ninguno"
    audiencia = "estudiantes de bachillerato (lenguaje accesible)" if nivel == "bach" else "estudiantes universitarios (rigor formal)"
    estilos = {
        "problema": "un problema concreto con su solución",
        "error": "un error común y cómo evitarlo",
        "dato": "un dato o intuición sorprendente",
        "demostracion": "una demostración formal breve y rigurosa de un resultado clásico",
    }
    return (
        f"Audiencia: {audiencia}. Estilo del contenido: {estilos.get(estilo, estilos['problema'])}.\n"
        f"Área temática: {area}.\n{shape}\n"
        f"Evita repetir estos temas ya publicados: {avoid_txt}.\n"
        f"Formato JSON exacto: {SCHEMA}"
    )


def _verify(content: dict) -> dict:
    prompt = (
        "Revisa este contenido de matemáticas como un corrector estricto. Resuelve de forma independiente cada problema "
        "o cálculo, comprueba cada afirmación y la notación LaTeX. Responde SOLO con JSON: "
        '{"ok": true|false, "issues": ["..."]}. Marca ok=false ante CUALQUIER error o ambigüedad matemática.\n\n'
        + json.dumps(content, ensure_ascii=False)
    )
    return _json(_ask(prompt, max_tokens=6000))


def generate(kind: str, area: str, avoid: list[str], nivel: str = "uni", estilo: str = "problema", retries: int = 3) -> dict:
    prompt = _prompt(kind, area, avoid, nivel, estilo)
    last_issues: list[str] = []
    for _ in range(retries):
        extra = f"\nCorrige estos errores detectados en el intento anterior: {last_issues}" if last_issues else ""
        content = _json(_ask(prompt + extra))
        slides = content.get("slides", [])
        n_ok = (4 <= len(slides) <= 6) if kind == "carousel" else (len(slides) == 1)
        if not n_ok:
            last_issues = [f"Número de slides inválido: {len(slides)}"]
            continue
        check = _verify(content)
        if check.get("ok"):
            return content
        last_issues = check.get("issues", ["error no especificado"])
    raise RuntimeError(f"No se obtuvo contenido verificado tras {retries} intentos: {last_issues}")
