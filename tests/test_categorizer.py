from project_name.categorizer import split_item
from project_name.schema import ItemInput, MicrocategoryDictEntry


def _dict_rows():
    return [
        MicrocategoryDictEntry(mcId=101, mcTitle="Сантехника", keyPhrases=["сантехника", "монтаж унитаза"]),
        MicrocategoryDictEntry(mcId=102, mcTitle="Электрика", keyPhrases=["электрика", "электромонтаж"]),
        MicrocategoryDictEntry(mcId=201, mcTitle="Ремонт под ключ", keyPhrases=["ремонт под ключ"]),
    ]


def test_split_when_separate_markers_exist():
    item = ItemInput(
        itemId=1,
        mcId=201,
        mcTitle="Ремонт под ключ",
        description="Делаем ремонт под ключ. Электрика отдельно, сантехника отдельно.",
    )
    result = split_item(item=item, dictionary=_dict_rows())
    assert result.shouldSplit is True
    assert [d.mcId for d in result.drafts] == [101, 102]


def test_no_split_for_only_complex_bundle():
    item = ItemInput(
        itemId=2,
        mcId=201,
        mcTitle="Ремонт под ключ",
        description="Ремонт под ключ, включая электрику и сантехнику.",
    )
    result = split_item(item=item, dictionary=_dict_rows())
    assert result.shouldSplit is False
