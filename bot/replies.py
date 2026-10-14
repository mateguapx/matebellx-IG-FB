"""
POOL DE RESPUESTAS PÚBLICAS al comentario de quien pidió el libro (se publican después de enviar el DM).
Edita, agrega o quita frases entre comillas. Mínimo 5 frases para que la rotación funcione.
No uses en ellas ninguna de las palabras clave (CALCULO, EDO, LINEAL, ALGEBRA...) para que el bot no se responda a sí mismo.
"""

REPLY_POOL = [
    "¡Enviado! 🙌",
    "Listooo, checa tu DM :)",
    "¡Ya está!! 📩",
    "¡Va! Te mandé mensaje 📚",
    "Ya te llegó el DM 😉",
    "¡Hecho! Revisa tus mensajes 🙌",
    "Listo, ya te escribí por DM ✅",
    "¡Te lo mandé! Checa tu bandeja 📬",
    "¡Dale! Ya tienes mensaje 🔥",
    "Ahí va, revisa tu DM 🚀",
]

# Una frase no se repite hasta que hayan salido otras N distintas (se limita solo si el pool es pequeño).
NO_REPETIR_ULTIMAS = 4
