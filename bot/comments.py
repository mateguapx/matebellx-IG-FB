"""Sondea comentarios en posts de palabra clave y envía UN mensaje privado con el link. Corre cada ~10 min por cron."""
import json
import os
import re
import unicodedata
from .config import BOOKS, DM_TEXT, LINK, ROOT
from . import meta

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


def run() -> int:
    posts = _load("kw_posts.json", {"ig": [], "fb": []})
    done = set(_load("processed.json", []))
    sent = 0
    for pid in posts["ig"][-30:]:
        for c in meta.ig_comments(pid):
            if c["id"] in done or not matches(c.get("text", "")):
                continue
            try:
                name = f", @{c['username']}" if c.get("username") else ""
                meta.ig_private_reply(c["id"], DM_TEXT.format(name=name, link=LINK))
                sent += 1
            except Exception as e:  # no reintentar en bucle: se marca igualmente
                print("IG reply error:", e)
            done.add(c["id"])
    fb_on = os.getenv("ENABLE_FB_DM", "false").lower() == "true"
    for pid in (posts["fb"][-30:] if fb_on else []):
        for c in meta.fb_comments(pid):
            if c["id"] in done or not matches(c.get("message", "")):
                continue
            try:
                n = (c.get("from") or {}).get("name", "").split(" ")[0]
                meta.fb_private_reply(c["id"], DM_TEXT.format(name=f", {n}" if n else "", link=LINK))
                sent += 1
            except Exception as e:
                print("FB reply error:", e)
            done.add(c["id"])
    _save("processed.json", sorted(done)[-5000:])
    print(f"Mensajes enviados: {sent}")
    return sent


if __name__ == "__main__":
    run()
