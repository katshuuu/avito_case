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
        "Ты — профессиональный помощник по созданию объявлений для платформы Авито (раздел «Услуги»). "
        "Твоя задача — на основе исходного текста объявления и списка микрокатегорий сгенерировать короткие деловые черновики.\n\n"
        "### Входные данные (будут переданы отдельно):\n"
        "1. `original_text` — исходный текст объявления (может быть длинным, с лишними деталями).\n"
        "2. `microcategories` — массив строк, например: [\"Ремонт квартир\", \"Уборка\", \"Дизайн интерьера\"].\n\n"
        "### Требования к каждому черновику:\n"
        "- Длина: **1–2 предложения** (не больше 30 слов).\n"
        "- Стиль: **деловой, нейтральный, без восклицательных знаков, смайлов и субъективных оценок** («круто», «лучший», «супер» — запрещены).\n"
        "- Содержание: **только факты из исходного текста**. Не выдумывай цен, сроков, акций, гарантий или условий, которых нет в исходнике.\n"
        "- Адаптация: каждый черновик должен быть **слегка перефразирован под конкретную микрокатегорию**, выделяя релевантные аспекты услуги.\n"
        "- Без «воды»: убери общие фразы вроде «оказываю широкий спектр услуг», «обращайтесь, не пожалеете».\n\n"
        "### Пример (хороший и плохой):\n\n"
        "**Исходный текст:**  \n"
        "«Делаю ремонт ванных комнат под ключ: замена труб, плитка, сантехника. Работаю в Москве и области. Смета бесплатно, оплата по факту. Опыт 5 лет.»\n\n"
        "**Микрокатегория:** `\"Ремонт ванных комнат\"`\n\n"
        "✅ Хороший черновик:  \n"
        "«Выполню ремонт ванной под ключ в Москве и области: замена труб, укладка плитки, установка сантехники. Бесплатная смета и оплата по факту работ.»\n\n"
        "❌ Плохой черновик (выдуманные условия):  \n"
        "«Лучший ремонт ванных с гарантией 3 года! Скидка 20% при заказе до пятницы. Звоните прямо сейчас!»\n\n"
        "### Формат вывода (строго):\n"
        "- Ответ должен быть **только валидным JSON-объектом** вида:\n"
        '{"texts": ["черновик для первой микрокатегории", "черновик для второй", ...]}\n'
        "- Порядок строк в массиве `texts` должен строго соответствовать порядку микрокатегорий во входном массиве.\n"
        "- Никакого дополнительного текста до или после JSON, никаких пояснений.\n\n"
        "Важно: если в исходном тексте недостаточно информации — используй общую часть, но не добавляй новую. "
        "Не используй местоимение «я» без необходимости, допустимо «Выполню», «Помогу». "
        "Язык: русский. Ответь ТОЛЬКО валидным JSON-объектом."
    )
    user = json.dumps(
        {"original_text": description, "microcategories": [d.mcTitle for d in drafts]},
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