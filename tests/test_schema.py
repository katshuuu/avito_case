from pydantic import ValidationError

from project_name.schema import Draft, ItemInput, MicrocategoryDictEntry, SplitResult


def test_item_schema_ok():
    payload = ItemInput(itemId=10, mcId=201, mcTitle="Ремонт под ключ", description="Текст")
    assert payload.itemId == 10


def test_split_schema_ok():
    payload = SplitResult(
        detectedMcIds=[101],
        shouldSplit=True,
        drafts=[Draft(mcId=101, mcTitle="Сантехника", text="Текст")],
    )
    assert payload.shouldSplit is True


def test_invalid_empty_title():
    try:
        MicrocategoryDictEntry(mcId=101, mcTitle="", keyPhrases=["сантехника"])
    except ValidationError:
        assert True
    else:
        assert False
