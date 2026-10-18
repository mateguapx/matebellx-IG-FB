"""COLA DE POSTS: el bot publica posts ya escritos, sin llamar a la API de Claude.

Los posts los escribe una tarea programada de Claude (fuera de GitHub) con exactamente las mismas reglas que antes
recibía la API (bot/prompts.py), y los deja en state/cola/<tipo>/<fecha>-<sello>-<n>.json. En cada horario,
bot/main.py toma el post de su carpeta que toca hoy, lo publica y lo borra. Un archivo por post para que la tarea
programada (que agrega) y el bot (que borra) nunca choquen al hacer git push.

Uso:
  python -m bot.cola estado                      # cuántos posts quedan por horario (y hasta qué fecha)
  python -m bot.cola plan --hasta 7 > plan.json  # qué posts faltan (formato, gancho, tema, libro, fondo…) según el aprendizaje
  python -m bot.cola instrucciones plan.json     # las instrucciones completas para escribir cada post del plan
  python -m bot.cola vista posts.json carpeta    # renderiza los posts escritos como los publicará el bot, para revisarlos
  python -m bot.cola agregar posts.json          # valida y mete los posts escritos a la cola
  python -m bot.cola revisar 3                   # (workflow) si la cola del horario 3 está vacía, avisa y marca SKIP=1

Formato de posts.json: lista de objetos = cada objeto del plan tal cual + los campos que pide SCHEMA en bot/prompts.py
(tema, caption, threads, slides=[{title, text, display, curva?}]). En los posts de frase basta el objeto del plan:
la frase sale del banco curado bot/frases.py.
"""
import argparse
import json
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from . import planner
from . import prompts as P
from .config import BOOKS, HORAS, N_IDEAS, PESOS_IDEA, ROOT, SLOTS
from .contenido import contenido_frase, normalizar
from .curvas import CATALOGO, descripcion_catalogo
from .frases import POR_ID as FRASES

STATE = ROOT / "state"
COLA = STATE / "cola"
CTA_DIR = ROOT / "assets" / "cta"
# Lo que decide el plan (lo mismo que antes decidía bot/planner.py en cada post) + la fecha prevista.
CAMPOS_PLAN = ("tipo", "kind", "cta", "formato", "hook", "tema_clave", "area", "key", "nivel", "fondo",
               "curva_tipo", "serie", "idea_id", "frase_id", "semilla", "modo", "fecha")
OBLIGATORIOS = ("tipo", "kind", "cta", "formato", "hook", "tema_clave", "area", "nivel", "fondo", "semilla", "fecha")
CORTE_H = 6  # un horario que GitHub dispara con retraso pasada la medianoche sigue contando como del día anterior


def _load(name: str, default):
    p = STATE / name
    try:
        return json.loads(p.read_text()) if p.exists() else default
    except json.JSONDecodeError:
        return default


def ahora_mx() -> datetime:
    return datetime.now(planner.TZ)


def dia_del_horario(ahora: datetime | None = None) -> date:
    """Día al que pertenece un horario que corre ahora (México). Antes de las 6:00 es un horario retrasado de ayer."""
    return ((ahora or ahora_mx()).astimezone(planner.TZ) - timedelta(hours=CORTE_H)).date()


# ---------------------------------------------------------------- leer la cola
def archivos(tipo: int) -> list[Path]:
    d = COLA / str(tipo)
    return sorted(d.glob("*.json")) if d.exists() else []


def _leer(f: Path) -> dict | None:
    try:
        return json.loads(f.read_text())
    except json.JSONDecodeError:
        return None


def pendientes() -> list[dict]:
    """Todos los posts en cola, en orden de fecha, como si ya se hubieran publicado (para planear sin repetir)."""
    items = [x for t in SLOTS for f in archivos(t) if (x := _leer(f))]
    return sorted(items, key=lambda x: (x.get("fecha") or "", HORAS.get(int(x.get("tipo") or 0), 0)))


def estado() -> dict:
    out = {}
    for t in SLOTS:
        fechas = sorted(x.get("fecha") or "" for f in archivos(t) if (x := _leer(f)))
        out[t] = {"posts": len(fechas), "hasta": fechas[-1] if fechas else None}
    return out


# ---------------------------------------------------------------- planear
def _publicado_hoy(tipo: int, posts: list[dict], hoy: date) -> bool:
    for p in reversed(posts[-12:]):
        if int(p.get("tipo") or 0) == tipo and p.get("ts"):
            if dia_del_horario(datetime.fromisoformat(p["ts"])) == hoy:
                return True
    return False


