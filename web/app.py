"""
Веб-интерфейс и API для анализа объявления (микрокатегории, split, черновики).
Запуск: uvicorn web.app:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from project_name import categorizer
from project_name.categorizer import split_item
from project_name.schema import ItemInput, MicrocategoryDictEntry
from project_name.utils import read_json
from web.draft_worker import enqueue_draft_job, get_draft_job

STATIC_DIR = Path(__file__).resolve().parent / "static"

_dictionary: Optional[List[MicrocategoryDictEntry]] = None
_result_store: dict = {}
_demo_samples: Optional[List[dict]] = None


def get_dictionary() -> List[MicrocategoryDictEntry]:
    global _dictionary
    if _dictionary is None:
        path = Path(__file__).resolve().parents[1] / "data" / "examples" / "microcategories_rnc.json"
        rows = read_json(path)
        _dictionary = [MicrocategoryDictEntry(**row) for row in rows]
    return _dictionary


class AnalyzeRequest(BaseModel):
    description: str = Field(default="", description="Текст объявления")
    mcId: int = Field(default=101, description="Исходная микрокатегория (не входит в detectedMcIds)")
    mcTitle: str = Field(default="Ремонт квартир и домов под ключ", description="Название исходной микрокатегории")
    use_llm_drafts: bool = Field(default=False, description="Улучшить тексты черновиков через API LLM")
    async_drafts: bool = Field(
        default=False,
        description="Быстрый sync-ответ только с флагами + фоновая генерация drafts",
    )
    demo_mode: bool = Field(
        default=False,
        description="Вернуть пошаговое объяснение и ссылку на скачивание результата",
    )
    demo_sample_id: Optional[str] = Field(
        default=None,
        description="ID заранее заготовленного примера для demo-режима",
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
    if not req.description.strip():
        raise HTTPException(status_code=422, detail="description is required for /api/analyze")
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


def _build_demo_steps(item: ItemInput, dictionary: List[MicrocategoryDictEntry]) -> list:
    steps = []
    norm = categorizer._normalize(item.description)
    steps.append(
        {
            "title": "Нормализация текста",
            "details": f"Длина исходного текста: {len(item.description)} символов; после нормализации: {len(norm)}.",
        }
    )

    detected_summary = []
    for mc in dictionary:
        mentions = categorizer._find_mentions_combined(item.description, mc.keyPhrases)
        if not mentions:
            continue
        standalone = any(categorizer._is_standalone_mention(item.description, m) for m in mentions)
        detected_summary.append(
            {
                "mcId": mc.mcId,
                "mcTitle": mc.mcTitle,
                "matchedPhrases": sorted({m.phrase for m in mentions})[:8],
                "standalone": standalone,
            }
        )

    steps.append(
        {
            "title": "Детекция микрокатегорий",
            "details": f"Найдено микрокатегорий: {len(detected_summary)}",
            "items": detected_summary,
        }
    )

    result = split_item(item=item, dictionary=dictionary, generate_text=True, use_llm_drafts=False)
    steps.append(
        {
            "title": "Решение о сплите",
            "details": (
                "shouldSplit=true: обнаружены самостоятельные услуги для дополнительных черновиков."
                if result.shouldSplit
                else "shouldSplit=false: услуги трактуются как комплекс или отсутствуют доп. категории."
            ),
        }
    )
    return steps


@app.post("/api/analyze_demo")
async def analyze_demo(req: AnalyzeRequest) -> dict:
    dictionary = get_dictionary()
    samples = get_demo_samples()
    selected = None
    if req.demo_sample_id:
        selected = next((s for s in samples if s.get("id") == req.demo_sample_id), None)
        if selected is None:
            raise HTTPException(status_code=404, detail="Demo sample not found")
    elif samples:
        selected = samples[0]

    if selected:
        raw_item = selected["item"]
        item = ItemInput(
            itemId=int(raw_item["itemId"]),
            mcId=int(raw_item["mcId"]),
            mcTitle=str(raw_item["mcTitle"]),
            description=str(raw_item["description"]),
        )
    else:
        item = ItemInput(
            itemId=1,
            mcId=req.mcId,
            mcTitle=req.mcTitle.strip(),
            description=req.description.strip(),
        )
    result = split_item(
        item=item,
        dictionary=dictionary,
        generate_text=True,
        use_llm_drafts=req.use_llm_drafts and not req.async_drafts,
    ).model_dump()
    steps = _build_demo_steps(item, dictionary)
    file_id = str(uuid.uuid4())
    _result_store[file_id] = result
    return {
        "result": result,
        "steps": steps,
        "downloadUrl": f"/api/result/{file_id}.json",
        "sample": {
            "id": selected.get("id"),
            "title": selected.get("title"),
            "expected": selected.get("expected", {}),
        }
        if selected
        else None,
    }


def get_demo_samples() -> List[dict]:
    global _demo_samples
    if _demo_samples is None:
        path = ROOT / "data" / "examples" / "demo_samples.json"
        rows = read_json(path) if path.exists() else []
        if not isinstance(rows, list):
            rows = []
        _demo_samples = rows
    return _demo_samples


@app.get("/api/demo_samples")
async def demo_samples(limit: int = Query(default=10, ge=1, le=10)) -> dict:
    rows = get_demo_samples()
    rows = rows[:limit]
    return {
        "samples": [
            {
                "id": r.get("id"),
                "title": r.get("title"),
                "expected": r.get("expected", {}),
                "item": {
                    "itemId": r.get("item", {}).get("itemId"),
                    "mcId": r.get("item", {}).get("mcId"),
                    "mcTitle": r.get("item", {}).get("mcTitle"),
                    "description": r.get("item", {}).get("description", ""),
                },
            }
            for r in rows
        ]
    }


@app.get("/api/result/{file_id}.json")
async def download_result(file_id: str) -> dict:
    payload = _result_store.get(file_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Result file not found")
    return payload


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/drafts/{job_id}")
async def drafts_job(job_id: str) -> dict:
    return get_draft_job(job_id)
