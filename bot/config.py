"""Configuración central."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
GRAPH_VERSION = os.getenv("GRAPH_VERSION", "v26.0")

HANDLE = os.getenv("PAGE_HANDLE", "@tu_pagina")
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

POST_TYPES = {1: ("carousel", "follow"), 2: ("carousel", "keyword"), 3: ("single", "follow"), 4: ("single", "keyword")}

DM_TEXT = "¡Hola{name}! 👋 Aquí tienes los libros de 1,000 ejercicios 📚 {link}"

SIZE = (1080, 1350)
