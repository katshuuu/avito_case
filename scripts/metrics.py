import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_name.utils import read_json


def _to_set(value: Any) -> Set[int]:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                return set()
            value = parsed
    if not isinstance(value, list):
        return set()
    result: Set[int] = set()
    for item in value:
        try:
            result.add(int(item))
        except (TypeError, ValueError):
            continue
    return result


def _index_by_item_id(rows: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    indexed: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        item_id = row.get("itemId")
        if item_id is None:
            continue
        try:
            indexed[int(item_id)] = row
        except (TypeError, ValueError):
            continue
    return indexed


def _extract_pred_mcs(row: Dict[str, Any]) -> Set[int]:
    explicit = _to_set(row.get("detectedMcIds", []))
    if explicit:
        return explicit
    drafts = row.get("drafts", [])
    if not isinstance(drafts, list):
        return set()
    draft_ids: Set[int] = set()
    for draft in drafts:
        if not isinstance(draft, dict):
            continue
        try:
            draft_ids.add(int(draft.get("mcId")))
        except (TypeError, ValueError):
            continue
    return draft_ids


def _extract_gold_mcs(row: Dict[str, Any]) -> Set[int]:
    # Competition rule: compare against targetDetectedMcIds.
    return _to_set(row.get("targetDetectedMcIds", []))


def _extract_gold_split(row: Dict[str, Any]) -> bool:
    target_split = _to_set(row.get("targetSplitMcIds", []))
    if target_split:
        return True
    if "shouldSplit" in row:
        return bool(row["shouldSplit"])
    return False


def _validate_gold_row(row: Dict[str, Any]) -> None:
    should_split = bool(row.get("shouldSplit", False))
    if not should_split:
        return
    target_detected = _to_set(row.get("targetDetectedMcIds", []))
    target_split = _to_set(row.get("targetSplitMcIds", []))
    if target_detected != target_split:
        item_id = row.get("itemId")
        raise ValueError(
            f"Invalid gold row itemId={item_id}: shouldSplit=true requires "
            "targetDetectedMcIds == targetSplitMcIds"
        )


def _compute_counts_for_rows(
    y_true_rows: List[Dict[str, Any]],
    y_pred_rows: List[Dict[str, Any]],
) -> Tuple[int, int, int, int, int]:
    true_by_id = _index_by_item_id(y_true_rows)
    pred_by_id = _index_by_item_id(y_pred_rows)
    common_ids = set(true_by_id.keys()) & set(pred_by_id.keys())

    tp = 0
    fp = 0
    fn = 0
    split_correct = 0

    for item_id in common_ids:
        true_row = true_by_id[item_id]
        pred_row = pred_by_id[item_id]

        true_mcs = _extract_gold_mcs(true_row)
        pred_mcs = _extract_pred_mcs(pred_row)

        tp += len(true_mcs & pred_mcs)
        fp += len(pred_mcs - true_mcs)
        fn += len(true_mcs - pred_mcs)

        true_split = _extract_gold_split(true_row)
        pred_split = bool(pred_row.get("shouldSplit", len(pred_mcs) > 0))
        if true_split == pred_split:
            split_correct += 1

    return tp, fp, fn, split_correct, len(common_ids)


def _counts_to_metrics(tp: int, fp: int, fn: int, split_correct: int, total: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    split_accuracy = split_correct / total if total else 0.0
    return {
        "matchedItems": float(total),
        "precision_micro": precision,
        "recall_micro": recall,
        "f1_micro": f1,
        "shouldSplit_accuracy": split_accuracy,
    }


def compute_metrics(
    y_true_rows: List[Dict[str, Any]],
    y_pred_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    for row in y_true_rows:
        if isinstance(row, dict):
            _validate_gold_row(row)

    tp, fp, fn, split_correct, total = _compute_counts_for_rows(y_true_rows, y_pred_rows)
    return _counts_to_metrics(tp, fp, fn, split_correct, total)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True, help="Path to ground truth JSON")
    parser.add_argument("--pred", required=True, help="Path to predictions JSON")
    args = parser.parse_args()

    gold_path = Path(args.gold)
    pred_path = Path(args.pred)

    gold_rows = read_json(gold_path)
    pred_rows = read_json(pred_path)

    if not isinstance(gold_rows, list) or not isinstance(pred_rows, list):
        raise ValueError("Both --gold and --pred files must contain JSON arrays")

    metrics = compute_metrics(gold_rows, pred_rows)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
