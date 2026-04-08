import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Set

from . import morph_detect
from .config import (
    HOLISTIC_NO_SPLIT_MIN_LEN,
    MASSIVE_AD_MIN_LEN,
    SHORT_ENUM_MAX_LEN,
    SINGLE_EXTRA_LONG_LEN,
)
from .llm_drafts import generate_draft_texts, llm_drafts_enabled
from .schema import Draft, ItemInput, MicrocategoryDictEntry, SplitResult

SEPARATE_MARKERS = (
    " отдельно",
    "отдельно,",
    "отдельно.",
    "по отдельности",
    "отдельные этапы",
    "как отдельная услуга",
    "самостоятельно",
)
COMPLEX_MARKERS = (
    "под ключ",
    "включая",
    "в составе",
    "комплекс",
)

# Поджать precision: короткие однословные триггеры (особенно только morph) дают FP.
MIN_SUBSTRING_SINGLE_LEN = 5
MIN_MORPH_SINGLE_LEN = 6
# Исключения: короткие устоявшиеся аббревиатуры и устойчивые термины (иначе режется recall).
SHORT_PHRASE_OK = frozenset({"гкл", "мдф", "пвх", "обои", "обоев"})

HOLISTIC_PHRASES = (
    "все виды внутренней отделки",
    "от косметического до капитального",
    "от косметического до копитального",
    "внутренней отделки от",
    "начиная от заливки",
    "начиная от заливки и выравнивания",
    "любой сложности и пожеланий",
)


@dataclass
class DetectionContext:
    phrase: str
    phrase_start: int
    phrase_end: int


_LATIN_TO_CYRILLIC = str.maketrans(
    {
        "A": "А",
        "B": "В",
        "C": "С",
        "E": "Е",
        "H": "Н",
        "K": "К",
        "M": "М",
        "O": "О",
        "P": "Р",
        "T": "Т",
        "X": "Х",
        "Y": "У",
        "a": "а",
        "b": "в",
        "c": "с",
        "e": "е",
        "k": "к",
        "m": "м",
        "o": "о",
        "p": "р",
        "t": "т",
        "x": "х",
        "y": "у",
    }
)


def _normalize(text: str) -> str:
    t = text.translate(_LATIN_TO_CYRILLIC)
    return re.sub(r"\s+", " ", t.lower()).strip()


def _find_phrase_mentions(text: str, phrases: Iterable[str]) -> List[DetectionContext]:
    normalized = _normalize(text)
    contexts: List[DetectionContext] = []
    for phrase in phrases:
        p = _normalize(phrase)
        if not p:
            continue
        start = normalized.find(p)
        while start != -1:
            contexts.append(
                DetectionContext(phrase=phrase, phrase_start=start, phrase_end=start + len(p))
            )
            start = normalized.find(p, start + 1)
    return contexts


def _phrase_word_count(norm_phrase: str) -> int:
    return len([w for w in norm_phrase.split() if w])


def _find_mentions_tagged(text: str, phrases: Iterable[str]) -> List[tuple]:
    """Возвращает список (\"substring\"|\"morph\", DetectionContext)."""
    phrase_list = [p for p in phrases if p and str(p).strip()]
    out: List[tuple] = []
    seen: set = set()
    for c in _find_phrase_mentions(text, phrase_list):
        key = (c.phrase_start, c.phrase_end, c.phrase)
        seen.add(key)
        out.append(("substring", c))
    if not morph_detect.MORPH_AVAILABLE:
        return out
    norm = _normalize(text)
    tokens = morph_detect.token_spans_lemmas(norm)
    for phrase, s, e in morph_detect.find_morph_hits(phrase_list, tokens):
        key = (s, e, phrase)
        if key in seen:
            continue
        seen.add(key)
        out.append(("morph", DetectionContext(phrase=phrase, phrase_start=s, phrase_end=e)))
    return out


def _mention_passes_precision(kind: str, ctx: DetectionContext) -> bool:
    """Отсекает слабые однословные срабатывания; многословные фразы всегда оставляем."""
    pn = _normalize(ctx.phrase)
    if not pn:
        return False
    if _phrase_word_count(pn) >= 2:
        return True
    if pn in SHORT_PHRASE_OK:
        return True
    if kind == "substring":
        return len(pn) >= MIN_SUBSTRING_SINGLE_LEN
    return len(pn) >= MIN_MORPH_SINGLE_LEN


def _find_mentions_combined(text: str, phrases: Iterable[str]) -> List[DetectionContext]:
    """Подстрочный поиск + морфология, с фильтром precision."""
    tagged = _find_mentions_tagged(text, phrases)
    return [ctx for kind, ctx in tagged if _mention_passes_precision(kind, ctx)]


def _window(text: str, start: int, end: int, size: int = 90) -> str:
    lo = max(0, start - size)
    hi = min(len(text), end + size)
    return text[lo:hi]


def _is_standalone_mention(text: str, mention: DetectionContext) -> bool:
    w = _window(_normalize(text), mention.phrase_start, mention.phrase_end)
    has_separate = any(m in w for m in SEPARATE_MARKERS)
    has_complex = any(m in w for m in COMPLEX_MARKERS)
    return has_separate or not has_complex


