# mateguapo-math-bot

Bot en GitHub Actions: 4 posts/día en Instagram + Facebook y respuesta privada automática a comentarios con palabra clave.

| Tipo | Contenido | Cierre |
|---|---|---|
| 1 | Carrusel 4-6 slides | Imagen "Síguenos" |
| 2 | Carrusel 4-6 slides | Imagen "Comenta PALABRA" |
| 3 | 1 imagen | Imagen "Síguenos" (se publica como carrusel de 2) |
| 4 | 1 imagen | Imagen "Comenta PALABRA" (carrusel de 2) |

**Contenido**: API de Claude (texto + LaTeX), con segunda pasada de verificación matemática. **Imágenes**: HTML + KaTeX + Playwright (sin generador de imágenes, así la notación nunca sale deformada).

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
