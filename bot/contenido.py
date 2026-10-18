"""Comprobaciones de forma del contenido de cada post (antes vivían en bot/llm.py, junto a la API de Claude).
El contenido ya no lo genera la API: lo escribe la tarea programada semanal y entra a la cola (bot/cola.py).
Aquí se aplican exactamente las mismas comprobaciones que el bot aplicaba a la respuesta de la API."""
from . import curvas
from .config import slides_rango
from .frases import POR_ID as FRASES


def normalizar(plan: dict, content: dict) -> list[str]:
    """Ajusta detalles de forma y devuelve los problemas que obligan a reescribir (lista vacía = correcto)."""
    slides = content.get("slides")
    if not isinstance(slides, list) or not all(isinstance(s, dict) for s in slides):
        return ["El campo slides debe ser una lista de objetos"]
    lo, hi = slides_rango(plan["kind"], plan["formato"])
    if not lo <= len(slides) <= hi:
        return [f"Número de slides inválido: {len(slides)} (debe ser exactamente {lo})"]
    s = slides[0]
    if s.get("layout") == "frase":  # las frases célebres salen tal cual del banco curado (ver contenido_frase)
        return [] if plan.get("frase_id") in FRASES and s.get("title") == FRASES[plan["frase_id"]]["texto"] else [
            "La frase no coincide con el banco curado (bot/frases.py)"]
    for k in ("title", "text", "display"):
        s[k] = str(s.get(k) or "").strip()
    for k in ("kicker", "layout"):
        s.pop(k, None)
    if not s["title"]:
        return ["Falta el título (title) de la imagen"]
    if plan.get("curva_tipo"):
        spec = s.get("curva") if isinstance(s.get("curva"), dict) else {}
        s["curva"] = curvas.normalizar({"tipo": plan["curva_tipo"], "params": spec.get("params") or {}})
        s["display"] = curvas.latex(s["curva"])  # la ecuación sale del código: siempre coincide con el dibujo
        s["layout"] = "curva"
    else:
        s.pop("curva", None)
        s["layout"] = "normal"
        if not s["display"] and not s["text"]:
            return ["Falta la fórmula protagonista (display) o la línea de apoyo (text)"]
    if not content.get("caption"):
        return ["Falta el caption"]
    return []


def contenido_frase(plan: dict) -> dict:
    """Las frases célebres no las escribe nadie: se publican tal cual del banco curado (bot/frases.py)."""
    f = FRASES[plan["frase_id"]]
    cita = f"«{f['texto']}»\n— {f['autor']}, {f['fuente']}"
    return {
        "tema": f"frase de {f['autor']}",
        "caption": f"{cita}\n\nGuárdala para cuando necesites recordar por qué amas las matemáticas.\n#matebellx #mateguapo #frasescelebres",
        "threads": f"{cita} 💛",
        "slides": [{"layout": "frase", "title": f["texto"], "text": "", "display": "", "autor": f["autor"], "fuente": f["fuente"]}],
        "_idea": {"tema": f["id"], "gancho": f["texto"][:70]},
    }
