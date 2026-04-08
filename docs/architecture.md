# Architecture

## Chosen approach

**Core:** deterministic dictionary + context heuristics for `detectedMcIds` and `shouldSplit` (no local LLM hosting).

**Optional:** remote Chat Completions API for improving `drafts[].text` only (`src/project_name/llm_drafts.py`), gated by `OPENAI_API_KEY` + `ENABLE_LLM_DRAFTS`.

Why this split:
- **Metrics & control:** categories and split decisions stay explainable and reproducible.
- **Speed:** full batch run on CPU stays within ~3s without LLM calls.
- **Draft quality:** optional LLM improves customer-facing copy without coupling classification to generative variance.

## Pipeline

1. Normalize text (whitespace, lowercase, light Latin→Cyrillic homoglyph fix for noisy ads).
2. Detect microcategories by matching `keyPhrases`.
3. Decide `shouldSplit` using document-level signals (bundle vs list vs long multi-trade ads; special case for a single extra microcategory).
4. Exclude source `mcId` from `detectedMcIds`.
5. Build `drafts` with template text; optionally rewrite texts via remote LLM.

## Evaluation policy

`scripts/metrics.py` compares predictions against `targetDetectedMcIds` from the gold dataset.

Reported metrics:
- micro `precision/recall/f1` for microcategory detection;
- `shouldSplit_accuracy`.

Technical fields `caseType` / `split` are not used in scoring.

## Scale assumptions

For the expected rollout (up to ~10 categories, each ~5-15 microcategories), maintenance is mostly dictionary curation plus small heuristic tweaks; LLM stays an optional presentation layer.
