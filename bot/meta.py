"""Publicación en Instagram (API con Instagram Login) y Facebook (token de Página). Verifica endpoints contra la doc vigente de Meta."""
import json
import os
import time
import requests
from .config import GRAPH_VERSION

IG_BASE = f"https://graph.instagram.com/{GRAPH_VERSION}"
TH_BASE = "https://graph.threads.net/v1.0"
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
    extra = {"caption": caption} if caption else {}
    parent = _ig_post(f"{IG_ID()}/media", media_type="CAROUSEL", children=",".join(children), **extra)["id"]
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


def ig_media_info(media_id: str) -> dict:
    """Datos básicos del post (no requieren permiso de insights)."""
    return _ig_get(media_id, fields="like_count,comments_count,timestamp,permalink,media_type")


def ig_media_insight(media_id: str, metric: str) -> float | None:
    """Una métrica de insights del post (requiere instagram_business_manage_insights).
    Se pide de una en una porque si una no aplica a ese tipo de post, Meta rechaza toda la petición."""
    data = _ig_get(f"{media_id}/insights", metric=metric).get("data", [])
    if not data:
        return None
    d = data[0]
    if d.get("total_value"):
        return d["total_value"].get("value")
    vals = d.get("values") or []
    return vals[0].get("value") if vals else None


def refresh_ig_token() -> str:
    """Renueva el token de larga duración (válido 60 días; renovable después de 24 h de emitido)."""
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": IG_TOKEN()}, timeout=60)
    return _check(r, "IG refresh")["access_token"]


# --- Facebook ---
def publish_facebook(image_urls: list[str], caption: str) -> str:
    """Una imagen -> foto publicada directamente (devuelve el id del post, que es el que lleva los comentarios).
    Varias imágenes -> fotos sin publicar + un post del feed que las agrupa."""
    if len(image_urls) == 1:
        extra = {"caption": caption} if caption else {}
        r = _fb_post(f"{PAGE_ID()}/photos", url=image_urls[0], published="true", **extra)
        return r.get("post_id") or r["id"]
    photo_ids = [_fb_post(f"{PAGE_ID()}/photos", url=u, published="false")["id"] for u in image_urls]
    attached = json.dumps([{"media_fbid": i} for i in photo_ids])
    extra = {"message": caption} if caption else {}
    return _fb_post(f"{PAGE_ID()}/feed", attached_media=attached, **extra)["id"]


def fb_comments(post_id: str) -> list[dict]:
    return _fb_get(f"{post_id}/comments", fields="id,message,from", filter="toplevel", limit=100).get("data", [])


def fb_private_reply(comment_id: str, text: str) -> None:
    """Respuesta privada a un comentario de la Página. Primero la Send API de Messenger
    (POST /{page-id}/messages con recipient.comment_id); si falla, el edge /{comment-id}/private_replies."""
    r = requests.post(
        f"{FB_BASE}/{PAGE_ID()}/messages",
        params={"access_token": PAGE_TOKEN()},
        json={"recipient": {"comment_id": comment_id}, "message": {"text": text}, "messaging_type": "RESPONSE"},
        timeout=60,
    )
    if r.ok:
        return
    first = f"FB send API -> {r.status_code}: {r.text}"
    try:
        _fb_post(f"{comment_id}/private_replies", message=text)
    except Exception as e:
        raise RuntimeError(f"{first} || {e}") from e


def fb_reply_comment(comment_id: str, text: str) -> None:
    """Respuesta pública al comentario (requiere pages_manage_engagement)."""
    _fb_post(f"{comment_id}/comments", message=text)


# --- Threads ---
TH_TOKEN = lambda: os.environ.get("THREADS_TOKEN", "")
TH_ID = lambda: os.environ.get("THREADS_USER_ID") or "me"


def threads_activo() -> bool:
    return bool(TH_TOKEN())


def _th(method: str, path: str, **params) -> dict:
    r = requests.request(method, f"{TH_BASE}/{path}", params={**params, "access_token": TH_TOKEN()}, timeout=60)
    return _check(r, f"Threads {method} {path}")


def publish_threads(image_url: str, text: str) -> str:
    """Post de una imagen en Threads: contenedor -> esperar a que termine de procesar -> publicar."""
    extra = {"text": text} if text else {}
    cont = _th("POST", f"{TH_ID()}/threads", media_type="IMAGE", image_url=image_url, **extra)["id"]
    time.sleep(10)
    for _ in range(18):  # hasta ~2 min
        st = _th("GET", cont, fields="status,error_message")
        if st.get("status") == "FINISHED":
            break
        if st.get("status") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Contenedor de Threads en estado {st.get('status')}: {st.get('error_message')}")
        time.sleep(7)
    return _th("POST", f"{TH_ID()}/threads_publish", creation_id=cont)["id"]

