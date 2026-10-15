"""Generación y verificación de contenido con la API de Claude. Los textos de los prompts viven en bot/prompts.py.
Flujo: ideas -> elegir la mejor -> escribir -> verificar (con reintentos y, si hace falta, la segunda mejor idea)."""
import json
import re
import anthropic
from . import curvas
from . import prompts as P
from .config import MODEL, N_IDEAS, PESOS_IDEA, slides_rango

_client = None


def _cli():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno
    return _client


def _ask(user: str, max_tokens: int = 8000) -> str:
    r = _cli().messages.create(
        model=MODEL, max_tokens=max_tokens, system=P.SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    # La respuesta puede traer bloques de razonamiento antes del texto: se concatenan solo los de tipo "text".
    text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    if not text.strip():
        raise RuntimeError(f"Respuesta sin texto (stop_reason={r.stop_reason}); sube max_tokens.")
    return text


def _json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            return json.loads(text[a:b + 1])
        raise


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def contexto_rendimiento(insights: dict | None) -> str:
    """Convierte state/insights.json en el bloque de texto para el prompt de ideas."""
    if not insights or not insights.get("top"):
        return ""

    def linea(p: dict) -> str:
        m = p.get("metricas", {})
        return (f"- \"{p.get('titulo', '')}\" (formato {p.get('formato')}, gancho {p.get('hook')}, tema {p.get('tema')}; "
                f"alcance {m.get('reach', '?')}, compartidos {m.get('shares', '?')}, guardados {m.get('saved', '?')}, "
                f"comentarios {m.get('comments', '?')})")

    return P.render(P.CONTEXTO_RENDIMIENTO,
                    top="\n".join(linea(p) for p in insights["top"]),
                    bottom="\n".join(linea(p) for p in insights.get("bottom", [])) or "- (sin datos)")


def _comun(plan: dict) -> dict:
    extra = []
    if plan.get("curva_tipo"):
        extra.append(P.render(P.CURVA, curva=plan["curva_tipo"], catalogo=curvas.descripcion_catalogo()))
    if plan.get("serie"):
        extra.append(P.render(P.SERIE, serie=plan["serie"]))
    return dict(
        manual=P.MANUAL,
        formato=P.FORMATOS[plan["formato"]],
        forma=P.FORMA[plan["kind"]],
        audiencia=P.AUDIENCIA.get(plan["nivel"], P.AUDIENCIA["general"]),
        area=plan["area"],
        extra="\n".join(extra),
    )


def ideas(plan: dict, evitar: list[str], contexto: str = "") -> list[dict]:
    """Pide N ideas y las devuelve ordenadas de mejor a peor según los pesos de config.PESOS_IDEA."""
    prompt = P.render(P.IDEAS, n_ideas=N_IDEAS, hook=P.HOOKS.get(plan["hook"], plan["hook"]),
                      contexto=contexto, evitar="; ".join(evitar[-60:]) or "ninguno", **_comun(plan))
    data = _json(_ask(prompt, max_tokens=6000))
    lista = [i for i in data.get("ideas", []) if isinstance(i, dict) and i.get("gancho")]
    if not lista:
        raise RuntimeError("Claude no devolvió ideas válidas")
    w = PESOS_IDEA.get(plan["formato"], PESOS_IDEA["default"])
    for i in lista:
        i["_puntaje"] = round(sum(_num(i.get(k)) * peso for k, peso in w.items()), 2)
    return sorted(lista, key=lambda i: i["_puntaje"], reverse=True)


def _normalizar(plan: dict, content: dict) -> list[str]:
    """Ajusta detalles de forma y devuelve los problemas que obligan a reescribir."""
    slides = content.get("slides")
    if not isinstance(slides, list) or not all(isinstance(s, dict) for s in slides):
        return ["El campo slides debe ser una lista de objetos"]
    lo, hi = slides_rango(plan["kind"], plan["formato"])
    if not lo <= len(slides) <= hi:
        return [f"Número de slides inválido: {len(slides)} (debe ser exactamente {lo})"]
    s = slides[0]
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


def _verify(plan: dict, content: dict) -> dict:
    limpio = {k: v for k, v in content.items() if not k.startswith("_")}
    prompt = P.render(P.VERIFICACION, formato=plan["formato"], contenido=json.dumps(limpio, ensure_ascii=False))
    return _json(_ask(prompt, max_tokens=6000))


def write(plan: dict, idea: dict, retries: int = 3) -> tuple[dict | None, list[str]]:
    idea_txt = json.dumps({k: v for k, v in idea.items() if not k.startswith("_")}, ensure_ascii=False)
    lo, hi = slides_rango(plan["kind"], plan["formato"])
    base = P.render(P.ESCRIBIR, idea=idea_txt, slides=f"{lo}" if lo == hi else f"entre {lo} y {hi}",
                    schema=P.SCHEMA, **_comun(plan))
    issues: list[str] = []
    for _ in range(retries):
        extra = P.render(P.CORRECCION, errores=issues) if issues else ""
        try:
            content = _json(_ask(base + extra))
        except (json.JSONDecodeError, ValueError):
            issues = ["La respuesta no era JSON válido; responde solo con el JSON pedido"]
            continue
        issues = _normalizar(plan, content)
        if issues:
            continue
        check = _verify(plan, content)
        if check.get("ok"):
            return content, []
        issues = check.get("issues") or ["error no especificado"]
    return None, issues


def generate(plan: dict, evitar: list[str], insights: dict | None = None) -> dict:
    """plan viene de bot/planner.py. Devuelve el contenido verificado, con la idea elegida en '_idea'."""
    # Los posts de exploración no ven los datos de rendimiento, para no sesgarlos hacia lo de siempre.
    contexto = contexto_rendimiento(insights) if plan.get("modo") != "explorar" else ""
    candidatas = ideas(plan, evitar, contexto)
    ultimo: list[str] = []
    for idea, intentos in zip(candidatas[:2], (3, 2)):  # mejor idea con 3 intentos; si falla, la segunda con 2
        content, ultimo = write(plan, idea, retries=intentos)
        if content:
            content["_idea"] = {k: v for k, v in idea.items() if k != "por_que"}
            content["_ideas_descartadas"] = [i.get("tema") for i in candidatas if i is not idea]
            return content
        print(f"Idea descartada tras verificación: {idea.get('tema')} -> {ultimo}")
    raise RuntimeError(f"No se obtuvo contenido verificado: {ultimo}")
