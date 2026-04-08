from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

from project_name.categorizer import split_item
from project_name.schema import ItemInput, MicrocategoryDictEntry

_executor = ThreadPoolExecutor(max_workers=2)
_lock = threading.Lock()
_jobs: Dict[str, dict] = {}


def enqueue_draft_job(
    item: ItemInput,
    dictionary: List[MicrocategoryDictEntry],
    use_llm_drafts: bool,
) -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {"status": "queued", "drafts": []}

    def _run() -> None:
        with _lock:
            _jobs[job_id]["status"] = "running"
        try:
            result = split_item(
                item=item,
                dictionary=dictionary,
                generate_text=True,
                use_llm_drafts=use_llm_drafts,
            )
            with _lock:
                _jobs[job_id] = {
                    "status": "completed",
                    "drafts": [d.model_dump() for d in result.drafts],
                }
        except Exception as exc:  # pragma: no cover
            with _lock:
                _jobs[job_id] = {"status": "failed", "error": str(exc), "drafts": []}

    _executor.submit(_run)
    return job_id


def get_draft_job(job_id: str) -> dict:
    with _lock:
        return _jobs.get(job_id, {"status": "not_found", "drafts": []})
