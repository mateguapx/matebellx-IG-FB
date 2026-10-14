"""Publicación en Instagram (API con Instagram Login) y Facebook (token de Página). Verifica endpoints contra la doc vigente de Meta."""
import json
import os
import time
import requests
from .config import GRAPH_VERSION

IG_BASE = f"https://graph.instagram.com/{GRAPH_VERSION}"
FB_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
IG_TOKEN = lambda: os.environ["IG_TOKEN"]          # token de usuario de Instagram (larga duración, 60 días)
PAGE_TOKEN = lambda: os.environ["META_PAGE_TOKEN"]  # token de Página (solo Facebook)
IG_ID = lambda: os.environ["IG_USER_ID"]
PAGE_ID = lambda: os.environ["FB_PAGE_ID"]


def _check(r: requests.Response, what: str) -> dict:
    if not r.ok:
        raise RuntimeError(f"{what} -> {r.status_code}: {r.text}")
    return r.json()


def _ig_post(path: str, **data) -> dict:
    return _check(requests.post(f"{IG_BASE}/{path}", data={**data, "access_token": IG_TOKEN()}, timeout=60), f"IG POST {path}")


def _ig_get(path: str, **params) -> dict:
    return _check(requests.get(f"{IG_BASE}/{path}", params={**params, "access_token": IG_TOKEN()}, timeout=60), f"IG GET {path}")


def _fb_post(path: str, **data) -> dict:
    return _check(requests.post(f"{FB_BASE}/{path}", data={**data, "access_token": PAGE_TOKEN()}, timeout=60), f"FB POST {path}")


def _fb_get(path: str, **params) -> dict:
    return _check(requests.get(f"{FB_BASE}/{path}", params={**params, "access_token": PAGE_TOKEN()}, timeout=60), f"FB GET {path}")


def _wait_ready(container_id: str, tries: int = 30) -> None:
    for _ in range(tries):
        status = _ig_get(container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Contenedor {container_id} en estado {status}")
        time.sleep(4)
    raise TimeoutError(f"Contenedor {container_id} no terminó a tiempo")


# --- Instagram ---
def publish_instagram(image_urls: list[str], caption: str) -> str:
    """Carrusel (2-10 imágenes). Los posts 'imagen única + CTA' son carruseles de 2."""
    children = []
    for url in image_urls:
        c = _ig_post(f"{IG_ID()}/media", image_url=url, is_carousel_item="true")["id"]
        _wait_ready(c)
        children.append(c)
    parent = _ig_post(f"{IG_ID()}/media", media_type="CAROUSEL", children=",".join(children), caption=caption)["id"]
    _wait_ready(parent)
    return _ig_post(f"{IG_ID()}/media_publish", creation_id=parent)["id"]


def ig_comments(media_id: str) -> list[dict]:
    return _ig_get(f"{media_id}/comments", fields="id,text,username,timestamp", limit=100).get("data", [])


def ig_private_reply(comment_id: str, text: str) -> None:
    # Una respuesta privada por comentario, dentro de 7 días; seguimientos solo si el usuario responde (24 h).
    r = requests.post(
        f"{IG_BASE}/{IG_ID()}/messages",
        params={"access_token": IG_TOKEN()},
        json={"recipient": {"comment_id": comment_id}, "message": {"text": text}},
        timeout=60,
    )
    _check(r, "IG private reply")


def ig_reply_comment(comment_id: str, text: str) -> None:
    """Respuesta pública al comentario (permiso instagram_business_manage_comments)."""
    _ig_post(f"{comment_id}/replies", message=text)


def refresh_ig_token() -> str:
    """Renueva el token de larga duración (válido 60 días; renovable después de 24 h de emitido)."""
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": IG_TOKEN()}, timeout=60)
    return _check(r, "IG refresh")["access_token"]


# --- Facebook ---
def publish_facebook(image_urls: list[str], caption: str) -> str:
    photo_ids = [_fb_post(f"{PAGE_ID()}/photos", url=u, published="false")["id"] for u in image_urls]
    attached = json.dumps([{"media_fbid": i} for i in photo_ids])
    return _fb_post(f"{PAGE_ID()}/feed", message=caption, attached_media=attached)["id"]


def fb_comments(post_id: str) -> list[dict]:
    return _fb_get(f"{post_id}/comments", fields="id,message,from", filter="toplevel", limit=100).get("data", [])


def fb_private_reply(comment_id: str, text: str) -> None:
    _fb_post(f"{comment_id}/private_replies", message=text)


def fb_reply_comment(comment_id: str, text: str) -> None:
    """Respuesta pública al comentario (requiere pages_manage_engagement)."""
    _fb_post(f"{comment_id}/comments", message=text)
