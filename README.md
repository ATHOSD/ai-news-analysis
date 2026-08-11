# AI News Analysis

这是一个基于 LLM agent 的 AI 行业日报生成 pipeline。系统从原始新闻记录出发，依次完成新闻事实标准化、事件级结构化抽取、日报生成和可视化渲染，最终产出一份可追溯、可复现、可展示的 AI 舆情分析日报。

整个项目的设计重点是将 LLM 的语义判断能力与代码的确定性处理能力分离：

```text
data/raw/raw_news.json
  -> data/processed/normalized_data.json
  -> data/processed/structured_data.json
  -> data/processed/daily_report.md
  -> data/processed/figures/*.svg
```

## 系统架构

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

核心组件说明：

- `agent/SKILL.md`：定义 agent 的工作流契约，包括执行顺序、输入输出路径和任务边界。
- `agent/prompts/`：存放三个任务级 prompt，分别对应新闻标准化、事件抽取和日报生成。
- `agent/schema.json`：定义最终事件级结构化数据的 JSON Schema。
- `src/agent.py`：pipeline 的主 orchestrator，负责读取 skill、加载 prompt、调用 LLM、校验输出并写入文件。
- `src/visualize.py`：基于结构化事件数据生成 SVG 图表，不依赖 LLM。

## 执行流程

### 1. 原始新闻输入

输入文件：

```text
data/raw/raw_news.json
```

原始数据层保存新闻记录及其来源信息，例如 `news_id`、`title`、`source`、`url`、`published_at` 和 `content`。这一层只保存原始输入，不做事件合并、重要性评分或日报分析。

### 2. 新闻事实标准化

使用 prompt：

```text
agent/prompts/normalize_news.md
```

输出文件：

```text
data/processed/normalized_data.json
```

该步骤将不同来源、不同表述方式的新闻整理成统一的事实记录。每条标准化记录保留原始来源信息，并新增：

- `standardized_summary`
- `key_facts`
- `evidence_snippets`

这一中间层的作用是降低原始新闻文本噪声，为后续事件抽取提供更稳定、可追溯的事实基础。

### 3. 事件级结构化抽取

使用 prompt 和 schema：

```text
agent/prompts/extract_structured_data.md
agent/schema.json
```

输出文件：

```text
data/processed/structured_data.json
```

结构化数据的基本单位是 **event**，不是 article。多条新闻如果描述的是同一主体、同一动作和同一结果，会通过 `source_news_ids` 合并为同一个事件。

每个事件包含：

- 事件 ID、名称、日期和描述；
- 事件类型与主题分类；
- 相关实体；
- 支撑该事件的新闻来源 ID；
- 关键点与证据；
- 重要性评分；
- 风险或机会信号；
- 用于日报分析的解释字段。

这一层是后续日报生成和可视化分析的核心数据契约。

### 4. 日报生成

使用 prompt：

```text
agent/prompts/generate_daily_report.md
```

输出文件：

```text
data/processed/daily_report.md
```

日报只基于 `structured_data.json` 生成，不直接读取 raw news。这样可以保证最终报告中的结论和分析都能追溯到结构化事件，而不是让模型直接基于原始文本自由生成。

在调用 LLM 生成日报前，`agent.py` 会先确定性计算以下元数据：

- 事件总数；
- 日期范围；
- 事件类型分布；
- 主题分布；
- 风险/机会信号统计；
- Top 事件排序。

这些统计信息由代码计算后再传给 LLM，避免模型在报告中自行计数或排序时出现不一致。

当前日报章节顺序为：

```text
今日一句话判断
Top 3 重要事件
重要事件深度分析
数据概览
结构化事件表
可视化图表
```

`agent.py` 还会在日报生成后进行后处理，确保章节顺序稳定、Top 事件数量固定为 3 个，并保证深度分析部分与 Top 3 事件一致。

### 5. 可视化生成

使用脚本：

```text
src/visualize.py
```

输出图表：

```text
data/processed/figures/event_type_distribution.svg
data/processed/figures/topic_distribution.svg
data/processed/figures/importance_ranking.svg
data/processed/figures/signal_counts.svg
```

