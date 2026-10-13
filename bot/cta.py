"""Genera UNA vez las imágenes finales reutilizables: assets/cta/follow.png y assets/cta/kw_<KEYWORD>.png.
Uso: python -m bot.cta   (luego haz commit de assets/cta/)"""
from .config import BOOKS, ROOT
from .render import cta_follow_html, cta_keyword_html, render_many

if __name__ == "__main__":
    out = ROOT / "assets" / "cta"
    inners = [cta_follow_html()]
    paths = [out / "follow.png"]
    for kw, b in BOOKS.items():
        inners.append(cta_keyword_html(kw, b["libro"]))
        paths.append(out / f"kw_{kw}.png")
    render_many(inners, paths)
    print("Generadas:", [p.name for p in paths])
