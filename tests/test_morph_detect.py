import pytest

pytest.importorskip("pymorphy2")

from project_name.morph_detect import MORPH_AVAILABLE, find_morph_hits, lemma_of, token_spans_lemmas


def test_morphology_enabled():
    assert MORPH_AVAILABLE is True


def test_lemma_russian_inflection():
    a, b = lemma_of("плиткой"), lemma_of("плитки")
    assert a and b and a == b


def test_morph_finds_inflected_form():
    text = "Нужна укладка плиткой в ванной и затирка швов."
    norm = text.lower()
    tokens = token_spans_lemmas(norm)
    hits = find_morph_hits(["укладка плитки"], tokens)
    assert hits, "ожидалось морфологическое совпадение многословной фразы"
