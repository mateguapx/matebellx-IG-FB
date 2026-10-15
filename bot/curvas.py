"""Catálogo de curvas que el bot sabe dibujar con exactitud (bot/fondos.js → drawCurva).
Claude solo elige el tipo y los parámetros; la ecuación en LaTeX la genera este archivo,
así el dibujo y la fórmula siempre coinciden."""
from fractions import Fraction

# tipo: (descripción para el prompt, parámetros por defecto, rangos permitidos)
CATALOGO = {
    "rosa": ("rosa polar r = cos(kθ); k entero da k pétalos si es impar y 2k si es par; k fraccionario da rosas entrelazadas",
             {"k": 4}, {"k": (0.2, 12)}),
    "cardioide": ("cardioide r = 1 − cos θ (forma de corazón)", {}, {}),
    "corazon": ("curva del corazón x = 16 sen³t, y = 13 cos t − 5 cos 2t − 2 cos 3t − cos 4t", {}, {}),
    "lemniscata": ("lemniscata de Bernoulli r² = cos 2θ (el símbolo de infinito)", {}, {}),
    "espiral_aurea": ("espiral logarítmica áurea r = φ^(2θ/π), la de los girasoles y los caracoles", {}, {}),
    "espiral_arquimedes": ("espiral de Arquímedes r = θ", {}, {}),
    "mariposa": ("mariposa de Fay r = e^(sen θ) − 2cos 4θ + sen⁵((2θ − π)/24)", {}, {}),
    "lissajous": ("curva de Lissajous x = sen(a t + δ), y = sen(b t)", {"a": 3, "b": 2, "delta": 0.5},
                  {"a": (1, 9), "b": (1, 9), "delta": (0, 3.1416)}),
    "hipotrocoide": ("espirógrafo interior (hipotrocoide) con radios R, r y distancia d", {"R": 5, "r": 3, "d": 5},
                     {"R": (2, 12), "r": (1, 11), "d": (0.5, 12)}),
    "epitrocoide": ("espirógrafo exterior (epitrocoide) con radios R, r y distancia d", {"R": 3, "r": 1, "d": 2},
                    {"R": (1, 12), "r": (1, 11), "d": (0.5, 12)}),
    "astroide": ("astroide x = cos³t, y = sen³t", {}, {}),
    "mandelbrot": ("conjunto de Mandelbrot z → z² + c", {}, {}),
    "julia": ("conjunto de Julia z → z² + c con c = c_re + i·c_im", {"c_re": -0.8, "c_im": 0.156},
              {"c_re": (-1.5, 1), "c_im": (-1, 1)}),
    "fourier": ("sumas parciales de Fourier de la onda cuadrada con n términos", {"n": 5}, {"n": (1, 25)}),
    "campana": ("campana de Gauss (distribución normal)", {}, {}),
}


def descripcion_catalogo() -> str:
    lineas = []
    for tipo, (desc, defaults, rangos) in CATALOGO.items():
        ps = ", ".join(f"{p} entre {a} y {b}" for p, (a, b) in rangos.items())
        lineas.append(f"- {tipo}: {desc}" + (f" (parámetros: {ps})" if ps else ""))
    return "\n".join(lineas)


def normalizar(spec: dict | None) -> dict | None:
    """Valida el tipo y recorta los parámetros a sus rangos. Devuelve None si el tipo no existe."""
    if not isinstance(spec, dict) or spec.get("tipo") not in CATALOGO:
        return None
    _, defaults, rangos = CATALOGO[spec["tipo"]]
    params = dict(defaults)
    for k, v in (spec.get("params") or {}).items():
        if k in rangos:
            try:
                a, b = rangos[k]
                params[k] = min(max(float(v), a), b)
            except (TypeError, ValueError):
                pass
    for k in ("a", "b", "n", "R", "r"):
        if k in params:
            params[k] = int(round(params[k]))
    if spec["tipo"] == "hipotrocoide" and params["r"] >= params["R"]:
        params["r"] = params["R"] - 1  # con r = R la curva degenera
    return {"tipo": spec["tipo"], "params": params}


def _num(x: float) -> str:
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    f = Fraction(x).limit_denominator(12)
    if abs(float(f) - x) < 1e-6:
        return rf"\tfrac{{{f.numerator}}}{{{f.denominator}}}"
    return f"{x:.2f}".rstrip("0").rstrip(".")


def latex(spec: dict) -> str:
    t, p = spec["tipo"], spec["params"]
    if t == "rosa":
        k = p["k"]
        return rf"r=\cos({_num(k)}\theta)" if k != 1 else r"r=\cos\theta"
    if t == "cardioide":
        return r"r=1-\cos\theta"
    if t == "corazon":
        return r"\begin{aligned}x&=16\sin^3 t\\ y&=13\cos t-5\cos 2t-2\cos 3t-\cos 4t\end{aligned}"
    if t == "lemniscata":
        return r"r^2=\cos 2\theta"
    if t == "espiral_aurea":
        return r"r=\varphi^{\,2\theta/\pi}"
    if t == "espiral_arquimedes":
        return r"r=\theta"
    if t == "mariposa":
        return r"r=e^{\sin\theta}-2\cos 4\theta+\sin^5\!\left(\tfrac{2\theta-\pi}{24}\right)"
    if t == "lissajous":
        d = p["delta"]
        fase = f"+{_num(d)}" if d > 1e-6 else ""
        return rf"\begin{{aligned}}x&=\sin({p['a']}t{fase})\\ y&=\sin({p['b']}t)\end{{aligned}}"
    if t in ("hipotrocoide", "epitrocoide"):
        R, r, d = p["R"], p["r"], _num(p["d"])
        A = R - r if t == "hipotrocoide" else R + r
        k = Fraction(A, r)
        ks = str(k.numerator) if k.denominator == 1 else rf"\tfrac{{{k.numerator}}}{{{k.denominator}}}"
        sig = "+" if t == "hipotrocoide" else "-"
        A = "" if A == 1 else A
        return (rf"\begin{{aligned}}x&={A}\cos t{sig}{d}\cos({ks}\,t)\\ "
                rf"y&={A}\sin t-{d}\sin({ks}\,t)\end{{aligned}}")
    if t == "astroide":
        return r"x^{2/3}+y^{2/3}=1"
    if t == "mandelbrot":
        return r"z_{n+1}=z_n^2+c"
    if t == "julia":
        cr, ci = p["c_re"], p["c_im"]
        return rf"z_{{n+1}}=z_n^2{cr:+.3g}{ci:+.3g}\,i"
    if t == "fourier":
        return rf"f(x)=\frac{{4}}{{\pi}}\sum_{{k=1}}^{{{p['n']}}}\frac{{\sin\big((2k-1)x\big)}}{{2k-1}}"
    if t == "campana":
        return r"f(x)=\frac{1}{\sqrt{2\pi}}\,e^{-x^2/2}"
    return ""
