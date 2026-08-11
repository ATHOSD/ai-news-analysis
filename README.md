# AI News Analysis

An LLM-orchestrated pipeline for generating an AI industry daily briefing from raw news records. The system converts raw news into normalized fact records, extracts event-level structured data, generates an evidence-backed Markdown report, and renders deterministic visualizations from the structured event layer.

The pipeline is designed around a clear separation between semantic tasks handled by the LLM and deterministic tasks handled by code:

```text
data/raw/raw_news.json
  -> data/processed/normalized_data.json
  -> data/processed/structured_data.json
  -> data/processed/daily_report.md
  -> data/processed/figures/*.svg
```

## Architecture

```text
ai-news-analysis/
├── agent/
│   ├── SKILL.md
│   ├── schema.json
│   └── prompts/
│       ├── normalize_news.md
│       ├── extract_structured_data.md
│       └── generate_daily_report.md
├── data/
│   ├── raw/
│   │   └── raw_news.json
│   └── processed/
│       ├── normalized_data.json
│       ├── structured_data.json
│       ├── daily_report.md
│       └── figures/
├── src/
│   ├── agent.py
│   └── visualize.py
├── .env.example
└── run.sh
```

Key components:

- `agent/SKILL.md` defines the workflow contract, step order, input/output paths, and execution boundaries.
- `agent/prompts/` contains task-specific LLM instructions for normalization, event extraction, and report generation.
- `agent/schema.json` defines the target event-level JSON structure used by downstream analysis.
- `src/agent.py` is the orchestrator. It reads the skill definition, loads prompts and data, calls the LLM, validates outputs, and writes artifacts.
- `src/visualize.py` renders SVG charts directly from `structured_data.json` without additional LLM calls.

## Execution Flow

### 1. Raw News Ingestion

Input:

```text
data/raw/raw_news.json
```

The raw layer stores source-grounded news records with metadata such as `news_id`, `title`, `source`, `url`, `published_at`, and `content`. This layer does not perform event merging, scoring, or analysis.

### 2. News Normalization

Prompt:

```text
agent/prompts/normalize_news.md
```

Output:

```text
data/processed/normalized_data.json
```

This step converts heterogeneous raw news records into consistent fact records. Each normalized item preserves source metadata and adds:

- `standardized_summary`
- `key_facts`
- `evidence_snippets`

The purpose of this layer is to reduce noise and provide a stable factual substrate for event extraction.

### 3. Event-Level Structured Extraction

Prompt and schema:

```text
agent/prompts/extract_structured_data.md
agent/schema.json
```

Output:

```text
data/processed/structured_data.json
```

The structured layer uses events as the core unit, not articles. Multiple news records may be merged into one event through `source_news_ids` when they describe the same actor, action, and result.

Each event contains:

- event identity, name, date, and description;
- event type and topic classification;
- involved entities;
- source news references;
- key points and evidence;
- importance scores;
- risk/opportunity signals;
- downstream explanation fields.

This structure is the main data contract for reporting and visualization.

### 4. Daily Report Generation

Prompt:

```text
agent/prompts/generate_daily_report.md
```

Output:

```text
data/processed/daily_report.md
```

The report is generated only from `structured_data.json`, not from raw news. Before calling the LLM, `agent.py` computes deterministic metadata such as event count, date range, event type distribution, topic distribution, signal counts, and top-event ordering. This prevents the model from manually recounting or re-sorting structured data.

Current report order:

```text
今日一句话判断
Top 3 重要事件
重要事件深度分析
数据概览
结构化事件表
可视化图表
```

`agent.py` also applies a post-processing step to enforce the report order, keep exactly three top events, and align the deep-analysis section with those same three events.

### 5. Visualization

Script:

```text
src/visualize.py
```

Outputs:

```text
data/processed/figures/event_type_distribution.svg
data/processed/figures/topic_distribution.svg
data/processed/figures/importance_ranking.svg
data/processed/figures/signal_counts.svg
```

Visualizations are generated deterministically from `structured_data.json` and embedded into the Markdown report. The implementation uses pure Python SVG rendering, so no plotting library is required.

## Agent Design

The LLM does not directly access local files or write outputs. File I/O and orchestration are handled by `src/agent.py`:

```text
read SKILL.md
-> resolve input/output paths and prompt routing
-> read prompt file and JSON input
-> call the LLM API
-> parse and validate response
-> write processed artifact
```

This design keeps `SKILL.md` as the reusable workflow specification while keeping each LLM call focused on one task-specific prompt.

## LLM Boundary

LLM responsibilities:

- normalize source-grounded facts;
- identify and merge event-level records;
- extract entities and classifications;
- assign and explain importance scores;
- write the final daily briefing.

Deterministic code responsibilities:

- local file reads and writes;
- prompt routing;
- LLM API calls;
- JSON parsing;
- schema-oriented validation;
- `total_score` correction;
- event sorting;
- aggregate statistics;
- report section post-processing;
- SVG visualization rendering.

This separation improves traceability and reduces the chance that the final report bypasses the structured data layer.

## Configuration

Create a local `.env` file:

```bash
cp .env.example .env
```

Example OpenRouter-compatible configuration:

```bash
LLM_API_KEY=your-api-key
LLM_MODEL=openai/gpt-5.6-luna
LLM_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_NAME=ai-news-analysis
OPENROUTER_SITE_URL=http://localhost
```

`.env` is excluded from git and should not be committed.

## Usage

Run the full pipeline:

```bash
./run.sh
```

Run without making LLM API calls:

```bash
./run.sh --dry-run
```

Run individual stages:

```bash
./run.sh --step normalize
./run.sh --step extract
./run.sh --step report
./run.sh --step visualize
```

## Outputs

Primary generated artifacts:

- `data/processed/normalized_data.json`
- `data/processed/structured_data.json`
- `data/processed/daily_report.md`
- `data/processed/figures/*.svg`

The repository includes a sample processed output so the report structure and visualization artifacts can be inspected without rerunning the LLM pipeline.

## Validation And Reproducibility

The pipeline includes several lightweight safeguards:

- required-field checks for normalized records;
- enum checks for event type, topic, and signals;
- source ID validation against known raw news IDs;
- deterministic correction of `importance.total_score`;
- deterministic sorting for top-event selection;
- deterministic aggregation for report metadata;
- dry-run mode for local workflow verification.

Because event merging and scoring depend on model judgment, different models may produce slightly different event counts. The schema and validation layer keep the output shape stable even when model-level semantic decisions vary.

## Notes

- Raw news records use source-grounded summaries and URLs rather than full article copies.
- `structured_data.json` is intentionally event-level; article-level duplication should be resolved during extraction.
- Visualization is downstream of structured data and does not require additional LLM tokens.
- For higher event-merging quality, use a stronger model or refine `extract_structured_data.md`.
