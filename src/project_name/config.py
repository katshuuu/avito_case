import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
PREDICTIONS_DIR = ARTIFACTS_DIR / "predictions"

DEFAULT_CATEGORY = "other"

# Split tuning knobs (can be set by env or tuned offline).
SHORT_ENUM_MAX_LEN = int(os.environ.get("SHORT_ENUM_MAX_LEN", "480"))
MASSIVE_AD_MIN_LEN = int(os.environ.get("MASSIVE_AD_MIN_LEN", "800"))
HOLISTIC_NO_SPLIT_MIN_LEN = int(os.environ.get("HOLISTIC_NO_SPLIT_MIN_LEN", "320"))
SINGLE_EXTRA_LONG_LEN = int(os.environ.get("SINGLE_EXTRA_LONG_LEN", "1100"))


def ensure_directories() -> None:
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
