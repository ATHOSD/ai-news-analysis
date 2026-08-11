# AI News Analysis

AI News Analysis 是一个面向 AI 行业新闻的结构化分析与日报生成系统。项目将原始新闻处理拆分为标准化、事件抽取、报告生成和可视化四个阶段，通过 LLM 完成语义理解，通过代码完成流程编排、数据校验和确定性统计。

```text
raw_news.json
  -> normalized_data.json
  -> structured_data.json
  -> daily_report.md
  -> figures/*.svg
```

## 核心设计

项目采用 **schema-driven workflow agent**，而不是完全自主规划型 agent。

- `agent/SKILL.md` 定义 pipeline 的执行顺序、输入输出路径和任务边界。
- `agent/prompts/` 定义每个 LLM 子任务的具体指令。
- `agent/schema.json` 定义事件级结构化数据的最终契约。
- `src/agent.py` 负责读取本地文件、调用 LLM、校验结果并写入产物。
- `src/visualize.py` 负责基于结构化数据生成 SVG 图表。

流程由代码和 skill 固定，LLM 不决定“下一步做什么”，只负责每一步内部的语义判断，例如事实提取、事件合并、分类、重要性解释和日报写作。

## 项目结构

```text
ai-news-analysis/
├── agent/
│   ├── SKILL.md
│   ├── schema.json
│   └── prompts/
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── agent.py
│   └── visualize.py
├── .env.example
└── run.sh
```

## Pipeline

### 1. 新闻标准化

输入：`data/raw/raw_news.json`

输出：`data/processed/normalized_data.json`

该步骤将原始新闻整理为统一的事实记录，主要包括：

- `standardized_summary`：统一口径的新闻摘要。
- `key_facts`：后续事件抽取依赖的关键事实。
- `evidence_snippets`：可追溯的来源片段。

### 2. 事件级结构化抽取

输入：`data/processed/normalized_data.json`

输出：`data/processed/structured_data.json`

结构化单位是 **event**，不是 article。多篇新闻如果描述同一主体、同一动作和同一结果，会被合并为一个事件，并通过 `source_news_ids` 记录来源映射。

### 3. 日报生成

输入：`data/processed/structured_data.json`

输出：`data/processed/daily_report.md`

日报只消费结构化事件数据，不直接读取原始新闻。当前报告结构包括：

- 今日一句话判断
- Top 3 重要事件
- 重要事件深度分析
- 数据概览
- 结构化事件表
- 可视化图表

### 4. 可视化生成

输入：`data/processed/structured_data.json`

输出：`data/processed/figures/`

当前生成四类 SVG 图表：

- `event_type_distribution.svg`
- `topic_distribution.svg`
- `importance_ranking.svg`
- `signal_counts.svg`

## Schema 设计

`agent/schema.json` 是日报生成的核心数据契约。它不追求完整复刻新闻全文，而是围绕日报所需的事件理解、排序、溯源和分析能力进行字段设计。

核心原则：

- 事件粒度：以 `event` 为单位，服务 Top 事件和深度分析，避免按宽泛 topic 聚合。
- 字段收敛：用 `entities` 统一表达公司、模型、产品、论文、政策等对象，减少大量稀疏字段。
- 证据可追溯：用 `source_news_ids` 和 `evidence` 连接结构化事件与原始新闻。
- 分析可复用：用 `key_points`、`why_it_matters` 和 `signals` 支撑日报中的摘要、解释和风险机会判断。
- 排序可控：用 `importance` 的多维评分支持 Top 事件选择，`total_score` 由代码重新计算。
- 统计友好：用 `event_type`、`topic` 和 `signals` 支持概览统计和图表生成。

主要字段：

```text
event_id
event_name
event_description
event_date
event_type
topic
entities
source_news_ids
key_points
importance
signals
why_it_matters
evidence
```

其中 `importance` 包含 `impact_score`、`source_score`、`novelty_score`、`relevance_score`、`urgency_score` 和 `total_score`。LLM 负责给出分项判断和理由，代码负责修正总分并完成排序，降低同分和算分错误导致的不稳定。

## LLM 与代码分工

LLM 负责：

- 新闻事实标准化
- 同事件合并判断
- 事件分类与主题识别
- 重要性理由生成
- 日报自然语言生成

代码负责：

- workflow 编排
- 本地文件读写
- LLM API 调用
- JSON 解析与 schema 校验
- 统计、排序和可视化
- 输出文件落盘

## 运行方式

准备环境变量：

```bash
cp .env.example .env
```

`.env` 示例：

```bash
LLM_API_KEY=your-api-key
LLM_MODEL=openai/gpt-5.6-luna
LLM_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_NAME=ai-news-analysis
OPENROUTER_SITE_URL=http://localhost
```

运行完整流程：

```bash
./run.sh
```

仅验证本地流程，不调用 LLM：

```bash
./run.sh --dry-run
```

分步骤运行：

```bash
./run.sh --step normalize
./run.sh --step extract
./run.sh --step report
./run.sh --step visualize
```

## 输出产物

完整运行后，产物位于 `data/processed/`：

- `normalized_data.json`：标准化新闻事实记录。
- `structured_data.json`：事件级结构化数据。
- `daily_report.md`：最终 AI 新闻日报。
- `figures/`：日报中嵌入的 SVG 可视化图表。

## 注意事项

- `.env` 包含 API key，不应提交到公开仓库。
- 当前 raw data 使用带来源 URL 的新闻摘要，不复制完整新闻正文。
- 事件合并和重要性判断依赖 LLM，不同模型可能产生轻微差异。
