"""HTML + KaTeX -> PNG con Playwright. Determinista: sin generadores de imagen, sin errores de notación."""
import html
from pathlib import Path
from playwright.sync_api import sync_playwright
from .config import BRAND, HANDLE, SIZE

VENDOR = Path(__file__).parent / "vendor"
W, H = SIZE


def _page(inner: str) -> str:
    b = BRAND
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="vendor/katex/katex.min.css">
<style>
@font-face{{font-family:Anton;src:url(vendor/fonts/anton-latin-400-normal.woff2)}}
@font-face{{font-family:Oswald;font-weight:400;src:url(vendor/fonts/oswald-latin-400-normal.woff2)}}
@font-face{{font-family:Oswald;font-weight:700;src:url(vendor/fonts/oswald-latin-700-normal.woff2)}}
*{{box-sizing:border-box;margin:0}}
body{{width:{W}px;height:{H}px;background:{b['bg']};color:{b['fg']};font-family:Oswald,sans-serif;overflow:hidden;position:relative}}
.wrap{{position:absolute;inset:0;padding:90px 80px;display:flex;flex-direction:column}}
.top{{display:flex;justify-content:space-between;font-size:30px;letter-spacing:2px;color:{b['accent']}}}
.main{{flex:1;display:flex;flex-direction:column;justify-content:center;gap:34px}}
.kicker{{display:inline-block;align-self:flex-start;background:{b['accent']};color:#000;font-weight:700;font-size:32px;padding:6px 22px;letter-spacing:3px;text-transform:uppercase}}
.title{{font-family:Anton;font-size:96px;line-height:1.05;text-transform:uppercase}}
.title.big{{font-size:118px}}
.text{{font-size:46px;line-height:1.35;font-weight:400}}
.display{{font-size:70px;text-align:center;padding:36px 20px;border:4px solid {b['accent']};color:{b['accent']}}}
.katex-display{{margin:0!important}}
.foot{{display:flex;justify-content:space-between;font-size:30px;color:#aaa}}
.accent{{color:{b['accent']}}} .alert{{color:{b['alert']}}}
.cta-big{{font-family:Anton;font-size:128px;line-height:1.02;text-transform:uppercase}}
.kw{{display:inline-block;font-family:Anton;font-size:150px;background:{b['accent']};color:#000;padding:6px 36px;margin:10px 0}}
</style></head><body>{inner}
<script src="vendor/katex/katex.min.js"></script>
<script src="vendor/katex/contrib/auto-render.min.js"></script>
<script>
renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}],throwOnError:false}});
document.querySelectorAll('.display').forEach(e=>katex.render(e.dataset.tex,e,{{displayMode:true,throwOnError:false}}));
document.fonts.ready.then(()=>{{
document.querySelectorAll('.display').forEach(e=>{{let fs=70;while(e.scrollWidth>e.clientWidth&&fs>24){{fs-=3;e.style.fontSize=fs+'px'}}}});
document.querySelectorAll('.kw').forEach(e=>{{let fs=150;while(e.offsetWidth>920&&fs>40){{fs-=4;e.style.fontSize=fs+'px'}}}});
window.__ready=true}});
</script></body></html>"""


def slide_html(s: dict, idx: int, total: int) -> str:
    e = html.escape
    first = idx == 0
    disp = f'<div class="display" data-tex="{e(s["display"], quote=True)}"></div>' if s.get("display") else ""
    swipe = "DESLIZA ›" if idx < total - 1 and total > 1 else ""
    counter = f"{idx + 1}/{total}" if total > 1 else ""
    return f"""<div class="wrap">
<div class="top"><span>{e(HANDLE)}</span><span>{counter}</span></div>
<div class="main">
<span class="kicker">{e(s.get('kicker', ''))}</span>
<div class="title {'big' if first else ''}">{e(s.get('title', ''))}</div>
<div class="text">{e(s.get('text', ''))}</div>{disp}
</div>
<div class="foot"><span>SABER MATEMÁTICAS ES DE GUAPOS</span><span class="accent">{swipe}</span></div>
</div>"""


def cta_follow_html() -> str:
    return f"""<div class="wrap"><div class="main" style="align-items:flex-start">
<div class="cta-big">¿Te sirvió?<br><span class="accent">Síguenos</span><br>para más<br>matemáticas</div>
<div class="text">Un problema nuevo cada día</div>
<div class="title alert" style="font-size:80px">{html.escape(HANDLE)}</div></div></div>"""


def cta_keyword_html(keyword: str, libro: str) -> str:
    e = html.escape
    return f"""<div class="wrap"><div class="main" style="align-items:flex-start">
<div class="cta-big" style="font-size:96px">¿Quieres más ejercicios?</div>
<div class="text">Comenta la palabra</div>
<div class="kw">{e(keyword)}</div>
<div class="text">y te mando dónde conseguir <span class="accent">{e(libro)}</span></div>
<div class="text" style="font-size:36px;color:#aaa">1,000 ejercicios · Con soluciones paso a paso</div></div></div>"""


def render_many(inners: list[str], out_paths: list[Path]) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        for inner, out in zip(inners, out_paths):
            tmp = Path(__file__).parent / "_tmp.html"
            tmp.write_text(_page(inner), encoding="utf-8")
            page.goto(tmp.as_uri())
            page.wait_for_function("window.__ready === true")
            out.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out))
            tmp.unlink()
        browser.close()
