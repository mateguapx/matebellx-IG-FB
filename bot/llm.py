"""Generación y verificación de contenido con la API de Claude. Los textos de los prompts viven en bot/prompts.py."""
import json
import re
import anthropic
from . import prompts as P
from .config import MODEL

client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno


def _ask(user: str, max_tokens: int = 8000) -> str:
    r = client.messages.create(
        model=MODEL, max_tokens=max_tokens, system=P.SYSTEM,
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
    return P.render(
        P.PROMPT,
        audiencia=P.AUDIENCIA.get(nivel, P.AUDIENCIA["uni"]),
        estilo=P.ESTILOS.get(estilo, P.ESTILOS["problema"]),
        area=area,
        forma=P.FORMA_CARRUSEL if kind == "carousel" else P.FORMA_IMAGEN,
        evitar="; ".join(avoid[-40:]) or "ninguno",
        schema=P.SCHEMA,
    )


def _verify(content: dict) -> dict:
    prompt = P.render(P.VERIFICACION, contenido=json.dumps(content, ensure_ascii=False))
    return _json(_ask(prompt, max_tokens=6000))


def generate(kind: str, area: str, avoid: list[str], nivel: str = "uni", estilo: str = "problema", retries: int = 3) -> dict:
    prompt = _prompt(kind, area, avoid, nivel, estilo)
    last_issues: list[str] = []
    for _ in range(retries):
        extra = P.render(P.CORRECCION, errores=last_issues) if last_issues else ""
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
