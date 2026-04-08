"""Морфологическое сопоставление ключевых фраз (русские словоформы) через pymorphy2."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable, List, Optional, Tuple

try:
    from pymorphy2 import MorphAnalyzer

    _MORPH = MorphAnalyzer()
    MORPH_AVAILABLE = True
except Exception:  # pragma: no cover
    _MORPH = None
    MORPH_AVAILABLE = False

# (phrase, start, end) в нормализованной строке
MorphHit = Tuple[str, int, int]


@lru_cache(maxsize=65536)
def lemma_of(word: str) -> Optional[str]:
    if not _MORPH or not word:
        return None
    w = word.lower().strip()
    if len(w) < 2 or not re.match(r"^[А-Яа-яЁёA-Za-z-]+$", w):
        return None
    try:
        return _MORPH.parse(w)[0].normal_form
    except Exception:
        return None


def _phrase_word_tokens(phrase: str) -> List[str]:
    return re.findall(r"[А-Яа-яЁёA-Za-z]+", phrase.lower())


def phrase_lemmas(phrase: str) -> List[str]:
    words = _phrase_word_tokens(phrase)
    out: List[str] = []
    for w in words:
        lem = lemma_of(w)
        out.append(lem if lem else w)
    return out


def token_spans_lemmas(norm: str) -> List[Tuple[int, int, str, str]]:
    """Список (start, end, surface_lower, lemma)."""
    out: List[Tuple[int, int, str, str]] = []
    for m in re.finditer(r"[А-Яа-яЁёA-Za-z]+", norm):
        w = m.group(0)
        surf = w.lower()
        lem = lemma_of(w)
        out.append((m.start(), m.end(), surf, lem if lem else surf))
    return out


def find_morph_hits(phrases: Iterable[str], tokens: List[Tuple[int, int, str, str]]) -> List[MorphHit]:
    """
    Находит вхождения по совпадению нормальных форм слов фразы с токенами текста
    (подряд для многословных фраз; для одного слова — любое вхождение токена с той же леммой).
    """
    if not MORPH_AVAILABLE or not tokens:
        return []

    hits: List[MorphHit] = []
    seen: Set[Tuple[int, int, str]] = set()

    for phrase in phrases:
        p = phrase.strip()
        if not p:
            continue
        pl = phrase_lemmas(p)
        if not pl:
            continue

        if len(pl) == 1:
            target = pl[0]
            for start, end, _surf, lem in tokens:
                if lem == target:
                    key = (start, end, p)
                    if key not in seen:
                        seen.add(key)
                        hits.append((p, start, end))
            continue

        if len(pl) > 8:
            continue

        n = len(tokens)
        L = len(pl)
        for i in range(n - L + 1):
            chunk = tokens[i : i + L]
            if [t[3] for t in chunk] != pl:
                continue
            start, end = chunk[0][0], chunk[-1][1]
            key = (start, end, p)
            if key not in seen:
                seen.add(key)
                hits.append((p, start, end))

    return hits


