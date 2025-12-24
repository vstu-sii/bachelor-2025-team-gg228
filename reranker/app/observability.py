from __future__ import annotations

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_langfuse():
    try:
        from langfuse import Langfuse
    except Exception:
        return None

    enabled = os.getenv("LANGFUSE_TRACING_ENABLED", "").lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return None
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY") or ""
    secret_key = os.getenv("LANGFUSE_SECRET_KEY") or ""
    if not public_key or not secret_key:
        return None
    base_url = os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST") or None
    return Langfuse(public_key=public_key, secret_key=secret_key, base_url=base_url)
