"""Configuración central."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v26.0")

HANDLE = os.getenv("PAGE_HANDLE", "@matebellx")
LINK = "https://www.mateguapo.com/materiales-de-estudio"

# Paleta Bellxs: negro profundo, crema y dorado
BRAND = {"bg": "#060608", "fg": "#F3EAD7", "accent": "#D9B56C", "alert": "#E06A5A"}
ESLOGAN = "Porque las Matemáticas son Bellxs"

# keyword -> libro. nivel: "uni" | "bach". El DM lleva siempre el mismo link, así que cualquier keyword dispara la misma respuesta.
BOOKS = {
    "CALCULO": {
        "libro": "1000 Ejercicios de Cálculo en 1 Variable", "nivel": "uni",
        "areas": ["límites y continuidad", "épsilon-delta", "derivadas y regla de la cadena", "optimización y razones relacionadas",
                  "técnicas de integración", "integrales impropias", "aplicaciones de la integral (áreas y volúmenes)"],
    },
    "MULTIVARIABLE": {
        "libro": "1000 Ejercicios de Cálculo Multivariable", "nivel": "uni",
        "areas": ["derivadas parciales y gradiente", "derivada direccional", "multiplicadores de Lagrange", "integrales dobles y triples",
                  "cambio de variables y jacobiano", "integrales de línea", "teoremas de Green, Stokes y divergencia"],
    },
    "EDO": {
        "libro": "1000 Ejercicios de Ecuaciones Diferenciales Ordinarias", "nivel": "uni",
        "areas": ["ecuaciones separables", "lineales de primer orden", "ecuaciones exactas", "segundo orden con coeficientes constantes",
                  "variación de parámetros", "transformada de Laplace", "sistemas lineales", "existencia y unicidad"],
    },
    "EDP": {
        "libro": "1000 Ejercicios de Ecuaciones Diferenciales Parciales", "nivel": "uni",
        "areas": ["ecuación del calor", "ecuación de onda", "ecuación de Laplace", "separación de variables",
                  "series de Fourier", "método de características"],
    },
    "LINEAL": {
        "libro": "1000 Ejercicios de Álgebra Lineal", "nivel": "uni",
        "areas": ["sistemas lineales y eliminación gaussiana", "matrices e inversas", "determinantes", "espacios y subespacios vectoriales",
                  "transformaciones lineales", "valores y vectores propios", "ortogonalidad y Gram-Schmidt"],
    },
    "ALGEBRA": {
        "libro": "1000 Ejercicios de Álgebra", "nivel": "bach",
        "areas": ["factorización", "ecuaciones y desigualdades", "sistemas de ecuaciones", "exponentes y radicales", "logaritmos"],
    },
    "TRIGONOMETRIA": {
        "libro": "1000 Ejercicios de Trigonometría", "nivel": "bach",
        "areas": ["identidades trigonométricas", "ecuaciones trigonométricas", "ley de senos y cosenos", "círculo unitario y radianes", "gráficas de funciones trigonométricas"],
    },
    "GEOMETRIA": {
        "libro": "1000 Ejercicios de Geometría Analítica", "nivel": "bach",
        "areas": ["la recta", "la circunferencia", "la parábola", "la elipse", "la hipérbola", "lugares geométricos"],
    },
    "PRECALCULO": {
        "libro": "1000 Ejercicios de Pre-Cálculo", "nivel": "bach",
        "areas": ["funciones y transformaciones", "polinomios y funciones racionales", "exponenciales y logaritmos", "sucesiones y series", "números complejos"],
    },
    "PROBABILIDAD": {
        "libro": "1000 Ejercicios de Probabilidad y Estadística", "nivel": "bach",
        "areas": ["combinatoria y conteo", "probabilidad condicional y Bayes", "variables aleatorias", "distribución binomial", "distribución normal", "media, varianza y desviación estándar"],
    },
    "FINANCIERAS": {
        "libro": "1000 Ejercicios de Matemáticas Financieras", "nivel": "bach",
        "areas": ["interés simple y compuesto", "tasas equivalentes", "anualidades", "amortización de créditos", "descuento", "inflación y valor presente"],
    },
}

# ---------------------------------------------------------------------------
# CONCEPTO: "Porque las Matemáticas son Bellxs". Todos los posts son de UNA imagen:
#   Instagram: la imagen + la imagen final (Síguenos / Comenta PALABRA) como carrusel de 2.
#   Facebook: solo la imagen; la invitación va al final del texto.
# Formatos (pilares):
#   identidad   fórmula o identidad que enamora (e^{iπ}+1=0, Basilea, Gauss, Ramanujan…)
#   curva       la ecuación y su dibujo exacto (rosas polares, mariposa, espirógrafos, fractales…)
#   demostracion demostración bella y corta, a veces casi sin palabras
#   naturaleza  matemáticas en la naturaleza, la música y el arte (sin mitos)
#   historia    historias humanas de matemáticas y matemáticos
#   infinito    el infinito y lo inalcanzable (tamaños de infinito, irracionales, incompletitud)
# Cada tipo de post (horario): cta = "follow" | "keyword"; tema = "libre" | "libro"; formatos con su peso base.
# ---------------------------------------------------------------------------
SLOTS = {
    1: {"kind": "single", "cta": "follow", "tema": "libre",            # 09:00 México
        "formatos": {"identidad": 3, "infinito": 2, "naturaleza": 2, "historia": 1}},
    2: {"kind": "single", "cta": "keyword", "tema": "libro",           # 13:00 · el único post de venta del día (tono suave)
        "formatos": {"demostracion": 2, "identidad": 2, "curva": 1}},
    3: {"kind": "single", "cta": "follow", "tema": "libre",            # 18:00 · "Ecuación del día": siempre una curva
        "formatos": {"curva": 1}},
    4: {"kind": "single", "cta": "follow", "tema": "libre",            # 20:00
        "formatos": {"historia": 2, "naturaleza": 2, "infinito": 1, "demostracion": 1}},
}
POST_TYPES = {k: (v["kind"], v["cta"]) for k, v in SLOTS.items()}

# Series semanales (día de la semana en México: 0 = lunes … 6 = domingo): {día: {tipo: (formato, nombre de la serie)}}
SERIES = {
    2: {4: ("historia", "Bellxs de la historia")},
    6: {1: ("demostracion", "Domingo de demostraciones"), 4: ("demostracion", "Domingo de demostraciones")},
}
SERIE_DIARIA = {3: "Ecuación del día"}

# Descripciones (caption) de los posts. False = las publicaciones salen solo con la imagen, sin texto, en las tres redes.
# Claude las sigue escribiendo (sirven para verificar y quedan en el resumen de cada corrida), pero no se publican.
PUBLICAR_DESCRIPCIONES = False

# Texto que se agrega al final del caption SOLO en Facebook (ahí no va la imagen final). {key} = palabra clave
FB_CTA = {
    "follow": "Síguenos: una dosis diaria de belleza matemática ✨",
    "keyword": "¿Te enamoraste? Comenta {key} y te mando 1,000 ejercicios con soluciones paso a paso 📚",
}

# Texto que se agrega al final del post de Threads (ahí tampoco va la imagen final; Threads sí permite links)
TH_CTA = {
    "follow": "Síguenos para tu dosis diaria de belleza matemática 💛",
    "keyword": "📚 1,000 ejercicios con soluciones paso a paso: {link}",
}
TH_LIMITE = 500  # caracteres (Threads cuenta cada emoji por sus bytes UTF-8)

# Bancos de temas por formato (el banco de ideas automático agrega ideas concretas encima de estos)
TEMAS = {
    "identidad": [
        "la identidad de Euler", "el problema de Basilea", "la integral de Gauss", "la fórmula de Euler para poliedros",
        "las series de Ramanujan para π", "la fracción continua del número áureo", "el producto de Wallis",
        "la serie de Leibniz para π", "la fórmula de Stirling", "e como límite y como serie", "la identidad de Vieta para π",
        "suma de cubos igual al cuadrado de la suma", "el número 1729 de Hardy y Ramanujan", "la fórmula de De Moivre",
    ],
    "infinito": [
        "hay infinitos más grandes que otros (Cantor)", "el hotel infinito de Hilbert", "0.999… = 1",
        "los números irracionales nunca se repiten", "el teorema de incompletitud de Gödel", "la paradoja de Zenón",
        "la serie armónica diverge", "hay tantos pares como naturales", "los números trascendentes", "los decimales de π",
        "la curva de Koch: perímetro infinito, área finita", "la trompeta de Gabriel",
    ],
    "naturaleza": [
        "espirales de Fibonacci en girasoles y piñas", "fractales en helechos, romanescos y costas", "hexágonos en los panales",
        "la armonía musical y las razones de frecuencias", "la catenaria en puentes y arcos", "simetrías en copos de nieve",
        "teselados de Escher", "el ángulo áureo en las plantas", "ondas, sonido y series de Fourier",
        "la geometría de las conchas de nautilo (sin mitos)", "las manchas animales y las ecuaciones de Turing",
    ],
    "historia": [
        "Srinivasa Ramanujan", "Emmy Noether", "Évariste Galois y la noche antes del duelo", "Sophie Germain",
        "Leonhard Euler escribiendo ciego", "Hipatia de Alejandría", "Kurt Gödel", "Georg Cantor", "Maryam Mirzakhani",
        "Carl Friedrich Gauss de niño", "Ada Lovelace", "Alan Turing", "Grigori Perelman y la conjetura de Poincaré",
        "Andrew Wiles y el último teorema de Fermat", "Paul Erdős", "Katherine Johnson",
    ],
    "demostracion": [
        "la suma de impares da un cuadrado", "√2 es irracional", "hay infinitos números primos", "el teorema de Pitágoras sin palabras",
        "la suma de Gauss 1+2+…+n", "la serie geométrica 1/2+1/4+… = 1", "los ángulos de un triángulo suman 180°",
        "el área del círculo desenrollando anillos", "suma de cubos sin palabras",
    ],
}

# Ganchos de la primera línea (el aprendizaje ajusta cuál funciona mejor)
HOOKS = ["pregunta", "asombro", "metafora", "historia", "dato_preciso"]
HOOKS_POR_FORMATO = {
    "historia": ["historia", "asombro", "pregunta"],
    "curva": ["asombro", "pregunta", "metafora"],
}

# Cómo se elige la mejor de las ideas que propone Claude (pesos de sus autoevaluaciones 1-10)
PESOS_IDEA = {"default": {"compartible": 0.50, "curiosidad": 0.30, "comentable": 0.20}}
N_IDEAS = 6


def slides_rango(kind: str, formato: str) -> tuple[int, int]:
    """Número de slides de contenido (sin contar la imagen final de CTA). Todos los posts son de 1 imagen."""
    return (1, 1)


# ---------------------------------------------------------------------------
# FONDOS (arte matemático generado en bot/fondos.js). Se elige según palabras del tema;
# si no hay coincidencia, uno de FONDOS_DEFAULT. En los posts de curva, uno discreto de FONDOS_CURVA.
# ---------------------------------------------------------------------------
FONDOS_POR_TEMA = [
    (["probab", "combinat", "conteo", "estadist", "bayes", "binomial", "normal", "gauss", "campana"], ["probabilidad", "red"]),
    (["complej", "euler", "de moivre", "constante e", " e como"], ["fractal", "formulas"]),
    (["infinit", "cantor", "hilbert", "zenon", "godel", "koch", "fractal", "trompeta", "irracional", "trascend"], ["fractal", "espiral"]),
    (["primo", "teoria de numeros", "1729", "erdos", "fermat"], ["primos"]),
    (["geometr", "circunferencia", "parabola", "elipse", "hiperbola", "recta", "pitagoras", "triangul", "poincare", "poliedro", "area"], ["geometria"]),
    (["trigonom", "seno", "coseno", "radian", "angulo"], ["trig"]),
    (["derivad", "integral", "limite", "calculo", "funcion", "optimiz", "gradiente", "lagrange", "multivariable", "stirling"], ["funciones"]),
    (["diferencial", "calor", "onda", "laplace", "fourier", "musica", "sonido", "armonia", "turing"], ["ondas"]),
    (["matri", "vector", "lineal", "determinante", "transformacion", "noether", "simetr"], ["rejilla", "geometria"]),
    (["fibonacci", "aure", "girasol", "nautilo", "espiral", "planta", "pina"], ["espiral", "lissajous"]),
    (["naturaleza", "arte", "escher", "tesel", "panal", "hexagon", "copo", "catenaria", "helecho"], ["geometria", "lissajous"]),
    (["ramanujan", "serie", "basilea", "wallis", "leibniz", "vieta", "producto", "suma"], ["formulas", "espiral"]),
    (["algebra", "ecuacion", "factoriz", "exponente", "logaritmo", "aritmet", "potencia"], ["formulas", "funciones"]),
]
FONDOS_DEFAULT = ["formulas", "lissajous", "espiral", "fractal", "geometria"]
FONDOS_CURVA = ["formulas", "geometria", "rejilla"]


# ---------------------------------------------------------------------------
# APRENDIZAJE (bot/learn.py y bot/planner.py)
# ---------------------------------------------------------------------------
EXPLORE_P = 0.30        # 30% de los posts prueban algo al azar; 70% aprovechan lo que va funcionando
MIN_DATOS = 12          # posts medidos necesarios antes de confiar en los pesos aprendidos
GAMMA = 2.0             # qué tan fuerte se favorece lo que funciona (1 = proporcional)
SHRINK_K = 2            # prudencia: con pocos datos, los pesos se quedan cerca de 1
COOLDOWN_TEMA = 6       # un tema no se repite en los últimos N posts (si hay alternativas)
MIN_EDAD_H = 48         # horas antes de medir un post
MAX_EDAD_DIAS = 10      # después de esto sus métricas se dan por finales
VENTANA = 40            # posts recientes usados para aprender
# Valor de cada interacción para el puntaje (compartir y seguir pesan más porque traen alcance nuevo)
PESOS_METRICAS = {"shares": 5, "saved": 3, "follows": 10, "comments": 2, "likes": 0.5}
PESO_ALCANCE = 0.4      # puntaje = 60% calidad de interacción por alcance + 40% alcance relativo

DM_TEXT = "¡Hola{name}! 👋 Aquí tienes los libros de 1,000 ejercicios 📚 {link}"

SIZE = (1080, 1350)
