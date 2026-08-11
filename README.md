# AI News Analysis

这是一个基于 LLM agent 的 AI 新闻日报生成系统。它从一批原始新闻出发，先把新闻标准化成可处理的事实记录，再抽取事件级结构化数据，最后生成一份带重点事件分析和可视化图表的 AI 舆情日报。

项目的核心目标不是简单“让模型写一篇总结”，而是把日报生成拆成一条可追踪、可校验、可复用的 pipeline：

```text
raw news
-> normalized fact records
-> structured events
-> daily report
-> visualizations
```

## 项目结构

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

其中：

- `data/raw/raw_news.json` 是最原始的新闻输入数据。
- `agent/SKILL.md` 定义整个 agent 的工作流、输入输出路径和执行顺序。
- `agent/prompts/` 放三段 LLM 任务 prompt，分别负责标准化、结构化抽取和日报生成。
- `agent/schema.json` 定义最终事件级结构化数据的字段。
- `src/agent.py` 是 pipeline 的主入口，负责读取 skill、读取 prompt、调用 LLM、校验输出和写文件。
- `src/visualize.py` 根据结构化事件数据生成 SVG 可视化图表。

## Pipeline 说明

### 1. 原始新闻输入

输入文件是：

```text
data/raw/raw_news.json
```

每条新闻包含标题、来源、URL、发布时间和正文摘要等字段。这个文件只保存原始新闻内容，不做事件合并、不做重要性打分，也不写日报分析。

### 2. 新闻标准化

第一步使用：

```text
agent/prompts/normalize_news.md
```

LLM 会把每条 raw news 转成更稳定的事实记录，输出到：

```text
data/processed/normalized_data.json
```

这一步的作用不是简单压缩，而是把不同来源、不同写法的新闻整理成统一格式，包括：

- `standardized_summary`
- `key_facts`
- `evidence_snippets`

这样后续结构化抽取时可以更稳定，也更容易追溯证据。

### 3. 事件级结构化抽取

第二步使用：

```text
agent/prompts/extract_structured_data.md
agent/schema.json
```

LLM 会从标准化新闻中抽取事件，并把多条描述同一件事的新闻合并成一个事件。例如，三篇不同媒体关于 Anthropic Claude 水印的新闻，应该合并成一个“Anthropic 为 Claude 推出水印能力”的事件。

输出文件是：

```text
data/processed/structured_data.json
```

这里的结构化单位是 **event**，不是 article。每个事件包含：

- 事件名和事件描述；
- 事件类型和主题；
- 涉及实体；
- 支撑该事件的 `source_news_ids`；
- 关键点；
- 重要性分数；
- 风险或机会信号；
- 证据片段。

#### Schema 设计

`agent/schema.json` 定义的是日报生成所需的最终结构化数据。它的基本单位是 **event**，而不是单篇新闻或 topic。这样设计是因为日报中的 Top 重要事件、深度分析和风险机会判断都应该围绕“发生了什么事”展开，而不是围绕某个宽泛主题做聚合。

一个 event 主要由几类字段组成：

- 基础描述字段：`event_id`、`event_name`、`event_description`、`event_date`，用于明确事件本身。
- 分类字段：`event_type` 和 `topic`，用于后续统计分布和生成可视化图表。
- 实体字段：`entities`，记录事件涉及的公司、模型、产品、论文、政策等对象。
- 溯源字段：`source_news_ids` 和 `evidence`，说明这个事件由哪些新闻支持，以及哪些文本片段支撑了事件描述、关键点和重要性判断。
- 日报分析字段：`key_points`、`why_it_matters` 和 `signals`，直接服务于日报中的重点事件摘要、深度分析和风险/机会判断。
- 排序字段：`importance`，由 `impact_score`、`source_score`、`novelty_score`、`relevance_score`、`urgency_score` 和 `total_score` 组成，用于筛选 Top 事件。

这里没有设计过多可选字段，例如 `related_products`、`related_companies` 这类字段没有单独拆出来，而是统一放进 `entities`。这样 schema 更简单，也能覆盖不同类型事件：有些事件涉及产品，有些涉及政策、论文、基础设施或商业策略，如果为每种情况都加专门字段，反而会让结构变复杂且经常为空。

`importance.total_score` 不是让模型自由决定的最终排序依据。LLM 会给出各维度评分和理由，代码会重新计算并修正 `total_score`，再结合事件日期、来源数量等确定性规则排序，降低同分或模型算错分带来的不稳定。