def _primera_fecha(tipo: int, posts: list[dict], ahora: datetime) -> date:
    """Fecha del siguiente post a planear para ese horario: el día después del último en cola; si la cola está vacía,
    hoy (si ese horario aún no se publicó hoy) o mañana."""
    fechas = [x.get("fecha") for f in archivos(tipo) if (x := _leer(f)) and x.get("fecha")]
    if fechas:
        return date.fromisoformat(max(fechas)) + timedelta(days=1)
    hoy = dia_del_horario(ahora)
    return hoy + timedelta(days=1) if _publicado_hoy(tipo, posts, hoy) else hoy


def evitar(posts: list[dict], cola: list[dict]) -> list[str]:
    """Temas y títulos ya publicados (los mismos últimos 60 que veía la API) + todo lo que ya está en cola."""
    viejos = _load("history.json", [])
    publicados = [x for p in posts[-80:] for x in (p.get("tema"), p.get("titulo")) if x]
    en_cola = [x for p in cola for x in (p.get("tema"), ((p.get("slides") or [{}])[0]).get("title")) if x]
    return (viejos + publicados)[-100:][-60:] + en_cola


def plan(hasta: int, seed: int | None = None, ahora: datetime | None = None) -> dict:
    """Para cada horario, planea los posts que faltan para tener `hasta` en cola, día por día.
    Usa el mismo planner y el mismo aprendizaje (state/weights.json) que antes usaba el bot en cada post; las series
    semanales salen solas porque cada post se planea con la fecha y hora en que se va a publicar."""
    rng = random.Random(seed)
    ahora = (ahora or ahora_mx()).astimezone(planner.TZ)
    weights = _load("weights.json", {})
    posts = _load("posts.json", [])
    cola = pendientes()
    historia = posts + cola
    banco = _load("ideas.json", [])
    reservadas = {x.get("idea_id") for x in cola if x.get("idea_id")}
    faltan = {t: max(0, hasta - len(archivos(t))) for t in SLOTS}
    fecha = {t: _primera_fecha(t, posts, ahora) for t in SLOTS}
    items = []
    dia = min(fecha.values())
    while any(faltan.values()):
        for t in SLOTS:  # dentro de cada día, en el orden de los horarios (como pasa en la vida real)
            if faltan[t] > 0 and fecha[t] <= dia:
                cuando = datetime(dia.year, dia.month, dia.day, HORAS[t], tzinfo=planner.TZ)
                libres = [i for i in banco if i.get("id") not in reservadas]
                p = planner.elegir(t, historia, weights, rng, ideas=libres, ahora=cuando)
                p["fecha"] = dia.isoformat()
                items.append(p)
                historia.append(p)
                if p.get("idea_id"):
                    reservadas.add(p["idea_id"])
                faltan[t] -= 1
        dia += timedelta(days=1)
    return {"evitar": evitar(posts, cola), "insights": _load("insights.json", {}), "posts": items}


# ---------------------------------------------------------------- instrucciones
def contexto_rendimiento(insights: dict | None) -> str:
    """Convierte state/insights.json en el bloque de datos de rendimiento (el mismo que veía la API)."""
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


def _entre(texto: str, desde: str, hasta: str) -> str:
    i = texto.index(desde)
    return texto[i:texto.index(hasta, i)].strip()


DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def instrucciones(plan_data: dict) -> str:
    """Texto completo para escribir cada post del plan: el mismo que recibía la API (bot/prompts.py)."""
    w = PESOS_IDEA["default"]
    partes = [
        "INSTRUCCIONES PARA ESCRIBIR LOS POSTS DE @MATEBELLX",
        "Son exactamente las reglas que antes recibía la API de Claude (bot/prompts.py). Síguelas al pie de la letra.",
        "", "ROL Y REGLAS GENERALES", P.SYSTEM, "", P.MANUAL, "",
        "CÓMO ELEGIR LA IDEA DE CADA POST (antes, paso de lluvia de ideas)",
        f"Para cada post, propone {N_IDEAS} ideas DISTINTAS sobre su tema de partida (puedes acercarte a él con libertad) "
        "y con su tipo de gancho.",
        _entre(P.IDEAS, "Cada idea debe ser específica", "Responde SOLO con JSON"),
        "Quédate con la de mayor puntaje = " + " + ".join(f"{v} × {k}" for k, v in w.items()) + ".",
        "Si el verificador encuentra un error real en la mejor y no se puede corregir, usa la segunda.",
    ]
    ctx = contexto_rendimiento(plan_data.get("insights"))
    if ctx:
        partes += ["", ctx, "(En los posts con modo \"explorar\" NO uses estos datos: se exploran sin sesgo.)"]
    partes += [
        "", "No repitas estos temas ya publicados o en cola: " + ("; ".join(plan_data.get("evitar", [])) or "ninguno"),
        "", "CATÁLOGO DE CURVAS (posts de curva: elige los parámetros dentro de estos rangos)", descripcion_catalogo(),
        "", "CÓMO ESCRIBIR CADA POST",
        _entre(P.ESCRIBIR, "Reglas de los campos:", "Formato JSON exacto"),
        "Formato JSON exacto de cada post: " + P.SCHEMA,
        "", "ANTES DE ENTREGAR, revisa cada post con este checklist del verificador (y comprueba con Python toda cuenta):",
        P.VERIFICACION.split("\n\n{contenido}")[0].replace("(formato: {formato})", "(formato: el de cada post)"),
        "", "REGLAS TÉCNICAS DEL RENDER (si no se cumplen, el post se ve roto o se rechaza):",
        "- En title y text el signo $ SOLO abre y cierra fórmulas ($...$, siempre en pares). Nunca lo uses como moneda: escribe \"pesos\".",
        "- En threads no uses $, LaTeX ni barras invertidas: fórmulas con símbolos Unicode (π, √, ², θ).",
        "- En posts con palabra clave no menciones el libro ni la palabra clave: la imagen final y el texto de cierre los agrega el código.",
        "", "FORMATO DE ENTREGA: una lista JSON con un objeto por post, en el mismo orden del plan. Cada objeto = el objeto",
        "del plan copiado tal cual (no cambies ninguno de sus campos) + tema, caption, threads y slides.",
        "Posts de formato \"frase\": no escribas nada; deja solo el objeto del plan (el código pone la frase del banco curado).",
        "",
    ]
    for i, p in enumerate(plan_data["posts"], 1):
        dia = date.fromisoformat(p["fecha"])
        partes.append(f"===== POST {i} — horario {p['tipo']} — {DIAS[dia.weekday()]} {p['fecha']} {HORAS[p['tipo']]}:00 =====")
        partes.append("Plan: " + json.dumps(p, ensure_ascii=False))
        if p["formato"] == "frase":
            f = FRASES[p["frase_id"]]
            partes += [f"Frase célebre del banco: «{f['texto']}» — {f['autor']}. No escribas nada para este post.", ""]
            continue
        partes += [
            "Formato: " + P.FORMATOS[p["formato"]],
            "Forma: " + P.FORMA[p["kind"]] + " Número de slides: 1.",
            "Audiencia: " + P.AUDIENCIA.get(p["nivel"], P.AUDIENCIA["general"]) + ". Área: " + p["area"] + ".",
            "Tipo de gancho: " + P.HOOKS.get(p["hook"], p["hook"]),
        ]
        if p.get("key"):
            partes.append(f"Post del libro «{BOOKS[p['key']]['libro']}» (tono suave: el libro no se menciona; el tema sale de su área).")
        if p.get("idea_id"):
            partes.append("Idea del banco de ideas (úsala como punto de partida): " + p["area"])
        if p.get("curva_tipo"):
            partes.append(P.render(P.CURVA, curva=p["curva_tipo"], catalogo="(ver catálogo arriba)")
                          + f" Descripción: {CATALOGO[p['curva_tipo']][0]}")
        if p.get("serie"):
            partes.append(P.render(P.SERIE, serie=p["serie"]))
        if p.get("modo") == "explorar":
            partes.append("Modo explorar: no te guíes por los datos de rendimiento.")
        partes.append("")
    return "\n".join(partes)


# ---------------------------------------------------------------- validar y agregar
def _pares_de_dolar(t: str) -> bool:
    return str(t or "").count("$") % 2 == 0


