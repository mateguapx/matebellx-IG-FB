"""HTML + KaTeX -> PNG con Playwright. Determinista: sin generadores de imagen, sin errores de notación.
Estilo Bellxs: editorial y elegante. Playfair Display (títulos) + Cormorant Garamond (texto), dorado sobre negro,
composición centrada, separadores finos y el eslogan como firma.
Layouts:
  "normal": título, línea de apoyo y fórmula protagonista.
  "curva":  título arriba, la curva dibujada con exactitud en el centro (bot/fondos.js → drawCurva) y su ecuación debajo.
Fondos: arte matemático generado por código (bot/fondos.js), muy oscurecido."""
import html
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from .config import BRAND, ESLOGAN, HANDLE, SIZE

VENDOR = Path(__file__).parent / "vendor"
W, H = SIZE


def _hex_rgb(h: str) -> list[int]:
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _page(inner: str) -> str:
    b = BRAND
    acento_rgb = json.dumps(_hex_rgb(b["accent"]))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="vendor/katex/katex.min.css">
<style>
@font-face{{font-family:Playfair;font-weight:500;src:url(vendor/fonts/playfair-display-latin-500-normal.woff2)}}
@font-face{{font-family:Playfair;font-weight:600;src:url(vendor/fonts/playfair-display-latin-600-normal.woff2)}}
@font-face{{font-family:Playfair;font-weight:500;font-style:italic;src:url(vendor/fonts/playfair-display-latin-500-italic.woff2)}}
@font-face{{font-family:Playfair;font-weight:600;font-style:italic;src:url(vendor/fonts/playfair-display-latin-600-italic.woff2)}}
@font-face{{font-family:Cormorant;font-weight:500;src:url(vendor/fonts/cormorant-garamond-latin-500-normal.woff2)}}
@font-face{{font-family:Cormorant;font-weight:600;src:url(vendor/fonts/cormorant-garamond-latin-600-normal.woff2)}}
@font-face{{font-family:Cormorant;font-weight:500;font-style:italic;src:url(vendor/fonts/cormorant-garamond-latin-500-italic.woff2)}}
@font-face{{font-family:Cormorant;font-weight:600;font-style:italic;src:url(vendor/fonts/cormorant-garamond-latin-600-italic.woff2)}}
*{{box-sizing:border-box;margin:0}}
body{{width:{W}px;height:{H}px;background:{b['bg']};color:{b['fg']};font-family:Cormorant,serif;overflow:hidden;position:relative}}
#bg,#bgf{{position:absolute;inset:0;z-index:0}} #bgf{{overflow:hidden}}
.velo{{position:absolute;inset:0;z-index:0;background:radial-gradient(ellipse at 50% 46%,rgba(0,0,0,.30) 0%,rgba(0,0,0,.62) 70%,rgba(0,0,0,.85) 100%)}}
.marco{{position:absolute;inset:34px;z-index:1;border:1px solid {b['accent']}33;pointer-events:none}}
.wrap{{position:absolute;inset:0;z-index:2;padding:92px 96px 84px;display:flex;flex-direction:column;align-items:center;text-align:center}}
.top{{font-family:Cormorant;font-weight:600;font-size:27px;letter-spacing:10px;text-transform:uppercase;color:{b['accent']};opacity:.85}}
.main{{flex:1;min-height:0;width:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:40px}}
.title{{font-family:Playfair;font-weight:500;font-size:86px;line-height:1.16;letter-spacing:-.5px;color:{b['fg']};max-width:900px}}
.title .katex{{font-size:1.08em}}
.em{{font-style:italic;color:{b['accent']}}}
.text{{font-family:Cormorant;font-weight:500;font-size:52px;line-height:1.3;color:{b['fg']};opacity:.88;max-width:860px}}
.text .katex{{font-size:.92em;white-space:nowrap}}
.text .em{{font-weight:600}}
.orn{{display:flex;align-items:center;gap:22px;width:430px;color:{b['accent']}}}
.orn::before,.orn::after{{content:"";flex:1;height:1px;background:linear-gradient(90deg,transparent,{b['accent']})}}
.orn::after{{background:linear-gradient(90deg,{b['accent']},transparent)}}
.orn span{{width:9px;height:9px;transform:rotate(45deg);border:1.5px solid {b['accent']}}}
.display{{font-size:76px;color:{b['accent']};width:900px;max-width:900px;text-shadow:0 0 28px {b['accent']}55}}
.katex-display{{margin:0!important}}
.curva-box{{position:relative;width:900px;height:640px;flex:none}}
#curva{{position:absolute;inset:0;width:900px;height:640px}}
.lay-curva .main{{gap:30px;justify-content:flex-start;padding-top:34px}}
.lay-curva .title{{font-size:74px}}
.lay-curva .display{{font-size:56px}}
.lay-curva .text{{font-size:44px}}
.foot{{display:flex;align-items:center;gap:20px;font-family:Cormorant;font-style:italic;font-weight:500;font-size:34px;color:{b['accent']};opacity:.92}}
.foot::before,.foot::after{{content:"";width:70px;height:1px;background:{b['accent']};opacity:.6}}
.title,.text,.top,.foot{{text-shadow:0 0 18px #000,0 0 40px #000}}
.cta-big{{font-family:Playfair;font-weight:500;font-size:104px;line-height:1.1;color:{b['fg']}}}
.kw{{display:inline-block;font-family:Playfair;font-weight:600;font-size:118px;letter-spacing:6px;color:{b['bg']};background:{b['accent']};padding:10px 44px 18px}}
.lay-frase .main{{gap:34px}}
.lay-frase .title{{font-style:italic;max-width:880px}}
.comillas{{font-family:Playfair;font-weight:600;font-size:210px;line-height:.6;height:96px;color:{b['accent']};opacity:.9;text-shadow:0 0 34px {b['accent']}66}}
.autor{{font-family:Cormorant;font-weight:600;font-size:46px;letter-spacing:7px;text-transform:uppercase;color:{b['accent']};text-shadow:0 0 18px #000}}
.fuente{{font-family:Cormorant;font-style:italic;font-weight:500;font-size:32px;color:{b['fg']};opacity:.7;margin-top:-22px;text-shadow:0 0 18px #000}}
.lay-libro .main{{gap:22px}}
.lay-libro .kw{{font-size:64px;letter-spacing:6px;padding:4px 34px 10px}}
.libro-box{{position:relative;height:600px;width:900px;display:flex;align-items:center;justify-content:center;flex:none}}
.libro-luz{{position:absolute;inset:40px 120px;background:radial-gradient(ellipse at 50% 55%,{b['accent']}44 0%,{b['accent']}10 45%,transparent 70%);filter:blur(10px)}}
.libro{{position:relative;max-height:600px;max-width:900px;-webkit-mask-image:radial-gradient(ellipse 58% 60% at 50% 50%,#000 62%,transparent 100%);mask-image:radial-gradient(ellipse 58% 60% at 50% 50%,#000 62%,transparent 100%)}}
</style></head><body>{inner}
<script src="vendor/katex/katex.min.js"></script>
<script src="vendor/katex/contrib/auto-render.min.js"></script>
<script>window.ACENTO_RGB={acento_rgb};</script>
<script src="fondos.js"></script>
<script>
const bgc=document.getElementById('bg');
if(bgc&&window.drawFondo)drawFondo(bgc.dataset.motivo,+bgc.dataset.semilla);
const cvc=document.getElementById('curva');
if(cvc&&window.drawCurva)drawCurva(cvc,cvc.dataset.tipo,JSON.parse(cvc.dataset.params||'{{}}'));
renderMathInElement(document.querySelector('.wrap')||document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}],throwOnError:false}});
document.querySelectorAll('.display').forEach(e=>katex.render(e.dataset.tex,e,{{displayMode:true,throwOnError:false}}));
const px=e=>parseFloat(getComputedStyle(e).fontSize);
function fitWidth(){{document.querySelectorAll('.display').forEach(e=>{{const k=()=>{{const h=e.querySelector('.katex-html');return h?[...h.children].reduce((a,c)=>a+c.getBoundingClientRect().width,0):e.scrollWidth}};let fs=px(e);while(k()>e.clientWidth+1&&fs>26){{fs-=2;e.style.fontSize=fs+'px'}}}})}}
function contentH(m){{const c=[...m.children];return c.reduce((a,x)=>a+x.offsetHeight,0)+parseFloat(getComputedStyle(m).rowGap||0)*Math.max(c.length-1,0)+parseFloat(getComputedStyle(m).paddingTop||0)}}
document.fonts.ready.then(()=>{{
fitWidth();
const m=document.querySelector('.main');
let k=0;
const MIN={{title:46,text:30,display:30}};
while(m&&contentH(m)>m.clientHeight&&k<60){{
  const cb=m.querySelector('.curva-box');
  if(cb&&cb.offsetHeight>440){{  // primero se reduce el dibujo
    const c=document.getElementById('curva');cb.style.height=(cb.offsetHeight-24)+'px';cb.style.width=(cb.offsetWidth-34)+'px';
    c.style.width=cb.style.width;c.style.height=cb.style.height;k++;continue}}
  let cambio=false;
  m.querySelectorAll('.title,.text,.display').forEach(e=>{{const t=e.classList.contains('title')?'title':e.classList.contains('text')?'text':'display';
    const f=px(e);if(f*0.95>=MIN[t]){{e.style.fontSize=(f*0.95)+'px';cambio=true}}}});
  fitWidth();k++;if(!cambio)break}}
document.querySelectorAll('.kw').forEach(e=>{{let fs=px(e);while(e.offsetWidth>880&&fs>30){{fs-=4;e.style.fontSize=fs+'px'}}}});
window.__ready=true}});
</script></body></html>"""


def _fmt(t: str) -> str:
    """Escapa HTML y convierte **palabra** en énfasis (cursiva dorada). Las fórmulas $...$ las dibuja KaTeX después."""
    t = html.escape(t)
    return re.sub(r"\*\*(.+?)\*\*", r'<span class="em">\1</span>', t)


def _fondo(fondo: str | None, semilla: int) -> str:
    if not fondo:
        return '<div class="velo"></div>'
    return (f'<canvas id="bg" width="{W}" height="{H}" data-motivo="{html.escape(fondo)}" data-semilla="{int(semilla)}"></canvas>'
            '<div id="bgf"></div><div class="velo"></div>')


def _marco(body: str, clase: str = "") -> str:
    e = html.escape
    return f"""<div class="marco"></div><div class="wrap {clase}">
<div class="top">{e(HANDLE.lstrip('@'))}</div>
<div class="main">{body}</div>
<div class="foot">{e(ESLOGAN)}</div>
</div>"""


ORNAMENTO = '<div class="orn"><span></span></div>'


def slide_html(s: dict, fondo: str | None = None, semilla: int = 1) -> str:
    """Un post = una sola imagen. s: title, text, display, layout ('normal' | 'curva'), curva {tipo, params}."""
    e = html.escape
    title = f'<div class="title">{_fmt(s["title"])}</div>' if s.get("title") else ""
    text = f'<div class="text">{_fmt(s["text"])}</div>' if s.get("text") else ""
    disp = f'<div class="display" data-tex="{e(s["display"], quote=True)}"></div>' if s.get("display") else ""
    if s.get("layout") == "frase":  # frase célebre: comillas, cita en cursiva, autor y fuente
        n = len(s.get("title", ""))
        fs = 92 if n < 40 else 78 if n < 90 else 68 if n < 140 else 60
        cita = f'<div class="title" style="font-size:{fs}px">{_fmt(s.get("title", ""))}</div>'
        body = (f'<div class="comillas">“</div>{cita}{ORNAMENTO}<div class="autor">{e(s.get("autor", ""))}</div>'
                + (f'<div class="fuente">{e(s["fuente"])}</div>' if s.get("fuente") else ""))
        return _fondo(fondo, semilla) + _marco(body, "lay-frase")
    curva = s.get("curva") if s.get("layout") == "curva" else None
    if curva:
        cv = (f'<div class="curva-box"><canvas id="curva" width="1800" height="1280" data-tipo="{e(curva["tipo"])}" '
              f'data-params="{e(json.dumps(curva.get("params", {})), quote=True)}"></canvas></div>')
        body = f"{title}{cv}{disp}{text}"
        return _fondo(fondo, semilla) + _marco(body, "lay-curva")
    partes = [title, ORNAMENTO if (disp or text) else "", disp, text] if disp else [title, ORNAMENTO if text else "", text]
    return _fondo(fondo, semilla) + _marco("".join(partes))


def cta_follow_html() -> str:
    body = (f'<div class="cta-big">Si esto te pareció <span class="em">bello</span>,<br>quédate.</div>{ORNAMENTO}'
            f'<div class="text">Una dosis diaria de belleza matemática</div>'
            f'<div class="text" style="font-size:64px;color:{BRAND["accent"]};font-weight:600">Síguenos</div>')
    return _fondo("espiral", 7) + _marco(body)


def cta_keyword_html(keyword: str, libro: str) -> str:
    """Cierre de los posts de palabra clave: el mockup del libro (assets/libros/KEY.jpg) + la palabra a comentar."""
    e = html.escape
    img = Path(__file__).resolve().parent.parent / "assets" / "libros" / f"{keyword}.jpg"
    mockup = (f'<div class="libro-box"><div class="libro-luz"></div><img class="libro" src="{img.as_uri()}"></div>'
              if img.exists() else ORNAMENTO)
    body = (f'<div class="cta-big" style="font-size:84px">¿Te <span class="em">enamoraste</span>?</div>{mockup}'
            f'<div class="text" style="font-size:42px">Comenta la palabra</div><div class="kw">{e(keyword)}</div>'
            f'<div class="text" style="font-size:36px;opacity:.78">y te mando <span class="em">{e(libro)}</span></div>')
    return _fondo("lissajous", 3) + _marco(body, "lay-libro")


def render_many(inners: list[str], out_paths: list[Path]) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H})
        for inner, out in zip(inners, out_paths):
            tmp = Path(__file__).parent / "_tmp.html"
            tmp.write_text(_page(inner), encoding="utf-8")
            page.goto(tmp.as_uri())
            page.wait_for_function("window.__ready === true", timeout=60000)
            out.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out))
            tmp.unlink()
        browser.close()