整体来说，schema 的目标不是尽可能完整地描述新闻，而是为日报生成保留最必要的结构化信息：

```text
能说明事件是什么
能追溯事件来自哪里
能判断事件为什么重要
能支持 Top 事件排序
能支持统计和可视化
```

### 4. 日报生成

第三步使用：

```text
agent/prompts/generate_daily_report.md
```

日报只基于 `structured_data.json` 生成，不直接读取 raw news。这样可以保证日报的分析来自已经结构化、可追溯的事件数据，而不是模型临时自由发挥。

输出文件是：

```text
data/processed/daily_report.md
```

当前日报结构是：

```text
今日一句话判断
Top 3 重要事件
重要事件深度分析
数据概览
结构化事件表
可视化图表
```

其中事件总数、类型分布、主题分布、信号统计和 Top 事件排序由代码确定性计算，再提供给 LLM 写报告，避免模型自己数错。

### 5. 可视化生成

最后一步由代码完成，不调用 LLM：

```text
src/visualize.py
```

它读取：

```text
data/processed/structured_data.json
```

并输出四张 SVG 图表：

```text
data/processed/figures/event_type_distribution.svg
data/processed/figures/topic_distribution.svg
data/processed/figures/importance_ranking.svg
data/processed/figures/signal_counts.svg
```

这些图表会自动嵌入到 `daily_report.md` 的可视化部分。

## Agent 如何工作

真实 LLM 不会自己读取本地文件，也不会自己写文件。实际流程是：

```text
agent.py 读取 SKILL.md
agent.py 根据 SKILL.md 找到 prompt 和数据路径
agent.py 读取本地 JSON 和 prompt
agent.py 把 prompt 内容和输入数据发送给 LLM
LLM 返回 JSON 或 Markdown
agent.py 解析、校验并写入 data/processed/
```

也就是说：

- `SKILL.md` 是 agent 的工作流说明书。
- `prompts/*.md` 是每次 LLM 调用的具体任务说明。
- `agent.py` 是真正执行文件读写、调用 LLM 和组织 pipeline 的程序。

## LLM 与代码的分工

LLM 负责语义判断：

- 提取关键事实；
- 判断哪些新闻描述同一事件；
- 抽取实体、事件类型和主题；
- 解释事件重要性；
- 生成日报文本。

代码负责确定性工作：

- 读取本地文件；
- 读取 prompt；
- 调用 LLM API；
- 解析 JSON；
- 校验字段；
- 修正 `total_score`；
- 排序 Top 事件；
- 计算数据统计；
- 生成可视化图表；
- 写入输出文件。

这样设计可以减少幻觉，也方便调试。

## 如何运行

先准备 `.env`：

```bash
cp .env.example .env
```

然后在 `.env` 中填写自己的 LLM 配置：

```bash
LLM_API_KEY=your-api-key
LLM_MODEL=openai/gpt-5.6-luna
LLM_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_NAME=ai-news-analysis
OPENROUTER_SITE_URL=http://localhost
```

一键运行完整 pipeline：

```bash
./run.sh
```

如果只想验证流程、不调用真实 LLM，可以运行：

```bash
./run.sh --dry-run
```

也可以单独运行某一步：

```bash
./run.sh --step normalize
./run.sh --step extract
./run.sh --step report
./run.sh --step visualize
```

## 输出结果

完整运行后，主要输出在：

```text
data/processed/
```

包括：

- `normalized_data.json`：标准化新闻事实记录；
- `structured_data.json`：事件级结构化数据；
- `daily_report.md`：最终日报；
- `figures/`：日报中使用的可视化图表。

## 设计亮点

- 使用 `SKILL.md` 定义 agent workflow，而不是把流程只藏在代码里。
- 每个 LLM 任务都有独立 prompt，职责清晰。
- 结构化数据以事件为粒度，而不是以新闻文章为粒度。
- 日报只基于结构化数据生成，保证分析可追溯。
- 数据统计和排序由代码完成，降低 LLM 计算错误。
- 可视化由代码生成，不额外消耗 LLM token。
- 支持 `--dry-run`，没有 API key 时也能验证完整 pipeline。

## 注意事项

- `.env` 中包含 API key，不要提交到公开仓库。
- 当前 raw news 使用的是带来源 URL 的新闻摘要，不复制完整新闻正文。
- 不同模型对事件合并的判断可能不同，因此 `structured_data.json` 的事件数量可能随模型略有变化。
- 如果要提高事件合并质量，可以使用更强的模型或继续加强 `extract_structured_data.md` 的合并规则。
