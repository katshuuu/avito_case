import argparse
import sys
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_name.categorizer import split_item
from project_name.schema import ItemInput, MicrocategoryDictEntry
from project_name.utils import read_json, write_json


def _to_item(row: Dict[str, Any]) -> ItemInput:
    item_id = row.get("itemId")
    mc_id = row.get("mcId", row.get("sourceMcId"))
    mc_title = row.get("mcTitle", row.get("sourceMcTitle"))
    description = row.get("description", "")

    if item_id is None or mc_id is None or mc_title is None:
        raise ValueError("Each row must contain itemId and mcId/sourceMcId + mcTitle/sourceMcTitle")

    return ItemInput(
        itemId=int(item_id),
        mcId=int(mc_id),
        mcTitle=str(mc_title),
        description=str(description),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Items JSON file")
    parser.add_argument("--dict", required=True, help="Microcategories dictionary JSON file")
    parser.add_argument("--output", required=True, help="Output JSON file")
    parser.add_argument(
        "--llm-drafts",
        action="store_true",
        help="Use remote LLM for draft texts (OPENAI_API_KEY + ENABLE_LLM_DRAFTS=1)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    dict_path = Path(args.dict)
    output_path = Path(args.output)

    records_payload = read_json(input_path)
    dictionary_payload = read_json(dict_path)
    dictionary = [MicrocategoryDictEntry(**row) for row in dictionary_payload]
    predictions = []
    skipped_rows = 0
    for row in records_payload:
        try:
            item = _to_item(row)
        except Exception:
            skipped_rows += 1
            continue
        result = split_item(
            item=item,
            dictionary=dictionary,
            generate_text=True,
            use_llm_drafts=args.llm_drafts,
        ).model_dump()
        # Competition format compares only additional microcategories.
        result["detectedMcIds"] = [mc_id for mc_id in result.get("detectedMcIds", []) if mc_id != item.mcId]
        result["itemId"] = item.itemId
        predictions.append(result)
    write_json(output_path, predictions)
    print(f"Saved {len(predictions)} predictions to {output_path}; skipped {skipped_rows} malformed rows")


if __name__ == "__main__":
    main()
