# Langfuse Visual Guide / Langfuse 图解学习指南

A visual, bilingual (English + 中文) guide to the **internals of
[Langfuse](https://github.com/langfuse/langfuse)** — the open-source **LLM engineering / observability
platform** — that takes you from *"what is LLM observability"* all the way to *"how the ingestion /
query paths work in the code"* and *"how to build, test and contribute a PR"*.

**📖 Read it online: <https://verdenmax.github.io/langfuse-visual-guide/>**

> **Disclaimer:** This is **third-party, unofficial** educational material *about* Langfuse. It contains
> **no Langfuse source code** beyond small, cited snippets; it explains Langfuse by quoting short,
> attributed excerpts. Langfuse itself is **MIT**-licensed by its own authors (except some enterprise
> features).

> **Status:** **complete** — all **12 parts / 61 lessons** authored, source-verified per milestone,
> and gate-checked (0 errors). See `docs/superpowers/specs/` for the design spec and
> `docs/superpowers/plans/` for the roadmap and per-milestone audit logs.

Part 12 is a **v4 supplement** pinned on 2026-09-23 to Langfuse Server **v4.42.0** and Python SDK **v4.15.4**. The original L01–L55 source tour remains intentionally tied to its v3.199.0-era baseline so the architectural delta stays explicit.

Every lesson is self-contained, embeds both languages (toggle in the page), and uses hand-drawn
diagrams, worked-example traces, real (cited) code, and a short self-test quiz.

---

## What it covers

The guide is organized into twelve parts that build up along the data lifecycle:

| Part | Topic | Lessons |
| --- | --- | --- |
| 1 | 宏观全景 — what Langfuse is, the data model, the monorepo, life of a trace | L01–05 |
| 2 | 前置基础 — instrumentation, dual store, ClickHouse wide events, Postgres schema, multi-tenancy, deployment | L06–11 |
| 3 | 摄取链路 — the ingestion (write) path: API, queue, IngestionService, cost, ClickhouseWriter, OTel, media | L12–19 |
| 4 | 查询链路 — the read path: web app, tRPC, repositories, filtering/search, tables, trace detail, sessions, public API | L20–27 |
| 5 | 评估与评分 — scoring model, LLM-as-judge, eval pipeline, code evals, human annotation, monitors | L28–33 |
| 6 | 数据集与实验 — datasets, runs, experiments | L34–36 |
| 7 | Prompt 管理与 Playground — prompt management, serving/caching, playground & LLM connections | L37–39 |
| 8 | 仪表盘·指标·成本 — dashboards/widgets, the query engine, models/pricing, usage metering | L40–43 |
| 9 | 自动化与集成 — automations/webhooks, Slack/notifications, analytics integrations, batch exports | L44–47 |
| 10 | 平台与运维 — auth, RBAC/API keys, EE/entitlements, self-observability, data lifecycle, build/test | L48–53 |
| 11 | 设计专题与终章 — design themes synthesis, capstone | L54–55 |
| 12 | v4 迁移与生产实战 — v3.199→v4.42 architecture delta, unified events, OTel SDK, agents/evals, self-hosted rollout | L56–61 |

## How to view

**Locally** (zero dependencies, just Python 3):

```bash
cd src
python3 build.py
# then open ../index.html in a browser
```

## How to print / export a PDF

```bash
cd src
python3 build_print.py
# open ../print_zh.html (Chinese) or ../print_en.html (English) in a browser,
# then File -> Print -> Save as PDF (Ctrl/Cmd+P). Each lesson starts on a new page.
```

## Project structure

```
src/            generators + tooling (pure Python 3, no dependencies)
  part1.py ..   lesson content (bilingual), one module per part
  quizzes.py    per-lesson self-test questions
  shell.py      page shell + the shared CSS design system
  registry.py   ordered filename -> content map
  build.py      builds index.html + lessons/*.html
  build_print.py builds print_zh.html + print_en.html
  check_html.py structural HTML validation (incl. SVG/CJK/visual-block floors)
  check_links.py internal link validation
lessons/        generated lesson pages (committed, kept in sync)
index.html      generated table of contents (committed)
glossary.html   generated concept index (committed)
print_*.html    generated print editions (committed)
docs/superpowers/   design spec, roadmap, per-milestone specs/plans + source maps
```

## Build & validate

```bash
cd src
python3 build.py          # regenerate index.html + lessons/*.html
python3 build_print.py    # regenerate print_zh.html + print_en.html
python3 check_html.py     # structural checks (0 error expected)
python3 check_links.py    # all internal links must resolve
```

The generated HTML is committed and kept in sync with the sources; a re-run of `build.py` should
produce no diff.

## License

Dual-licensed:

- **Code** (the Python generators and validation scripts under `src/`) — MIT, see [LICENSE](LICENSE).
- **Content** (the lesson text and diagrams rendered into `index.html`, `lessons/*.html`,
  `print_*.html`) — CC BY 4.0, see [LICENSE-CONTENT](LICENSE-CONTENT).

---

## 中文说明

这是一份 [Langfuse](https://github.com/langfuse/langfuse) 内部原理的**图解、双语**学习指南，从
"什么是 LLM 可观测性"一路讲到"摄取/查询链路在代码里怎么走"以及"怎么本地构建、测试、提一个 PR"。

**📖 在线阅读：<https://verdenmax.github.io/langfuse-visual-guide/>**

> **声明：** 本项目是**第三方、非官方**的学习材料，**不包含 Langfuse 源码**（仅引用少量、标注来源的
> 代码片段来讲解）。Langfuse 本身由其作者以 **MIT** 许可发布（部分企业版功能除外）。

> **进度：** **已完成** —— **12 个部分 / 61 课**全部完成，逐里程碑核验源码忠实、全部 gate 通过（0 错误）。
> 设计规格见 `docs/superpowers/specs/`，路线图与逐里程碑审计日志见 `docs/superpowers/plans/`。

第 12 部分是 **v4 补充章节**：截至 2026-09-23 对照 Langfuse Server **v4.42.0** 与 Python SDK **v4.15.4**；原 L01–L55 仍保留 v3.199.0 时代的源码基线，用于清楚展示架构演进。

每一课都自成一体、内嵌中英双语（页内可切换），用手绘图、worked-example 追踪图、真实（标注来源的）
代码和一段自测题来讲清一个概念。

**怎么看：** 本地零依赖，`cd src && python3 build.py` 后用浏览器打开 `index.html`。

**怎么打印：** `cd src && python3 build_print.py`，再打开 `print_zh.html`（中文）或 `print_en.html`
（英文），用 `Ctrl/Cmd+P` 导出 PDF，每课自动分页。

**许可：** 双许可 —— 代码（`src/` 下的 Python 生成器与校验脚本）用 MIT（见 LICENSE），教学内容
（课程文字与图）用 CC BY 4.0（见 LICENSE-CONTENT）。
