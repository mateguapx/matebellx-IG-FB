"""Configuración central."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v26.0")

HANDLE = os.getenv("PAGE_HANDLE", "@matebellx")
LINK = "https://www.mateguapo.com/materiales-de-estudio"

# Paleta Mateguapo
BRAND = {"bg": "#000000", "fg": "#FFFFFF", "accent": "#ffde59", "alert": "#ff3131"}

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
# MEZCLA DE CONTENIDO POR HORARIO (tipo de post). Todos los posts son de UNA imagen:
#   Instagram: la imagen + la imagen final (Síguenos / Comenta PALABRA) como carrusel de 2.
#   Facebook: solo la imagen; la invitación (seguir / palabra clave) va al final del texto.
#   cta:  "follow" (Síguenos) | "keyword" (Comenta PALABRA)
#   tema: "libre" (temas virales de cualquier área) | "libro" (área de uno de los libros, para que la palabra clave tenga sentido)
#   formatos: peso base de cada formato. El aprendizaje automático multiplica estos pesos según el rendimiento.
#   Para forzar un formato, deja solo ese (ej. tipo 3 = siempre reto básico).
# ---------------------------------------------------------------------------
SLOTS = {
    1: {"kind": "single", "cta": "follow", "tema": "libre",
        "formatos": {"wow": 3, "reto_logico": 2, "error": 2, "dato": 1, "motivacion": 1, "tips": 1, "chiste": 1}},
    2: {"kind": "single", "cta": "keyword", "tema": "libro",
        "formatos": {"problema": 3, "error": 2, "wow": 1, "dato": 1}},
    3: {"kind": "single", "cta": "follow", "tema": "libre",
        "formatos": {"reto_basico": 1}},  # 1 reto de matemática básica al día
    4: {"kind": "single", "cta": "keyword", "tema": "libro",
        "formatos": {"error": 2, "problema": 2, "dato": 1}},
}
POST_TYPES = {k: (v["kind"], v["cta"]) for k, v in SLOTS.items()}

# Texto que se agrega al final del caption SOLO en Facebook (ahí no va la imagen final). {key} = palabra clave
FB_CTA = {
    "follow": "Síguenos para un reto y un dato nuevo cada día 🧠",
    "keyword": "📚 ¿Quieres 1,000 ejercicios con soluciones paso a paso? Comenta {key} y te mando el link.",
}

# Temas para los posts de tema "libre" (alcance amplio, cualquier persona)
TEMAS_LIBRES = [
    "aritmética y orden de operaciones", "porcentajes y fracciones en la vida diaria", "el infinito y sus paradojas",
    "números complejos y la constante e", "probabilidad que engaña a la intuición", "lógica y acertijos",
    "números primos y teoría de números", "geometría con resultados curiosos", "conteo y combinatoria cotidiana",
    "matemáticas del dinero (descuentos, interés, ofertas)", "historias de genios de las matemáticas",
    "demostraciones elegantes y cortas", "errores comunes de álgebra", "teoría de juegos y estrategia",
    "patrones y sucesiones sorprendentes", "matemáticas en la naturaleza, la música y el arte",
]
# Temas para los retos (se rotan para no repetir)
TEMAS_RETO_BASICO = [
    "orden de operaciones con trampa", "porcentajes que engañan", "fracciones y decimales", "potencias y signos",
    "problemas de razonamiento con números (máquinas, trabajadores, precios)", "ecuaciones de una incógnita en la vida diaria",
    "promedios y velocidades medias", "cuál es mayor (comparar números o expresiones)", "patrones numéricos: el número que sigue",
]
TEMAS_RETO_LOGICO = [
    "monedas y balanzas", "cajas con etiquetas equivocadas", "los 100 focos o las 100 puertas", "dilema del prisionero y teoría de juegos",
    "Monty Hall y probabilidad condicional", "prisioneros y sombreros de colores", "cruzar el río con restricciones",
    "caballeros que dicen la verdad y bribones que mienten", "relojes, calendarios y edades", "contar cuadrados, triángulos o caminos",
]

TEMAS_MOTIVACION = [
    "estudiar lo que te apasiona aunque otros no lo entiendan", "la cultura de la mediocridad y conformarse",
    "reprobar un examen no te define", "disciplina contra motivación", "por qué vale la pena aprender matemáticas de verdad",
    "el síndrome del impostor en estudiantes", "compararte con otros en la escuela", "elegir carrera por pasión o por dinero",
]
TEMAS_TIPS = [
    "cómo estudiar para un examen de matemáticas", "la técnica Feynman", "repetición espaciada", "no bloquearte en un examen",
    "cómo tomar apuntes de matemáticas", "practicar con ejercicios en vez de solo leer teoría", "estudiar en bloques (pomodoro)",
    "cómo entender una demostración", "qué hacer cuando no entiendes una clase",
]

# Tipos de gancho para el primer slide (el aprendizaje ajusta cuál funciona mejor)
HOOKS = ["pregunta", "numero_impactante", "mito_vs_realidad", "paradoja", "error_comun", "historia_curiosa", "desafio", "humor"]
HOOK_RETO = "desafio"  # los retos siempre usan gancho de desafío
# Ganchos permitidos por formato (los que no aparecen aquí usan todos menos desafio y humor)
HOOKS_POR_FORMATO = {
    "reto_basico": ["desafio"], "reto_logico": ["desafio"], "chiste": ["humor"],
    "motivacion": ["pregunta", "mito_vs_realidad", "historia_curiosa"], "tips": ["pregunta", "error_comun", "mito_vs_realidad"],
}

# Cómo se elige la mejor de las ideas que propone Claude (pesos de sus autoevaluaciones 1-10)
PESOS_IDEA = {"default": {"compartible": 0.45, "curiosidad": 0.25, "comentable": 0.30},
              "reto": {"compartible": 0.30, "curiosidad": 0.20, "comentable": 0.50}}
N_IDEAS = 6


def slides_rango(kind: str, formato: str) -> tuple[int, int]:
    """Número de slides de contenido (sin contar la imagen final de CTA). Hoy todos los posts son de 1 imagen."""
    return (1, 1)


# ---------------------------------------------------------------------------
# FONDOS (arte matemático generado en bot/fondos.js). Se elige según palabras del tema;
# si no hay coincidencia, uno de FONDOS_DEFAULT. El aprendizaje también mide qué fondos funcionan mejor.
# ---------------------------------------------------------------------------
FONDOS_POR_TEMA = [
    (["probab", "combinat", "conteo", "estadist", "bayes", "binomial", "normal", "monty", "varianza", "cumplea"], ["probabilidad", "red"]),
    (["complej", "constante e", "euler"], ["fractal", "formulas"]),
    (["infinit", "paradoj", "sucesion", "serie", "patron"], ["fractal", "espiral"]),
    (["primo", "teoria de numeros"], ["primos"]),
    (["geometr", "circunferencia", "parabola", "elipse", "hiperbola", "recta", "lugar", "cuadrado", "triangul"], ["geometria"]),
    (["trigonom", "seno", "coseno", "circulo unitario", "radian", "angulo", "reloj"], ["trig"]),
    (["derivad", "integral", "limite", "calculo", "funcion", "optimiz", "continuidad", "epsilon", "gradiente",
      "lagrange", "parcial", "multivariable", "green", "stokes", "jacobiano"], ["funciones"]),
    (["diferencial", "calor", "onda", "laplace", "fourier", "separab", "exacta", "caracteristica", "coeficientes"], ["ondas"]),
    (["matri", "vector", "lineal", "determinante", "transformacion", "propio", "gram", "espacio"], ["rejilla"]),
    (["logic", "acertijo", "juego", "prisioner", "caballero", "moneda", "caja", "foco", "puerta", "rio", "sombrero"], ["red", "formulas"]),
    (["dinero", "interes", "financ", "porcentaje", "descuento", "anualidad", "amortiz", "inflacion", "valor presente", "tasa"], ["funciones", "formulas"]),
    (["naturaleza", "musica", "arte", "fibonacci", "aureo", "elegante"], ["espiral", "lissajous"]),
    (["aritmetica", "operacion", "fraccion", "decimal", "potencia", "signo", "promedio", "razonamiento", "mayor",
      "ecuacion", "factoriz", "exponente", "radical", "logaritmo", "algebra", "desigualdad"], ["formulas", "rejilla", "funciones"]),
]
FONDOS_DEFAULT = ["formulas", "lissajous", "espiral", "fractal", "geometria"]


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
