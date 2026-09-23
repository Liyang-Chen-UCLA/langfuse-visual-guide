"""Shared HTML shell (CSS design system + navigation) for the Langfuse visual guide."""

import base64
import re

# ---- favicon (inline SVG, base64) ----
_FAVICON_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
    "<rect width='32' height='32' rx='7' fill='#059669'/>"
    "<path d='M9 16 L22 8.5 M9 16 L22 23.5' stroke='#fff' stroke-width='1.7' fill='none'/>"
    "<circle cx='9' cy='16' r='3' fill='#fff'/>"
    "<circle cx='22' cy='8.5' r='3' fill='#fff'/>"
    "<circle cx='22' cy='23.5' r='3' fill='#fff'/></svg>"
)
FAVICON = "data:image/svg+xml;base64," + base64.b64encode(_FAVICON_SVG.encode()).decode()


def esc(s):
    """Escape plain text for an HTML text/attribute context.

    For chrome/meta strings that are NOT meant to carry inline markup (page
    titles, descriptions). Do NOT use on lesson body content or bi() inputs,
    which may legitimately contain inline tags.
    """
    return (
        str(s).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def head_meta(title, description, og_type="website"):
    """SEO / social meta tags + favicon for a page <head>."""
    t = esc(title)
    d = esc(description)
    return (
        f'<meta name="description" content="{d}">\n'
        f'<meta name="theme-color" content="#059669">\n'
        f'<link rel="icon" type="image/svg+xml" href="{FAVICON}">\n'
        f'<meta property="og:type" content="{og_type}">\n'
        f'<meta property="og:site_name" content="Langfuse 图解教程">\n'
        f'<meta property="og:title" content="{t}">\n'
        f'<meta property="og:description" content="{d}">\n'
        f'<meta name="twitter:card" content="summary">\n'
        f'<meta name="twitter:title" content="{t}">\n'
        f'<meta name="twitter:description" content="{d}">'
    )


# Ordered list of all pages:
# (filename, title_zh, title_en, part_zh, part_en)
# Grows one Part per milestone; M0 ships only L01 to prove the pipeline.
PAGES = [
    ("01-what-is-langfuse.html", "Langfuse 是什么", "What is Langfuse",
     "第一部分 · 宏观全景", "Part 1 · The Big Picture"),
    ("02-observability-2-and-wide-events.html", "可观测性 2.0 与宽事件", "Observability 2.0 & wide events",
     "第一部分 · 宏观全景", "Part 1 · The Big Picture"),
    ("03-three-pillars-deep.html", "三大支柱深入：trace/observation/score", "The three pillars in depth",
     "第一部分 · 宏观全景", "Part 1 · The Big Picture"),
    ("04-project-map-monorepo.html", "项目全景地图（monorepo 与窄腰）", "Project map (monorepo & narrow waist)",
     "第一部分 · 宏观全景", "Part 1 · The Big Picture"),
    ("05-life-of-a-trace.html", "一条 trace 的一生·鸟瞰", "Life of a trace (bird's-eye)",
     "第一部分 · 宏观全景", "Part 1 · The Big Picture"),
    ("06-instrumenting-an-llm-app.html", "给 LLM 应用埋点", "Instrumenting an LLM app",
     "第二部分 · 前置基础", "Part 2 · Foundations"),
    ("07-dual-store-architecture.html", "双存储架构", "The dual-store architecture",
     "第二部分 · 前置基础", "Part 2 · Foundations"),
    ("08-clickhouse-wide-events.html", "ClickHouse 与宽事件表", "ClickHouse & the wide-event tables",
     "第二部分 · 前置基础", "Part 2 · Foundations"),
    ("09-postgres-metadata-schema.html", "元数据 schema（Postgres/Prisma）", "The metadata schema (Postgres)",
     "第二部分 · 前置基础", "Part 2 · Foundations"),
    ("10-multi-tenancy.html", "多租户：org → project → environment", "Multi-tenancy",
     "第二部分 · 前置基础", "Part 2 · Foundations"),
    ("11-deployment-topology.html", "部署拓扑与依赖", "Deployment topology",
     "第二部分 · 前置基础", "Part 2 · Foundations"),
    ("12-ingestion-api.html", "摄取 API", "The ingestion API",
     "第三部分 · 摄取链路", "Part 3 · The Ingestion Path"),
    ("13-event-types-merge.html", "事件类型与合并语义", "Event types & merge semantics",
     "第三部分 · 摄取链路", "Part 3 · The Ingestion Path"),
    ("14-ingestion-queue.html", "摄取队列", "The ingestion queue",
     "第三部分 · 摄取链路", "Part 3 · The Ingestion Path"),
    ("15-ingestion-service.html", "IngestionService：合并的心脏", "IngestionService: the merge heart",
     "第三部分 · 摄取链路", "Part 3 · The Ingestion Path"),
    ("16-token-counting-cost.html", "Token 计数与成本", "Token counting & cost",
     "第三部分 · 摄取链路", "Part 3 · The Ingestion Path"),
    ("17-clickhouse-writer.html", "ClickhouseWriter：批量落盘", "ClickhouseWriter: batched persistence",
     "第三部分 · 摄取链路", "Part 3 · The Ingestion Path"),
    ("18-opentelemetry-ingestion.html", "OpenTelemetry 摄取", "OpenTelemetry ingestion",
     "第三部分 · 摄取链路", "Part 3 · The Ingestion Path"),
    ("19-media-blob-storage.html", "媒体与 blob 存储", "Media & blob storage",
     "第三部分 · 摄取链路", "Part 3 · The Ingestion Path"),
    ("20-web-app-architecture.html", "web 应用架构", "The web app architecture",
     "第四部分 · 查询链路", "Part 4 · The Read Path"),
    ("21-trpc-backbone.html", "tRPC 骨架", "The tRPC backbone",
     "第四部分 · 查询链路", "Part 4 · The Read Path"),
    ("22-repository-layer.html", "仓储层：从 ClickHouse 读", "The repository layer",
     "第四部分 · 查询链路", "Part 4 · The Read Path"),
    ("23-filtering-search-bar.html", "过滤·搜索栏·查询构建", "Filtering & the search bar",
     "第四部分 · 查询链路", "Part 4 · The Read Path"),
    ("24-lists-and-tables.html", "列表与表格", "Lists & tables",
     "第四部分 · 查询链路", "Part 4 · The Read Path"),
    ("25-trace-detail-tree.html", "trace 详情与观测树", "Trace detail & the observation tree",
     "第四部分 · 查询链路", "Part 4 · The Read Path"),
    ("26-sessions.html", "sessions", "Sessions",
     "第四部分 · 查询链路", "Part 4 · The Read Path"),
    ("27-public-rest-api.html", "公共 REST API", "The public REST API",
     "第四部分 · 查询链路", "Part 4 · The Read Path"),
    ("28-scoring-model.html", "评分模型", "The scoring model",
     "第五部分 · 评估与评分", "Part 5 · Evaluation & Scoring"),
    ("29-llm-as-a-judge.html", "LLM 当裁判", "LLM-as-a-judge",
     "第五部分 · 评估与评分", "Part 5 · Evaluation & Scoring"),
    ("30-eval-execution-pipeline.html", "eval 执行流水线", "The eval execution pipeline",
     "第五部分 · 评估与评分", "Part 5 · Evaluation & Scoring"),
    ("31-code-based-evaluation.html", "代码 eval", "Code-based evaluation",
     "第五部分 · 评估与评分", "Part 5 · Evaluation & Scoring"),
    ("32-human-annotation.html", "人工标注", "Human annotation",
     "第五部分 · 评估与评分", "Part 5 · Evaluation & Scoring"),
    ("33-monitors-and-alerting.html", "监控器与告警", "Monitors & alerting",
     "第五部分 · 评估与评分", "Part 5 · Evaluation & Scoring"),
    ("34-datasets-and-items.html", "数据集与数据项", "Datasets & items",
     "第六部分 · 数据集与实验", "Part 6 · Datasets & Experiments"),
    ("35-dataset-runs.html", "数据集运行与运行项", "Dataset runs & run items",
     "第六部分 · 数据集与实验", "Part 6 · Datasets & Experiments"),
    ("36-experiments-and-comparison.html", "实验与对比", "Experiments & comparison",
     "第六部分 · 数据集与实验", "Part 6 · Datasets & Experiments"),
    ("37-prompt-management.html", "Prompt 管理", "Prompt management",
     "第七部分 · Prompt 与 Playground", "Part 7 · Prompts & Playground"),
    ("38-prompt-serving-caching.html", "Prompt 服务与缓存", "Prompt serving & caching",
     "第七部分 · Prompt 与 Playground", "Part 7 · Prompts & Playground"),
    ("39-playground-llm-connections.html", "Playground 与 LLM 连接", "Playground & LLM connections",
     "第七部分 · Prompt 与 Playground", "Part 7 · Prompts & Playground"),
    ("40-dashboards-and-widgets.html", "仪表盘与 widget 系统", "Dashboards & widgets",
     "第八部分 · 仪表盘·指标·成本", "Part 8 · Dashboards, Metrics & Cost"),
    ("41-query-engine.html", "查询引擎", "The query engine",
     "第八部分 · 仪表盘·指标·成本", "Part 8 · Dashboards, Metrics & Cost"),
    ("42-models-and-pricing.html", "模型与定价", "Models & pricing",
     "第八部分 · 仪表盘·指标·成本", "Part 8 · Dashboards, Metrics & Cost"),
    ("43-cloud-usage-metering.html", "云用量计量与花费", "Cloud usage metering & spend",
     "第八部分 · 仪表盘·指标·成本", "Part 8 · Dashboards, Metrics & Cost"),
    ("44-automations-webhooks.html", "自动化与 webhook", "Automations & webhooks",
     "第九部分 · 自动化与集成", "Part 9 · Automation & Integrations"),
    ("45-slack-and-notifications.html", "Slack 与通知", "Slack & notifications",
     "第九部分 · 自动化与集成", "Part 9 · Automation & Integrations"),
    ("46-analytics-integrations.html", "分析集成", "Analytics integrations",
     "第九部分 · 自动化与集成", "Part 9 · Automation & Integrations"),
    ("47-batch-exports-and-actions.html", "批量导出与批量操作", "Batch exports & actions",
     "第九部分 · 自动化与集成", "Part 9 · Automation & Integrations"),
    ("48-auth-and-sessions.html", "鉴权与会话", "Auth & sessions",
     "第十部分 · 平台与运维", "Part 10 · Platform & Operations"),
    ("49-rbac-apikeys-scim.html", "RBAC · API key · SCIM", "RBAC, API keys & SCIM",
     "第十部分 · 平台与运维", "Part 10 · Platform & Operations"),
    ("50-open-core-and-entitlements.html", "开源核与权益", "Open-core & entitlements",
     "第十部分 · 平台与运维", "Part 10 · Platform & Operations"),
    ("51-self-observability-and-config.html", "自我可观测与配置", "Self-observability & config",
     "第十部分 · 平台与运维", "Part 10 · Platform & Operations"),
    ("52-data-lifecycle-and-deletion.html", "数据生命周期与删除", "Data lifecycle & deletion",
     "第十部分 · 平台与运维", "Part 10 · Platform & Operations"),
    ("53-build-test-dev-workflow.html", "构建·测试·开发流", "Build, test & dev workflow",
     "第十部分 · 平台与运维", "Part 10 · Platform & Operations"),
    ("54-design-themes-synthesis.html", "设计专题综合", "Design themes synthesis",
     "第十一部分 · 设计专题与终章", "Part 11 · Design Themes & Capstone"),
    ("55-capstone-trace-life.html", "终章·一条 trace 的完整一生", "Capstone: the full life of a trace",
     "第十一部分 · 设计专题与终章", "Part 11 · Design Themes & Capstone"),
    ("56-v4-architecture-delta.html", "v4 架构总览：从 v3.199 到 v4.42", "V4 architecture delta: v3.199 → v4.42",
     "第十二部分 · v4 迁移与生产实战", "Part 12 · V4 Migration & Production Practice"),
    ("57-v4-unified-events.html", "v4 统一 events 数据模型", "V4 unified events data model",
     "第十二部分 · v4 迁移与生产实战", "Part 12 · V4 Migration & Production Practice"),
    ("58-python-sdk-v4-otel.html", "Python SDK v4：OTel 原生埋点", "Python SDK v4: OTel-native tracing",
     "第十二部分 · v4 迁移与生产实战", "Part 12 · V4 Migration & Production Practice"),
    ("59-agent-langchain-v4.html", "Agent / LangChain v4 实战", "Agent & LangChain tracing in v4",
     "第十二部分 · v4 迁移与生产实战", "Part 12 · V4 Migration & Production Practice"),
    ("60-v4-evals-real-time.html", "v4 实时查询与评估闭环", "V4 real-time reads & evaluation loop",
     "第十二部分 · v4 迁移与生产实战", "Part 12 · V4 Migration & Production Practice"),
    ("61-v4-self-hosted-migration.html", "自托管 v4 迁移与上线", "Self-hosted v4 migration & rollout",
     "第十二部分 · v4 迁移与生产实战", "Part 12 · V4 Migration & Production Practice"),
]


def bi(zh, en):
    """Inline bilingual pair; only the active language is shown (CSS-controlled)."""
    return f'<span class="lang-zh">{zh}</span><span class="lang-en">{en}</span>'


INDEX_FILE = "index.html"

CSS = r"""
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #f6f7f9; --panel: #ffffff; --panel-2: #f0f2f5; --ink: #1d2129;
  --muted: #5b6470; --faint: #6b7480; --line: #e1e5ea;
  --accent: #059669; --accent-soft: #d1fae5; --accent-ink: #047857;
  --blue: #2563eb; --blue-soft: #e7efff; --amber: #b4690e; --amber-soft: #fdf1dd;
  --purple: #7c3aed; --purple-soft: #f0e9ff; --red: #d23f3f; --red-soft: #fbe6e6;
  --teal: #0e7490; --teal-soft: #cffafe;
  --code-bg: #0f172a; --code-ink: #e2e8f0; --code-line: #1e293b;
  --shadow: 0 1px 2px rgba(16,24,40,.06), 0 8px 24px rgba(16,24,40,.06);
  --radius: 14px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0e1116; --panel: #161b22; --panel-2: #1c232c; --ink: #e6edf3;
    --muted: #9aa6b2; --faint: #808b98; --line: #2a323c;
    --accent: #34d399; --accent-soft: #064e3b; --accent-ink: #6ee7b7;
    --blue: #6ea8fe; --blue-soft: #16243f; --amber: #e0a44a; --amber-soft: #33270f;
    --purple: #b794f6; --purple-soft: #271a40; --red: #f08080; --red-soft: #3a1a1a;
    --teal: #22d3ee; --teal-soft: #083344;
    --code-bg: #0a0f1a; --code-ink: #d8e2f0; --code-line: #14202f;
    --shadow: 0 1px 2px rgba(0,0,0,.4), 0 10px 30px rgba(0,0,0,.35);
  }
}
html { scroll-behavior: smooth; overflow-x: hidden; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC",
    "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  background: var(--bg); color: var(--ink); line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration: none; }
code, .mono { font-family: "SF Mono", "JetBrains Mono", "Fira Code", ui-monospace, Menlo, Consolas, monospace; overflow-wrap: break-word; }

/* ---- top progress bar ---- */
.topbar {
  position: sticky; top: 0; z-index: 50; background: var(--panel);
  border-bottom: 1px solid var(--line); backdrop-filter: blur(8px);
}
.topbar-inner {
  max-width: 960px; margin: 0 auto; padding: .7rem 1.25rem;
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
}
.topbar .home { font-size: .82rem; color: var(--muted); font-weight: 600; display:flex; gap:.5rem; align-items:center; }
.topbar .home b { color: var(--accent); }
.topbar .pill { font-size: .72rem; color: var(--muted); background: var(--panel-2);
  padding: .2rem .6rem; border-radius: 999px; border: 1px solid var(--line); white-space: nowrap; }
.progress { height: 3px; background: var(--panel-2); }
.progress > span { display: block; height: 100%; background: linear-gradient(90deg, var(--accent), var(--purple)); }

.wrap { max-width: 820px; margin: 0 auto; padding: 2.4rem 1.25rem 5rem; }

/* ---- hero ---- */
.hero { margin-bottom: 2rem; }
.hero .part { font-size: .76rem; letter-spacing: .08em; text-transform: uppercase;
  color: var(--accent); font-weight: 700; margin-bottom: .55rem; }
.hero h1 { font-size: 2.05rem; line-height: 1.2; letter-spacing: -.01em; font-weight: 750; }
.hero .lead { margin-top: .9rem; font-size: 1.06rem; color: var(--muted); }

h2 { font-size: 1.32rem; margin: 2.4rem 0 .9rem; letter-spacing: -.01em;
  display: flex; align-items: center; gap: .55rem; }
h2::before { content: ""; width: 4px; height: 1.05em; background: var(--accent); border-radius: 3px; display: inline-block; }
h3 { font-size: 1.05rem; margin: 1.4rem 0 .5rem; }
p { margin: .7rem 0; }
ul, ol { margin: .6rem 0 .6rem 1.3rem; }
li { margin: .3rem 0; }
strong { color: var(--ink); font-weight: 680; }
.inline { background: var(--panel-2); border: 1px solid var(--line); border-radius: 6px;
  padding: .08em .4em; font-size: .9em; color: var(--accent-ink); }

/* ---- callout cards ---- */
.card { border-radius: var(--radius); padding: 1.05rem 1.2rem; margin: 1.2rem 0;
  border: 1px solid var(--line); background: var(--panel); box-shadow: var(--shadow); }
.card .tag { font-size: .72rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase;
  display: inline-flex; align-items: center; gap: .4rem; margin-bottom: .5rem; }
.card.macro { border-left: 4px solid var(--blue); }
.card.macro .tag { color: var(--blue); }
.card.detail { border-left: 4px solid var(--purple); }
.card.detail .tag { color: var(--purple); }
.card.analogy { border-left: 4px solid var(--amber); background: var(--amber-soft); }
.card.analogy .tag { color: var(--amber); }
.card.key { border-left: 4px solid var(--accent); background: var(--accent-soft); }
.card.key .tag { color: var(--accent-ink); }
.card.warn { border-left: 4px solid var(--red); background: var(--red-soft); }
.card.warn .tag { color: var(--red); }
.card.prereq { border-left: 4px solid var(--teal); background: var(--teal-soft); }
.card.prereq .tag { color: var(--teal); }
.card.spark { border-left: 4px solid #e0a000;
  background: linear-gradient(100deg, rgba(224,160,0,.12), transparent 70%); }
.card.spark .tag { color: #c98a00; }
@media (prefers-color-scheme: dark) { .card.spark .tag { color: #f0c050; } }

/* ---- code file callout ---- */
.codefile { margin: 1.2rem 0; border-radius: 12px; overflow: hidden; border: 1px solid var(--line);
  box-shadow: var(--shadow); }
.codefile .cf-head { display: flex; align-items: center; gap: .55rem; padding: .5rem .85rem;
  background: var(--panel-2); border-bottom: 1px solid var(--line); font-size: .8rem; }
.codefile .cf-head .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--accent); flex-shrink:0; }
.codefile .cf-head .path { font-family: ui-monospace, monospace; color: var(--ink); font-weight: 600; }
.codefile .cf-head .ln { margin-left: auto; color: var(--faint); font-size: .72rem; }
.codefile pre { background: var(--code-bg); color: var(--code-ink); padding: .9rem 1rem;
  overflow-x: auto; font-size: .82rem; line-height: 1.6; }
.codefile pre .cm { color: #7d8aa3; }
.codefile pre .kw { color: #c792ea; }
.codefile pre .fn { color: #82aaff; }
.codefile pre .st { color: #c3e88d; }
.codefile pre .nb { color: #f78c6c; }

pre.code { background: var(--code-bg); color: var(--code-ink); padding: .9rem 1rem; border-radius: 12px;
  overflow-x: auto; font-size: .83rem; line-height: 1.6; margin: 1.1rem 0; box-shadow: var(--shadow); }
pre.code .cm { color: #7d8aa3; } pre.code .kw { color: #c792ea; }
pre.code .fn { color: #82aaff; } pre.code .st { color: #c3e88d; } pre.code .nb { color: #f78c6c; }

/* ---- collapsible accordion (details/summary) ---- */
.accordion { border: 1px solid var(--line); border-radius: 12px; background: var(--panel);
  margin: .7rem 0; box-shadow: var(--shadow); overflow: hidden; }
.accordion > summary { cursor: pointer; padding: .85rem 1.1rem; font-weight: 650; font-size: .96rem;
  list-style: none; display: flex; align-items: center; gap: .6rem; user-select: none; }
.accordion > summary::-webkit-details-marker { display: none; }
.accordion > summary::after { content: "▶"; font-size: .68rem; color: var(--accent);
  margin-left: auto; transition: transform .15s ease; }
.accordion[open] > summary::after { transform: rotate(90deg); }
.accordion > summary:hover { background: var(--panel-2); }
.accordion[open] > summary { border-bottom: 1px solid var(--line); }
.accordion .badge-num { background: var(--accent-soft); color: var(--accent-ink);
  width: 1.6rem; height: 1.6rem; border-radius: 7px; display: inline-flex; align-items: center;
  justify-content: center; font-size: .82rem; font-weight: 700; flex-shrink: 0; }
.accordion .hint { font-size: .72rem; color: var(--faint); font-weight: 400; }
.acc-body { padding: .9rem 1.1rem 1.1rem; }
.acc-intro { color: var(--muted); font-size: .9rem; margin: .2rem 0 .4rem; }
.qa { margin: 1rem 0; }
.qa:first-child { margin-top: .3rem; }
.qa .q { font-weight: 680; font-size: .9rem; display: flex; gap: .45rem; align-items: center; margin-bottom: .3rem; }
.qa .a { color: var(--muted); font-size: .9rem; }
.qa .a strong { color: var(--ink); }
.qa pre.code { margin: .5rem 0 0; font-size: .78rem; }

/* ---- flow diagram ---- */
.flow { display: flex; align-items: stretch; gap: 0; flex-wrap: wrap; margin: 1.3rem 0;
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 1.2rem 1rem; box-shadow: var(--shadow); }
.flow .node { flex: 1 1 0; min-width: 110px; text-align: center; padding: .7rem .5rem;
  border-radius: 10px; background: var(--panel-2); border: 1px solid var(--line); }
.flow .node .nt { font-weight: 700; font-size: .92rem; }
.flow .node .nd { font-size: .76rem; color: var(--muted); margin-top: .2rem; }
.flow .node.hl { background: var(--accent-soft); border-color: var(--accent); }
.flow .arrow { align-self: center; color: var(--faint); font-size: 1.3rem; padding: 0 .35rem; }

/* vertical flow */
.vflow { margin: 1.3rem 0; }
.vflow .step { display: flex; gap: .9rem; position: relative; padding-bottom: 1.1rem; }
.vflow .step:not(:last-child)::before { content:""; position:absolute; left: 15px; top: 34px; bottom: -2px;
  width: 2px; background: var(--line); }
.vflow .num { width: 32px; height: 32px; border-radius: 50%; background: var(--accent); color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: .85rem; flex-shrink: 0; z-index:1; }
.vflow .sc h4 { margin: .25rem 0 .2rem; font-size: 1rem; }
.vflow .sc p { margin: .15rem 0; font-size: .92rem; color: var(--muted); }
.vflow .sc .mono { font-size: .8rem; color: var(--accent-ink); }

/* layered architecture */
.layers { margin: 1.3rem 0; display: flex; flex-direction: column; gap: .55rem; }
.layer { border-radius: 12px; padding: .85rem 1.1rem; border: 1px solid var(--line); background: var(--panel);
  box-shadow: var(--shadow); }
.layer .lh { display: flex; align-items: center; gap: .6rem; }
.layer .lh .badge { font-size: .7rem; font-weight: 700; padding: .12rem .5rem; border-radius: 999px; }
.layer .lh .name { font-weight: 700; font-family: ui-monospace, monospace; }
.layer .ld { font-size: .85rem; color: var(--muted); margin-top: .35rem; }
.layer.l-core { border-left: 4px solid var(--accent); } .layer.l-core .badge { background: var(--accent-soft); color: var(--accent-ink); }
.layer.l-main { border-left: 4px solid var(--blue); } .layer.l-main .badge { background: var(--blue-soft); color: var(--blue); }
.layer.l-part { border-left: 4px solid var(--purple); } .layer.l-part .badge { background: var(--purple-soft); color: var(--purple); }
.layer.l-app { border-left: 4px solid var(--amber); } .layer.l-app .badge { background: var(--amber-soft); color: var(--amber); }

/* two-column compare */
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.2rem 0; }
@media (max-width: 640px) { .cols { grid-template-columns: 1fr; } }
.col { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 1rem 1.1rem; box-shadow: var(--shadow); min-width: 0; }
.col h4 { margin: 0 0 .4rem; font-size: .95rem; }

table.t { width: 100%; border-collapse: collapse; margin: 1.1rem 0; font-size: .9rem;
  background: var(--panel); border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); }
table.t th, table.t td { padding: .6rem .8rem; text-align: left; border-bottom: 1px solid var(--line); }
table.t th { background: var(--panel-2); font-size: .8rem; letter-spacing: .02em; }
table.t tr:last-child td { border-bottom: none; }
table.t td.mono, table.t td .mono { font-family: ui-monospace, monospace; font-size: .82rem; color: var(--accent-ink); }
@media (max-width: 640px) {
  /* Wide multi-column tables: scroll within their own box instead of
     forcing page-level horizontal overflow (which clipped right columns). */
  table.t { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
  table.t th, table.t td { padding: .5rem .6rem; }
  /* TOC rows: stack title over subtitle so the blurb reads left-aligned
     under the title instead of being crammed to the right on a phone. */
  .toc a { flex-direction: column; align-items: flex-start; gap: .3rem; }
  .toc .ts { margin-left: 0; text-align: left; }
  .toc .n { margin-bottom: -.2rem; }
}
.selftest { margin: 2.2rem 0 0; border-top: 2px dashed var(--line); padding-top: 1.2rem; }
.selftest > h2 { margin-top: .2rem; }
.quiz { background: var(--panel); border: 1px solid var(--line); border-left: 4px solid var(--blue);
  border-radius: 12px; padding: .9rem 1.1rem; margin: 1rem 0; box-shadow: var(--shadow); }
.quiz .qn { font-weight: 650; }
.quiz ol.opts { list-style: upper-alpha; margin: .55rem 0 .6rem 1.5rem; padding: 0; }
.quiz ol.opts li { margin: .3rem 0; padding-left: .15rem; }
.quiz details.accordion { margin: .5rem 0 0; }
.selftest code { font-family: ui-monospace, monospace; font-size: .9em; color: var(--accent-ink);
  background: var(--accent-soft); padding: 0 .28em; border-radius: 4px; }

/* footer nav */
.footnav { display: flex; justify-content: space-between; gap: 1rem; margin-top: 3rem;
  padding-top: 1.4rem; border-top: 1px solid var(--line); }
.footnav a { flex: 1; padding: .85rem 1.1rem; border-radius: 12px; border: 1px solid var(--line);
  background: var(--panel); box-shadow: var(--shadow); transition: .15s; }
.footnav a:hover { border-color: var(--accent); transform: translateY(-1px); }
.footnav a.next { text-align: right; }
.footnav .dir { font-size: .72rem; color: var(--faint); text-transform: uppercase; letter-spacing: .05em; }
.footnav .ttl { font-weight: 700; color: var(--ink); margin-top: .15rem; }
.footnav a.disabled { opacity: .35; pointer-events: none; }

/* index page */
.toc { display: grid; gap: .7rem; margin-top: 1.6rem; }
.toc-part { font-size: .78rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
  color: var(--accent); margin: 1.4rem 0 .2rem; }
.toc a { display: flex; align-items: center; gap: .9rem; padding: .85rem 1.05rem; border-radius: 12px;
  background: var(--panel); border: 1px solid var(--line); box-shadow: var(--shadow); transition: .15s; }
.toc a:hover { border-color: var(--accent); transform: translateX(3px); }
.toc .n { width: 30px; height: 30px; border-radius: 8px; background: var(--accent-soft); color: var(--accent-ink);
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: .85rem; flex-shrink: 0; }
.toc .tt { font-weight: 650; color: var(--ink); }
.toc .ts { font-size: .8rem; color: var(--muted); margin-left: auto; text-align: right; }
.toc-search { position: relative; margin: 1.6rem 0 -.4rem; }
.toc-search input { width: 100%; box-sizing: border-box; padding: .75rem 2.8rem .75rem 1rem;
  border-radius: 12px; border: 1px solid var(--line); background: var(--panel); color: var(--ink);
  font-size: .98rem; box-shadow: var(--shadow); }
.toc-search input:focus { outline: none; border-color: var(--accent); }
.toc-search .qcount { position: absolute; right: 1rem; top: 50%; transform: translateY(-50%);
  color: var(--faint); font-size: .8rem; pointer-events: none; }
.toc a.hide, .toc .toc-part.hide { display: none; }
.t tr.hide, table.t.hide, h2.hide { display: none; }
.toc-empty { display: none; color: var(--muted); padding: 1rem; text-align: center; }
.toc-empty.show { display: block; }
.hero.index h1 { font-size: 2.3rem; }
.legend { display:flex; gap:1.2rem; flex-wrap:wrap; margin-top:1rem; font-size:.8rem; color:var(--muted); }
.legend span { display:flex; align-items:center; gap:.4rem; }
.legend i { width:12px; height:12px; border-radius:3px; display:inline-block; }
.pdf-btn { display:inline-flex; align-items:center; gap:.4rem; padding:.55rem 1.1rem;
  background:var(--accent); color:#fff; border-radius:10px; font-size:.9rem; font-weight:650;
  box-shadow:var(--shadow); transition:.15s; }
.pdf-btn:hover { background:var(--accent-ink); transform:translateY(-1px); }

/* ---- bilingual language switch ----
   Contract: <html> must carry data-lang="zh" (default) or "en".
   page()/index_page() hard-code data-lang="zh"; LANG_BOOT may switch to "en". */
html[data-lang="en"] .lang-zh { display: none !important; }
html[data-lang="zh"] .lang-en { display: none !important; }
.langtoggle { font-size:.72rem; font-weight:700; color:var(--accent-ink);
  background:var(--accent-soft); border:1px solid var(--accent); border-radius:999px;
  padding:.22rem .7rem; cursor:pointer; line-height:1.4; white-space:nowrap; }
.langtoggle:hover { background:var(--accent); color:#fff; }

/* ---- schematic: cell strips (vector rows / quant blocks / KV columns) ---- */
.cellgroup { margin: 1.2rem 0; background: var(--panel); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 1rem 1.1rem; box-shadow: var(--shadow); }
.cellgroup .cg-cap { font-size: .82rem; color: var(--muted); margin-bottom: .55rem; }
.cellgroup .cg-cap b { color: var(--ink); }
.cells { display: flex; flex-wrap: wrap; gap: .35rem; align-items: center; }
.cells + .cells { margin-top: .5rem; }
.cell { min-width: 2.1rem; padding: .38rem .5rem; text-align: center; border-radius: 8px;
  background: var(--panel-2); border: 1px solid var(--line); font-size: .78rem;
  font-family: ui-monospace, monospace; white-space: nowrap; }
.cell.scale { background: var(--amber-soft); border-color: var(--amber); color: var(--amber); font-weight: 700; }
.cell.hl    { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-ink); font-weight: 700; }
.cell.q     { background: var(--blue-soft); border-color: var(--blue); color: var(--blue); }
.cell.dim   { opacity: .45; }
.cells .lab { font-size: .76rem; color: var(--faint); padding: 0 .35rem; }
.cells .sep { color: var(--faint); padding: 0 .1rem; }

/* ---- schematic: timeline lanes (write vs read, step-by-step) ---- */
.timeline { margin: 1.2rem 0; display: flex; flex-direction: column; gap: .5rem;
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 1rem 1.1rem; box-shadow: var(--shadow); }
.timeline .lane { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
.timeline .lane-label { min-width: 6rem; font-size: .8rem; font-weight: 700; color: var(--muted); }
.timeline .tslot { padding: .4rem .6rem; border-radius: 8px; background: var(--panel-2);
  border: 1px solid var(--line); font-size: .78rem; text-align: center; font-family: ui-monospace, monospace; }
.timeline .tslot.span { flex: 1; min-width: 8rem; background: var(--blue-soft); border-color: var(--blue);
  color: var(--blue); font-weight: 700; }
.timeline .tslot.now { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-ink); font-weight: 700; }
.timeline .tl-row { display: flex; align-items: flex-start; gap: .6rem; padding: .12rem 0; }
.timeline .tl-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--accent); flex-shrink: 0; margin-top: .45rem; }
.timeline .tl-t { font-family: ui-monospace, monospace; font-weight: 700; color: var(--accent-ink); min-width: 2.4rem; font-size: .82rem; flex-shrink: 0; margin-top: .18rem; }
.timeline .tl-c { font-size: .9rem; color: var(--muted); }

/* ---- worked-example trace: one concrete input, stepped through ---- */
.trace { margin: 1.3rem 0; background: var(--panel); border: 1px solid var(--line);
  border-left: 4px solid var(--accent); border-radius: var(--radius); padding: 1rem 1.1rem; box-shadow: var(--shadow); }
.trace .tcap { font-size: .82rem; color: var(--muted); margin-bottom: .7rem; }
.trace .tcap b { color: var(--accent-ink); }
.trace .stations { display: flex; align-items: stretch; gap: 0; flex-wrap: wrap; }
.trace .stn { flex: 1 1 0; min-width: 116px; border: 1px solid var(--line); border-radius: 10px;
  padding: .55rem; background: var(--bg); }
.trace .stn h5 { margin: 0 0 .45rem; font-size: .8rem; color: var(--ink); }
.trace .cellrow { display: flex; gap: .3rem; align-items: center; flex-wrap: wrap; }
.trace .vc { min-width: 2.1rem; padding: .32rem .45rem; text-align: center; border-radius: 7px;
  background: var(--panel-2); border: 1px solid var(--line); font: 600 .76rem ui-monospace, monospace; white-space: nowrap; }
.trace .vc.hot  { background: var(--accent-soft); border-color: var(--accent); color: var(--accent-ink); }
.trace .vc.blue { background: var(--blue-soft); border-color: var(--blue); color: var(--blue); }
.trace .vc.dim  { opacity: .42; }
.trace .tlab { font-size: .68rem; color: var(--faint); margin-top: .35rem; }
.trace .op { align-self: center; color: var(--accent); font: 700 .72rem ui-monospace, monospace;
  padding: 0 .5rem; text-align: center; white-space: nowrap; }
.trace svg { max-width: 100%; height: auto; display: block; margin: .3rem auto; }
@media (max-width: 640px) { .trace .stations { flex-direction: column; } .trace .op { padding: .3rem 0; } }
/* --- hand-drawn figure (inline SVG illustrations) --- */
.fig { margin: 1.3rem 0; background: var(--panel); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 1rem 1rem .85rem; box-shadow: var(--shadow); text-align: center; }
.fig svg { max-width: 100%; height: auto; display: block; margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", sans-serif; }
.fig svg text:not([fill]) { fill: var(--ink); }
.fig .figcap { margin: .72rem auto 0; font-size: .8rem; color: var(--muted); line-height: 1.55; max-width: 46rem; }
.fig .figcap b { color: var(--accent-ink); font-weight: 700; }
/* inter-lesson cross-reference links (第N课 / Lesson N / LNN), added at build time */
.xref { color: var(--accent-ink); text-decoration: none; border-bottom: 1px dotted var(--accent); white-space: nowrap; }
.xref:hover { border-bottom-style: solid; background: var(--accent-soft); }
"""

SEARCH_JS = """
(function(){
  var q=document.getElementById('q'); if(!q) return;
  var toc=document.querySelector('.toc');
  var empty=document.getElementById('tocempty');
  var count=document.getElementById('qcount');
  var links=[].slice.call(toc.querySelectorAll('a'));
  var heads=[].slice.call(toc.querySelectorAll('.toc-part'));
  links.forEach(function(a){ a.setAttribute('data-s',((a.textContent||'')+' '+(a.getAttribute('data-keywords')||'')).toLowerCase()); });
  function run(){
    var t=(q.value||'').toLowerCase().trim(), n=0;
    links.forEach(function(a){
      var hit=!t||a.getAttribute('data-s').indexOf(t)>=0;
      a.classList.toggle('hide',!hit); if(hit)n++;
    });
    heads.forEach(function(h){
      var el=h.nextElementSibling, any=false;
      while(el && !el.classList.contains('toc-part')){
        if(el.tagName==='A' && !el.classList.contains('hide')){any=true;break;}
        el=el.nextElementSibling;
      }
      h.classList.toggle('hide',!any);
    });
    empty.classList.toggle('show', !!t && n===0);
    count.textContent = t ? String(n) : '';
  }
  q.addEventListener('input',run);
})();
"""

GLOSSARY_JS = """
(function(){
  function wire(inputId, countId, emptyId, scope){
    var q=document.getElementById(inputId); if(!q) return;
    var root=document.querySelector(scope); if(!root) return;
    var empty=document.getElementById(emptyId), count=document.getElementById(countId);
    var tables=[].slice.call(root.querySelectorAll('table.t'));
    var rows=[].slice.call(root.querySelectorAll('table.t tr')).filter(function(tr){return tr.querySelector('td');});
    rows.forEach(function(tr){ tr.setAttribute('data-s',(tr.textContent||'').toLowerCase()); });
    function run(){
      var t=(q.value||'').toLowerCase().trim(), n=0;
      rows.forEach(function(tr){
        var hit=!t||tr.getAttribute('data-s').indexOf(t)>=0;
        tr.classList.toggle('hide',!hit); if(hit)n++;
      });
      tables.forEach(function(tb){
        var any=[].slice.call(tb.querySelectorAll('tr')).some(function(tr){
          return tr.querySelector('td') && !tr.classList.contains('hide');
        });
        tb.classList.toggle('hide', !any);
        var h=tb.previousElementSibling;
        if(h && h.tagName==='H2') h.classList.toggle('hide', !any);
      });
      if(empty) empty.classList.toggle('show', !!t && n===0);
      if(count) count.textContent = t ? String(n) : '';
    }
    q.addEventListener('input',run);
  }
  wire('qglzh','qglzhc','qglzhe','.lang-zh');
  wire('qglen','qglenc','qglene','.lang-en');
})();
"""

LANG_JS = """
function lvgSetLang(l){
  l=(l==='en')?'en':'zh';
  var d=document.documentElement;
  d.dataset.lang=l; d.lang=(l==='en'?'en':'zh-CN');
  try{localStorage.setItem('lvg-lang',l);}catch(e){}
}
function lvgToggleLang(){
  lvgSetLang(document.documentElement.dataset.lang==='en'?'zh':'en');
}
"""

# Runs in <head> before first paint to avoid a flash of the wrong language.
LANG_BOOT = (
    "<script>try{var l=localStorage.getItem('lvg-lang');"
    "if(l==='en'){document.documentElement.dataset.lang='en';"
    "document.documentElement.lang='en';}}catch(e){}</script>"
)


# ---- cross-reference auto-linking -------------------------------------------
# Lessons constantly mention sibling lessons in prose ("第24课" / "Lesson 24" /
# "L24") but those were plain text. autolink() wraps them in <a> so a reader can
# jump. It splits the HTML into protected chunks (code/svg/existing anchors/raw
# tags) vs plain text and only rewrites the plain text, so it never links inside
# <code>, inside SVG diagrams, inside attribute values, or double-wraps an
# existing link. Applied to web lesson bodies only (the print build concatenates
# everything into one file where per-file hrefs wouldn't resolve).
_PROTECT = re.compile(
    r"(<code\b[^>]*>.*?</code>|<svg\b[^>]*>.*?</svg>|<a\b[^>]*>.*?</a>|<[^>]+>)", re.S
)
_XREF_PATTERNS = (
    re.compile(r"第\s*(\d{1,2})\s*课"),
    re.compile(r"Lesson\s+(\d{1,2})\b"),
    re.compile(r"\bL(\d{2})\b"),
)
# Compact Chinese list, e.g. 「第 5、15 课」/「第 7、8、10 课」 — the single-ref
# pattern above can't see the inner numbers, so each one is linked individually.
_ZH_LIST = re.compile(r"第\s*\d{1,2}(?:\s*[、,，]\s*\d{1,2})+\s*课")


def _link_zh_list(seg, self_num, order):
    def repl(m):
        def lk(nm):
            n = int(nm.group(0))
            if n == self_num or not (1 <= n <= len(order)):
                return nm.group(0)
            return f'<a class="xref" href="{order[n - 1]}">{nm.group(0)}</a>'
        return re.sub(r"\d{1,2}", lk, m.group(0))
    return _ZH_LIST.sub(repl, seg)


def autolink(html, self_num, order):
    """Wrap inter-lesson references in <a class="xref">. ``order`` is the list of
    lesson filenames (index 0 = lesson 01); ``self_num`` is this lesson's number
    (1-based) so self-references stay plain."""
    parts = _PROTECT.split(html)
    for i in range(0, len(parts), 2):  # even indices = unprotected text
        seg = _link_zh_list(parts[i], self_num, order)
        for pat in _XREF_PATTERNS:
            def repl(m):
                n = int(m.group(1))
                if n == self_num or not (1 <= n <= len(order)):
                    return m.group(0)
                return f'<a class="xref" href="{order[n - 1]}">{m.group(0)}</a>'
            seg = pat.sub(repl, seg)
        parts[i] = seg
    return "".join(parts)


# --- Part-finale tag suffix -------------------------------------------------
# The last lesson of each Part gets its 「🎯 本课要点 / 🎯 Key points」 card tagged
# as that Part's wrap-up, so every Part closes with a consistent marker (the very
# last lesson of the book is marked as the whole-book finale instead). Derived
# from PAGES so it stays correct if Part boundaries ever change.
_CN_NUM = ("零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二")


def _part_ender_map():
    """fname -> 1-based Part number, for the last lesson of each Part (grouped by
    the Part label carried in PAGES[i][3])."""
    enders, groups, cur, last = {}, [], [], None
    for p in PAGES:
        label = p[3]
        if label != last:
            if cur:
                groups.append(cur)
            cur, last = [], label
        cur.append(p[0])
    if cur:
        groups.append(cur)
    for i, g in enumerate(groups, 1):
        enders[g[-1]] = i
    return enders


PART_ENDERS = _part_ender_map()


def add_part_finale(html, fname, lang):
    """If ``fname`` is the last lesson of its Part, append a wrap-up suffix to its
    single key-points card tag. Exactly one such tag exists per lesson."""
    n = PART_ENDERS.get(fname)
    if not n:
        return html
    is_capstone = fname == PAGES[-1][0]
    if lang == "zh":
        suffix = " · 全书终" if is_capstone else f" · 第{_CN_NUM[n]}部分收官"
        return html.replace("🎯 本课要点", "🎯 本课要点" + suffix, 1)
    suffix = " · The end" if is_capstone else f" · Part {n} wrap-up"
    return html.replace("🎯 Key points", "🎯 Key points" + suffix, 1)


def _prereq_card(fname, self_num, order):
    """Render the optional 「🧭 读前 / Before you start」 card for lessons that have
    a real prerequisite. Lesson references inside the hint are auto-linked."""
    hint = PREREQS.get(fname)
    if not hint:
        return ""
    zh, en = hint
    card = (
        '<div class="card prereq">'
        f'<div class="tag">🧭 {bi("读前", "Before you start")}</div>'
        f'<div class="lang-zh">{zh}</div><div class="lang-en">{en}</div>'
        "</div>"
    )
    return autolink(card, self_num, order)


def page(filename, content, home_href="../index.html"):
    """Wrap one lesson's bilingual content in the full HTML shell.

    ``content`` is a dict ``{"zh": html, "en": html}``. Both are emitted; CSS
    shows only the active language. Navigation uses plain relative ``href``
    links so the site works via file:// and any static server (lessons share
    one directory; home defaults to ``../index.html``).
    """
    idx = next(i for i, p in enumerate(PAGES) if p[0] == filename)
    fname, title_zh, title_en, part_zh, part_en = PAGES[idx]
    total = len(PAGES)
    pct = int((idx + 1) / total * 100)
    home = home_href

    if idx > 0:
        p = PAGES[idx - 1]
        prev_link = (
            f'<a class="prev" href="{p[0]}"><div class="dir">{bi("← 上一课", "← Prev")}</div>'
            f'<div class="ttl">{bi(esc(p[1]), esc(p[2]))}</div></a>'
        )
    else:
        prev_link = (
            f'<a class="prev" href="{home}"><div class="dir">{bi("← 返回", "← Back")}</div>'
            f'<div class="ttl">{bi("目录", "Contents")}</div></a>'
        )
    if idx + 1 < total:
        p = PAGES[idx + 1]
        next_link = (
            f'<a class="next" href="{p[0]}"><div class="dir">{bi("下一课 →", "Next →")}</div>'
            f'<div class="ttl">{bi(esc(p[1]), esc(p[2]))}</div></a>'
        )
    else:
        next_link = (
            f'<a class="next" href="{home}"><div class="dir">{bi("完成 →", "Done →")}</div>'
            f'<div class="ttl">{bi("返回目录", "Back to index")}</div></a>'
        )

    title_tag = f"{idx+1:02d} · {title_zh} / {title_en} - Langfuse 图解教程"
    desc = f"{part_zh}｜{title_zh} - Langfuse 图解教程（中英双语，配真实源码对应、折叠深挖与设计取舍）"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN" data-lang="zh"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{LANG_BOOT}
<title>{esc(title_tag)}</title>
{head_meta(title_tag, desc, og_type="article")}
<style>{CSS}</style>
</head><body>
<div class="topbar">
  <div class="topbar-inner">
    <a class="home" href="{home}">🪢 <b class="lang-zh">Langfuse 图解教程</b><b class="lang-en">Langfuse Visual Guide</b></a>
    <span class="pill">{bi(esc(part_zh), esc(part_en))}</span>
    <span class="pill">{idx+1:02d} / {total:02d}</span>
    <button class="langtoggle" onclick="lvgToggleLang()" aria-label="switch language"><span class="lang-zh">EN</span><span class="lang-en">中</span></button>
  </div>
  <div class="progress"><span style="width:{pct}%"></span></div>
</div>
<div class="wrap">
  <div class="hero">
    <div class="part">{bi(esc(part_zh), esc(part_en))}</div>
    <h1><span class="lang-zh">{esc(title_zh)}</span><span class="lang-en">{esc(title_en)}</span></h1>
  </div>
  {_prereq_card(fname, idx + 1, [p[0] for p in PAGES])}
  <div class="lang-zh">{content["zh"]}</div>
  <div class="lang-en">{content["en"]}</div>
  <div class="footnav">{prev_link}{next_link}</div>
</div>
<script>{LANG_JS}</script>
</body></html>"""
    return html


# Per-lesson TOC subtitle: filename -> (zh, en). Missing entries render blank.
# Grows one Part per milestone alongside PAGES.
SUBTITLES = {
    "01-what-is-langfuse.html": ("LLM 可观测性 · trace/observation/score · 为何要这样一套平台",
                                 "LLM observability; trace/observation/score; why a platform like this"),
    "02-observability-2-and-wide-events.html": ("可观测性 1.0 的困境 · 宽事件 · 十条原则 · unknown unknowns",
                                                "the 1.0 trouble; wide events; the principles; unknown unknowns"),
    "03-three-pillars-deep.html": ("trace 薄 · observation 厚（10 型·树）· score 两维 · 落到三张 CH 表",
                                   "thin trace; heavy observation (10 types, tree); score 2-D; three CH tables"),
    "04-project-map-monorepo.html": ("monorepo · 四工作区 · 窄腰依赖 · Turbo 编排 · 高频目录速查",
                                     "monorepo; four workspaces; narrow-waist deps; Turbo; hot-dir cheat-sheet"),
    "05-life-of-a-trace.html": ("写：SDK→API→队列→worker→CH · 读：UI→tRPC→仓储→CH · 异步·最终一致",
                                "write: SDK→API→queue→worker→CH; read: UI→tRPC→repo→CH; async; eventual consistency"),
    "06-instrumenting-an-llm-app.html": ("两个入口：SDK 原生事件 / OTel · 事件信封 · create+update 增量",
                                         "two entries: native SDK events / OTel; the event envelope; incremental create+update"),
    "07-dual-store-architecture.html": ("四存储分工：PG 配置 · CH 宽事件 · Redis 队列/缓存 · S3 真相之源 · OLTP vs OLAP",
                                        "four stores: PG config; CH wide events; Redis queue/cache; S3 source-of-truth; OLTP vs OLAP"),
    "08-clickhouse-wide-events.html": ("ReplacingMergeTree · 排序键 project_id 打头 · 月分区 · ZSTD/Map/bloom · 少扫才是关键",
                                       "ReplacingMergeTree; ordering key project_id-first; monthly partitions; ZSTD/Map/bloom; scan-less"),
    "09-postgres-metadata-schema.html": ("控制面 vs 数据面 · Project 枢纽 · 模型分组 · Legacy 残留 · API key 哈希",
                                         "control plane vs data plane; Project hub; model groups; Legacy remnants; hashed API keys"),
    "10-multi-tenancy.html": ("三层嵌套 org→project→env · project 硬隔离 · environment 软切片 · project_id 贯穿",
                              "three levels org→project→env; hard project isolation; soft environment slice; project_id threaded"),
    "11-deployment-topology.html": ("2 应用 + 4 基础设施 · docker-compose · web vs worker · MinIO 替身 · env 启动即校验",
                                    "2 apps + 4 infra; docker-compose; web vs worker; MinIO stand-in; env validated at startup"),
    "12-ingestion-api.html": ("鉴权+Zod+入队 · processEventBatch · 攒批上报 · 两道关 · 快返回",
                              "auth+Zod+enqueue; processEventBatch; batched reporting; two gates; fast return"),
    "13-event-types-merge.html": ("事件信封 · discriminatedUnion · body 继承链 · 两套 id · 合并最新者胜 · 18→3",
                                  "event envelope; discriminatedUnion; body inheritance; two ids; latest-wins merge; 18→3"),
    "14-ingestion-queue.html": ("Redis+BullMQ · 队列放指针 fileKey · S3 存本体 · 分片 · 主/次队列 · 重试退避",
                                "Redis+BullMQ; queue holds fileKey pointer; S3 stores body; sharding; primary/secondary; retry backoff"),
    "15-ingestion-service.html": ("mergeAndWrite 分派 · S3 事件+CH 记录双输入 · mergeRecords 左折叠 · 只入队不直写",
     "mergeAndWrite dispatch; S3 events + CH record; mergeRecords left-fold; enqueue, never direct-write"),
    "16-token-counting-cost.html": ("provided 压倒 computed · findModel 正则匹配 · tokenizer 分词 · matchPricingTier 选档",
     "provided beats computed; findModel regex; tokenizer counting; matchPricingTier; price × units"),
    "17-clickhouse-writer.html": ("单例批写器 · 每表内存队列 · batchSize/writeInterval 双触发 · 批量 INSERT · 优雅排空 · 内存换吞吐(S3 兜底)",
                                  "singleton writer; per-table memory queues; batchSize/writeInterval triggers; bulk INSERT; graceful drain"),
    "18-opentelemetry-ingestion.html": ("OTLP 端点 · protobuf/JSON · 万能适配器 · 优先级属性键 gen_ai/ai/llm · 映射成原生事件 · 边缘适配核心归一",
                                        "OTLP endpoint; protobuf/JSON; universal adapter; priority keys gen_ai/ai/llm; adapt-at-edge, unify-at-core"),
    "19-media-blob-storage.html": ("大二进制不进 ClickHouse · langfuseMedia 引用串 · presigned 直传 S3 · sha256 内容寻址去重",
     "big binaries stay out of ClickHouse; langfuseMedia reference; presigned direct S3 upload; sha256 dedup"),
    "20-web-app-architecture.html": ("Next.js Pages Router 为主 · 三种 API(tRPC/REST/App-Router) · 对内类型安全、对外契约稳定",
     "Next.js, mostly Pages Router; three APIs (tRPC/REST/App-Router); internal type-safety, external stability"),
    "21-trpc-backbone.html": ("appRouter 聚合 ~64 路由 · context 注入 session/prisma · 可叠中间件栈 · 安全靠结构",
     "appRouter aggregates ~64 routers; context injects session/prisma; stackable middleware; security by structure"),
    "22-repository-layer.html": ("queryClickhouse 统一执行器 · OTel/log_comment 标签/退避重试/资源错误包装 · 回看时间窗 2天/1小时 · 流式变体",
                                "queryClickhouse unified executor; OTel tags + backoff retry + resource-error wrap; look-back windows 2d/1h"),
    "23-filtering-search-bar.html": ("FilterState 中间契约 · 编译到 CH/PG 两套 SQL · 随机占位符防注入 · 搜索栏与 AI filter 同源",
     "FilterState contract; compiles to CH/PG SQL; random placeholders block injection; search bar & AI filter, one source"),
    "24-lists-and-tables.html": ("紧凑行 vs 指标双查并发 · 按 id 合并 · 按需 JOIN/FINAL · 表态以 URL 为真源",
     "compact rows vs metrics, parallel; merge by id; conditional JOIN/FINAL; table state as URL-truth"),
    "25-trace-detail-tree.html": ("全量取观测树 · 树与评分并行 · includeIO:false 懒加载 · verbosity 给巨型 trace 封顶",
     "fetch the whole tree; tree+scores in parallel; includeIO:false lazy-load; verbosity caps giant traces"),
    "26-sessions.html": ("session = traces 按 session_id 分组聚合 · 派生视图非新实体 · 复用第 24 课表格机制",
     "session = traces grouped by session_id; a derived view, not a new entity; reuses Lesson 24's tables"),
    "27-public-rest-api.html": ("路由工厂统一鉴权/限流/校验 · Redis 缓存+负缓存 · 文件夹版本 v1/v2/v3 · Fern 生成 SDK",
     "route factory unifies auth/rate-limit/validation; Redis + negative caching; Fern generates SDKs"),
    "28-scoring-model.html": ("score=评估原子单位 · 三种刻度 数值/分类/布尔 · config 是某 name 的 schema · 三来源同写 scores 表",
     "score = the atomic unit; three scales numeric/categorical/boolean; config is a name's schema; three sources, one table"),
    "29-llm-as-a-judge.html": ("一个 LLM 给另一个评分 · 模板/评估器/执行 · 变量映射填占位符 · source=EVAL 回流摄取链路",
     "one LLM scores another; template/evaluator/execution; variable mapping fills placeholders; source=EVAL flows back"),
    "30-eval-execution-pipeline.html": ("createEvalJobs 扇出到 ACTIVE 评估器 · 两级队列 · 三道闸 去重/采样/延迟 · 前缀防无限循环",
     "createEvalJobs fans out to ACTIVE evaluators; two-stage queues; three gates dedup/sampling/delay; prefix guards loops"),
    "31-code-based-evaluation.html": ("确定性代码评估 vs LLM 概率判断 · dispatcher 策略模式 · 沙箱铁律 禁网络+限大小+超时",
     "deterministic code eval vs LLM judgment; dispatcher strategy; sandbox iron rules: no-network + size caps + timeout"),
    "32-human-annotation.html": ("第三种来源 source=ANNOTATION · 常作 ground truth 校准 AI · 标注队列绑 scoreConfigIds · 5 分钟软锁",
     "third source ANNOTATION; often ground truth to calibrate the AI; annotation queue binds scoreConfigIds; 5-min soft lock"),
    "33-monitors-and-alerting.html": ("质量监测从拉变推(越线告警) · 复用 widget 查询 · severity 状态机 · 只在变化时告警",
     "quality monitoring from pull to push (alert); reuses a widget's query; severity state machine; alert only on change"),
    "34-datasets-and-items.html": ("数据集=测试用例 · 题可从真实 trace 提拔 · 数据项 SCD Type2 版本化 · run 钉住版本保可复现",
     "a dataset = test cases; questions promotable from traces; items versioned SCD Type 2; a run pins the version"),
    "35-dataset-runs.html": ("run=一场考试 · run item 钉 runId+itemId→traceId · upsert 自动触发评分 · 按 run 聚合均分",
     "a run = an exam; a run item pins runId+itemId→traceId; upsert auto-triggers scoring; aggregate scores per run"),
    "36-experiments-and-comparison.html": ("实验=prompt×数据集×模型，服务端自动跑 · 评分自动接 L30/35 · 对比靠 baseline+增量",
     "experiment = prompt × dataset × model, run server-side; scoring auto-connects (L30/35); compare via baseline + deltas"),
    "37-prompt-management.html": ("prompt = 专为 prompt 的 git · 版本不可变 · label 可移动指针(零部署发布/回滚) · 依赖可组合",
     "a prompt = git for prompts; immutable versions; a label is a movable pointer (zero-deploy release/rollback)"),
    "38-prompt-serving-caching.html": ("生产每次调用都取 prompt 故须快 · Redis read-through · 服务时解析依赖内联 · epoch 失效 O(1)",
     "production fetches a prompt every call, so it must be fast; Redis read-through; epoch invalidation O(1)"),
    "39-playground-llm-connections.html": ("Playground=同一引擎的交互前台 · API key 用 AES-256-GCM 即用即解 · LlmSchema/LlmTool 可复用积木",
     "Playground = the engine's interactive front desk; API keys AES-256-GCM, decrypt-on-use; reusable blocks"),
    "40-dashboards-and-widgets.html": ("仪表盘=布局+一排 widget · widget=声明式查询+图表 · 查询与呈现解耦 · 一份查询形状三处复用",
     "a dashboard = layout + a row of widgets; widget = declarative query + chart; query and presentation decoupled"),
    "41-query-engine.html": ("声明式查询→ClickHouse SQL 编译器 · 语义层映射逻辑名 · 值走 parameters 防注入 · 一引擎多消费",
     "a declarative-query → ClickHouse SQL compiler; a semantic layer maps logical names; one engine, many consumers"),
    "42-models-and-pricing.html": ("定价数据模型喂成本计算 · matchPattern 一条正则统一命名 · 默认档+条件档分级 · 规则即数据",
     "the pricing model feeds cost computation; matchPattern unifies naming via regex; default + conditional tiers"),
    "43-cloud-usage-metering.html": ("Cloud 专属平台计费 · 按观测数每小时报 Stripe · 命门「恰好一次」cronJobs 锁+整点对齐+兜底接管",
     "Cloud-exclusive platform billing; meter usage events hourly to Stripe; exactly-once via cronJobs lock + hour-align"),
    "44-automations-webhooks.html": ("自动化 Trigger→Action · 命门是 SSRF · 纵深防御黑白名单+fail-closed · HMAC 签名+重试+自动停用",
     "automation Trigger→Action; the SSRF risk; defense-in-depth allow/blocklists; HMAC signing + retry"),
    "45-slack-and-notifications.html": ("Slack 一等公民投递 · OAuth 把 bot 令牌加密入库 · 用时解密发 Block Kit 富消息 · 站内通知队列",
     "Slack as a first-class channel; the OAuth bot token stored encrypted; decrypt at use for Block Kit messages"),
    "46-analytics-integrations.html": ("把数据导回你的 PostHog/S3 · 三个同构集成 · 两级 fan-out 调度+处理 · 增量水位+按日切块流式导出",
     "export your data to PostHog/S3; three isomorphic integrations; two-level fan-out; incremental watermark"),
    "47-batch-exports-and-actions.html": ("一个查询两条路：导出(只读产文件) vs 操作(改数据) · 流式+分块防内存爆 · 操作分块 1000+幂等",
     "one query, two paths: export (read-only file) vs action (mutate); stream + chunk to bound memory"),
    "48-auth-and-sessions.html": ("谁能进：鉴权=你是谁 · 密码(bcrypt)+十几种 SSO · 密码登录四护栏 · 会话=无状态 JWT 利于扩展",
     "who gets in: auth = who you are; password (bcrypt) + a dozen SSO; session = a stateless JWT that scales out"),
    "49-rbac-apikeys-scim.html": ("你能干什么：人走 RBAC、机器走 API key · 角色→scope，前后端双查 · API key 两层哈希 · SCIM 企业自动开通",
     "what you can do: humans via RBAC, machines via API keys; role→scope dual-checked; API-key two-tier hash"),
    "50-open-core-and-entitlements.html": ("开源核：全代码开放，区别在运行时能否启用 · plan 分层 · entitlementAccess 总表+一道闸 · EE 许可证按前缀判",
     "open core: all code is open, the difference is runtime enablement; plan tiers via one entitlementAccess table"),
    "51-self-observability-and-config.html": ("自我可观测 dogfooding · instrumentAsync span 包装器 · 每行日志盖 trace_id · 配置过 Zod 启动即校验",
     "self-observability (dogfooding) on the same OTel; instrumentAsync span wrapper; trace_id on every log line"),
    "52-data-lifecycle-and-deletion.html": ("一条 trace 散在三存储，删除须一处不漏 · 删除有序先 CH+S3 后 PG · 三种删除 · 后台迁移在线做手术",
     "one trace spans three stores, deletion must miss none; ordered CH+S3 first, PG last; three deletion kinds"),
    "53-build-test-dev-workflow.html": ("平台自己怎么构建/测试 · pnpm monorepo 依赖只朝下 · Turbo 拓扑序+内容哈希缓存 · 一键 dx 从空环境到能跑",
     "how the platform is built/tested; pnpm monorepo, deps point down; Turbo topological order + hash cache"),
    "54-design-themes-synthesis.html": ("退一步收成六主题：宽事件/不可变/异步/双存储/多租户/成本 · 非六技巧而是一套世界观的六切面",
     "step back into six themes: wide events / immutability / async / dual storage / multi-tenancy / cost"),
    "55-capstone-trace-life.html": ("跟一条 trace 走完一生，把 55 课串成流水线 · 七驿站 · 三隐线 · trace→score 闭环反哺应用",
     "follow one trace through its whole life, stringing all 55 lessons; seven stations; three hidden threads"),
    "56-v4-architecture-delta.html": ("v3.199→v4.42 · observation-first · events unified · OTel-native · 分阶段迁移",
     "v3.199→v4.42; observation-first; unified events; OTel-native; staged migration"),
    "57-v4-unified-events.html": ("events_full · root observation · 反范式化 · ReplacingMergeTree · core/full 分层读取",
     "events_full; root observation; denormalization; ReplacingMergeTree; core/full reads"),
    "58-python-sdk-v4-otel.html": ("get_client/@observe · OTel context · update_current_span · flush · 实时读取一起迁",
     "get_client/@observe; OTel context; update_current_span; flush; migrate real-time reads too"),
    "59-agent-langchain-v4.html": ("CallbackHandler+手工埋点 · Agent/tool/generation 边界 · State≠trace · context 传播",
     "CallbackHandler + manual spans; agent/tool/generation boundaries; State≠trace; context propagation"),
    "60-v4-evals-real-time.html": ("Observations v2/Metrics v2/Scores v3 · bad case→dataset→experiment→回归",
     "Observations v2 / Metrics v2 / Scores v3; bad case→dataset→experiment→regression"),
    "61-v4-self-hosted-migration.html": ("基础设施先行 · legacy→dual→events_only · backfill · 容量 · 上线检查",
     "upgrade infra first; legacy→dual→events_only; backfill; capacity; cutover checks"),
}

# Optional 「读前 / Before you start」 prerequisite hints: filename -> (zh, en).
# One concise sentence pointing at the lesson(s) that genuinely set this one up;
# lesson references auto-link. Foundational/self-contained lessons are omitted.
PREREQS = {
    "05-life-of-a-trace.html": (
        "先读 第3课 摸清 trace / observation / score 三件套，本课才好把它们串成一条端到端流水线。",
        "Read Lesson 3 to nail down trace / observation / score first; this lesson strings them into one end-to-end pipeline."),
    "06-instrumenting-an-llm-app.html": (
        "先读 第3课 理解三大支柱，本课讲如何用 SDK 把它们埋进真实应用。",
        "Read Lesson 3 on the three pillars; this lesson shows how to instrument them into a real app via the SDK."),
    "07-dual-store-architecture.html": (
        "先读 第2课 的宽事件理念，本课讲为什么要 Postgres + ClickHouse 双存储。",
        "Read Lesson 2 on wide events; this lesson explains why there are two stores — Postgres + ClickHouse."),
    "08-clickhouse-wide-events.html": (
        "先读 第7课 的双存储分工，本课深入 ClickHouse 的三张宽事件表。",
        "Read Lesson 7 on the dual-store split; this lesson dives into ClickHouse's three wide-event tables."),
    "09-postgres-metadata-schema.html": (
        "先读 第7课 知道 Postgres 管配置元数据，本课细看它的 Prisma schema。",
        "Read Lesson 7 — Postgres holds config metadata; this lesson details its Prisma schema."),
    "10-multi-tenancy.html": (
        "先读 第9课 的元数据 schema，本课讲 org → project → environment 如何隔离。",
        "Read Lesson 9 on the metadata schema; this lesson covers org → project → environment isolation."),
    "11-deployment-topology.html": (
        "先读 第7课 的四存储分工，本课讲它们如何在容器拓扑里部署与互相依赖。",
        "Read Lesson 7 on the four stores; this lesson covers how they deploy and depend on each other in the container topology."),
    "12-ingestion-api.html": (
        "先读 第6课 的埋点入口，本课讲数据进平台的第一站——摄取 API。",
        "Read Lesson 6 on instrumentation entry points; this lesson covers the first stop into the platform — the ingestion API."),
    "13-event-types-merge.html": (
        "先读 第12课 摄取 API 与 第3课 的 observation 类型，本课讲事件如何合并。",
        "Read Lesson 12 (ingestion API) and Lesson 3 (observation types); this lesson covers how events merge."),
    "14-ingestion-queue.html": (
        "先读 第12课 摄取 API 与 第7课 里 Redis 的角色，本课讲摄取队列如何削峰。",
        "Read Lesson 12 (ingestion API) and Redis's role in Lesson 7; this lesson covers how the ingestion queue absorbs spikes."),
    "15-ingestion-service.html": (
        "先读 第13课 的合并语义与 第14课 的队列，本课进入合并的心脏 IngestionService。",
        "Read Lesson 13 (merge semantics) and Lesson 14 (the queue); this lesson enters the merge heart, IngestionService."),
    "16-token-counting-cost.html": (
        "先读 第13课 的事件字段，本课讲 token 计数与成本是怎么算出来的。",
        "Read Lesson 13 on event fields; this lesson covers how token counts and cost are computed."),
    "17-clickhouse-writer.html": (
        "先读 第14课 的队列与 第8课 的 CH 表，本课讲 ClickhouseWriter 如何批量落盘。",
        "Read Lesson 14 (the queue) and Lesson 8 (the CH tables); this lesson covers how ClickhouseWriter batches to disk."),
    "18-opentelemetry-ingestion.html": (
        "先读 第12课 的原生摄取 API，本课讲 OpenTelemetry 这条并行入口。",
        "Read Lesson 12 on the native ingestion API; this lesson covers OpenTelemetry as a parallel entry point."),
    "19-media-blob-storage.html": (
        "先读 第12课 摄取与 第7课 里 S3 的角色，本课讲媒体与大块 blob 怎么存。",
        "Read Lesson 12 (ingestion) and S3's role in Lesson 7; this lesson covers how media and large blobs are stored."),
    "20-web-app-architecture.html": (
        "先读 第4课 的 monorepo 全景，本课聚焦 web 这个工作区的内部架构。",
        "Read Lesson 4 on the monorepo map; this lesson zooms into the web workspace's architecture."),
    "21-trpc-backbone.html": (
        "先读 第20课 的 web 架构，本课讲贯穿前后端的 tRPC 骨架。",
        "Read Lesson 20 on the web architecture; this lesson covers the tRPC backbone spanning front and back."),
    "22-repository-layer.html": (
        "先读 第8课 的 CH 表与 第21课 的 tRPC，本课讲仓储层如何从 ClickHouse 读。",
        "Read Lesson 8 (the CH tables) and Lesson 21 (tRPC); this lesson covers how the repository layer reads from ClickHouse."),
    "23-filtering-search-bar.html": (
        "先读 第22课 的仓储层，本课讲过滤、搜索栏与查询如何一步步构建。",
        "Read Lesson 22 on the repository layer; this lesson covers filtering, the search bar, and how queries are built."),
    "24-lists-and-tables.html": (
        "先读 第22课 仓储层与 第23课 的过滤，本课讲列表与表格如何高效渲染。",
        "Read Lesson 22 (repository) and Lesson 23 (filtering); this lesson covers how lists and tables render efficiently."),
    "25-trace-detail-tree.html": (
        "先读 第3课 的 observation 树与 第19课 的媒体存储，本课讲 trace 详情页怎么拼出来。",
        "Read Lesson 3 (the observation tree) and Lesson 19 (media storage); this lesson covers how the trace detail page is assembled."),
    "26-sessions.html": (
        "先读 第25课 的 trace 详情，本课讲多条 trace 聚成的 session 视图。",
        "Read Lesson 25 on trace detail; this lesson covers the session view that groups multiple traces."),
    "27-public-rest-api.html": (
        "先读 第21课 的 tRPC 与 第12课 的摄取，本课讲对外的公共 REST API。",
        "Read Lesson 21 (tRPC) and Lesson 12 (ingestion); this lesson covers the outward-facing public REST API."),
    "28-scoring-model.html": (
        "先读 第3课 的 score 维度，本课深入评分模型的数据结构。",
        "Read Lesson 3 on the score dimensions; this lesson dives into the scoring model's data structures."),
    "29-llm-as-a-judge.html": (
        "先读 第28课 的评分模型，本课讲用 LLM 当裁判自动评分。",
        "Read Lesson 28 on the scoring model; this lesson covers using an LLM as a judge to score automatically."),
    "30-eval-execution-pipeline.html": (
        "先读 第29课 的 LLM 裁判与 第14课 的队列，本课讲 eval 执行流水线。",
        "Read Lesson 29 (LLM judge) and Lesson 14 (the queue); this lesson covers the eval execution pipeline."),
    "31-code-based-evaluation.html": (
        "先读 第30课 的 eval 流水线，本课讲用代码而非 LLM 来评估。",
        "Read Lesson 30 on the eval pipeline; this lesson covers evaluating with code instead of an LLM."),
    "32-human-annotation.html": (
        "先读 第28课 的评分模型，本课讲人工标注如何产出 score。",
        "Read Lesson 28 on the scoring model; this lesson covers how human annotation produces scores."),
    "33-monitors-and-alerting.html": (
        "先读 第28课 的 score 与 第30课 的 eval，本课讲监控器与告警怎么联动。",
        "Read Lesson 28 (scores) and Lesson 30 (eval); this lesson covers how monitors and alerting tie together."),
    "34-datasets-and-items.html": (
        "先读 第3课 的三大支柱，本课讲数据集与数据项的结构。",
        "Read Lesson 3 on the three pillars; this lesson covers the structure of datasets and items."),
    "35-dataset-runs.html": (
        "先读 第34课 的数据集与 第30课 的 eval，本课讲数据集运行与运行项。",
        "Read Lesson 34 (datasets) and Lesson 30 (eval); this lesson covers dataset runs and run items."),
    "36-experiments-and-comparison.html": (
        "先读 第35课 的数据集运行，本课讲多次运行如何对比成实验。",
        "Read Lesson 35 on dataset runs; this lesson covers how multiple runs compare into experiments."),
    "37-prompt-management.html": (
        "先读 第9课 的元数据 schema，本课讲 prompt 如何版本化管理。",
        "Read Lesson 9 on the metadata schema; this lesson covers how prompts are versioned and managed."),
    "38-prompt-serving-caching.html": (
        "先读 第37课 的 prompt 管理，本课讲服务端如何缓存与下发 prompt。",
        "Read Lesson 37 on prompt management; this lesson covers how the server caches and serves prompts."),
    "39-playground-llm-connections.html": (
        "先读 第37课 的 prompt 管理，本课讲 Playground 与 LLM 连接如何配置。",
        "Read Lesson 37 on prompt management; this lesson covers the Playground and LLM connection config."),
    "40-dashboards-and-widgets.html": (
        "先读 第8课 的宽事件表，本课讲仪表盘与 widget 如何聚合展示。",
        "Read Lesson 8 on the wide-event tables; this lesson covers how dashboards and widgets aggregate and display."),
    "41-query-engine.html": (
        "先读 第8课 的 CH 表与 第22课 的仓储层，本课讲通用查询引擎。",
        "Read Lesson 8 (the CH tables) and Lesson 22 (the repository layer); this lesson covers the general query engine."),
    "42-models-and-pricing.html": (
        "先读 第16课 的 token 与成本，本课讲模型与定价表如何配置。",
        "Read Lesson 16 on tokens and cost; this lesson covers how models and the pricing table are configured."),
    "43-cloud-usage-metering.html": (
        "先读 第16课 的成本计算与 第42课 的定价，本课讲云用量计量与花费。",
        "Read Lesson 16 (cost) and Lesson 42 (pricing); this lesson covers cloud usage metering and spend."),
    "44-automations-webhooks.html": (
        "先读 第30课 的执行流水线与 第14课 的队列，本课讲自动化与 webhook（含 SSRF 防护）。",
        "Read Lesson 30 (the execution pipeline) and Lesson 14 (the queue); this lesson covers automations and webhooks (incl. SSRF defense)."),
    "45-slack-and-notifications.html": (
        "先读 第44课 的自动化，本课讲 Slack 与通知这一具体落地。",
        "Read Lesson 44 on automations; this lesson covers Slack and notifications as a concrete landing."),
    "46-analytics-integrations.html": (
        "先读 第7课 的存储与 第19课 的媒体导出，本课讲分析集成（PostHog / S3 等）。",
        "Read Lesson 7 (storage) and Lesson 19 (media export); this lesson covers analytics integrations (PostHog / S3, etc.)."),
    "47-batch-exports-and-actions.html": (
        "先读 第46课 的集成与 第30课 的状态机，本课讲批量导出与批量操作（幂等）。",
        "Read Lesson 46 (integrations) and Lesson 30 (the state machine); this lesson covers batch exports and actions (idempotency)."),
    "48-auth-and-sessions.html": (
        "先读 第20课 的 web 架构，本课讲鉴权与会话（NextAuth / JWT）。",
        "Read Lesson 20 on the web architecture; this lesson covers auth and sessions (NextAuth / JWT)."),
    "49-rbac-apikeys-scim.html": (
        "先读 第48课 的鉴权与 第10课 的多租户，本课讲 RBAC、API key 与 SCIM。",
        "Read Lesson 48 (auth) and Lesson 10 (multi-tenancy); this lesson covers RBAC, API keys, and SCIM."),
    "50-open-core-and-entitlements.html": (
        "先读 第10课 的多租户，本课讲开源核与商业权益的边界。",
        "Read Lesson 10 on multi-tenancy; this lesson covers the open-core / commercial entitlement boundary."),
    "51-self-observability-and-config.html": (
        "先读 第18课 的 OTel 摄取，本课讲 Langfuse 如何自我观测与配置。",
        "Read Lesson 18 on OTel ingestion; this lesson covers how Langfuse observes and configures itself."),
    "52-data-lifecycle-and-deletion.html": (
        "先读 第7课 的四存储与 第19课 的媒体，本课讲数据保留期与跨存储删除。",
        "Read Lesson 7 (the four stores) and Lesson 19 (media); this lesson covers retention and cross-store deletion."),
    "53-build-test-dev-workflow.html": (
        "先读 第4课 的 monorepo 全景，本课讲构建、测试与开发流。",
        "Read Lesson 4 on the monorepo map; this lesson covers the build, test, and dev workflow."),
    "54-design-themes-synthesis.html": (
        "先回顾 第2课 的宽事件与 第7课 的双存储两大基石，本课把六大设计专题综合起来。",
        "Revisit Lesson 2 (wide events) and Lesson 7 (dual storage); this lesson synthesizes the six design themes."),
    "55-capstone-trace-life.html": (
        "先读 第5课 的一生鸟瞰，本课跟一条 trace 走完贯穿 55 课的完整旅程。",
        "Read Lesson 5 for the bird's-eye life; this capstone follows one trace through the full journey across all 55 lessons."),
    "56-v4-architecture-delta.html": (
        "先读 第55课 串起 v3.199.0 的完整全景，本部分再专门补 v4 架构差异与迁移。",
        "Read Lesson 55 to connect the v3.199.0 architecture first; Part 12 then focuses on the v4 delta and migration."),
    "57-v4-unified-events.html": (
        "先读 第56课 的 v4 总览，本课深入统一 events 与 root observation。",
        "Read Lesson 56 for the v4 overview; this lesson dives into unified events and root observations."),
    "58-python-sdk-v4-otel.html": (
        "先读 第56课 与 第18课，本课把 OTel 从服务端入口延伸到 Python SDK v4。",
        "Read Lesson 56 and Lesson 18; this lesson extends OTel from server ingestion into the Python SDK v4."),
    "59-agent-langchain-v4.html": (
        "先读 第58课 的 OTel context，本课再讲 LangChain/Agent 的观测边界与上下文传播。",
        "Read Lesson 58 on OTel context; this lesson applies it to LangChain/Agent boundaries and propagation."),
    "60-v4-evals-real-time.html": (
        "先读 第56课 的新数据模型，并回顾 第28课 与 第34课 的 score/dataset，本课把它们串成 v4 质量闭环。",
        "Read Lesson 56, then revisit Lesson 28 and Lesson 34 on scores/datasets; this lesson connects them into the v4 quality loop."),
    "61-v4-self-hosted-migration.html": (
        "先读 第56课 的迁移全景与 第11课 的部署拓扑，本课落到自托管升级与上线步骤。",
        "Read Lesson 56 for the migration map and Lesson 11 for deployment topology; this lesson turns them into a self-hosted rollout."),
}

# Extra search keywords (not shown) so trimming the TOC subtitles above doesn't
# drop searchable jargon. Indexed into each TOC entry's hidden data-keywords so
# the index search still recalls these terms. Filename -> space-separated terms.
SEARCH_KEYWORDS = {
    "15-ingestion-service.html": "overwriteObject immutableEntityKeys mergeWith",
    "16-token-counting-cost.html": "matchPricingTier tokenizerId provided computed usage cost",
    "18-opentelemetry-ingestion.html": "OTLP protobuf gen_ai adapter span",
    "19-media-blob-storage.html": "presigned content-addressed dedup blob_storage_file_log MEDIA_REFERENCE_PATTERN",
    "21-trpc-backbone.html": "enforceUserIsAuthedAndProjectMember protectedProjectProcedure middleware RBAC",
    "22-repository-layer.html": "queryClickhouse log_comment backoff look-back streaming",
    "23-filtering-search-bar.html": "FilterState injection parameterized createFilterFromFilterState AI filter",
    "24-lists-and-tables.html": "getTracesTableGeneric joinTableCoreAndMetrics FINAL conditional JOIN URL state",
    "25-trace-detail-tree.html": "byIdWithObservationsAndScores includeIO lazy verbosity latency",
    "28-scoring-model.html": "ScoreSchema dataType NUMERIC CATEGORICAL BOOLEAN scoreConfig comparable",
    "29-llm-as-a-judge.html": "LLM-as-a-judge variable mapping structured output reasoning EVAL",
    "30-eval-execution-pipeline.html": "createEvalJobs JobExecution dedup sampling delay state machine",
    "31-code-based-evaluation.html": "dispatcher sandbox no-network Lambda vm CODE_EVAL timeout SOURCE_TOO_LARGE",
    "32-human-annotation.html": "AnnotationQueue scoreConfigIds soft lock ground truth ANNOTATION",
    "33-monitors-and-alerting.html": "monitor severity OK WARNING ALERT threshold WebhookQueue computeSeverity",
    "34-datasets-and-items.html": "dataset SCD Type 2 validFrom validTo sourceTraceId bitemporal reproducible",
    "35-dataset-runs.html": "dataset run run item agg_scores_avg dataset-run-item-upsert ReplacingMergeTree",
    "36-experiments-and-comparison.html": "experiment baseline delta comparison createExperimentJobClickhouse",
    "37-prompt-management.html": "prompt label production version immutable PromptDependency protected labels",
    "38-prompt-serving-caching.html": "PromptService Redis read-through epoch invalidation TTL cache dependency",
    "39-playground-llm-connections.html": "Playground fetchLLMCompletion AES-256-GCM authTag LlmSchema LlmTool LlmApiKeys",
    "40-dashboards-and-widgets.html": "dashboard widget DashboardWidget chartType view dimensions metrics",
    "41-query-engine.html": "query engine QueryBuilder semantic layer dataModel parameters view version",
    "42-models-and-pricing.html": "matchPattern matchPricingTier pricingTiers default-model-prices tokenizerId",
    "43-cloud-usage-metering.html": "metering Stripe exactly-once cronJobs meterEvents observation count cloudSpendAlert",
    "44-automations-webhooks.html": "automation Trigger Action SSRF DNS-rebinding fail-closed HMAC x-langfuse-signature webhook 169.254.169.254",
    "45-slack-and-notifications.html": "Slack OAuth bot token Block Kit notificationQueue WebClient encryption",
    "46-analytics-integrations.html": "PostHog Mixpanel S3 fan-out lastSyncAt watermark incremental sync streaming export",
    "47-batch-exports-and-actions.html": "batch export batch action idempotent CHUNK_SIZE getSignedUrl streaming state machine",
    "48-auth-and-sessions.html": "NextAuth bcrypt SSO JWT session timing attack CredentialsProvider PrismaAdapter",
    "49-rbac-apikeys-scim.html": "RBAC scope projectRoleAccessRights API key sha256 bcrypt SCIM throwIfNoProjectAccess",
    "50-open-core-and-entitlements.html": "open core entitlement entitlementAccess hasEntitlement plan EE license oss",
    "51-self-observability-and-config.html": "dogfooding OTel instrumentAsync trace_id winston Zod env validation fail-fast",
    "52-data-lifecycle-and-deletion.html": "data retention deletion retentionDays cascade background migration cross-store",
    "53-build-test-dev-workflow.html": "monorepo pnpm Turbo cache dependsOn dx seed turborepo CI",
    "54-design-themes-synthesis.html": "wide events immutability async dual storage multi-tenancy cost ReplacingMergeTree",
    "55-capstone-trace-life.html": "capstone trace life seven stations closed loop self-observability projectId",
    "56-v4-architecture-delta.html": "v4 migration observation-first unified events root observation OpenTelemetry OTel v4Transition dual events_only",
    "57-v4-unified-events.html": "events_full events_core is_app_root parent_span_id ReplacingMergeTree denormalization full-text",
    "58-python-sdk-v4-otel.html": "python sdk v4 get_client observe start_as_current_observation update_current_span flush OTLP context",
    "59-agent-langchain-v4.html": "LangChain LangGraph CallbackHandler propagate_attributes agent tool generation state contextvars",
    "60-v4-evals-real-time.html": "Observations API v2 Metrics API v2 Scores API v3 evaluator dataset experiment regression bad case",
    "61-v4-self-hosted-migration.html": "self-hosted migration docker compose backfill ClickHouse Redis Postgres legacy dual events_only rollback capacity",
}


def index_page(lesson_prefix="lessons/"):
    """Build the bilingual index (table of contents). Always relative links."""
    order = []   # ordered list of (part_zh, part_en)
    groups = {}  # part_zh -> [(num, fname, title_zh, title_en), ...]
    for i, (fname, tz, te, pz, pe) in enumerate(PAGES):
        if pz not in groups:
            groups[pz] = []
            order.append((pz, pe))
        groups[pz].append((i + 1, fname, tz, te))

    blocks = []
    for pz, pe in order:
        blocks.append(f'<div class="toc-part">{bi(esc(pz), esc(pe))}</div>')
        for num, fname, tz, te in groups[pz]:
            sz, se = SUBTITLES.get(fname, ("", ""))
            kw = SEARCH_KEYWORDS.get(fname, "")
            blocks.append(
                f'<a href="{lesson_prefix}{fname}" data-keywords="{esc(kw)}"><span class="n">{num:02d}</span>'
                f'<span class="tt"><span class="lang-zh">{esc(tz)}</span>'
                f'<span class="lang-en">{esc(te)}</span></span>'
                f'<span class="ts"><span class="lang-zh">{esc(sz)}</span>'
                f'<span class="lang-en">{esc(se)}</span></span></a>'
            )
    toc = "\n".join(blocks)
    total = len(PAGES)
    nparts = len(order)

    title_tag = "Langfuse 图解教程 · 看懂 LLM 可观测性平台内部 / Langfuse Visual Guide"
    desc = ("从零理解整个 Langfuse LLM 工程平台的中英双语图解教程：宏观结构、数据模型、双存储、"
            "摄取链路、查询链路、评估、数据集、Prompt、仪表盘、平台与运维，每课配真实源码对应与设计取舍。")

    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-lang="zh"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{LANG_BOOT}
<title>{esc(title_tag)}</title>
{head_meta(title_tag, desc, og_type="website")}
<style>{CSS}</style>
</head><body>
<div class="topbar">
  <div class="topbar-inner">
    <span class="home">🪢 <b class="lang-zh">Langfuse 图解教程</b><b class="lang-en">Langfuse Visual Guide</b></span>
    <span class="pill"><span class="lang-zh">共 {total} 课 · {nparts} 个部分</span><span class="lang-en">{total} lesson{'' if total == 1 else 's'} · {nparts} part{'' if nparts == 1 else 's'}</span></span>
    <a class="pill" href="glossary.html"><span class="lang-zh">📖 术语表</span><span class="lang-en">📖 Glossary</span></a>
    <button class="langtoggle" onclick="lvgToggleLang()" aria-label="switch language"><span class="lang-zh">EN</span><span class="lang-en">中</span></button>
  </div>
  <div class="progress"><span style="width:100%"></span></div>
</div>
<div class="wrap">
  <div class="hero index">
    <div class="part">{bi("面向工程师 · 从第一性原理到源码", "For engineers · first principles to source")}</div>
    <h1><span class="lang-zh">用图解读懂整个 Langfuse</span><span class="lang-en">Understand all of Langfuse, visually</span></h1>
    <p class="lead"><span class="lang-zh">这套教程带你<strong>层层深入</strong>：先建立<strong>宏观全景</strong>与<strong>可观测性 2.0 / 宽事件</strong>基础，看懂 <strong>trace/observation/score 数据模型</strong>与 <strong>Postgres+ClickHouse 双存储</strong>，
    然后顺着数据走一遍<strong>摄取（写）</strong>与<strong>查询（读）</strong>两条链路，再逐个拆解<strong>评估</strong>·<strong>数据集</strong>·<strong>Prompt</strong>·<strong>仪表盘</strong>等子系统，最后讲透<strong>鉴权与权限</strong>·<strong>运维</strong>与<strong>如何贡献</strong>。每课配真实源码对应、手绘图与设计取舍。</span>
    <span class="lang-en">A layered tour: build the <strong>big picture</strong> and the <strong>Observability 2.0 / wide-event</strong> foundation first, understand the <strong>trace/observation/score data model</strong> and the <strong>Postgres + ClickHouse dual store</strong>,
    then follow the data through the <strong>ingestion (write)</strong> and <strong>query (read)</strong> paths, take apart the <strong>evaluation</strong>, <strong>datasets</strong>, <strong>prompt</strong> and <strong>dashboard</strong> subsystems, and finally master <strong>auth &amp; RBAC</strong>, <strong>operations</strong> and <strong>how to contribute</strong>. Every lesson maps to real source, with hand-drawn diagrams and design trade-offs.</span></p>
    <div class="legend">
      <span><i style="background:var(--blue)"></i>{bi("宏观理解", "Big picture")}</span>
      <span><i style="background:var(--purple)"></i>{bi("细节 / 源码", "Details / source")}</span>
      <span><i style="background:var(--amber)"></i>{bi("生活类比", "Analogy")}</span>
      <span><i style="background:var(--accent)"></i>{bi("关键要点", "Key points")}</span>
    </div>
    <p style="margin:.8rem 0 0;color:var(--faint);font-size:.8rem">{bi("📌 对照 langfuse/langfuse 仓库真实源码核实 · 源码引用以“文件 + 符号名/行号”标注（行号随上游更新而变）", "📌 Verified against the real langfuse/langfuse source; references cite file + symbol/line (line numbers drift upstream)")}</p>
  </div>
  <div class="toc-search">
    <input id="q" type="search" placeholder="🔎 搜索课程 / Search lessons" autocomplete="off" aria-label="search">
    <span class="qcount" id="qcount"></span>
  </div>
  <div class="toc">{toc}</div>
  <div class="toc-empty" id="tocempty">{bi("没有匹配的课程，换个关键词试试。", "No matching lessons, try another keyword.")}</div>
  <p style="margin:2.4rem 0 0;color:var(--faint);font-size:.78rem;text-align:center">{bi("本项目是第三方、非官方的学习材料，不含 Langfuse 源码（仅引用少量标注来源的片段）；Langfuse 由其作者以 MIT 许可发布（部分企业版功能除外）。", "Third-party, unofficial learning material; contains no Langfuse source code beyond small, cited snippets. Langfuse is MIT-licensed by its authors (except some enterprise features).")}</p>
</div>
<script>{LANG_JS}</script>
<script>{SEARCH_JS}</script>
</body></html>"""


# ---- glossary / concept index ----------------------------------------------
# (term_zh, term_en, def_zh, def_en, lesson_filename). Grouped by the lesson's
# Part at render time. Each term links to the lesson that introduces it.
GLOSSARY = [
    ("宽事件", "wide event", "把一次操作的全部上下文(输入/输出/模型/用量/耗时)塞进一行又宽又富的事件，保住高基数以事后任意切片", "one row holding all of an operation's context (input/output/model/usage/latency), preserving high cardinality to slice any way later", "02-observability-2-and-wide-events.html"),
    ("可观测性 2.0", "Observability 2.0", "以宽事件为唯一分析单位、记录一切，取代 metrics/logs/traces 三件套", "treat wide events as the single analytical unit, recording everything, replacing the metrics/logs/traces trio", "02-observability-2-and-wide-events.html"),
    ("unknown unknowns", "unknown unknowns", "事前没想到要问的问题；宽事件+高基数让你事后仍能回答", "questions you didn't know to ask; wide events + high cardinality let you answer them later", "02-observability-2-and-wide-events.html"),
    ("trace", "trace", "一次完整调用的根、关联句柄，挂载多个 observation", "the root of one full call, a correlation handle holding observations", "03-three-pillars-deep.html"),
    ("observation", "observation", "trace 里的一步(SPAN/EVENT/GENERATION… 共 10 型)，真正承载数据", "one step in a trace (SPAN/EVENT/GENERATION…, 10 types), the actual data carrier", "03-three-pillars-deep.html"),
    ("score", "score", "评估的原子单位(name/value/dataType/source)，挂在 trace 或 observation 上", "the atomic unit of evaluation (name/value/dataType/source), attached to a trace or observation", "03-three-pillars-deep.html"),
    ("窄腰依赖", "narrow waist", "web/worker/ee 都依赖 shared，shared 不反向依赖——单向收口", "web/worker/ee depend on shared, shared depends on none — a one-way waist", "04-project-map-monorepo.html"),
    ("事件信封", "event envelope", "摄取事件的统一外壳(id/type/timestamp/body)，body 按类型判别联合", "the unified wrapper of an ingestion event (id/type/timestamp/body); body is a discriminated union", "06-instrumenting-an-llm-app.html"),
    ("OLTP vs OLAP", "OLTP vs OLAP", "事务型(精确单条+强一致, Postgres) vs 分析型(海量扫描聚合, ClickHouse)", "transactional (precise single-row + strong consistency, Postgres) vs analytical (massive scan + aggregation, ClickHouse)", "07-dual-store-architecture.html"),
    ("控制面 / 数据面", "control plane / data plane", "Postgres 存配置元数据(控制面)，ClickHouse 存遥测洪流(数据面)", "Postgres holds config metadata (control plane), ClickHouse holds the telemetry flood (data plane)", "07-dual-store-architecture.html"),
    ("ReplacingMergeTree", "ReplacingMergeTree", "ClickHouse 引擎：同主键后写覆盖先写，查询时合并去重保留最新", "a ClickHouse engine: later write of the same key wins, dedup-merge at query keeping the latest", "08-clickhouse-wide-events.html"),
    ("排序键", "ordering key", "ClickHouse 表的物理排序(project_id 打头)，决定查询能少扫多少", "a table's physical sort (project_id first) deciding how little a query scans", "08-clickhouse-wide-events.html"),
    ("多租户", "multi-tenancy", "每张表/查询/消息都带 projectId；project 硬隔离、environment 软切片", "projectId on every table/query/message; project = hard isolation, environment = soft slice", "10-multi-tenancy.html"),
    ("project_id", "project_id", "贯穿全栈的硬隔离键，焊进 ClickHouse 排序键前缀", "the hard isolation key threaded through the stack, welded into the CH ordering-key prefix", "10-multi-tenancy.html"),
    ("摄取队列", "ingestion queue", "Redis+BullMQ 队列放 fileKey 指针、本体在 S3，是 web(快)与 worker(慢)的交接点", "a Redis+BullMQ queue holding a fileKey pointer (body in S3), the handoff between web and worker", "14-ingestion-queue.html"),
    ("分片", "sharding", "按 projectId-eventBodyId 哈希取模把队列摊成 N 条，同实体永远同 shard", "hash-mod splits the queue into N shards; one entity always lands on the same shard", "14-ingestion-queue.html"),
    ("IngestionService / mergeAndWrite", "IngestionService / mergeAndWrite", "把同一实体的多条事件 merge 成一条记录，再交批写器", "merges an entity's multiple events into one record, then hands it to the batch writer", "15-ingestion-service.html"),
    ("ClickhouseWriter", "ClickhouseWriter", "单例批写器：每表内存队列，攒满或定时批量 INSERT", "a singleton batch writer: per-table memory queue, bulk INSERT on size or timer", "17-clickhouse-writer.html"),
    ("OTLP", "OTLP", "OpenTelemetry 的传输协议；适配器把 span 映射成原生摄取事件", "OpenTelemetry's wire protocol; an adapter maps spans to native ingestion events", "18-opentelemetry-ingestion.html"),
    ("presigned URL", "presigned URL", "服务端签发的有时效直传/下载地址，让大块负载绕过应用层", "a server-signed time-limited upload/download URL letting bulky payloads bypass the app layer", "19-media-blob-storage.html"),
    ("内容寻址去重", "content-addressed dedup", "按 sha256 指纹判同一性，相同字节只存一份", "identity by sha256 fingerprint; identical bytes are stored once", "19-media-blob-storage.html"),
    ("tRPC", "tRPC", "前后端共享类型的内部 API；改后端字段，前端编译即报错", "a type-shared internal API; change a backend field and the front-end compile breaks", "21-trpc-backbone.html"),
    ("queryClickhouse", "queryClickhouse", "统一执行器：给每条查询套 OTel/标签/退避重试/资源错误包装", "the unified executor wrapping every query with OTel/tags/backoff-retry/error-wrap", "22-repository-layer.html"),
    ("回看时间窗", "look-back window", "利用观测集中在 trace 之后的有界时间，避免跨表全表扫", "exploit that observations cluster in a bounded window after the trace, avoiding full scans", "22-repository-layer.html"),
    ("FilterState", "FilterState", "UI 过滤的中间契约，编译成参数化的 ClickHouse/Postgres SQL", "the intermediate contract for UI filters, compiled to parameterized ClickHouse/Postgres SQL", "23-filtering-search-bar.html"),
    ("RBAC", "RBAC", "角色→scope 映射；判权限问角色是否含该 scope，前端隐藏+后端强制", "role→scope mapping; check the role contains the scope, front-end hide + back-end enforce", "21-trpc-backbone.html"),
    ("session", "session", "traces 按 session_id 分组的派生视图，非新实体、永远一致", "a derived view of traces grouped by session_id, not a new entity, always consistent", "26-sessions.html"),
    ("dataType", "dataType", "score 的刻度：NUMERIC / CATEGORICAL / BOOLEAN(锁死的特殊分类)", "a score's scale: NUMERIC / CATEGORICAL / BOOLEAN (a locked special category)", "28-scoring-model.html"),
    ("score config", "score config", "某 name 的 schema：声明刻度与约束、强制校验以保证可比", "a name's schema: declares scale & constraints, enforced for comparability", "28-scoring-model.html"),
    ("LLM-as-a-judge", "LLM-as-a-judge", "用一个 LLM 给另一个的输出评分，结构化输出 {score,reasoning}", "use one LLM to score another's output, with structured output {score,reasoning}", "29-llm-as-a-judge.html"),
    ("JobExecution", "JobExecution", "eval 工单的状态机 PENDING→COMPLETED/ERROR/CANCELLED/DELAYED", "the eval ticket's state machine PENDING→COMPLETED/ERROR/CANCELLED/DELAYED", "30-eval-execution-pipeline.html"),
    ("沙箱", "sandbox", "跑用户评估器代码的隔离环境：禁网络、限大小、限时", "the isolated environment running user eval code: no network, size caps, timeout", "31-code-based-evaluation.html"),
    ("标注队列", "annotation queue", "绑一组 scoreConfigIds 的人工评审任务，含待评 item 与 5 分钟软锁", "a human-review task binding scoreConfigIds, with items to review + a 5-minute soft lock", "32-human-annotation.html"),
    ("monitor / severity", "monitor / severity", "把质量监测从拉变推：越阈值告警，severity 状态机只在变化时 emit", "turn quality monitoring from pull to push: alert on threshold, severity emits only on change", "33-monitors-and-alerting.html"),
    ("数据集", "dataset", "一组测试用例(input/expectedOutput/metadata)，题可从真实 trace 提拔", "a set of test cases (input/expectedOutput/metadata), promotable from real traces", "34-datasets-and-items.html"),
    ("SCD Type 2", "SCD Type 2", "数据项用 validFrom/validTo 双时态版本化；改题=关旧版+插新版", "bitemporal item versioning via validFrom/validTo; editing = close old + insert new", "34-datasets-and-items.html"),
    ("dataset run", "dataset run", "某配置在整套题上的一次「考试」，run item 钉住题目版本", "one 'exam' of a config over the whole set; run items pin the question version", "35-dataset-runs.html"),
    ("实验对比", "experiment comparison", "prompt×数据集×模型服务端自动跑，靠 baseline+增量做决策", "prompt × dataset × model run server-side, decided via baseline + deltas", "36-experiments-and-comparison.html"),
    ("prompt label", "prompt label", "指向某 prompt 版本的可移动指针(production/latest)，零部署发布/回滚", "a movable pointer to a prompt version (production/latest), zero-deploy release/rollback", "37-prompt-management.html"),
    ("epoch 失效", "epoch invalidation", "缓存 key 嵌项目级令牌；改动只转令牌、旧 key 按 TTL 过期(O(1) 不漏)", "the cache key embeds a project epoch token; rotate to invalidate, old keys expire by TTL (O(1))", "38-prompt-serving-caching.html"),
    ("fetchLLMCompletion", "fetchLLMCompletion", "Playground、评估、实验共用的统一 LLM 调用引擎", "the one LLM-call engine shared by the Playground, evaluation, and experiments", "39-playground-llm-connections.html"),
    ("AES-256-GCM", "AES-256-GCM", "认证加密：authTag 防篡改、随机 IV，用于存 provider API key", "authenticated encryption (authTag anti-tamper, random IV) used to store provider API keys", "39-playground-llm-connections.html"),
    ("widget / 查询引擎", "widget / query engine", "声明式查询(view+dimensions+metrics+filters)，引擎编译成 ClickHouse SQL", "a declarative query (view+dimensions+metrics+filters) the engine compiles to ClickHouse SQL", "41-query-engine.html"),
    ("语义层", "semantic layer", "把逻辑名(如 totalCost)映射到真实 SQL 列/表达式的字典", "a dictionary mapping logical names (e.g. totalCost) to real SQL columns/expressions", "41-query-engine.html"),
    ("matchPattern / matchPricingTier", "matchPattern / matchPricingTier", "一条正则统一各家模型命名 + 按用量选中价目档", "one regex unifies model naming + tier selection picks the price by usage", "42-models-and-pricing.html"),
    ("exactly-once", "exactly-once", "计量必须不重不漏：cronJobs 锁 + 整点对齐 + 20 分钟兜底接管", "metering must neither double nor miss: cronJobs lock + hour-align + 20-min takeover", "43-cloud-usage-metering.html"),
    ("自动化 Trigger→Action", "automation Trigger→Action", "事件触发器(何时)绑动作(webhook/Slack/GitHub，做什么)", "an event Trigger (when) bound to an Action (webhook/Slack/GitHub, what)", "44-automations-webhooks.html"),
    ("SSRF", "SSRF", "服务器被诱导请求内网/元数据接口；纵深防御+fail-closed+请求时校验真实 IP", "the server tricked into hitting internal/metadata endpoints; defended in depth + fail-closed + real-IP check at request time", "44-automations-webhooks.html"),
    ("fan-out", "fan-out", "一个调度员按项目扇出 N 个处理任务(评估/集成/删除)", "one scheduler fans out N per-project processing jobs (eval/integration/deletion)", "46-analytics-integrations.html"),
    ("增量水位", "watermark (lastSyncAt)", "只同步上次之后的新数据，带缓冲与按日切块", "sync only data since last time, with a buffer and day-sized chunks", "46-analytics-integrations.html"),
    ("幂等", "idempotency", "同一操作重复执行不出错、不翻倍副作用——批量操作的铁律", "repeating an operation neither errors nor doubles side effects — the iron rule for batch actions", "47-batch-exports-and-actions.html"),
    ("JWT session", "JWT session", "无状态自带签名身份的会话，本地验签利于多实例水平扩展", "a stateless self-signed session; local verification scales horizontally across instances", "48-auth-and-sessions.html"),
    ("API key 两层哈希", "API key two-tier hash", "fastHashedSecretKey(sha256 快查) + hashedSecretKey(bcrypt 安全)", "fastHashedSecretKey (sha256 for fast lookup) + hashedSecretKey (bcrypt for security)", "49-rbac-apikeys-scim.html"),
    ("SCIM", "SCIM", "让 Okta/AzureAD 自动开通/注销 Langfuse 用户的标准协议(EE)", "a standard protocol letting Okta/AzureAD auto-provision/deprovision users (EE)", "49-rbac-apikeys-scim.html"),
    ("entitlement", "entitlement", "运行时功能门控：entitlementAccess 总表 + hasEntitlement 一道闸", "runtime feature gating: one entitlementAccess table + one hasEntitlement gate", "50-open-core-and-entitlements.html"),
    ("开源核", "open core", "全代码开放(含企业功能)，免费/付费的区别在运行时能否启用", "all code is open (incl. enterprise); free vs paid is runtime enablement, not code presence", "50-open-core-and-entitlements.html"),
    ("dogfooding / instrumentAsync", "dogfooding / instrumentAsync", "Langfuse 用同一套 OTel 观测自己；instrumentAsync 是 span 包装器", "Langfuse observes itself with the same OTel; instrumentAsync is a span wrapper", "51-self-observability-and-config.html"),
    ("配置即校验", "config-as-validation", "所有 env 过 Zod 启动即校验：fail-fast + 类型安全 + server/client 边界", "all env validated by Zod at boot: fail-fast + type-safe + server/client boundary", "51-self-observability-and-config.html"),
    ("数据保留", "data retention", "按 retentionDays 自动跨三存储清旧数据(EE)", "auto-delete old data across all three stores by retentionDays (EE)", "52-data-lifecycle-and-deletion.html"),
    ("后台迁移", "background migration", "给亿万行的表在线做手术，state 可断点续传、单 worker 锁", "online schema surgery on billions of rows; state is resumable, single-worker lock", "52-data-lifecycle-and-deletion.html"),
    ("monorepo / Turbo", "monorepo / Turbo", "一个仓库 + Turbo 内容哈希缓存，只重建真正改了的包", "one repo + Turbo content-hash cache rebuilding only the packages that actually changed", "53-build-test-dev-workflow.html"),
    ("不可变", "immutability", "事件写入后基本不动；改＝追加新行 + 查询时去重保留最新（ReplacingMergeTree FINAL），避开高规模更新的隐藏成本", "events barely change once written; modify = append a new row + dedup-keep-latest at query (ReplacingMergeTree FINAL), avoiding the hidden cost of updates at scale", "08-clickhouse-wide-events.html"),
    ("异步", "async", "摄取请求只落 S3 + 入 Redis 队列就返回，重活交给后台 worker——削峰、解耦、可重试", "the ingestion request just lands in S3 + enqueues to Redis then returns; heavy work goes to a background worker — peak-shaving, decoupling, retryable", "05-life-of-a-trace.html"),
]


def glossary_page(lesson_prefix="lessons/"):
    """Bilingual glossary / concept index. Terms grouped by the lesson's Part,
    each linking to the lesson that introduces it. Reuses GLOSSARY_JS (per-lang
    table.t row filtering) for search."""
    # fname -> (lesson_num, part_zh, part_en); part order follows PAGES.
    pmeta = {}
    part_order = []
    for i, (fname, tz, te, pz, pe) in enumerate(PAGES):
        pmeta[fname] = (i + 1, pz, pe)
        if (pz, pe) not in part_order:
            part_order.append((pz, pe))

    def lang_block(lang):
        ids = ("qglzh", "qglzhc", "qglzhe") if lang == "zh" else ("qglen", "qglenc", "qglene")
        ph = "🔎 搜索术语 / 概念…" if lang == "zh" else "🔎 Search a term / concept…"
        empty = "没有匹配的术语，换个关键词。" if lang == "zh" else "No matching term, try another keyword."
        out = [f'<div class="lang-{lang}">']
        out.append(
            f'<div class="toc-search"><input id="{ids[0]}" type="search" placeholder="{esc(ph)}" '
            f'autocomplete="off" aria-label="search glossary"><span class="qcount" id="{ids[1]}"></span></div>'
        )
        for pz, pe in part_order:
            terms = [g for g in GLOSSARY if pmeta.get(g[4], (0,))[0] and pmeta[g[4]][1] == pz]
            if not terms:
                continue
            terms.sort(key=lambda g: pmeta[g[4]][0])
            out.append(f"<h2>{esc(pz if lang == 'zh' else pe)}</h2>")
            rows = []
            for tz, te, dz, de, fname in terms:
                num = pmeta[fname][0]
                term = esc(tz if lang == "zh" else te)
                desc = esc(dz if lang == "zh" else de)
                rows.append(
                    f'<tr><td><b>{term}</b></td><td>{desc}</td>'
                    f'<td><a class="xref" href="{lesson_prefix}{fname}">L{num:02d}</a></td></tr>'
                )
            head = ("术语", "一句话定义", "课") if lang == "zh" else ("Term", "One-line definition", "Lesson")
            out.append(
                f'<table class="t"><tr><th>{head[0]}</th><th>{head[1]}</th><th>{head[2]}</th></tr>'
                + "".join(rows) + "</table>"
            )
        out.append(f'<div class="toc-empty" id="{ids[2]}">{esc(empty)}</div>')
        out.append("</div>")
        return "\n".join(out)

    body = lang_block("zh") + "\n" + lang_block("en")
    title_tag = "术语表 / Glossary · Langfuse 图解教程"
    desc = "Langfuse 图解教程的术语表：核心概念一句话定义 + 跳转到对应课程。"
    nterms = len(GLOSSARY)
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-lang="zh"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{LANG_BOOT}
<title>{esc(title_tag)}</title>
{head_meta(title_tag, desc, og_type="website")}
<style>{CSS}</style>
</head><body>
<div class="topbar">
  <div class="topbar-inner">
    <a class="home" href="index.html">🪢 <b class="lang-zh">Langfuse 图解教程</b><b class="lang-en">Langfuse Visual Guide</b></a>
    <span class="pill"><span class="lang-zh">术语表 · {nterms} 个概念</span><span class="lang-en">Glossary · {nterms} concepts</span></span>
    <button class="langtoggle" onclick="lvgToggleLang()" aria-label="switch language"><span class="lang-zh">EN</span><span class="lang-en">中</span></button>
  </div>
</div>
<div class="wrap">
  <div class="hero">
    <div class="part">{bi("术语表 / 概念索引", "Glossary / Concept index")}</div>
    <h1><span class="lang-zh">核心概念速查</span><span class="lang-en">Core concepts at a glance</span></h1>
    <p class="lead">{bi("每个核心概念一句话定义，点右侧「课」跳到首次讲解它的那一课。用上方搜索框过滤。", "A one-line definition for each core concept; click the lesson on the right to jump to where it's introduced. Filter with the search box above.")}</p>
  </div>
  {body}
  <div class="footnav"><a class="prev" href="index.html"><div class="dir">{bi("← 返回", "← Back")}</div><div class="ttl">{bi("目录", "Contents")}</div></a></div>
</div>
<script>{LANG_JS}</script>
<script>{GLOSSARY_JS}</script>
</body></html>"""
