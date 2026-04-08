import json
from pathlib import Path

from project_name.categorizer import split_item
from project_name.schema import ItemInput, MicrocategoryDictEntry


def test_regression_cases_from_markup():
    root = Path(__file__).resolve().parents[1]
    dataset = json.loads((root / "rnc_dataset_markup.json").read_text(encoding="utf-8"))
    regression = json.loads((root / "data/examples/regression_cases.json").read_text(encoding="utf-8"))
    dictionary = [
        MicrocategoryDictEntry(**r)
        for r in json.loads((root / "data/examples/microcategories_rnc.json").read_text(encoding="utf-8"))
    ]
    by_id = {int(str(r.get("itemId"))): r for r in dataset if isinstance(r, dict) and str(r.get("itemId", "")).isdigit()}

    for case in regression:
        item_id = int(case["itemId"])
        row = by_id[item_id]
        item = ItemInput(
            itemId=item_id,
            mcId=int(row.get("mcId", row.get("sourceMcId"))),
            mcTitle=str(row.get("mcTitle", row.get("sourceMcTitle"))),
            description=str(row.get("description", "")),
        )
        pred = split_item(item=item, dictionary=dictionary, generate_text=False)
        assert sorted(pred.detectedMcIds) == sorted(case["expectedDetectedMcIds"])
        assert pred.shouldSplit is bool(case["expectedShouldSplit"])
