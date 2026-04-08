"""Optional remote LLM generation for draft texts (no local model hosting)."""

import json
import os
import urllib.error
import urllib.request
from typing import List

from .schema import Draft

DEFAULT_TIMEOUT_S = float(os.environ.get("LLM_TIMEOUT_S", "2.5"))
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def llm_drafts_enabled() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip()) and _env_flag("ENABLE_LLM_DRAFTS")


def generate_draft_texts(
    description: str,
    drafts: List[Draft],
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> List[str]:
    """One batched chat completion; returns texts in the same order as drafts."""
    if not drafts:
        return []

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return [d.text for d in drafts]

    base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"

    items = [
        {"mcId": d.mcId, "mcTitle": d.mcTitle}
        for d in drafts
    ]
    system = (
        "Ты помощник для Авито. Ответь ТОЛЬКО валидным JSON-объектом вида "
        '{"texts": ["...", "..."]} — массив строк в том же порядке, что и drafts. '
        "По исходному тексту объявления напиши короткий текст отдельного черновика "
        "для каждой микрокатегории (1–2 предложения, деловой стиль, без воды, "
        "без выдуманных условий). Язык: русский."
    )
    user = json.dumps(
        {"originalDescription": description, "drafts": items},
        ensure_ascii=False,
    )

    body = json.dumps(
        {
            "model": DEFAULT_MODEL,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return [d.text for d in drafts]

    try:
        content = payload["choices"][0]["message"]["content"]
        data = json.loads(content)
        texts = data.get("texts")
        if not isinstance(texts, list) or len(texts) != len(drafts):
            return [d.text for d in drafts]
        out: List[str] = []
        for i, t in enumerate(texts):
            out.append(str(t).strip() if t is not None else drafts[i].text)
        return out
    except (KeyError, IndexError, TypeError, ValueError):
        return [d.text for d in drafts]
