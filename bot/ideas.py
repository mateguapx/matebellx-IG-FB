"""Banco de ideas para los próximos posts (state/ideas.json), sin la API de Claude.
Uso:
  python -m bot.ideas instrucciones > ideas.txt   # qué formatos necesitan ideas y con qué reglas (el prompt BANCO_IDEAS)
  python -m bot.ideas agregar ideas.json          # agrega las ideas escritas: [{"formato": "...", "idea": "..."}]

La tarea programada semanal lo rellena antes de planear la cola. bot/planner.py usa estas ideas como tema de partida
(bot/cola.py → plan) y bot/main.py las marca como usadas al publicar."""
import json
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from . import prompts as P
from .config import ROOT, SLOTS

STATE = ROOT / "state"
MINIMO = 8          # ideas pendientes deseadas por formato
POR_LLAMADA = 30    # ideas que se piden en cada ronda
FORMATOS = sorted({f for s in SLOTS.values() for f in s["formatos"] if f not in ("curva", "frase")})  # curvas y frases tienen su propio catálogo


def _load(name: str, default):
    p = STATE / name
    try:
        return json.loads(p.read_text()) if p.exists() else default
    except json.JSONDecodeError:
        return default


def _clave(t: str) -> str:
    t = "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c))
    return " ".join("".join(c if c.isalnum() else " " for c in t).split())[:80]


def faltan() -> list[str]:
    banco = _load("ideas.json", [])
    pendientes = {f: sum(1 for i in banco if not i.get("usada") and i.get("formato") == f) for f in FORMATOS}
    print("Ideas pendientes por formato:", pendientes, file=sys.stderr)
    return [f for f, n in pendientes.items() if n < MINIMO]


def instrucciones() -> str:
    """El mismo prompt que antes recibía la API (BANCO_IDEAS), o cadena vacía si el banco está lleno."""
    formatos = faltan()
    if not formatos:
        return ""
    banco = _load("ideas.json", [])
    posts = _load("posts.json", [])
    vistos = [p.get("tema") or p.get("titulo") for p in posts[-150:]] + [i["idea"] for i in banco[-200:]]
    return P.render(P.BANCO_IDEAS, manual=P.MANUAL, n=POR_LLAMADA,
                    formatos="\n".join(f"- {f}: {P.FORMATOS[f]}" for f in formatos),
                    evitar="; ".join(x for x in vistos if x)[-6000:] or "nada")


def agregar(nuevas: list[dict]) -> int:
    banco = _load("ideas.json", [])
    validos = set(faltan()) or set(FORMATOS)
    claves = {_clave(i["idea"]) for i in banco}
    ahora = datetime.now(timezone.utc)
    hoy, sello = ahora.strftime("%Y%m%d"), ahora.strftime("%Y%m%d%H%M")
    agregadas = 0
    for n, i in enumerate(nuevas):
        if not isinstance(i, dict) or i.get("formato") not in validos or not i.get("idea"):
            continue
        k = _clave(i["idea"])
        if k in claves:
            continue
        claves.add(k)
        banco.append({"id": f"{sello}-{n:02d}", "formato": i["formato"], "idea": i["idea"].strip(), "creada": hoy, "usada": None})
        agregadas += 1
    # se conservan todas las pendientes y las últimas 300 usadas (para no repetir)
    usadas = [i for i in banco if i.get("usada")][-300:]
    banco = usadas + [i for i in banco if not i.get("usada")]
    STATE.mkdir(exist_ok=True)
    (STATE / "ideas.json").write_text(json.dumps(banco, ensure_ascii=False, indent=1))
    return agregadas


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "instrucciones":
        texto = instrucciones()
        print(texto or "El banco de ideas está lleno; no hace falta escribir ideas nuevas.")
    elif len(sys.argv) > 2 and sys.argv[1] == "agregar":
        print("Ideas nuevas agregadas:", agregar(json.loads(Path(sys.argv[2]).read_text())))
    else:
        print(__doc__)
