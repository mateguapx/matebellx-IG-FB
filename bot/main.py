"""Uso: python -m bot.main --type 1|2|3|4 [--dry]   (concepto: "Porque las Matemáticas son Bellxs")
Todos los posts son de UNA imagen. Instagram: imagen + imagen final (Síguenos / Comenta PALABRA).
Facebook y Threads: solo la imagen, con la invitación al final del texto (Threads lleva su propio texto con 💛).
1 y 4 seguir · 2 palabra clave (tono suave) · 3 "Ecuación del día" (curva) + seguir. Mezcla y series en bot/config.py."""
import argparse
import json
import os
import re
from datetime import datetime, timezone
from .config import FB_CTA, LINK, POST_TYPES, PUBLICAR_DESCRIPCIONES, ROOT, TH_CTA, TH_LIMITE
from . import llm, meta, planner
from .render import render_many, slide_html

OUT = ROOT / "out"
STATE = ROOT / "state"


def _load(name: str, default):
    p = STATE / name
    try:
        return json.loads(p.read_text()) if p.exists() else default
    except json.JSONDecodeError:
        return default


def _save(name: str, data) -> None:
    STATE.mkdir(exist_ok=True)
    (STATE / name).write_text(json.dumps(data, ensure_ascii=False, indent=1))


def _evitar(posts: list[dict]) -> list[str]:
    """Temas y títulos ya publicados (incluye el historial antiguo)."""
    viejos = _load("history.json", [])
    nuevos = [x for p in posts[-80:] for x in (p.get("tema"), p.get("titulo")) if x]
    return (viejos + nuevos)[-100:]


def caption_facebook(caption: str, cta: str, key: str | None) -> str:
    """En Facebook no va la imagen final, así que la invitación se agrega al texto, antes de los hashtags."""
    linea = FB_CTA[cta].format(key=key or "")
    m = re.search(r"(\s*(#\w+\s*)+)$", caption)
    if m:
        return caption[:m.start()].rstrip() + "\n\n" + linea + "\n\n" + m.group(1).strip()
    return caption.rstrip() + "\n\n" + linea


def _largo_threads(t: str) -> int:
    """Threads cuenta cada emoji por sus bytes UTF-8; el resto de los caracteres, como 1."""
    return sum(len(c.encode()) if ord(c) >= 0x2190 else 1 for c in t)