def validar(item: dict) -> list[str]:
    """Mismas comprobaciones de forma que hacía el bot con la respuesta de la API (bot/contenido.py → normalizar),
    más las que evitan que algo se vea roto o que la palabra clave no la detecte bot/comments.py."""
    errores = [f"falta '{k}'" for k in OBLIGATORIOS if item.get(k) in (None, "")]
    if errores:
        return errores
    t = int(item["tipo"])
    if t not in SLOTS:
        return [f"tipo inválido: {item['tipo']}"]
    if item["formato"] not in P.FORMATOS and item["formato"] != "frase":
        return [f"formato inválido: {item['formato']}"]
    if item["hook"] not in P.HOOKS:
        return [f"gancho inválido: {item['hook']}"]
    if item["cta"] != SLOTS[t]["cta"] or item["kind"] != SLOTS[t]["kind"]:
        return [f"cta/kind no corresponden al horario {t}"]
    if item["cta"] == "keyword":
        if item.get("key") not in BOOKS:
            return [f"palabra clave inválida: {item.get('key')} (debe ser una de bot/config.py → BOOKS)"]
        if not (CTA_DIR / f"kw_{item['key']}.png").exists():
            return [f"falta la imagen final assets/cta/kw_{item['key']}.png"]
    if item["formato"] == "curva" and item.get("curva_tipo") not in CATALOGO:
        return [f"curva inválida: {item.get('curva_tipo')}"]
    if item["formato"] == "frase" and item.get("frase_id") not in FRASES:
        return [f"frase inválida: {item.get('frase_id')}"]
    try:
        date.fromisoformat(item["fecha"])
    except (TypeError, ValueError):
        return [f"fecha inválida: {item.get('fecha')}"]
    for s in item.get("slides") or []:
        if isinstance(s, dict) and not all(_pares_de_dolar(s.get(k)) for k in ("title", "text")):
            return ["un signo $ suelto en title/text: $ solo abre y cierra fórmulas; para dinero escribe \"pesos\""]
    th = str(item.get("threads") or "")
    if "$" in th or "\\" in th:
        return ["threads no puede llevar $, LaTeX ni barras invertidas"]
    return normalizar(item, item)


def agregar(lista: list[dict]) -> tuple[int, list[str]]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    ok, malos = 0, []
    for i, item in enumerate(lista):
        if item.get("formato") == "frase" and item.get("frase_id") in FRASES:
            item.update({k: v for k, v in contenido_frase(item).items() if not k.startswith("_")})
        item.pop("_idea", None)
        errores = validar(item)
        if errores:
            malos.append(f"post {i + 1} ({item.get('tema', item.get('tema_clave', '?'))}): {'; '.join(errores)}")
            continue
        d = COLA / str(int(item["tipo"]))
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{item['fecha']}-{stamp}-{i:03d}.json").write_text(json.dumps(item, ensure_ascii=False, indent=1))
        ok += 1
    return ok, malos


# ---------------------------------------------------------------- tomar (lo usa bot/main.py)
def tomar(tipo: int, ahora: datetime | None = None) -> tuple[dict | None, Path | None]:
    """Post que toca publicar en ese horario. No borra el archivo (eso lo hace bot/main.py al publicar).
    Prioridad: el fechado para hoy; si no hay, el atrasado más antiguo; si no, el siguiente. Los inválidos se descartan."""
    hoy = dia_del_horario(ahora).isoformat()
    validos = []
    for f in archivos(tipo):
        item = _leer(f)
        if item is None:
            print(f"::warning::Post ilegible en la cola, se descarta: {f.name}")
            f.unlink()
            continue
        errores = validar(item)
        if errores:
            print(f"::warning::Post inválido en la cola, se descarta ({f.name}): {errores}")
            f.unlink()
            continue
        validos.append((item, f))
    if not validos:
        return None, None
    for item, f in validos:
        if item["fecha"] == hoy:
            return item, f
    atrasados = [(i, f) for i, f in validos if i["fecha"] < hoy]
    return (atrasados or validos)[0]