def detect_microcategories(
    item: ItemInput, dictionary: List[MicrocategoryDictEntry]
) -> Dict[int, Dict[str, bool]]:
    detected: Dict[int, Dict[str, bool]] = {}
    for mc in dictionary:
        mentions = _find_mentions_combined(item.description, mc.keyPhrases)
        if not mentions:
            continue
        standalone = any(_is_standalone_mention(item.description, m) for m in mentions)
        detected[mc.mcId] = {"standalone": standalone}
    return detected


def _has_holistic_offer(norm: str) -> bool:
    return any(p in norm for p in HOLISTIC_PHRASES)


def _has_under_key(norm: str) -> bool:
    return "под ключ" in norm


def _has_explicit_separate(norm: str) -> bool:
    return any(
        x in norm
        for x in (
            "отдельно",
            "отдельные этапы",
            "по отдельности",
            "частичный ремонт",
            "частичный)",
        )
    )


def _bullet_or_section_list(raw: str) -> bool:
    lines = raw.splitlines()
    dash_lines = sum(1 for ln in lines if re.match(r"^\s*[-–—•]\s*\S", ln))
    if dash_lines >= 2:
        return True
    if re.search(r"(^|\n)\s*[-–—]\s*[а-яёa-z]", raw, re.IGNORECASE):
        return True
    if re.search(r"(^|\n)\s*[-–—]\s*сантех", raw, re.IGNORECASE):
        return True
    return False


def _short_comma_enumeration(norm: str, raw: str, num_detected_extra: int) -> bool:
    """Короткое объявление со списком услуг через запятую (как 1000012), без «под ключ»."""
    if _has_under_key(norm):
        return False
    if len(raw) > SHORT_ENUM_MAX_LEN:
        return False
    if _has_holistic_offer(norm):
        return False
    if norm.count(",") < 2 and " и " not in norm:
        return False
    return num_detected_extra >= 2


def _massive_multi_trade_ad(norm: str, raw: str) -> bool:
    """Длинное объявление с перечислением разных направлений без «под ключ» (как 1000004)."""
    if _has_under_key(norm):
        return False
    if len(raw) < MASSIVE_AD_MIN_LEN:
        return False
    if "сантехника" in norm and "электрик" in norm:
        return True
    if len(raw) > 2000 and norm.count("ремонт") >= 2:
        return True
    return False


def _split_single_extra(norm: str, raw: str, detected_map: Dict[int, Dict[str, bool]], mc_id: int) -> bool:
    """Одна дополнительная микрокатегория: эталон часто не дробит короткие узкие объявления (см. 1002306 vs 1002461)."""
    if _has_explicit_separate(norm):
        return True
    if len(raw) >= SINGLE_EXTRA_LONG_LEN:
        return True
    return bool(detected_map.get(mc_id, {}).get("standalone")) and _bullet_or_section_list(raw)


def _should_split_document(
    raw: str,
    norm: str,
    allowed_ids: Set[int],
    detected_map: Dict[int, Dict[str, bool]],
) -> bool:
    if not allowed_ids:
        return False

    if _bullet_or_section_list(raw) and len(allowed_ids) >= 2:
        return True

    if _short_comma_enumeration(norm, raw, len(allowed_ids)):
        return True

    if _massive_multi_trade_ad(norm, raw):
        return True

    if _has_holistic_offer(norm) and len(raw) > HOLISTIC_NO_SPLIT_MIN_LEN and not _bullet_or_section_list(raw):
        return False

    if _has_under_key(norm):
        if _has_explicit_separate(norm) or _bullet_or_section_list(raw):
            return any(detected_map[mid]["standalone"] for mid in allowed_ids)
        return False

    if len(allowed_ids) == 1:
        only = next(iter(allowed_ids))
        return _split_single_extra(norm, raw, detected_map, only)

    return any(detected_map[mid]["standalone"] for mid in allowed_ids)


def _build_draft_text(mc_title: str, description: str) -> str:
    base = description.strip().rstrip(".")
    if len(base) > 220:
        base = base[:220].rsplit(" ", 1)[0]
    title = mc_title.lower()
    return f"Выполняем работы по категории «{title}». {base}."


def split_item(
    item: ItemInput,
    dictionary: List[MicrocategoryDictEntry],
    generate_text: bool = True,
    use_llm_drafts: bool = False,
) -> SplitResult:
    detected_map = detect_microcategories(item=item, dictionary=dictionary)
    detected_ids = sorted(detected_map.keys())
    allowed_ids: Set[int] = set(detected_ids) - {item.mcId}

    title_by_id = {mc.mcId: mc.mcTitle for mc in dictionary}
    norm = _normalize(item.description)
    raw = item.description

    split_allowed = _should_split_document(raw, norm, allowed_ids, detected_map)
    if split_allowed:
        split_ids = sorted(allowed_ids)
    else:
        split_ids = []

    drafts: List[Draft] = []
    if generate_text and split_ids:
        for mc_id in split_ids:
            drafts.append(
                Draft(
                    mcId=mc_id,
                    mcTitle=title_by_id.get(mc_id, str(mc_id)),
                    text=_build_draft_text(title_by_id.get(mc_id, str(mc_id)), item.description),
                )
            )
        if use_llm_drafts and llm_drafts_enabled():
            texts = generate_draft_texts(item.description, drafts)
            drafts = [
                Draft(mcId=d.mcId, mcTitle=d.mcTitle, text=t or d.text)
                for d, t in zip(drafts, texts)
            ]

    return SplitResult(
        detectedMcIds=[mc_id for mc_id in detected_ids if mc_id != item.mcId],
        shouldSplit=bool(split_ids),
        drafts=drafts,
    )