def texto_threads(content: dict, cta: str, key: str | None) -> str:
    base = (content.get("threads") or "").strip()
    if not base:  # respaldo: primer párrafo del caption, sin hashtags
        base = re.sub(r"#\w+", "", content.get("caption", "")).strip().split("\n\n")[0].strip() + " 💛"
    cierre = "\n\n" + TH_CTA[cta].format(link=LINK, key=key or "")
    while _largo_threads(base + cierre) > TH_LIMITE and " " in base:
        base = base.rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return base + cierre


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", type=int, required=True, choices=POST_TYPES)
    ap.add_argument("--dry", action="store_true", help="genera y renderiza pero no publica ni guarda estado")
    a = ap.parse_args()

    posts = _load("posts.json", [])
    plan = planner.elegir(a.type, posts, _load("weights.json", {}), ideas=_load("ideas.json", []))
    print("Plan:", json.dumps(plan, ensure_ascii=False))
    content = llm.generate(plan, _evitar(posts), _load("insights.json", {}))
    print("Idea elegida:", json.dumps(content.get("_idea"), ensure_ascii=False))

    slide = content["slides"][0]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    img = OUT / f"{stamp}-t{a.type}.png"
    render_many([slide_html(slide, plan["fondo"], plan["semilla"])], [img])

    cta_name = "follow.png" if plan["cta"] == "follow" else f"kw_{plan['key']}.png"
    cta_dst = OUT / f"{stamp}-t{a.type}-cta.png"
    cta_dst.write_bytes((ROOT / "assets" / "cta" / cta_name).read_bytes())
    fb_caption = caption_facebook(content["caption"], plan["cta"], plan["key"])
    th_text = texto_threads(content, plan["cta"], plan["key"])
    ig_caption = content["caption"]
    if not PUBLICAR_DESCRIPCIONES:  # solo la imagen, sin texto, en las tres redes
        ig_caption = fb_caption = th_text = ""
        print("Descripciones desactivadas (config.PUBLICAR_DESCRIPCIONES = False): se publica solo la imagen.")
    print("Renderizado:", img.name, "+", cta_dst.name, "(la imagen final solo va en Instagram)")
    print("Título:", slide.get("title"))
    print("Fórmula:", slide.get("display", ""))
    print("Caption IG:", content["caption"])
    print("Caption FB:", fb_caption)
    print("Texto Threads:", th_text)

    record = {
        "id": f"{stamp}-t{a.type}", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **{k: plan.get(k) for k in ("tipo", "kind", "cta", "formato", "hook", "tema_clave", "area", "key", "nivel",
                                    "fondo", "modo", "curva_tipo", "serie", "idea_id", "frase_id")},
        "tema": content.get("tema") or (content.get("_idea") or {}).get("tema", ""),
        "titulo": slide.get("title", ""), "respuesta": content.get("respuesta", ""),
        "puntaje_idea": (content.get("_idea") or {}).get("_puntaje"),
    }
    (OUT / "post.json").write_text(json.dumps({"record": record, "content": content}, ensure_ascii=False, indent=1))
    if a.dry:
        return

    repo, branch = os.environ["GITHUB_REPOSITORY"], os.getenv("MEDIA_BRANCH", "media")
    url = lambda p: f"https://raw.githubusercontent.com/{repo}/{branch}/{p.name}"
    # El workflow sube out/ a la rama 'media' antes de llamar a --publish-step (ver post.yml)
    (OUT / "urls.json").write_text(json.dumps({
        "ig_urls": [url(img), url(cta_dst)], "fb_urls": [url(img)], "th_url": url(img),
        "caption": ig_caption, "fb_caption": fb_caption, "th_text": th_text, "cta": plan["cta"], "record": record,
    }, ensure_ascii=False))


def publish_step() -> None:
    """Segunda fase (tras subir imágenes a la rama media): publica en IG y FB de forma independiente.
    Si una red falla, la otra se publica igual y el estado se guarda; el fallo queda como advertencia visible."""
    d = json.loads((OUT / "urls.json").read_text())
    ig_urls = d.get("ig_urls") or d.get("urls")
    fb_urls = d.get("fb_urls") or ig_urls[:1]
    ig = fb = None
    errores = []
    try:
        ig = meta.publish_instagram(ig_urls, d["caption"])
        print("IG:", ig)
    except Exception as e:
        errores.append(f"Instagram: {e}")
    try:
        fb = meta.publish_facebook(fb_urls, d.get("fb_caption", d["caption"]))
        print("FB:", fb)
    except Exception as e:
        errores.append(f"Facebook: {e}")
    th = None
    if meta.threads_activo() and d.get("th_url"):
        try:
            th = meta.publish_threads(d["th_url"], d.get("th_text", d["caption"]))
            print("Threads:", th)
        except Exception as e:
            errores.append(f"Threads: {e}")
    for err in errores:
        print(f"::warning title=Fallo de publicación::{err}")
    if d["cta"] == "keyword":
        posts = _load("kw_posts.json", {"ig": [], "fb": []})
        if ig:
            posts["ig"].append(ig)
        if fb:
            posts["fb"].append(fb)
        _save("kw_posts.json", posts)
    if ig or fb or th:
        record = d.get("record") or {}
        record.update({"ig_id": ig, "fb_id": fb, "th_id": th, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        posts = _load("posts.json", [])
        posts.append(record)
        _save("posts.json", posts[-500:])
        if record.get("idea_id"):  # la idea del banco ya se usó
            ideas = _load("ideas.json", [])
            for i in ideas:
                if i.get("id") == record["idea_id"]:
                    i["usada"] = record["ts"]
            _save("ideas.json", ideas)
    else:
        raise RuntimeError("No se publicó en ninguna red: " + " | ".join(errores))


if __name__ == "__main__":
    import sys
    if "--publish-step" in sys.argv:
        publish_step()
    else:
        main()
