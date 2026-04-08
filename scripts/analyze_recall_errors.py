import ast
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_name.categorizer import split_item
from project_name.schema import ItemInput, MicrocategoryDictEntry
from project_name.utils import read_json, write_json


def _to_set(value):
    if isinstance(value, str):
        value = ast.literal_eval(value)
    return {int(x) for x in value}


def main() -> None:
    dataset = read_json(ROOT / "rnc_dataset_markup.json")
    dictionary_rows = read_json(ROOT / "data/examples/microcategories_rnc.json")
    dictionary = [MicrocategoryDictEntry(**r) for r in dictionary_rows]
    title_by_id = {r["mcId"]: r["mcTitle"] for r in dictionary_rows}

    fn_counter = Counter()
    phrase_counter = defaultdict(Counter)

    for row in dataset:
        if not isinstance(row, dict):
            continue
        try:
            item = ItemInput(
                itemId=int(row["itemId"]),
                mcId=int(row.get("mcId", row.get("sourceMcId"))),
                mcTitle=str(row.get("mcTitle", row.get("sourceMcTitle"))),
                description=str(row.get("description", "")),
            )
        except Exception:
            continue

        pred = split_item(item=item, dictionary=dictionary, generate_text=False)
        pred_set = set(pred.detectedMcIds)
        gold_set = _to_set(row.get("targetDetectedMcIds", []))
        missed = gold_set - pred_set
        if not missed:
            continue
        norm_desc = item.description.lower()
        for mc_id in missed:
            fn_counter[mc_id] += 1
            # Cheap candidate phrases: top words in missed examples.
            for token in norm_desc.replace(",", " ").replace(".", " ").split():
                if len(token) < 6:
                    continue
                phrase_counter[mc_id][token] += 1

    report = []
    for mc_id, count in fn_counter.most_common():
        report.append(
            {
                "mcId": mc_id,
                "mcTitle": title_by_id.get(mc_id, str(mc_id)),
                "falseNegativeCount": count,
                "topCandidateTokens": [w for w, _ in phrase_counter[mc_id].most_common(20)],
            }
        )

    out = {"report": report}
    write_json(ROOT / "artifacts/predictions/recall_error_report.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
