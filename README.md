# mateguapo-math-bot

Bot en GitHub Actions: 4 posts/día en Instagram + Facebook, respuesta automática a comentarios con palabra clave y aprendizaje automático del contenido.

**Concepto: "Porque las Matemáticas son Bellxs".** Mostrar la belleza de las matemáticas, romantizándolas con medida.
Todos los posts son de **una imagen**. Instagram: la imagen + la imagen final ("Síguenos" o "Comenta PALABRA", con el mockup del libro de `assets/libros/`). Facebook: solo la imagen, con la invitación al final del texto. **Threads**: solo la imagen con un texto propio, más conversacional, con 💛 (y el link a los libros en los posts de palabra clave). Threads se activa al crear los secrets `THREADS_TOKEN` (y opcional `THREADS_USER_ID`).

| Tipo | Hora (México) | Contenido (mezcla en `bot/config.py` → `SLOTS`) | Cierre |
|---|---|---|---|
| 1 | 09:00 | Identidad que enamora, infinito, naturaleza y arte, historia | Síguenos |
| 2 | 13:00 | Tema de un libro: demostración bella, identidad o curva (único post de venta, tono suave) | Comenta PALABRA |
| 3 | 18:00 | **Ecuación del día**: una curva dibujada con exactitud y su ecuación | Síguenos |
| 4 | 20:00 | Historia, naturaleza y arte, infinito, demostración | Síguenos |

Series semanales: miércoles 20:00 **Bellxs de la historia**; domingo **Domingo de demostraciones** (09:00 y 20:00).

**Estilo**: Playfair Display + Cormorant Garamond, dorado sobre negro, composición centrada, marco fino y el eslogan como firma. Título con alma (fórmulas `$...$`, énfasis `**así**` en cursiva dorada), fórmula protagonista y una línea de apoyo. Curvas exactas desde el catálogo de `bot/curvas.py` (rosas polares, cardioide, corazón, lemniscata, espirales, mariposa de Fay, Lissajous, espirógrafos, astroide, Mandelbrot, Julia, Fourier, campana); la ecuación la escribe el código, así siempre coincide con el dibujo. Fondos de arte matemático según el tema (`bot/fondos.js`).

**Cómo se genera cada post**: `planner.py` elige formato, gancho, tema, curva y fondo (series semanales, 70% lo que mejor funciona, 30% exploración, sin repetir temas recientes, y ideas del banco) → Claude propone 6 ideas y las puntúa → se escribe la mejor → una segunda llamada verifica matemáticas y datos históricos. Los prompts están en `bot/prompts.py`.

**Banco de ideas** (`ideas.yml`, domingos 07:20 México): `bot/ideas.py` mantiene `state/ideas.json` con ideas concretas pendientes por formato; el planificador las usa y se marcan como usadas al publicar.

**Tokens** (`tokens.yml`, lunes 08:10 México): `bot/tokens.py` renueva `IG_TOKEN` y `THREADS_TOKEN` otros 60 días (requiere el secret `GH_PAT`) y revisa `META_PAGE_TOKEN`. Si algo falla, la corrida queda en rojo. Si Meta invalida las sesiones (cambio de contraseña, cuentas nuevas, revisión de seguridad) hay que generar los tokens a mano.

**Aprendizaje** (`learn.yml`, diario 07:40 México): `bot/learn.py` mide los posts de Instagram con más de 48 h (alcance, compartidos, guardados, seguidores, comentarios), calcula un puntaje relativo a su tipo de post (y aprende qué formatos, ganchos, temas y fondos funcionan) y actualiza `state/weights.json` y `state/insights.json`. El informe legible queda en `state/informe.md` y en el resumen de cada corrida. Requiere el permiso `instagram_business_manage_insights` en `IG_TOKEN`.

**Imágenes**: HTML + KaTeX + Playwright (sin generador de imágenes, así la notación nunca sale deformada).

## Puesta en marcha
1. Repo **público** en GitHub (Meta necesita URLs públicas; las imágenes viven en la rama `media`). No subas secretos.
2. Edita `bot/config.py`: `BOOKS` con tus libros reales (keyword, nombre del libro, áreas temáticas).
3. `pip install -r requirements.txt && playwright install chromium && python -m bot.cta` → regenera `assets/cta/` y haz commit.
4. Prueba local sin publicar: `ANTHROPIC_API_KEY=... python -m bot.main --type 2 --dry` (revisa `out/`).
5. Meta: cuenta IG profesional + Página de Facebook; app con Instagram Login (permisos `instagram_business_basic`, `_content_publish`, `_manage_comments`, `_manage_messages`) y casos de uso de Página/Messenger (requiere App Review para producción).
6. Secrets del repo: `ANTHROPIC_API_KEY`, `IG_TOKEN` (token de Instagram de larga duración, **renovar antes de 60 días**), `META_PAGE_TOKEN` (solo Facebook), `IG_USER_ID`, `FB_PAGE_ID`. Variable: `PAGE_HANDLE` (ej. `@mi_pagina`).
7. Actions → `post` → Run workflow con `dry=true` para probar; luego déjalo correr por cron.

## Horarios (UTC → México)
`post.yml`: 15:00, 19:00, 00:00, 02:00 UTC = tipos 1-4. Cámbialos a gusto. El cron de GitHub puede retrasarse varios minutos.

## Pendientes a verificar con la doc vigente de Meta
- Versión de Graph API (`GRAPH_VERSION`) y endpoint de respuestas privadas de IG (aquí: `/{PAGE_ID}/messages` con `recipient.comment_id`, flujo Facebook Login).
- Ventana de días y límite de una respuesta privada por comentario: por eso el DM es un solo mensaje con saludo + link.

## Variables y secrets finales
- Secrets: `ANTHROPIC_API_KEY`, `IG_TOKEN`, `META_PAGE_TOKEN`, `IG_USER_ID`, `FB_PAGE_ID` (+ `GH_PAT` solo si usas `refresh-ig-token`).
- Variables: `PAGE_HANDLE`, `ENABLE_FB_DM` (`true` activa el DM por comentarios de Facebook; requiere `pages_read_user_content` en el token de Página).
- Tras cambiar `bot/config.py` (libros/keywords), regenera las imágenes finales: `python -m bot.cta` y haz commit de `assets/cta/`.