可视化完全基于 `structured_data.json` 生成，不再调用 LLM。图表使用纯 Python 生成 SVG，因此不依赖 `matplotlib`、`pandas` 等额外绘图库。生成后的图表会自动嵌入到 `daily_report.md` 的可视化部分。

## Agent 设计

真实 LLM 不会直接访问本地文件，也不会直接写入输出文件。文件读写和流程编排由 `src/agent.py` 完成：

```text
读取 SKILL.md
-> 解析输入/输出路径和 prompt 路由
-> 读取任务 prompt 与 JSON 输入
-> 调用 LLM API
-> 解析并校验 LLM 返回结果
-> 写入 data/processed/
```

在这个设计中：

- `SKILL.md` 是 agent 的 workflow specification。
- `prompts/*.md` 是每一次 LLM 调用的 task instruction。
- `agent.py` 是实际执行 orchestration、validation 和 artifact writing 的程序。

这种拆分使得全局工作流、单步语义任务和确定性工程逻辑分别维护，便于调试和扩展。

## LLM 与代码的职责边界

LLM 负责语义判断：

- 标准化新闻事实；
- 判断多条新闻是否描述同一事件；
- 抽取事件实体、类型和主题；
- 生成并解释重要性评分；
- 编写日报中的自然语言分析。

代码负责确定性处理：

- 读取和写入本地文件；
- 路由 prompt；
- 调用 LLM API；
- 解析 JSON；
- 校验必要字段和枚举值；
- 修正 `importance.total_score`；
- 排序 Top 事件；
- 计算数据概览统计；
- 后处理日报章节结构；
- 生成 SVG 可视化图表。

这样可以降低模型幻觉和统计错误的影响，并确保最终日报不会绕过结构化数据层。

## 配置方式

复制环境变量模板：

```bash
cp .env.example .env
```

OpenRouter-compatible 配置示例：

```bash
LLM_API_KEY=your-api-key
LLM_MODEL=openai/gpt-5.6-luna
LLM_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_NAME=ai-news-analysis
OPENROUTER_SITE_URL=http://localhost
```

`.env` 包含 API key，已通过 `.gitignore` 排除，不应提交到公开仓库。

## 运行方式

运行完整 pipeline：

```bash
./run.sh
```

不调用真实 LLM，仅验证本地流程：

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

## 输出结果

主要输出文件位于：

```text
data/processed/
```

包括：

- `normalized_data.json`
- `structured_data.json`
- `daily_report.md`
- `figures/*.svg`

仓库中保留了一份 sample processed output，便于不重新调用 LLM 的情况下查看日报结构和可视化效果。

## 校验与可复现性

pipeline 中包含若干轻量级校验和确定性处理：

- 检查标准化记录的必要字段；
- 校验事件类型、主题和信号是否落在 schema 枚举范围内；
- 校验 `source_news_ids` 是否引用了已知新闻；
- 自动修正 `importance.total_score`；
- 使用确定性规则排序 Top 事件；
- 使用代码计算日报统计信息；
- 支持 `--dry-run` 验证本地 workflow。

需要注意的是，事件合并和重要性判断依赖模型的语义判断，因此不同模型可能产生略有差异的事件数量。schema 和 validation 层负责保证输出结构稳定，模型负责完成语义层面的判断。

## 设计特点

- 使用 `SKILL.md` 显式定义 agent workflow，而不是只在代码中隐式写死流程。
- 将三类 LLM 任务拆成独立 prompt，降低上下文污染。
- 以事件为结构化粒度，避免日报按文章或 topic 粗粒度堆叠。
- 日报只消费结构化事件数据，保证分析可追溯。
- 统计、排序和可视化由代码完成，减少 LLM 计算误差。
- 可视化不消耗额外 LLM token，也不依赖外部绘图库。

## 注意事项

- 当前 raw news 使用带来源 URL 的新闻摘要，而不是完整复制新闻正文。
- `structured_data.json` 是事件级数据，文章级重复应在抽取阶段合并。
- 若需要更高质量的事件合并，可切换更强模型或继续强化 `extract_structured_data.md` 的合并规则。
