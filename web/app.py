"""
Веб-интерфейс и API для анализа объявления (микрокатегории, split, черновики).
Запуск: uvicorn web.app:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from project_name.categorizer import split_item
from project_name.schema import ItemInput, MicrocategoryDictEntry
from project_name.utils import read_json
from web.draft_worker import enqueue_draft_job, get_draft_job

STATIC_DIR = Path(__file__).resolve().parent / "static"

_dictionary: Optional[List[MicrocategoryDictEntry]] = None


def get_dictionary() -> List[MicrocategoryDictEntry]:
    global _dictionary
    if _dictionary is None:
        path = Path(__file__).resolve().parents[1] / "data" / "examples" / "microcategories_rnc.json"
        rows = read_json(path)
        _dictionary = [MicrocategoryDictEntry(**row) for row in rows]
    return _dictionary


class AnalyzeRequest(BaseModel):
    description: str = Field(min_length=1, description="Текст объявления")
    mcId: int = Field(default=101, description="Исходная микрокатегория (не входит в detectedMcIds)")
    mcTitle: str = Field(default="Ремонт квартир и домов под ключ", description="Название исходной микрокатегории")
    use_llm_drafts: bool = Field(default=False, description="Улучшить тексты черновиков через API LLM")
    async_drafts: bool = Field(
        default=False,
        description="Быстрый sync-ответ только с флагами + фоновая генерация drafts",
    )


app = FastAPI(title="Avito Microcategory Splitter", version="1.0.0")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="static/index.html not found")
    return index_path.read_text(encoding="utf-8")


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> dict:
    dictionary = get_dictionary()
    item = ItemInput(
        itemId=1,
        mcId=req.mcId,
        mcTitle=req.mcTitle.strip(),
        description=req.description.strip(),
    )
    # Fast sync path for production SLA: categories + split quickly, drafts later.
    if req.async_drafts and req.use_llm_drafts:
        quick = split_item(
            item=item,
            dictionary=dictionary,
            generate_text=False,
            use_llm_drafts=False,
        ).model_dump()
        quick["drafts"] = []
        if quick.get("shouldSplit"):
            quick["draftJobId"] = enqueue_draft_job(
                item=item,
                dictionary=dictionary,
                use_llm_drafts=True,
            )
        else:
            quick["draftJobId"] = None
        return quick

    result = split_item(
        item=item,
        dictionary=dictionary,
        generate_text=True,
        use_llm_drafts=req.use_llm_drafts,
    )
    return result.model_dump()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/drafts/{job_id}")
async def drafts_job(job_id: str) -> dict:
    return get_draft_job(job_id)
