"""Renueva y revisa los tokens de Meta. Uso: python -m bot.tokens [--renovar-ig ARCHIVO]
(corre cada semana con .github/workflows/tokens.yml)

- IG_TOKEN: se renueva (Meta lo extiende otros 60 días). El token nuevo se escribe en ARCHIVO para que el workflow
  actualice el secret; nunca se imprime.
- META_PAGE_TOKEN: no se puede renovar por API; se comprueba que funcione, que sea de la página correcta y cuándo caduca.
Si algo falla, el workflow termina en rojo: GitHub te avisa por correo y en la pestaña Actions.
Ojo: si Meta invalida las sesiones (cambio de contraseña, cuentas nuevas en el Centro de cuentas, revisión de seguridad),
ningún token se puede recuperar solo: hay que generarlos de nuevo a mano."""
import os
import sys
from datetime import datetime, timezone
import requests
from .config import GRAPH_VERSION

IG = "https://graph.instagram.com"
FB = f"https://graph.facebook.com/{GRAPH_VERSION}"
AVISO_DIAS = 14


def _get(url: str, **params) -> dict:
    r = requests.get(url, params=params, timeout=60)
    try:
        data = r.json()
    except ValueError:
        data = {"error": {"message": r.text[:300]}}
    if not r.ok or "error" in data:
        raise RuntimeError((data.get("error") or {}).get("message", r.text[:300]))
    return data


def renovar_ig(destino: str | None) -> list[str]:
    problemas = []
    token = os.environ.get("IG_TOKEN", "")
    try:
        me = _get(f"{IG}/me", fields="username", access_token=token)
        print(f"IG_TOKEN: válido para @{me.get('username')}")
    except Exception as e:
        return [f"IG_TOKEN no funciona ({e}). Hay que generarlo de nuevo a mano."]
    if not destino:
        return problemas
    try:
        r = _get(f"{IG}/refresh_access_token", grant_type="ig_refresh_token", access_token=token)
        nuevo, dias = r["access_token"], int(r.get("expires_in", 0)) // 86400
        with open(destino, "w") as f:
            f.write(nuevo)
        print(f"IG_TOKEN: renovado, vale {dias} días más")
    except Exception as e:
        problemas.append(f"No se pudo renovar IG_TOKEN ({e})")
    return problemas


def revisar_pagina() -> list[str]:
    token, page_id = os.environ.get("META_PAGE_TOKEN", ""), os.environ.get("FB_PAGE_ID", "")
    try:
        me = _get(f"{FB}/me", fields="id,name", access_token=token)
    except Exception as e:
        return [f"META_PAGE_TOKEN no funciona ({e}). Hay que generarlo de nuevo a mano."]
    if page_id and me.get("id") != page_id:
        return [f"META_PAGE_TOKEN es de '{me.get('name')}' ({me.get('id')}), no de la página {page_id}."]
    print(f"META_PAGE_TOKEN: válido para la página {me.get('name')}")
    try:  # cuándo caduca (si Meta deja consultarlo con el propio token)
        d = _get(f"{FB}/debug_token", input_token=token, access_token=token)["data"]
        exp = int(d.get("expires_at") or 0)
        if exp == 0:
            print("META_PAGE_TOKEN: no caduca")
        else:
            dias = (datetime.fromtimestamp(exp, timezone.utc) - datetime.now(timezone.utc)).days
            print(f"META_PAGE_TOKEN: caduca en {dias} días")
            if dias <= AVISO_DIAS:
                return [f"META_PAGE_TOKEN caduca en {dias} días: genera uno nuevo (Tipo Page, Caducidad Nunca)."]
    except Exception as e:
        print(f"(No se pudo consultar la caducidad del token de página: {e})")
    return []


def main() -> None:
    destino = sys.argv[sys.argv.index("--renovar-ig") + 1] if "--renovar-ig" in sys.argv else None
    problemas = renovar_ig(destino) + revisar_pagina()
    for p in problemas:
        print(f"::error title=Tokens de Meta::{p}")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
