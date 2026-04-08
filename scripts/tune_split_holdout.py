import ast
import importlib
import itertools
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_name import categorizer, config
from project_name.schema import ItemInput, MicrocategoryDictEntry
from project_name.utils import read_json, write_json


def _to_item(row: dict) -> ItemInput:
    return ItemInput(
        itemId=int(row["itemId"]),
        mcId=int(row.get("mcId", row.get("sourceMcId"))),
        mcTitle=str(row.get("mcTitle", row.get("sourceMcTitle"))),
        description=str(row.get("description", "")),
    )


def _target_set(row: dict) -> set:
    val = row.get("targetDetectedMcIds", [])
    if isinstance(val, str):
        val = ast.literal_eval(val)
    return {int(x) for x in val}


def run_once(rows, dictionary):
    correct = 0
    total = 0
    for row in rows:
        try:
            item = _to_item(row)
        except Exception:
            continue
        pred = categorizer.split_item(item=item, dictionary=dictionary, generate_text=False)
        gold = bool(row.get("shouldSplit", False))
        if pred.shouldSplit == gold:
            correct += 1
        total += 1
    return correct / total if total else 0.0


def main() -> None:
    dataset = read_json(ROOT / "rnc_dataset_markup.json")
    dictionary = [MicrocategoryDictEntry(**r) for r in read_json(ROOT / "data/examples/microcategories_rnc.json")]

    holdout = [r for r in dataset if isinstance(r, dict) and str(r.get("itemId", "")).isdigit() and int(r["itemId"]) % 5 == 0]

    grid = {
        "SHORT_ENUM_MAX_LEN": [420, 480, 540],
        "MASSIVE_AD_MIN_LEN": [700, 800, 900],
        "HOLISTIC_NO_SPLIT_MIN_LEN": [260, 320, 380],
        "SINGLE_EXTRA_LONG_LEN": [900, 1100, 1300],
    }

    best = {"score": -1.0, "params": {}}
    for vals in itertools.product(*grid.values()):
        params = dict(zip(grid.keys(), vals))
        for k, v in params.items():
            os.environ[k] = str(v)
        importlib.reload(config)
        importlib.reload(categorizer)
        score = run_once(holdout, dictionary)
        if score > best["score"]:
            best = {"score": score, "params": params}

    out = {
        "strategy": "itemId % 5 == 0 holdout",
        "metric": "shouldSplit_accuracy",
        "best": best,
    }
    write_json(ROOT / "artifacts/predictions/split_tuning_report.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
