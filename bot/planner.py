"""Decide QUÉ publicar en cada post: formato, gancho, tema, fondo y (si aplica) la curva y la idea del banco.
- Series semanales (bot/config.py → SERIES): ciertos días un horario tiene formato fijo (ej. Domingo de demostraciones).
- 70% de las veces aprovecha lo que mejor ha funcionado (pesos de state/weights.json, calculados por bot/learn.py).
- 30% explora al azar para seguir descubriendo cosas nuevas.
- Banco de ideas (state/ideas.json, lo llena bot/ideas.py cada semana): si hay una idea pendiente del formato, se usa.
- Enfriamiento: no repite un tema usado en los últimos posts, para que el contenido no sea monótono."""
import random
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo
from .config import (BOOKS, COOLDOWN_TEMA, EXPLORE_P, FONDOS_CURVA, FONDOS_DEFAULT, FONDOS_POR_TEMA, GAMMA, HOOKS,
                     HOOKS_POR_FORMATO, MIN_DATOS, SERIE_DIARIA, SERIES, SLOTS, TEMAS)
from .curvas import CATALOGO
from .frases import FRASES

TZ = ZoneInfo("America/Mexico_City")
P_USAR_IDEA = 0.6  # probabilidad de usar una idea del banco cuando hay alguna pendiente del formato


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


def _sin_recientes(candidatos: list[str], recientes: list) -> list[str]:
    libres = [c for c in candidatos if c not in recientes]
    return libres or candidatos


def elegir(tipo: int, posts: list[dict], weights: dict, rng: random.Random | None = None,
           ideas: list[dict] | None = None, ahora: datetime | None = None) -> dict:
    rng = rng or random.Random()
    ahora = (ahora or datetime.now(TZ)).astimezone(TZ)
    slot = SLOTS[tipo]
    usar_pesos = int(weights.get("n", 0)) >= MIN_DATOS
    explorar = usar_pesos and rng.random() < EXPLORE_P
    recientes = [p.get("tema_clave") for p in posts[-COOLDOWN_TEMA:]]
    recientes_area = [p.get("area") for p in posts[-COOLDOWN_TEMA * 2:]]

    # 1) Libro (solo posts con palabra clave) -> nivel
    key, nivel = None, "general"
    if slot["tema"] == "libro":
        claves = _sin_recientes([f"libro:{k}" for k in BOOKS], recientes)
        key = _elegir({c: 1.0 for c in claves}, weights, "tema", explorar, usar_pesos, rng).split(":", 1)[1]
        nivel = BOOKS[key]["nivel"]

    # 2) Formato (las series semanales mandan)
    serie = SERIE_DIARIA.get(tipo)
    fijo = SERIES.get(ahora.weekday(), {}).get(tipo)
    if fijo:
        formato, serie = fijo
    else:
        formato = _elegir(slot["formatos"], weights, "formato", explorar, usar_pesos, rng)

    # 3) Tema / área (y curva)
    curva, idea = None, None
    pendientes = [i for i in (ideas or []) if not i.get("usada") and i.get("formato") == formato]
    frase = None
    if formato == "frase":  # del banco curado, sin repetir en los últimos 120 posts
        usadas = {p.get("frase_id") for p in posts[-120:]}
        frase = rng.choice([f for f in FRASES if f["id"] not in usadas] or FRASES)
        tema_clave, area = f"frase:{frase['autor']}", frase["texto"]
    elif formato == "curva":
        tipos = _sin_recientes(list(CATALOGO), [p.get("curva_tipo") for p in posts[-8:]])
        curva = _elegir({t: 1.0 for t in tipos}, weights, "curva", explorar, usar_pesos, rng)
        tema_clave = f"curva:{curva}"
        area = CATALOGO[curva][0]
    elif slot["tema"] == "libro":
        area = rng.choice(_sin_recientes(BOOKS[key]["areas"], recientes_area))
        tema_clave = f"libro:{key}"
    elif pendientes and rng.random() < P_USAR_IDEA:
        idea = rng.choice(pendientes)
        tema_clave, area = f"idea:{formato}", idea["idea"]
    else:
        banco = TEMAS.get(formato) or TEMAS["identidad"]
        tema_clave = _elegir({t: 1.0 for t in _sin_recientes(banco, recientes)}, weights, "tema", explorar, usar_pesos, rng)
        area = tema_clave

    # 4) Gancho
    permitidos = ["asombro"] if formato == "frase" else (HOOKS_POR_FORMATO.get(formato) or HOOKS)
    hook = _elegir({h: 1.0 for h in permitidos}, weights, "hook", explorar, usar_pesos, rng)

    # 5) Fondo (sin repetir el del post anterior si hay alternativas)
    base = FONDOS_CURVA if formato == "curva" else fondos_para(f"{area} {key or ''}")
    candidatos = _sin_recientes(base, [p.get("fondo") for p in posts[-1:]])
    fondo = _elegir({f: 1.0 for f in candidatos}, weights, "fondo", explorar, usar_pesos, rng)
    return {
        "tipo": tipo, "kind": slot["kind"], "cta": slot["cta"], "formato": formato, "hook": hook,
        "tema_clave": tema_clave, "area": area, "key": key, "nivel": nivel, "fondo": fondo,
        "curva_tipo": curva, "serie": serie, "idea_id": idea.get("id") if idea else None,
        "frase_id": frase["id"] if frase else None,
        "semilla": rng.randrange(1, 10**6),
        "modo": "explorar" if explorar else ("explotar" if usar_pesos else "inicial"),
    }
