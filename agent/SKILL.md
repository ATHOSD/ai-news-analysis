---
name: ai-news-daily
description: Use this skill to turn raw AI news into standardized fact records, event-level structured data, and an AI daily insight report with evidence-backed analysis.
---

# AI News Daily Workflow

Use this workflow for the AI 舆情分析日报 task.

## Data Contract

- Raw news input lives in `data/raw/`.
- Standardized intermediate output should be written to `data/processed/normalized_data.json`.
- Final structured event output should be written to `data/processed/structured_data.json`.
- Daily report output should be written to `data/processed/daily_report.md`.
- Visualization outputs should be written to `data/processed/figures/`.
- The final report must be generated from `structured_data.json`; do not generate it directly from raw news.

## Required Order

1. Standardize raw news into concise fact records.
2. Extract event-level structured data from standardized news.
3. Generate the daily report from structured data.
4. Generate visualizations from structured data.

Do not skip the standardized intermediate step. Do not feed all raw news directly into report generation.

## Prompt Routing

- Use `prompts/normalize_news.md` for raw news standardization.
- Use `prompts/extract_structured_data.md` for event-level extraction.
- Use `prompts/generate_daily_report.md` for daily report analysis.

## Structured Data Rules

- The unit of `structured_data.json` is an event, not an article.
- Multiple news records can map to the same event through `source_news_ids`.
- Top events should be selected from event-level records by `importance.total_score`, then `urgency_score`, then `impact_score`, then number of supporting source news ids.
- Use `agent/schema.json` as the target schema for `structured_data.json`.
- If a field cannot be supported by standardized news evidence, use a conservative value and explain the uncertainty in `importance.reason` or `why_it_matters`.

## AI Usage Boundary

AI may help with:

- factual standardization;
- event extraction;
- entity extraction;
- event classification;
- importance explanation;
- report writing from structured data.

Code or deterministic rules should handle:

- file paths;
- JSON parsing;
- schema validation;
- total score calculation;
- sorting;
- output naming.
- visualization rendering.
