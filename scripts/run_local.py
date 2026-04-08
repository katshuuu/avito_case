import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_name.categorizer import split_item
from project_name.schema import ItemInput, MicrocategoryDictEntry
from project_name.utils import read_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="Ad description")
    parser.add_argument(
        "--dict",
        default="data/examples/microcategories_rnc.json",
        help="Path to microcategories dictionary JSON",
    )
    parser.add_argument("--item-mcid", type=int, default=101, help="Original item mcId")
    parser.add_argument("--item-mctitle", default="Ремонт под ключ", help="Original mcTitle")
    parser.add_argument(
        "--llm-drafts",
        action="store_true",
        help="Use remote LLM for draft texts (OPENAI_API_KEY + ENABLE_LLM_DRAFTS=1)",
    )
    args = parser.parse_args()

    dictionary_payload = read_json(Path(args.dict))
    dictionary = [MicrocategoryDictEntry(**row) for row in dictionary_payload]
    item = ItemInput(
        itemId=1,
        mcId=args.item_mcid,
        mcTitle=args.item_mctitle,
        description=args.text,
    )
    result = split_item(
        item=item,
        dictionary=dictionary,
        generate_text=True,
        use_llm_drafts=args.llm_drafts,
    )
    print(result.model_dump_json(ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
