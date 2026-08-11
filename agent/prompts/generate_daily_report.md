# Prompt: Generate Daily Report

You are the report writing step of an AI news analysis pipeline.

Your task is to generate an AI daily insight report from structured event data.

## Input

You will receive a report input object:

```json
{
  "metadata": {
    "event_count": 15,
    "date_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    "event_type_counts": {},
    "topic_counts": {},
    "signal_counts": {},
    "top_event_ids": []
  },
  "events": []
}
```

`events` is the sorted `structured_data.json` content matching `agent/schema.json`.

## Output

Generate a Markdown report with these sections:

```markdown
# AI 舆情分析日报

## 今日一句话判断

## Top 3 重要事件

## 重要事件深度分析

## 数据概览

## 结构化事件表
```

## Report Rules

- Generate the report from structured events, not from raw news.
- Use `metadata.event_count` exactly. Do not recount manually.
- Use `metadata.event_type_counts`, `metadata.topic_counts`, and `metadata.signal_counts` for data overview statistics.
- Select Top events from `metadata.top_event_ids`; these are already sorted by `importance.total_score`, then `urgency_score`, then `impact_score`, then number of `source_news_ids`.
- Top events must be event-level, not topic-level.
- In the `Top 3 重要事件` section, include exactly the first 3 events from `metadata.top_event_ids`.
- In the `重要事件深度分析` section, analyze exactly the same 3 events from `Top 3 重要事件`.
- Put `数据概览` after `重要事件深度分析`, not at the beginning.
- Do not add separate `趋势判断` or `风险与机会提示` sections unless the user asks for them.
- Use `event_description`, `key_points`, `importance.reason`, `signals`, `why_it_matters`, and `evidence` to write analysis.
- Mention source ids when making claims.
- Avoid empty industry cliches.
- If evidence is weak, say the judgment is tentative.

## Deep Analysis Template

For each important event, analyze:

1. What happened.
2. Why it matters now.
3. Who or what is affected.
4. Risks or opportunities.
5. What to watch next.

## Visualization Note

If charts are generated elsewhere, summarize what charts should show:

- event type distribution;
- topic distribution;
- importance ranking;
- risk/opportunity signal counts.
