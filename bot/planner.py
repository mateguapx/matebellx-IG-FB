"""Decide QUÉ publicar en cada post: formato, gancho, tema y fondo.
- 70% de las veces aprovecha lo que mejor ha funcionado (pesos de state/weights.json, calculados por bot/learn.py).
- 30% explora al azar para seguir descubriendo cosas nuevas.
- Enfriamiento: no repite un tema usado en los últimos posts, para que el contenido no sea monótono."""
import random
import unicodedata
from .config import (BOOKS, COOLDOWN_TEMA, EXPLORE_P, FONDOS_DEFAULT, FONDOS_POR_TEMA, GAMMA, HOOKS, HOOKS_POR_FORMATO,
                     MIN_DATOS, SLOTS, TEMAS_LIBRES, TEMAS_MOTIVACION, TEMAS_RETO_BASICO, TEMAS_RETO_LOGICO, TEMAS_TIPS)


def _sin_acentos(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c))


def fondos_para(texto: str) -> list[str]:
    """Motivos de fondo que encajan con el tema (bot/config.py → FONDOS_POR_TEMA)."""
    t = _sin_acentos(texto)
    out: list[str] = []
    for claves, motivos in FONDOS_POR_TEMA:
        if any(c in t for c in claves):
            out += [m for m in motivos if m not in out]
    return out or list(FONDOS_DEFAULT)


def _factor(weights: dict, dim: str, valor: str) -> float:
    return float(weights.get(dim, {}).get(valor, 1.0))


def _elegir(opciones: dict[str, float], weights: dict, dim: str, explorar: bool, usar_pesos: bool,
            rng: random.Random) -> str:
    """opciones: {valor: peso_base}. Explorar = uniforme; si no, peso_base × factor_aprendido^GAMMA."""
    claves = list(opciones)
    if explorar:
        return rng.choice(claves)
    pesos = [opciones[k] * (_factor(weights, dim, k) ** GAMMA if usar_pesos else 1.0) for k in claves]
    return rng.choices(claves, weights=pesos, k=1)[0]


def _sin_recientes(candidatos: list[str], recientes: list[str]) -> list[str]:
    libres = [c for c in candidatos if c not in recientes]
    return libres or candidatos


def elegir(tipo: int, posts: list[dict], weights: dict, rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()
    slot = SLOTS[tipo]
    usar_pesos = int(weights.get("n", 0)) >= MIN_DATOS
    explorar = usar_pesos and rng.random() < EXPLORE_P
    recientes = [p.get("tema_clave") for p in posts[-COOLDOWN_TEMA:]]
    recientes_area = [p.get("area") for p in posts[-COOLDOWN_TEMA * 2:]]

    # 1) Libro (solo posts con palabra clave) -> define nivel y área
    key = None
    nivel = "general"
    if slot["tema"] == "libro":
        claves = _sin_recientes([f"libro:{k}" for k in BOOKS], recientes)
        tema_clave = _elegir({c: 1.0 for c in claves}, weights, "tema", explorar, usar_pesos, rng)
        key = tema_clave.split(":", 1)[1]
        nivel = BOOKS[key]["nivel"]

    # 2) Formato
    formatos = {f: w for f, w in slot["formatos"].items() if f != "demostracion" or nivel == "uni"}
    formato = _elegir(formatos, weights, "formato", explorar, usar_pesos, rng)

    # 3) Tema / área
    if slot["tema"] == "libro":
        area = rng.choice(_sin_recientes(BOOKS[key]["areas"], recientes_area))
    else:
        banco = {"reto_basico": TEMAS_RETO_BASICO, "reto_logico": TEMAS_RETO_LOGICO,
                 "motivacion": TEMAS_MOTIVACION, "tips": TEMAS_TIPS}.get(formato, TEMAS_LIBRES)
        tema_clave = _elegir({t: 1.0 for t in _sin_recientes(banco, recientes)}, weights, "tema", explorar, usar_pesos, rng)
        area = tema_clave

    # 4) Gancho
    permitidos = HOOKS_POR_FORMATO.get(formato) or [h for h in HOOKS if h not in ("desafio", "humor")]
    hook = _elegir({h: 1.0 for h in permitidos}, weights, "hook", explorar, usar_pesos, rng)
    # 5) Fondo según el tema (sin repetir el del post anterior si hay alternativas)
    candidatos = _sin_recientes(fondos_para(f"{area} {key or ''}"), [p.get("fondo") for p in posts[-1:]])
    fondo = _elegir({f: 1.0 for f in candidatos}, weights, "fondo", explorar, usar_pesos, rng)
    return {
        "tipo": tipo, "kind": slot["kind"], "cta": slot["cta"], "formato": formato, "hook": hook,
        "tema_clave": tema_clave, "area": area, "key": key, "nivel": nivel, "fondo": fondo,
        "semilla": rng.randrange(1, 10**6),
        "modo": "explorar" if explorar else ("explotar" if usar_pesos else "inicial"),
    }