def vista(lista: list[dict], carpeta: Path) -> list[str]:
    """Renderiza cada post escrito tal como lo publicará el bot (mismo fondo y semilla del plan), deja una hoja por día
    para revisarlas de un vistazo y avisa si algo se sale del marco. Devuelve los avisos."""
    import copy
    from .main import caption_facebook, texto_threads
    from .render import render_many, slide_html
    carpeta.mkdir(parents=True, exist_ok=True)
    avisos, inners, salidas, textos = [], [], [], []
    for i, item in enumerate(lista, 1):
        x = copy.deepcopy(item)
        if x.get("formato") == "frase" and x.get("frase_id") in FRASES:
            x.update({k: v for k, v in contenido_frase(x).items() if not k.startswith("_")})
        errores = validar(x)
        if errores:
            avisos.append(f"post {i}: {'; '.join(errores)}")
            continue
        inners.append(slide_html(x["slides"][0], x["fondo"], x["semilla"]))
        salidas.append(carpeta / f"{i:02d}-{x['fecha']}-t{x['tipo']}.png")
        cta = "follow.png" if x["cta"] == "follow" else f"kw_{x['key']}.png"
        textos.append(f"===== post {i} · {x['fecha']} · horario {x['tipo']} · imagen final {cta}\n"
                      f"[Facebook]\n{caption_facebook(x['caption'], x['cta'], x.get('key'))}\n"
                      f"[Threads]\n{texto_threads(x, x['cta'], x.get('key'))}\n")
    if inners:
        render_many(inners, salidas)
    (carpeta / "textos.txt").write_text("\n".join(textos))
    try:  # opcional: revisión de márgenes y hojas por día (requiere Pillow y numpy)
        import numpy as np
        from PIL import Image
        for f in salidas:
            a = np.asarray(Image.open(f).convert("L")).astype(int)[300:1150]
            cols = np.where((a > 150).sum(axis=0) > 0)[0]
            if len(cols) and (cols.min() < 60 or cols.max() > 1020):
                avisos.append(f"{f.name}: algo se acerca o se sale del marco (x {cols.min()}–{cols.max()}); acorta la fórmula o el texto")
        for fecha in sorted({f.name.split("-t")[0][3:] for f in salidas}):
            hoja = Image.new("RGB", (1080, 1350), "black")
            for f in salidas:
                if f.name[3:].startswith(fecha):
                    t = int(f.stem.split("-t")[-1])
                    hoja.paste(Image.open(f).resize((540, 675)), ((t - 1) % 2 * 540, (t - 1) // 2 * 675))
            hoja.save(carpeta / f"dia-{fecha}.png")
    except ImportError:
        avisos.append("(sin Pillow/numpy: no se revisaron márgenes ni se hicieron hojas por día; revisa cada imagen)")
    return avisos


def revisar(tipo: int) -> bool:
    """Para el workflow: si la cola de ese horario está vacía, deja el aviso y marca SKIP=1 (no se instala nada)."""
    if archivos(tipo):
        print(f"Cola del horario {tipo}: {len(archivos(tipo))} posts")
        return True
    print(f"::warning title=Cola vacía::No hay posts en la cola del horario {tipo}; no se publica.")
    if os.getenv("GITHUB_ENV"):
        with open(os.environ["GITHUB_ENV"], "a") as f:
            f.write("SKIP=1\n")
    return False


def _main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("estado")
    sp = sub.add_parser("plan")
    sp.add_argument("--hasta", type=int, default=7)
    sp.add_argument("--seed", type=int)
    si = sub.add_parser("instrucciones")
    si.add_argument("plan")
    sa = sub.add_parser("agregar")
    sa.add_argument("archivo")
    sr = sub.add_parser("revisar")
    sr.add_argument("tipo", type=int)
    sv = sub.add_parser("vista")
    sv.add_argument("archivo")
    sv.add_argument("carpeta")
    a = ap.parse_args()
    if a.cmd == "estado":
        print(json.dumps(estado(), ensure_ascii=False))
    elif a.cmd == "plan":
        print(json.dumps(plan(a.hasta, a.seed), ensure_ascii=False, indent=1))
    elif a.cmd == "instrucciones":
        print(instrucciones(json.loads(Path(a.plan).read_text())))
    elif a.cmd == "agregar":
        ok, malos = agregar(json.loads(Path(a.archivo).read_text()))
        print(f"Agregados: {ok}")
        for m in malos:
            print("RECHAZADO:", m)
        print("Cola:", json.dumps(estado(), ensure_ascii=False))
        if malos:
            sys.exit(1)
    elif a.cmd == "revisar":
        revisar(a.tipo)
    elif a.cmd == "vista":
        avisos = vista(json.loads(Path(a.archivo).read_text()), Path(a.carpeta))
        print("Imágenes, hojas por día (dia-AAAA-MM-DD.png) y textos.txt en", a.carpeta)
        for m in avisos:
            print("AVISO:", m)
        if avisos:
            sys.exit(1)


if __name__ == "__main__":
    _main()
