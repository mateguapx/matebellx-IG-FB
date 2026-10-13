"""Imprime el token de Instagram renovado (lo usa el workflow refresh-ig-token)."""
from . import meta

if __name__ == "__main__":
    print(meta.refresh_ig_token())
