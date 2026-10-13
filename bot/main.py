"""Uso: python -m bot.main --type 1|2|3|4 [--dry]
1 carrusel+seguir · 2 carrusel+palabra clave · 3 imagen+seguir · 4 imagen+palabra clave"""
import argparse
import json
import os
import random
from datetime import datetime, timezone
from .config import BOOKS, POST_TYPES, ROOT
from . import llm, meta
from .render import render_many, slide_html

OUT = ROOT / "out"
STATE = ROOT / "state"


def _history() -> list[str]:
    p = STATE / "history.json"
    return json.loads(p.read_text()) if p.exists() else []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", type=int, required=True, choices=POST_TYPES)
    ap.add_argument("--dry", action="store_true", help="genera y renderiza pero no publica")
    a = ap.parse_args()

    kind, cta = POST_TYPES[a.type]
    history = _history()

    key = random.choice(list(BOOKS))  # libro/keyword del post (en 'follow' solo define el área temática)
    area = random.choice(BOOKS[key]["areas"])
    nivel = BOOKS[key]["nivel"]
    estilos = ["problema"] * 5 + ["error"] * 2 + ["dato"] * 2 + (["demostracion"] * 2 if nivel == "uni" else [])
    content = llm.generate(kind, area, history, nivel=nivel, estilo=random.choice(estilos))

    slides = content["slides"]
    dif = (content.get("dificultad") or "").strip()
    if dif in ("*", "**"):
        slides[0]["kicker"] = f"{slides[0].get('kicker', '')}  {dif}".strip()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    paths = [OUT / f"{stamp}-t{a.type}-{i + 1}.png" for i in range(len(slides))]
    total = len(slides) + 1  # +1 por la imagen final de CTA
    render_many([slide_html(s, i, total) for i, s in enumerate(slides)], paths)

    cta_name = "follow.png" if cta == "follow" else f"kw_{key}.png"
    cta_src = ROOT / "assets" / "cta" / cta_name
    cta_dst = OUT / f"{stamp}-t{a.type}-cta.png"
    cta_dst.write_bytes(cta_src.read_bytes())
    all_files = paths + [cta_dst]
    print("Renderizado:", [p.name for p in all_files])

    history.append(slides[0].get("title", area))
    (STATE / "history.json").write_text(json.dumps(history[-300:], ensure_ascii=False, indent=1))
    if a.dry:
        return

    repo, branch = os.environ["GITHUB_REPOSITORY"], os.getenv("MEDIA_BRANCH", "media")
    urls = [f"https://raw.githubusercontent.com/{repo}/{branch}/{p.name}" for p in all_files]
    # El workflow sube out/ a la rama 'media' antes de llamar a --publish-step (ver post.yml)
    os.environ.setdefault("MEDIA_URLS", json.dumps(urls))
    (OUT / "urls.json").write_text(json.dumps({"urls": urls, "caption": content["caption"], "cta": cta}))


def publish_step() -> None:
    """Segunda fase (tras subir imágenes a la rama media): publica en IG y FB de forma independiente.
    Si una red falla, la otra se publica igual y el estado se guarda; el fallo queda como advertencia visible."""
    d = json.loads((OUT / "urls.json").read_text())
    ig = fb = None
    errores = []
    try:
        ig = meta.publish_instagram(d["urls"], d["caption"])
        print("IG:", ig)
    except Exception as e:
        errores.append(f"Instagram: {e}")
    try:
        fb = meta.publish_facebook(d["urls"], d["caption"])
        print("FB:", fb)
    except Exception as e:
        errores.append(f"Facebook: {e}")
    for err in errores:
        print(f"::warning title=Fallo de publicación::{err}")
    if d["cta"] == "keyword":
        p = STATE / "kw_posts.json"
        posts = json.loads(p.read_text())
        if ig:
            posts["ig"].append(ig)
        if fb:
            posts["fb"].append(fb)
        p.write_text(json.dumps(posts))
    if not ig and not fb:
        raise RuntimeError("No se publicó en ninguna red: " + " | ".join(errores))


if __name__ == "__main__":
    import sys
    if "--publish-step" in sys.argv:
        publish_step()
    else:
        main()
