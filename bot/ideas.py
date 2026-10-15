"""Banco de ideas que se renueva solo.
Uso: python -m bot.ideas   (corre cada semana con .github/workflows/ideas.yml)

Mantiene state/ideas.json con ideas concretas y pendientes para los próximos posts. Si quedan menos de MINIMO
pendientes por formato, le pide a Claude ideas nuevas que no repitan lo publicado ni lo que ya está en el banco.
bot/planner.py usa estas ideas como tema de partida y bot/main.py las marca como usadas al publicar."""
import json
import unicodedata
from datetime import datetime, timezone
from . import llm
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


def run() -> None:
    banco = _load("ideas.json", [])
    posts = _load("posts.json", [])
    pendientes = {f: sum(1 for i in banco if not i.get("usada") and i.get("formato") == f) for f in FORMATOS}
    faltan = [f for f, n in pendientes.items() if n < MINIMO]
    print("Ideas pendientes por formato:", pendientes)
    if not faltan:
        print("El banco está lleno; no se piden ideas nuevas.")
        return

    vistos = [p.get("tema") or p.get("titulo") for p in posts[-150:]] + [i["idea"] for i in banco[-200:]]
    prompt = P.render(P.BANCO_IDEAS, manual=P.MANUAL, n=POR_LLAMADA,
                      formatos="\n".join(f"- {f}: {P.FORMATOS[f]}" for f in faltan),
                      evitar="; ".join(x for x in vistos if x)[-6000:] or "nada")
    nuevas = llm._json(llm._ask(prompt, max_tokens=8000)).get("ideas", [])

    claves = {_clave(i["idea"]) for i in banco}
    ahora = datetime.now(timezone.utc)
    hoy, sello = ahora.strftime("%Y%m%d"), ahora.strftime("%Y%m%d%H%M")
    agregadas = 0
    for n, i in enumerate(nuevas):
        if not isinstance(i, dict) or i.get("formato") not in faltan or not i.get("idea"):
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
    print(f"Ideas nuevas agregadas: {agregadas}")
    for i in banco[-agregadas:] if agregadas else []:
        print(f"- [{i['formato']}] {i['idea']}")


if __name__ == "__main__":
    run()
