"""Banco CURADO de frases célebres de matemáticas, cada una con su fuente documentada.
Las frases no las inventa ni las elige Claude: muchas "citas famosas" que circulan son apócrifas o están mal atribuidas
(p. ej. "las matemáticas son el lenguaje con el que Dios escribió el universo" NO es literal de Galileo).
Para agregar una frase: pon el texto en español (traducción fiel), el autor y la obra/fecha/contexto de donde sale.
Si una frase es de autoría dudosa, NO la agregues; si es "atribuida" o reportada por otra persona, dilo en 'fuente'."""

FRASES = [
    {"id": "hardy-belleza", "autor": "G. H. Hardy", "fuente": "A Mathematician's Apology, 1940",
     "texto": "La belleza es la primera prueba: no hay lugar permanente en el mundo para las matemáticas feas."},
    {"id": "hardy-patrones", "autor": "G. H. Hardy", "fuente": "A Mathematician's Apology, 1940",
     "texto": "Un matemático, como un pintor o un poeta, es un creador de patrones."},
    {"id": "russell-belleza", "autor": "Bertrand Russell", "fuente": "«El estudio de las matemáticas», 1907",
     "texto": "Las matemáticas, vistas correctamente, poseen no solo verdad, sino belleza suprema: una belleza fría y austera, como la de una escultura."},
    {"id": "galileo-libro", "autor": "Galileo Galilei", "fuente": "Il Saggiatore, 1623",
     "texto": "El universo está escrito en lengua matemática, y sus caracteres son triángulos, círculos y otras figuras geométricas."},
    {"id": "gauss-reina", "autor": "Carl Friedrich Gauss", "fuente": "citado por Sartorius von Waltershausen, 1856",
     "texto": "Las matemáticas son la reina de las ciencias, y la aritmética es la reina de las matemáticas."},
    {"id": "gauss-pauca", "autor": "Carl Friedrich Gauss", "fuente": "su lema personal",
     "texto": "Pocos, pero maduros."},
    {"id": "poincare-bella", "autor": "Henri Poincaré", "fuente": "Ciencia y método, 1908",
     "texto": "El científico no estudia la naturaleza porque sea útil; la estudia porque le deleita, y le deleita porque es bella."},
    {"id": "hilbert-sabremos", "autor": "David Hilbert", "fuente": "discurso en Königsberg, 1930 (grabado en su tumba)",
     "texto": "Debemos saber. Sabremos."},
    {"id": "hilbert-paraiso", "autor": "David Hilbert", "fuente": "«Sobre el infinito», 1926",
     "texto": "Nadie podrá expulsarnos del paraíso que Cantor ha creado para nosotros."},
    {"id": "cantor-libertad", "autor": "Georg Cantor", "fuente": "Fundamentos de una teoría general de conjuntos, 1883",
     "texto": "La esencia de las matemáticas reside en su libertad."},
    {"id": "newton-gigantes", "autor": "Isaac Newton", "fuente": "carta a Robert Hooke, 1676",
     "texto": "Si he visto más lejos, es porque estoy sobre hombros de gigantes."},
    {"id": "leibniz-musica", "autor": "Gottfried Leibniz", "fuente": "carta a Christian Goldbach, 1712",
     "texto": "La música es un ejercicio oculto de aritmética del alma, que no sabe que está contando."},
    {"id": "kronecker-enteros", "autor": "Leopold Kronecker", "fuente": "conferencia de 1886, citado por Heinrich Weber",
     "texto": "Dios creó los números enteros; todo lo demás es obra del hombre."},
    {"id": "mirzakhani-paciencia", "autor": "Maryam Mirzakhani", "fuente": "entrevista con el Clay Mathematics Institute, 2008",
     "texto": "La belleza de las matemáticas solo se muestra a sus seguidores más pacientes."},
    {"id": "einstein-poesia", "autor": "Albert Einstein", "fuente": "homenaje a Emmy Noether, The New York Times, 1935",
     "texto": "Las matemáticas puras son, a su manera, la poesía de las ideas lógicas."},
    {"id": "weyl-bello", "autor": "Hermann Weyl", "fuente": "citado por Freeman Dyson, 1956",
     "texto": "Mi trabajo siempre ha intentado unir lo verdadero con lo bello; pero cuando tuve que elegir uno u otro, casi siempre elegí lo bello."},
    {"id": "dirac-ecuaciones", "autor": "Paul Dirac", "fuente": "Scientific American, 1963",
     "texto": "Es más importante que haya belleza en las ecuaciones que hacerlas encajar con el experimento."},
    {"id": "fourier-naturaleza", "autor": "Joseph Fourier", "fuente": "Teoría analítica del calor, 1822",
     "texto": "El estudio profundo de la naturaleza es la fuente más fecunda de descubrimientos matemáticos."},
    {"id": "lovelace-telar", "autor": "Ada Lovelace", "fuente": "Notas sobre la máquina analítica, 1843",
     "texto": "La máquina analítica teje patrones algebraicos, así como el telar de Jacquard teje flores y hojas."},
    {"id": "wigner-regalo", "autor": "Eugene Wigner", "fuente": "«La irrazonable eficacia de las matemáticas», 1960",
     "texto": "El milagro de que el lenguaje de las matemáticas sea el apropiado para formular las leyes de la física es un regalo maravilloso que no entendemos ni merecemos."},
    {"id": "euclides-camino", "autor": "Euclides", "fuente": "según Proclo, al rey Ptolomeo",
     "texto": "No hay camino real hacia la geometría."},
    {"id": "renyi-cafe", "autor": "Alfréd Rényi", "fuente": "frase popularizada por Paul Erdős",
     "texto": "Un matemático es una máquina que convierte café en teoremas."},
]

POR_ID = {f["id"]: f for f in FRASES}
