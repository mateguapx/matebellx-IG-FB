"""Sondea comentarios en posts de palabra clave y envía UN mensaje privado con el link. Corre cada ~10 min por cron."""
import json
import os
import random
import re
import unicodedata
from .config import BOOKS, DM_TEXT, LINK, ROOT
from . import meta
from .replies import NO_REPETIR_ULTIMAS, REPLY_POOL

STATE = ROOT / "state"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())


KEYS = {norm(k).strip() for k in BOOKS}


def matches(text: str) -> bool:
    return bool(KEYS & set(norm(text).split()))


def _load(name: str, default):
    p = STATE / name
    return json.loads(p.read_text()) if p.exists() else default


def _save(name: str, data) -> None:
    (STATE / name).write_text(json.dumps(data, ensure_ascii=False, indent=1))


def pick_reply(recent: list[int]) -> int:
    """Elige un índice del pool que no esté entre los últimos usados; actualiza `recent` en sitio."""
    n = len(REPLY_POOL)
    ventana = min(NO_REPETIR_ULTIMAS, n - 1)
    candidatos = [i for i in range(n) if i not in recent[-ventana:]] if ventana > 0 else list(range(n))
    i = random.choice(candidatos)
    recent.append(i)
    del recent[:-20]
    return i


def run() -> int:
    posts = _load("kw_posts.json", {"ig": [], "fb": []})
    done = set(_load("processed.json", []))
    recent = _load("last_replies.json", [])
    sent = 0
    print(f"[diag] posts IG registrados: {len(posts['ig'])} -> {posts['ig'][-30:]}")
    print(f"[diag] posts FB registrados: {len(posts['fb'])}; ya procesados: {len(done)}")
    for pid in posts["ig"][-30:]:
        try:
            comms = meta.ig_comments(pid)
        except Exception as e:
            print(f"[diag] ERROR leyendo comentarios de {pid}: {e}")
            continue
        print(f"[diag] post {pid}: {len(comms)} comentarios")
        for c in comms:
            print(f"[diag]   {c.get('username')!r}: {c.get('text')!r} | ya_procesado={c['id'] in done} | coincide={matches(c.get('text', ''))}")
            if c["id"] in done or not matches(c.get("text", "")):
                continue
            try:
                name = f", @{c['username']}" if c.get("username") else ""
                meta.ig_private_reply(c["id"], DM_TEXT.format(name=name, link=LINK))
                sent += 1
                try:  # la respuesta pública es un extra: si falla, el DM ya salió
                    meta.ig_reply_comment(c["id"], REPLY_POOL[pick_reply(recent)])
                except Exception as e:
                    print("IG public reply error:", e)
            except Exception as e:  # no reintentar en bucle: se marca igualmente
                print("IG reply error:", e)
            done.add(c["id"])
    fb_on = os.getenv("ENABLE_FB_DM", "false").lower() == "true"
    print(f"[diag] Facebook activo (ENABLE_FB_DM): {fb_on}")
    for pid in (posts["fb"][-30:] if fb_on else []):
        try:
            fcomms = meta.fb_comments(pid)
        except Exception as e:
            print(f"[diag] ERROR leyendo comentarios FB de {pid}: {e}")
            continue
        print(f"[diag] post FB {pid}: {len(fcomms)} comentarios")
        for c in fcomms:
            print(f"[diag]   FB {(c.get('from') or {}).get('name')!r}: {c.get('message')!r} | ya_procesado={c['id'] in done} | coincide={matches(c.get('message', ''))}")
            if c["id"] in done or not matches(c.get("message", "")):
                continue
            try:
                n = (c.get("from") or {}).get("name", "").split(" ")[0]
                meta.fb_private_reply(c["id"], DM_TEXT.format(name=f", {n}" if n else "", link=LINK))
                sent += 1
                try:
                    meta.fb_reply_comment(c["id"], REPLY_POOL[pick_reply(recent)])
                except Exception as e:
                    print("FB public reply error:", e)
            except Exception as e:
                print("FB reply error:", e)
            done.add(c["id"])
    _save("processed.json", sorted(done)[-5000:])
    _save("last_replies.json", recent)
    print(f"Mensajes enviados: {sent}")
    return sent


if __name__ == "__main__":
    run()
