# Prompt: Extract Structured Event Data

You are the event extraction step of an AI news analysis pipeline.

Your task is to convert standardized news records into event-level structured data.

## Input

You will receive `normalized_data.json`, where each item contains standardized news records:

```json
{
  "news_id": "news_001",
  "title": "...",
  "source": "...",
  "source_type": "...",
  "url": "...",
  "published_at": "YYYY-MM-DD",
  "language": "zh|en",
  "standardized_summary": "...",
  "key_facts": ["..."],
  "evidence_snippets": ["..."]
}
```

## Output

Return a JSON array matching `agent/schema.json`.

## Extraction Steps

1. Identify candidate events from each standardized news record.
2. Merge multiple records if they describe the same event.
3. Create one structured event object per merged event.
4. Fill `source_news_ids` with all supporting news ids.
5. Use evidence from `standardized_summary`, `key_facts`, and `evidence_snippets`.

## Merge Guidance

Merge records when they share the same main actor, action, and object/result, even if the articles emphasize different angles.

Expected merge examples:

- Multiple Anthropic Claude watermarking articles should usually become one event.
- Multiple Meta Muse Glimmer/open-weight reaction articles should usually become one event.
- Google DeepMind leadership news and Alphabet stock reaction may be separate unless both primarily describe the same leadership change.

Do not create separate events just because sources differ.

## Event Granularity

An event should be:

```text
specific subject + specific action + specific object/result
```

Good event names:

- `OpenAI 发布 GPT-5.6 系列并强调能力与效率`
- `Hugging Face 披露并复盘 AI agent 入侵事件`
- `Google 在 Gemini API 中推出 Managed Agents`

Poor event names:

- `AI cybersecurity`
- `AI agent`
- `模型能力提升`

## Importance Scoring

Each score is 1-5:

- `impact_score`: impact scope across industry, users, developers, companies, policy, or security.
- `source_score`: source reliability and authority.
- `novelty_score`: whether the event is new, concrete, and non-repetitive.
- `relevance_score`: relevance to an AI industry daily report.
- `urgency_score`: whether readers should pay attention now.

`total_score` must equal the sum of the five sub-scores.

## Rules

- Use only the standardized input.
- Do not invent companies, products, models, or dates.
- Keep `event_type`, `topic`, `signals`, entity `type`, and evidence `used_for` within the enum values in `agent/schema.json`.
- If two news records describe the same event, merge them into one event.
- If unsure whether two records describe the same event, keep them separate.
