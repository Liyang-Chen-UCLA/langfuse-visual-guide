"""Part 12 — v4 迁移与生产实战 / V4 Migration & Production Practice. Lessons L56–L61.

Supplement pinned on 2026-09-23 to:
- Langfuse Server v4.42.0, commit 11fe5cca6d63b91b1d33ad3b4e4eb0ef03b8c6db
- Langfuse Python SDK v4.15.4, commit 65392c73731e07711828745de337fdf7bba31fbc

The original L01–L55 guide remains a v3.199.0-era source tour. This Part explains
the architectural delta and production migration, with external field reports
used only as operational anecdotes, not as normative product guarantees.
"""

_ZH56 = r"""<p class="lead">原版教程的源码基线是 <strong>Langfuse Server v3.199.0</strong>。到本补充编写时，主仓库已经是 <strong>v4.42.0</strong>。v4 不是“把几个 API 改名”这么简单：它把<strong>数据模型、摄取协议、SDK 上下文模型和查询入口</strong>一起往 OpenTelemetry（OTel）和 observation-first 方向收拢。</p>
<div class="card analogy"><div class="tag">📋 生活类比</div>v3 像一家快递公司：先建“订单表（trace）”，再把每个运输节点放进“轨迹表（observation）”，查询时经常要把两边拼起来。v4 更像把每个运输节点都做成一张<strong>自带订单关键信息的宽事件</strong>，根节点就是整单的代表。这样写入更统一，查询也少做 JOIN。</div>
<h2>先抓住六个真正的变化</h2>
<table class="t"><thead><tr><th>维度</th><th>v3 教程基线</th><th>v4.42 的方向</th></tr></thead><tbody>
<tr><td>核心实体</td><td>trace + observations 分开理解</td><td><strong>observation-first</strong>；trace 由 root observation 表达</td></tr>
<tr><td>ClickHouse</td><td>traces / observations 等表并存</td><td><code>events_full</code> / <code>events_core</code> 统一事件读模型</td></tr>
<tr><td>埋点</td><td>Langfuse 自有事件模型为主，OTel 是并行入口</td><td><strong>OTel 原生</strong>成为 SDK 与摄取主线</td></tr>
<tr><td>Python SDK</td><td>stateful trace/span/generation client</td><td><code>get_client()</code> + 当前 OTel span/context</td></tr>
<tr><td>读取</td><td>legacy trace/metrics API</td><td>Observations API v2 / Metrics API v2 / Scores API v3</td></tr>
<tr><td>升级</td><td>单一旧数据模型</td><td><code>legacy → dual → events_only</code> 分阶段迁移</td></tr>
</tbody></table>
<div class="flow"><div class="node"><div class="nt">v3</div><div class="nd">trace 是显式顶层实体</div></div><div class="arrow">→</div><div class="node hl"><div class="nt">v4</div><div class="nd">root observation 代表一次应用调用</div></div><div class="arrow">→</div><div class="node"><div class="nt">统一查询</div><div class="nd">events 表承担主要分析</div></div></div>
<h2>哪些东西没有变？</h2>
<p>v4 没有推翻 Langfuse 的基本世界观：仍然是 <strong>web + worker</strong> 两个应用层，仍然用 PostgreSQL 保存事务型配置/元数据，用 ClickHouse 扛遥测分析，用 Redis 做队列/缓存，用 S3/MinIO 保存 blob、媒体与部分异步载荷。真正变化的是<strong>“遥测数据怎样表示和流动”</strong>。</p>
<div class="cols"><div class="col"><h4>控制面仍然稳定</h4><p>project、prompt、dataset、API key、配置等仍然适合 PostgreSQL。</p></div><div class="col"><h4>数据面被重做</h4><p>trace/observation 的分析模型统一为 events，SDK 也对齐 OTel span/context。</p></div></div>
<h2>为什么这次升级值得单独学？</h2>
<p>因为它解决的是规模问题，而不是语法问题。v3 时代为了展示一条 trace，经常需要跨 trace/observation 表拼装；v4 让常用 trace 属性直接跟 observation 一起进入宽事件。代价是行更宽、冗余更多，但换来更直接的过滤、聚合和全文检索。</p>
<div class="card detail"><div class="tag">🔎 源码锚点</div>
<ul><li>Server 版本：根目录 <code>package.json</code> = <strong>4.42.0</strong>（本补充 pin 到 commit <code>11fe5cca...</code>）。</li>
<li>统一事件表：<code>packages/shared/clickhouse/migrations/canonical/0039_create_events_full.up.sql</code>。</li>
<li>核心读取：<code>packages/shared/src/server/repositories/events.ts</code>。</li>
<li>Python SDK：<code>langfuse/langfuse-python</code> v4.15.4（pin 到 commit <code>65392c73...</code>）。</li></ul></div>
<div class="card key"><div class="tag">🎯 本课要点</div><ul>
<li>v4 的主线是 <strong>observation-first + unified events + OTel-native</strong>。</li>
<li>trace 没消失，而是从“独立顶层记录”变成由根 observation 表达的一次调用。</li>
<li>基础设施角色基本没变；变化集中在遥测数据模型、SDK/摄取和查询 API。</li>
</ul></div>"""
_EN56 = r"""<p class="lead">The original guide is pinned to <strong>Langfuse Server v3.199.0</strong>. At the time of this supplement, the main repository is <strong>v4.42.0</strong>. V4 is not just an API rename: the <strong>data model, ingestion protocol, SDK context model, and read APIs</strong> all converge around OpenTelemetry (OTel) and an observation-first design.</p>
<div class="card analogy"><div class="tag">📋 Analogy</div>Think of v3 as a parcel system with a separate “order” record (trace) and “tracking events” (observations) that often need to be joined. V4 makes each tracking event a <strong>wide event carrying the key order context</strong>; the root event represents the whole shipment. Writes become more uniform and reads need fewer joins.</div>
<h2>Six changes that actually matter</h2>
<table class="t"><thead><tr><th>Area</th><th>v3 guide baseline</th><th>v4.42 direction</th></tr></thead><tbody>
<tr><td>Core entity</td><td>trace + observations as separate concepts</td><td><strong>observation-first</strong>; a trace is represented by a root observation</td></tr>
<tr><td>ClickHouse</td><td>traces / observations tables coexist</td><td><code>events_full</code> / <code>events_core</code> unified event read model</td></tr>
<tr><td>Instrumentation</td><td>Langfuse-native events first, OTel as a parallel path</td><td><strong>OTel-native</strong> is the main SDK and ingestion direction</td></tr>
<tr><td>Python SDK</td><td>stateful trace/span/generation client</td><td><code>get_client()</code> + current OTel span/context</td></tr>
<tr><td>Reads</td><td>legacy trace/metrics APIs</td><td>Observations API v2 / Metrics API v2 / Scores API v3</td></tr>
<tr><td>Upgrade</td><td>one legacy data model</td><td>staged <code>legacy → dual → events_only</code> migration</td></tr>
</tbody></table>
<div class="flow"><div class="node"><div class="nt">v3</div><div class="nd">trace is an explicit top-level entity</div></div><div class="arrow">→</div><div class="node hl"><div class="nt">v4</div><div class="nd">root observation represents one app call</div></div><div class="arrow">→</div><div class="node"><div class="nt">Unified reads</div><div class="nd">events tables carry analytics</div></div></div>
<h2>What did not change?</h2>
<p>V4 keeps the same broad system shape: <strong>web + worker</strong>, PostgreSQL for transactional configuration and metadata, ClickHouse for telemetry analytics, Redis for queues/caches, and S3/MinIO for blobs, media and selected async payloads. What changed most is <strong>how telemetry is represented and moved</strong>.</p>
<div class="cols"><div class="col"><h4>Control plane stays familiar</h4><p>Projects, prompts, datasets, API keys and configuration still fit PostgreSQL.</p></div><div class="col"><h4>Data plane was redesigned</h4><p>Trace/observation analytics converge on events while SDKs align with OTel spans and context.</p></div></div>
<h2>Why learn this as an architecture change?</h2>
<p>Because the motivation is scale, not syntax. V3 reads often assembled traces across separate structures; v4 pushes commonly queried trace context onto observations in a wide-event model. That spends more bytes and accepts denormalization in exchange for simpler filtering, aggregation and full-text search.</p>
<div class="card detail"><div class="tag">🔎 Source anchors</div><ul>
<li>Server version: root <code>package.json</code> = <strong>4.42.0</strong>, pinned here to commit <code>11fe5cca...</code>.</li>
<li>Unified table: <code>packages/shared/clickhouse/migrations/canonical/0039_create_events_full.up.sql</code>.</li>
<li>Core reads: <code>packages/shared/src/server/repositories/events.ts</code>.</li>
<li>Python SDK: <code>langfuse/langfuse-python</code> v4.15.4, pinned to <code>65392c73...</code>.</li>
</ul></div>
<div class="card key"><div class="tag">🎯 Key points</div><ul>
<li>The v4 through-line is <strong>observation-first + unified events + OTel-native</strong>.</li>
<li>Trace did not disappear; it is represented by the root observation rather than a separate top-level record.</li>
<li>The infrastructure roles remain familiar; telemetry data, SDK/ingestion and read APIs changed most.</li>
</ul></div>"""
LESSON_56 = {"zh": _ZH56, "en": _EN56}

_ZH57 = r"""<p class="lead">v4 最重要的服务端变化，是把分析主线收敛到统一的 <strong>events</strong> 模型。先别把 <code>events_full</code> 理解成“又一张新表”；它更像是 v4 的<strong>统一事实表</strong>：一个 observation 的身份、trace 上下文、模型、token、成本、输入输出、metadata、工具调用和 instrumentation 来源，都尽量在同一行里。</p>
<div class="card analogy"><div class="tag">📋 生活类比</div>传统关系库喜欢“学生表、课程表、成绩表”各放各的，再 JOIN。分析系统面对亿级事件时更愿意把常用维度直接抄到“成绩事件”这一行。多存一点，换来查询时少拼表。<strong>events_full 就是这种面向分析的反范式化。</strong></div>
<h2>events_full 一行里有什么？</h2>
<table class="t"><thead><tr><th>字段组</th><th>例子</th><th>为什么重要</th></tr></thead><tbody>
<tr><td>身份/树</td><td><code>trace_id</code>, <code>span_id</code>, <code>parent_span_id</code></td><td>不用额外树表就能重建调用结构</td></tr>
<tr><td>trace 上下文</td><td><code>trace_name</code>, user/session/tags</td><td>把高频过滤维度放到 event 行</td></tr>
<tr><td>类型</td><td><code>type</code>, <code>is_app_root</code></td><td>区分 generation/tool/agent 等，同时标出根 observation</td></tr>
<tr><td>LLM</td><td>model、usage、cost、prompt</td><td>直接做模型/成本/Prompt 维度聚合</td></tr>
<tr><td>I/O 与工具</td><td>input/output、tool calls</td><td>调试与全文检索</td></tr>
<tr><td>OTel 来源</td><td>service/scope/sdk name/version</td><td>把标准遥测来源保留下来</td></tr>
</tbody></table>
<div class="layers">
<div class="layer l-core"><div class="lh"><span class="badge">root</span><span class="name">is_app_root = true</span></div><div class="ld">代表一次应用调用的根 observation；它承担过去“trace 顶层记录”的大部分语义。</div></div>
<div class="layer l-main"><div class="lh"><span class="badge">child</span><span class="name">parent_span_id</span></div><div class="ld">每个子 observation 只需指向父 span；乱序写入也能在读时拼树。</div></div>
<div class="layer l-part"><div class="lh"><span class="badge">analytics</span><span class="name">wide columns</span></div><div class="ld">user/session/tags/model/cost 等常用维度直接在行上，避免热点 JOIN。</div></div>
</div>
<h2>为什么还有 events_core？</h2>
<p><code>events_full</code> 是“信息最全”的读模型，但并不是每个列表/聚合都需要大字段。v4 同时保留更轻量的 core 视图/表来服务不需要完整 I/O 的查询。思路和原教程第24课的“紧凑列表 vs 详情懒加载”一致：<strong>先少扫，再按需拿重字段。</strong></p>
<h2>ReplacingMergeTree 仍然重要</h2>
<p>当前 <code>events_full</code> 使用 <code>ReplacingMergeTree(event_ts, is_deleted)</code>，按 project、时间和 trace hash 排序。它允许同一个事件随着补全/更新继续追加版本，再由读取语义收敛到最新状态。这延续了原教程第8课的核心思想：高吞吐遥测里，尽量把“更新”变成<strong>追加 + 合并</strong>。</p>
<div class="card warn"><div class="tag">⚠️ 取舍</div><strong>反范式化不是免费午餐。</strong> user/session/tags 等字段在多条 observation 上重复，会增加存储与写入字节；但它换来的是热点查询少 JOIN、列裁剪更直接，以及更容易做全文索引。对可观测平台来说，这通常是值得的交换。</div>
<div class="card detail"><div class="tag">🔎 源码锚点</div><code>0039_create_events_full.up.sql</code> 直接定义了字段、全文索引、<code>ReplacingMergeTree</code>、月分区和排序键；<code>repositories/events.ts</code> 则展示 v4 如何围绕统一 events 构建 trace/observation 的读取。</div>
<div class="card key"><div class="tag">🎯 本课要点</div><ul>
<li>v4 的 trace/observation 分析核心是一张<strong>统一宽事件</strong>，不是简单把旧表换名字。</li>
<li><code>trace_id + span_id + parent_span_id + is_app_root</code> 足以表达一次应用调用和树结构。</li>
<li><code>events_full</code> 追求完整，轻量读取则尽量走 core/裁剪字段，避免扫描巨大 I/O。</li>
</ul></div>"""
_EN57 = r"""<p class="lead">The most important server-side v4 shift is convergence on a unified <strong>events</strong> model. Do not think of <code>events_full</code> as merely “one more table”. It acts as a <strong>unified analytics fact table</strong>: observation identity, trace context, model, tokens, cost, I/O, metadata, tool calls and instrumentation source are deliberately colocated.</p>
<div class="card analogy"><div class="tag">📋 Analogy</div>A normalized database keeps students, courses and grades separate and joins them later. At billions of analytical events, a system often copies hot dimensions onto each “grade event”. More bytes are stored, but reads avoid expensive joins. <strong>events_full is this analytics-oriented denormalization.</strong></div>
<h2>What lives on one events_full row?</h2>
<table class="t"><thead><tr><th>Group</th><th>Examples</th><th>Why it matters</th></tr></thead><tbody>
<tr><td>Identity/tree</td><td><code>trace_id</code>, <code>span_id</code>, <code>parent_span_id</code></td><td>rebuild the call tree without a separate relation</td></tr>
<tr><td>Trace context</td><td><code>trace_name</code>, user/session/tags</td><td>put hot filter dimensions on the event row</td></tr>
<tr><td>Type</td><td><code>type</code>, <code>is_app_root</code></td><td>distinguish generation/tool/agent and mark the root observation</td></tr>
<tr><td>LLM</td><td>model, usage, cost, prompt</td><td>aggregate directly by model/cost/prompt</td></tr>
<tr><td>I/O & tools</td><td>input/output, tool calls</td><td>debugging and full-text search</td></tr>
<tr><td>OTel source</td><td>service/scope/sdk name/version</td><td>preserve standard telemetry provenance</td></tr>
</tbody></table>
<div class="layers">
<div class="layer l-core"><div class="lh"><span class="badge">root</span><span class="name">is_app_root = true</span></div><div class="ld">Represents the root observation of one application call and carries much of the old top-level trace meaning.</div></div>
<div class="layer l-main"><div class="lh"><span class="badge">child</span><span class="name">parent_span_id</span></div><div class="ld">Each child points only to its parent, allowing out-of-order writes and read-time tree reconstruction.</div></div>
<div class="layer l-part"><div class="lh"><span class="badge">analytics</span><span class="name">wide columns</span></div><div class="ld">User/session/tags/model/cost live on the row to eliminate hot joins.</div></div>
</div>
<h2>Why is there also an events_core?</h2>
<p><code>events_full</code> is the rich read model, but list and aggregate queries do not always need large I/O fields. V4 also uses a lighter core representation for paths that can avoid full payloads. The idea matches Lesson 24: <strong>scan little first, fetch heavy fields only when needed.</strong></p>
<h2>ReplacingMergeTree still matters</h2>
<p>The current <code>events_full</code> uses <code>ReplacingMergeTree(event_ts, is_deleted)</code>, partitioned by month and ordered by project, time and trace hash. An event can gain newer appended versions while read semantics converge on the latest state. This extends Lesson 8's pattern: turn expensive in-place updates into <strong>append + merge</strong>.</p>
<div class="card warn"><div class="tag">⚠️ Trade-off</div><strong>Denormalization is not free.</strong> User/session/tags are repeated across observations, increasing stored and written bytes. The payoff is fewer joins on hot reads, direct column pruning and easier full-text indexing — a sensible exchange for observability analytics.</div>
<div class="card detail"><div class="tag">🔎 Source anchors</div><code>0039_create_events_full.up.sql</code> defines the columns, text indexes, <code>ReplacingMergeTree</code>, monthly partitioning and ordering key. <code>repositories/events.ts</code> shows v4 trace/observation reads built around unified events.</div>
<div class="card key"><div class="tag">🎯 Key points</div><ul>
<li>V4 centers trace/observation analytics on a <strong>unified wide event</strong>; this is not a table rename.</li>
<li><code>trace_id + span_id + parent_span_id + is_app_root</code> express the app call and tree structure.</li>
<li><code>events_full</code> favors completeness; lighter reads should use core/projection paths and avoid scanning huge I/O.</li>
</ul></div>"""
LESSON_57 = {"zh": _ZH57, "en": _EN57}

_ZH58 = r"""<p class="lead">Python SDK v4 在 2026 年重写为 <strong>OpenTelemetry 原生 SDK</strong>。最关键的心智变化是：你不再手工维护一个“Langfuse trace 对象”，而是让<strong>当前 OTel context/span</strong>决定父子关系；Langfuse 在这个标准上下文之上增加 generation、agent、tool 等语义。</p>
<div class="card analogy"><div class="tag">📋 生活类比</div>v3 像你自己拿一本族谱，创建每个人时手动告诉系统“这个人爸爸是谁”。v4 更像线程里已经有一个“当前家庭上下文”：进入一个 span，它自动成为当前节点；里面再开的 observation 自然就是它的孩子。</div>
<h2>代码风格怎么变？</h2>
<div class="cols"><div class="col"><h4>旧式思路</h4><pre class="code">langfuse = Langfuse()
trace = langfuse.trace(name="request")
span = trace.span(name="retrieve")
generation = trace.generation(name="answer")</pre></div>
<div class="col"><h4>v4 思路</h4><pre class="code">from langfuse import get_client, observe

langfuse = get_client()

@observe()
def run():
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="answer"
    ) as gen:
        ...
        gen.update(output="done")</pre></div></div>
<p><code>get_client()</code> 拿到客户端；<code>@observe()</code> 自动把函数边界变成 observation；<code>start_as_current_observation()</code> 适合你需要显式控制类型和生命周期的地方；<code>update_current_span()</code> 用来给当前 span 补 input/output/metadata 等属性。</p>
<h2>OTel 原生意味着什么？</h2>
<div class="flow"><div class="node"><div class="nt">App / LangChain</div><div class="nd">产生 span/context</div></div><div class="arrow">→</div><div class="node hl"><div class="nt">OTLP</div><div class="nd">标准 trace 载荷</div></div><div class="arrow">→</div><div class="node"><div class="nt">Langfuse</div><div class="nd">映射为 events</div></div></div>
<p>这使 Langfuse 能和其它 OTel instrumentation 共存：HTTP、数据库、队列、LLM 都可以在一棵标准 trace 树里。对平台迁移而言，这比“换一个 decorator 名字”重要得多，因为<strong>上下文传播的责任从专用 client 对象转向 OTel context</strong>。</p>
<h2>两个很实用的坑</h2>
<div class="card warn"><div class="tag">⚠️ 实战</div><ul>
<li><strong>先加载环境变量，再 <code>get_client()</code>。</strong> 第三方 v4 实战中最常见的“为什么没上报/401”之一，就是初始化顺序错了。</li>
<li><strong>短生命周期脚本最后 <code>flush()</code>。</strong> SDK 会批量异步上报；进程太快退出时，不 flush 可能让最后一批 span 还没发出去。</li>
</ul></div>
<h2>实时链路也变了</h2>
<p>当前 Python SDK README 明确把 v4 OTel 摄取 + Observations API v2 / Metrics API v2 作为实时路径。也就是说“写入走新 events，但读取还走旧 trace API”会造成你误以为数据没到；<strong>producer 和 reader 要一起迁移。</strong></p>
<div class="card detail"><div class="tag">🔎 源码锚点</div>
<ul><li><code>langfuse-python/pyproject.toml</code>：v4.15.4，直接依赖 OTel API/SDK/OTLP exporter。</li>
<li><code>langfuse/_client/client.py</code>：<code>start_as_current_observation</code>、<code>update_current_span</code> 等核心入口。</li>
<li><code>langfuse/_client/observe.py</code>：<code>@observe</code> 如何围绕当前 context 创建 observation。</li></ul></div>
<div class="card key"><div class="tag">🎯 本课要点</div><ul>
<li>v4 Python SDK 的核心不再是 trace object，而是<strong>当前 OTel span/context</strong>。</li>
<li><code>@observe</code> 管函数边界，<code>start_as_current_observation</code> 管显式 observation，<code>update_current_span</code> 补属性。</li>
<li>初始化顺序与 <code>flush()</code> 是小事，但非常容易造成“平台上看不到 trace”的假故障。</li>
</ul></div>"""
_EN58 = r"""<p class="lead">The Python SDK v4 was rewritten in 2026 as an <strong>OpenTelemetry-native SDK</strong>. The core mental shift is that you no longer carry a stateful “Langfuse trace object”. Instead, the <strong>current OTel context/span</strong> determines parent-child structure, with Langfuse adding semantics such as generation, agent and tool.</p>
<div class="card analogy"><div class="tag">📋 Analogy</div>V3 is like carrying a genealogy book and manually telling every new person who their parent is. V4 is more like entering a current family context: open a span and it becomes current; observations created inside it naturally become children.</div>
<h2>How does the code style change?</h2>
<div class="cols"><div class="col"><h4>Legacy mindset</h4><pre class="code">langfuse = Langfuse()
trace = langfuse.trace(name="request")
span = trace.span(name="retrieve")
generation = trace.generation(name="answer")</pre></div>
<div class="col"><h4>V4 mindset</h4><pre class="code">from langfuse import get_client, observe

langfuse = get_client()

@observe()
def run():
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="answer"
    ) as gen:
        ...
        gen.update(output="done")</pre></div></div>
<p><code>get_client()</code> obtains the client; <code>@observe()</code> turns a function boundary into an observation; <code>start_as_current_observation()</code> is for explicit type/lifetime control; <code>update_current_span()</code> enriches the current span with input/output/metadata.</p>
<h2>What does OTel-native buy you?</h2>
<div class="flow"><div class="node"><div class="nt">App / LangChain</div><div class="nd">creates span/context</div></div><div class="arrow">→</div><div class="node hl"><div class="nt">OTLP</div><div class="nd">standard trace payload</div></div><div class="arrow">→</div><div class="node"><div class="nt">Langfuse</div><div class="nd">maps to events</div></div></div>
<p>Langfuse can coexist with other OTel instrumentation: HTTP, databases, queues and LLM work can share one standard trace tree. The important migration is therefore not a decorator rename; <strong>context propagation moves from a proprietary client object to OTel context.</strong></p>
<h2>Two practical gotchas</h2>
<div class="card warn"><div class="tag">⚠️ Practice</div><ul>
<li><strong>Load environment variables before <code>get_client()</code>.</strong> A common v4 field failure is constructing the client before credentials/base URL are present.</li>
<li><strong>Call <code>flush()</code> in short-lived scripts.</strong> The SDK batches asynchronously; a process can exit before the last batch is exported.</li>
</ul></div>
<h2>The real-time path changed too</h2>
<p>The current Python SDK README identifies v4 OTel ingestion together with Observations API v2 / Metrics API v2 as the real-time path. If the producer writes the new events model while your reader still polls legacy trace APIs, you can misdiagnose fresh data as missing. <strong>Migrate producers and readers together.</strong></p>
<div class="card detail"><div class="tag">🔎 Source anchors</div><ul>
<li><code>langfuse-python/pyproject.toml</code>: v4.15.4 with direct OTel API/SDK/OTLP exporter dependencies.</li>
<li><code>langfuse/_client/client.py</code>: <code>start_as_current_observation</code>, <code>update_current_span</code>.</li>
<li><code>langfuse/_client/observe.py</code>: how <code>@observe</code> creates observations around current context.</li>
</ul></div>
<div class="card key"><div class="tag">🎯 Key points</div><ul>
<li>V4 Python tracing centers on the <strong>current OTel span/context</strong>, not a stateful trace object.</li>
<li>Use <code>@observe</code> for function boundaries, <code>start_as_current_observation</code> for explicit observations, and <code>update_current_span</code> to enrich the current span.</li>
<li>Initialization order and <code>flush()</code> are small details that cause surprisingly many “missing trace” failures.</li>
</ul></div>"""
LESSON_58 = {"zh": _ZH58, "en": _EN58}

_ZH59 = r"""<p class="lead">复杂 Agent 接 Langfuse v4，最容易犯的错是“每一层都自己手工造 span”。正确思路是先决定<strong>观测边界</strong>：谁代表一次用户请求，谁代表 Agent 决策，谁代表 tool/retriever，谁才是真正的 generation。然后让 LangChain callback、<code>@observe</code> 和手工 observation 各管自己最擅长的边界。</p>
<div class="card analogy"><div class="tag">📋 生活类比</div>监控一家餐厅，不需要给“拿起勺子、走两步、打开冰箱”都装摄像头。真正有价值的是：一桌订单、厨师决策、取原料、烹饪、上菜。Agent tracing 也是一样：<strong>边界比数量重要。</strong></div>
<h2>推荐的 Agent 观测树</h2>
<div class="layers">
<div class="layer l-core"><div class="lh"><span class="badge">root</span><span class="name">request / agent run</span></div><div class="ld">一次用户任务；在这里挂 user_id、session_id、tags、release/version。</div></div>
<div class="layer l-main"><div class="lh"><span class="badge">agent</span><span class="name">planner / supervisor</span></div><div class="ld">一次真正改变流程的 LLM 决策；保留选择了哪个工具/子 Agent。</div></div>
<div class="layer l-part"><div class="lh"><span class="badge">tool</span><span class="name">search / retriever / API</span></div><div class="ld">外部 I/O；记录参数、结果摘要、耗时和失败。</div></div>
<div class="layer l-app"><div class="lh"><span class="badge">generation</span><span class="name">model call</span></div><div class="ld">模型、prompt、token、成本与输出；这是成本/质量分析的关键单位。</div></div>
</div>
<h2>LangChain CallbackHandler 能覆盖什么？</h2>
<p>v4 Python SDK 仍提供 <code>langfuse.langchain.CallbackHandler</code>。LangChain/LangGraph 自己会发出 model、chain、tool、retriever 等 callback 事件，handler 把这些事件转换成 Langfuse/OTel observation。对“框架内发生的调用”非常省事。</p>
<div class="cols"><div class="col"><h4>Callback 适合</h4><ul><li>标准 LangChain model/tool/retriever</li><li>create_agent / LangGraph 内部链路</li><li>自动保持大部分父子关系</li></ul></div>
<div class="col"><h4>手工 observe 适合</h4><ul><li>业务层 supervisor / route 逻辑</li><li>非 LangChain 的 HTTP/DB/自研工具</li><li>需要明确类型、input/output、业务 metadata</li></ul></div></div>
<h2>不要把“LangGraph State”误当成 trace 自动保存</h2>
<p>Callback 能观测<strong>发生了哪些调用</strong>，但不会自动把整个 LangGraph State 在每一步完整快照下来。State 是应用运行时状态；trace 是观测记录。若一个 state 字段对 debug 很重要，应在合适的 observation 上<strong>显式记录摘要或关键字段</strong>，而不是期待平台从 reducer/return value 猜出全部状态。</p>
<h2>跨层共享属性：用 context 传播</h2>
<p>v4 SDK 提供 <code>propagate_attributes</code> 一类机制，把 user/session/tags 等属性放进当前上下文，使下面创建的 observations 一致继承。这样不用每个 tool call 重复传一遍。</p>
<pre class="code">from langfuse import get_client, propagate_attributes

lf = get_client()

with propagate_attributes(
    user_id="u-123",
    session_id="s-456",
    tags=["prod", "shop-agent"]
):
    agent.invoke(...)</pre>
<div class="card warn"><div class="tag">⚠️ 实战边界</div>异步 task 通常能沿 contextvars/OTel context 传播，但<strong>线程池、进程池、消息队列</strong>是天然边界。跨这些边界时要验证 trace context 是否被显式注入/提取；否则最常见的症状就是“子 span 飘成了新的 root”。</div>
<h2>面试里真正能证明你做过的点</h2>
<table class="t"><thead><tr><th>问题</th><th>有经验的回答</th></tr></thead><tbody>
<tr><td>为什么不全用 callback？</td><td>callback 覆盖框架事件，但业务状态/自研 I/O/关键边界仍需要手工 observation。</td></tr>
<tr><td>为什么不每个函数都 @observe？</td><td>会制造海量低价值 span、成本和噪声；应按可诊断的业务边界埋点。</td></tr>
<tr><td>State 怎么进 Langfuse？</td><td>只记录 debug 所需的关键快照/摘要，不默认复制整个 state。</td></tr>
</tbody></table>
<div class="card key"><div class="tag">🎯 本课要点</div><ul>
<li>复杂 Agent 的关键是<strong>观测边界设计</strong>，不是 span 数量。</li>
<li>LangChain CallbackHandler 负责框架事件，<code>@observe</code>/手工 observation 补业务边界。</li>
<li>应用 state 与 trace 是两件事；重要 state 要主动选择性记录。</li>
</ul></div>"""
_EN59 = r"""<p class="lead">The most common mistake when tracing a complex agent in Langfuse v4 is manually creating spans at every layer. Start by defining <strong>observation boundaries</strong>: what represents the user request, an agent decision, a tool/retriever call, and a real model generation. Then let the LangChain callback, <code>@observe</code>, and manual observations each own the boundary they fit best.</p>
<div class="card analogy"><div class="tag">📋 Analogy</div>To monitor a restaurant you do not need a camera event for “picked up spoon” and “walked two steps”. You care about the table order, chef decision, ingredient fetch, cooking and serving. Agent tracing is the same: <strong>boundaries matter more than span count.</strong></div>
<h2>A practical agent observation tree</h2>
<div class="layers">
<div class="layer l-core"><div class="lh"><span class="badge">root</span><span class="name">request / agent run</span></div><div class="ld">One user task; attach user_id, session_id, tags and release/version here.</div></div>
<div class="layer l-main"><div class="lh"><span class="badge">agent</span><span class="name">planner / supervisor</span></div><div class="ld">An LLM decision that actually changes control flow; preserve the selected tool/sub-agent.</div></div>
<div class="layer l-part"><div class="lh"><span class="badge">tool</span><span class="name">search / retriever / API</span></div><div class="ld">External I/O; record parameters, result summary, latency and failure.</div></div>
<div class="layer l-app"><div class="lh"><span class="badge">generation</span><span class="name">model call</span></div><div class="ld">Model, prompt, tokens, cost and output — the key unit for quality/cost analysis.</div></div>
</div>
<h2>What does LangChain CallbackHandler cover?</h2>
<p>The v4 Python SDK still ships <code>langfuse.langchain.CallbackHandler</code>. LangChain/LangGraph emit model, chain, tool and retriever callbacks, and the handler converts those framework events into Langfuse/OTel observations. It is excellent for calls that happen inside the framework.</p>
<div class="cols"><div class="col"><h4>Callback fits</h4><ul><li>standard LangChain model/tool/retriever events</li><li>create_agent / LangGraph execution</li><li>automatic parent-child structure for framework activity</li></ul></div>
<div class="col"><h4>Manual observe fits</h4><ul><li>business supervisor/routing logic</li><li>non-LangChain HTTP/DB/custom tools</li><li>explicit type, input/output and business metadata</li></ul></div></div>
<h2>Do not confuse LangGraph State with automatic trace snapshots</h2>
<p>A callback observes <strong>which calls happened</strong>; it does not automatically snapshot the entire LangGraph State at every step. State is application runtime state, while a trace is an observability record. If a state field matters for debugging, explicitly record a <strong>summary or selected fields</strong> on the relevant observation rather than expecting the platform to infer state from reducers and return values.</p>
<h2>Shared attributes belong in context propagation</h2>
<p>V4 exposes mechanisms such as <code>propagate_attributes</code> to put user/session/tags into current context so descendant observations inherit them consistently, instead of repeating arguments on every tool call.</p>
<pre class="code">from langfuse import get_client, propagate_attributes

lf = get_client()

with propagate_attributes(
    user_id="u-123",
    session_id="s-456",
    tags=["prod", "shop-agent"]
):
    agent.invoke(...)</pre>
<div class="card warn"><div class="tag">⚠️ Boundary</div>Async tasks commonly inherit contextvars/OTel context, but <strong>thread pools, process pools and message queues</strong> are natural propagation boundaries. Verify explicit context injection/extraction across them; otherwise children often show up as new roots.</div>
<h2>Questions that reveal real implementation experience</h2>
<table class="t"><thead><tr><th>Question</th><th>Experienced answer</th></tr></thead><tbody>
<tr><td>Why not callback only?</td><td>It covers framework events, not every business state transition or custom I/O boundary.</td></tr>
<tr><td>Why not @observe every function?</td><td>It creates low-value span volume, cost and noise; instrument diagnostic business boundaries.</td></tr>
<tr><td>How does State enter Langfuse?</td><td>Record selected debug-relevant snapshots/summaries; do not clone all state by default.</td></tr>
</tbody></table>
<div class="card key"><div class="tag">🎯 Key points</div><ul>
<li>Complex-agent observability is an <strong>observation-boundary design problem</strong>, not a span-count contest.</li>
<li>Use LangChain CallbackHandler for framework events and manual observations for business boundaries.</li>
<li>Application state and trace data are different; explicitly record only the state needed for diagnosis.</li>
</ul></div>"""
LESSON_59 = {"zh": _ZH59, "en": _EN59}

_ZH60 = r"""<p class="lead">v4 的读取也跟着数据模型变了。最容易踩的坑是：写入已经是新 OTel/events 路径，但你仍用旧 trace API 判断“数据有没有到”。正确做法是把<strong>写入、读取、评估</strong>看成一条整体迁移链路。</p>
<div class="card analogy"><div class="tag">📋 生活类比</div>你把仓库换成了新货架，却还拿旧仓库的货位表去找货，当然会以为“货丢了”。v4 的 Observations API v2，就是和新 events 模型对齐的新货位表。</div>
<h2>生产读路径应该怎么分？</h2>
<table class="t"><thead><tr><th>需求</th><th>v4 主路径</th><th>概念</th></tr></thead><tbody>
<tr><td>查调用明细</td><td>Observations API v2</td><td>以 observation/root observation 为统一单位</td></tr>
<tr><td>做聚合指标</td><td>Metrics API v2</td><td>直接面向新 events 查询</td></tr>
<tr><td>查评分</td><td>Scores API v3</td><td>独立评分实体，挂到 observation/root 上</td></tr>
<tr><td>离线回归</td><td>Dataset + Experiment</td><td>固定测试集，比较模型/prompt/agent 版本</td></tr>
</tbody></table>
<h2>把“看 trace”升级成质量闭环</h2>
<div class="vflow">
<div class="step"><div class="num">1</div><div class="sc"><h4>Production observations</h4><p>在线流量产出真实 observation，保留输入、输出、工具链和成本。</p></div></div>
<div class="step"><div class="num">2</div><div class="sc"><h4>Scores / evaluators</h4><p>规则、代码、LLM-as-a-judge 或人工评分，给结果加质量信号。</p></div></div>
<div class="step"><div class="num">3</div><div class="sc"><h4>Bad-case mining</h4><p>按 score、错误类型、成本或 latency 过滤，找真正值得修的样本。</p></div></div>
<div class="step"><div class="num">4</div><div class="sc"><h4>Dataset</h4><p>把代表性 bad case 固化成可重复的回归集，而不是只看一次 trace。</p></div></div>
<div class="step"><div class="num">5</div><div class="sc"><h4>Experiment</h4><p>新 prompt/model/agent 版本重跑同一数据集，对比质量、成本和延迟。</p></div></div>
</div>
<h2>Online eval 和 offline experiment 不要混</h2>
<div class="cols"><div class="col"><h4>Online</h4><p>针对真实生产 observations 持续抽样/评分。目标是<strong>发现问题和漂移</strong>。</p></div><div class="col"><h4>Offline</h4><p>对固定 dataset 重跑候选版本。目标是<strong>上线前比较与回归</strong>。</p></div></div>
<p>两者通过 Dataset 串起来：线上坏样本进入 dataset，离线实验验证修复，再回到线上继续采样。这个闭环比“做一个 dashboard 看平均分”更接近真正的 Agent 工程。</p>
<h2>对复杂 Agent，评分应挂在哪一层？</h2>
<p>v4 里 root observation 很适合作为<strong>整次任务结果</strong>的评价对象；具体 tool/generation 则适合挂局部 score。这样你能同时回答“整单任务成功了吗？”与“是哪一个步骤拖垮了结果？”。</p>
<div class="card warn"><div class="tag">⚠️ 迁移提醒</div>切到 events-only 前，要确认旧的 trace-level evaluator、导出脚本和内部查询是否仍假设“trace 是独立实体”。在 observation-first 模型里，这些逻辑通常要改成<strong>root observation / observation id</strong>。</div>
<div class="card key"><div class="tag">🎯 本课要点</div><ul>
<li>v4 的实时读取要和新 events 写入一起迁移，不能只换 SDK。</li>
<li>Observations v2 / Metrics v2 / Scores v3 分别承担明细、聚合和评分读取。</li>
<li>真正有价值的 eval 链路是：生产 observation → score → bad case → dataset → experiment → 回归上线。</li>
</ul></div>"""
_EN60 = r"""<p class="lead">Reads changed with the v4 data model. A common migration bug is writing through the new OTel/events path while still using legacy trace APIs to decide whether data “arrived”. Treat <strong>ingestion, reads and evaluation</strong> as one migration unit.</p>
<div class="card analogy"><div class="tag">📋 Analogy</div>If you move inventory to a new warehouse but keep using the old aisle map, you will conclude that stock disappeared. Observations API v2 is the aisle map aligned with the new events model.</div>
<h2>How should production reads split?</h2>
<table class="t"><thead><tr><th>Need</th><th>V4 main path</th><th>Concept</th></tr></thead><tbody>
<tr><td>Call detail</td><td>Observations API v2</td><td>observation/root observation as the unified unit</td></tr>
<tr><td>Aggregates</td><td>Metrics API v2</td><td>query the new events model directly</td></tr>
<tr><td>Scores</td><td>Scores API v3</td><td>separate score records attached to observations/root</td></tr>
<tr><td>Offline regression</td><td>Dataset + Experiment</td><td>fixed cases to compare model/prompt/agent versions</td></tr>
</tbody></table>
<h2>Turn “looking at traces” into a quality loop</h2>
<div class="vflow">
<div class="step"><div class="num">1</div><div class="sc"><h4>Production observations</h4><p>Real traffic produces observations with I/O, tool chain and cost.</p></div></div>
<div class="step"><div class="num">2</div><div class="sc"><h4>Scores / evaluators</h4><p>Rules, code, LLM-as-a-judge or humans add quality signals.</p></div></div>
<div class="step"><div class="num">3</div><div class="sc"><h4>Bad-case mining</h4><p>Filter by score, error type, cost or latency to find cases worth fixing.</p></div></div>
<div class="step"><div class="num">4</div><div class="sc"><h4>Dataset</h4><p>Promote representative failures into a repeatable regression set.</p></div></div>
<div class="step"><div class="num">5</div><div class="sc"><h4>Experiment</h4><p>Run a new prompt/model/agent version on the same set and compare quality, cost and latency.</p></div></div>
</div>
<h2>Do not mix online eval and offline experiments</h2>
<div class="cols"><div class="col"><h4>Online</h4><p>Continuously sample/score real production observations to <strong>detect failures and drift</strong>.</p></div><div class="col"><h4>Offline</h4><p>Replay candidate versions on a fixed dataset for <strong>pre-release comparison and regression</strong>.</p></div></div>
<p>Datasets connect them: production failures become test cases, offline experiments validate fixes, then the new version returns to production and the loop continues. This is more useful than a dashboard with only an average score.</p>
<h2>Where should a complex agent be scored?</h2>
<p>In v4, the root observation is a natural target for <strong>whole-task outcome</strong> scores, while individual tool/generation observations can carry local scores. This lets you answer both “did the task succeed?” and “which step caused the failure?”.</p>
<div class="card warn"><div class="tag">⚠️ Migration note</div>Before events-only cutover, audit legacy trace-level evaluators, export jobs and internal queries that assume a trace is a standalone entity. In an observation-first model those usually need to target the <strong>root observation / observation id</strong>.</div>
<div class="card key"><div class="tag">🎯 Key points</div><ul>
<li>V4 real-time reads must migrate together with events ingestion; changing only the SDK is incomplete.</li>
<li>Observations v2 / Metrics v2 / Scores v3 cover detail, aggregation and scoring reads.</li>
<li>The useful eval loop is production observation → score → bad case → dataset → experiment → regression release.</li>
</ul></div>"""
LESSON_60 = {"zh": _ZH60, "en": _EN60}

_ZH61 = r"""<p class="lead">自托管从 v3 升到 v4，最大的错误是把它当成“镜像标签从 <code>:3</code> 改成 <code>:4</code>”。v4 没增加新的基础设施服务，但<strong>ClickHouse 数据模型和生产者/消费者协议都在迁移</strong>，所以应该把它当成一次数据平台变更。</p>
<div class="card analogy"><div class="tag">📋 生活类比</div>这不是“给商场换招牌”，而是“营业期间把仓库货架换掉”。正确方法是先让旧货架和新货架同时接货（dual write），确认新仓库能查、能算、能回滚，再把旧货架停掉。</div>
<h2>基础设施先升级到能承载 v4</h2>
<table class="t"><thead><tr><th>组件</th><th>迁移基线</th><th>职责</th></tr></thead><tbody>
<tr><td>PostgreSQL</td><td>15+（16 推荐）</td><td>项目、用户、prompt、dataset、配置</td></tr>
<tr><td>ClickHouse</td><td>25.12+（26.4 推荐）</td><td>events 宽事件与分析查询</td></tr>
<tr><td>Redis</td><td>7.0+（7.2 推荐）</td><td>BullMQ 队列、缓存、锁/限流</td></tr>
<tr><td>S3 / MinIO</td><td>兼容对象存储</td><td>媒体、blob、导出和部分异步载荷</td></tr>
<tr><td>web / worker</td><td>同一 v4 release</td><td>请求/UI 与后台任务</td></tr>
</tbody></table>
<h2>迁移不要一步跳：legacy → dual → events_only</h2>
<div class="vflow">
<div class="step"><div class="num">1</div><div class="sc"><h4>备份 + 升基础设施</h4><p>先备份 PostgreSQL 和 ClickHouse，再升级数据库/Redis 到支持版本。</p></div></div>
<div class="step"><div class="num">2</div><div class="sc"><h4>v4 server，先保 legacy/dual</h4><p>让应用升级，但继续保留旧路径，同时开始给新 events 写数据。</p></div></div>
<div class="step"><div class="num">3</div><div class="sc"><h4>回填历史数据</h4><p>将旧 traces/observations 转成新 events；大实例需要预留明显的额外 ClickHouse 空间。</p></div></div>
<div class="step"><div class="num">4</div><div class="sc"><h4>迁移所有生产者和读取者</h4><p>SDK/OTel producer、Observations/Metrics/Scores reader、eval、export 一起切新路径。</p></div></div>
<div class="step"><div class="num">5</div><div class="sc"><h4>events_only</h4><p>确认覆盖率、延迟、错误率和历史数据后，再停止 legacy 写入。</p></div></div>
</div>
<h2>历史回填为什么可能吃掉很多磁盘？</h2>
<p>迁移期间旧表不能立刻删，新 events 表又要逐步生成，所以一段时间内你会同时保留<strong>旧数据 + 新数据 + merge/临时空间</strong>。官方迁移说明给出的容量规划量级可到约 <strong>3× ClickHouse headroom</strong>。如果历史数据非常多，另一种策略是只保留迁移窗口，等待旧数据随 retention 滚出，而不是一次性全回填。</p>
<h2>第三方自托管实战暴露的一个真实坑</h2>
<div class="card warn"><div class="tag">⚠️ 实战经验</div>Jacar 在 v4.37.0 的 Docker Compose 实测里遇到过：<strong>worker 在 web 完成迁移前先启动，模型价格未正确加载，导致新 generation 没有成本</strong>；迁移完成后重启 worker，后续数据恢复正常。它不是“协议保证”，但提醒你：升级后不要只看容器是否 Up，要检查 web/worker 日志、迁移完成状态，以及一条真实 generation 是否能算出 token/cost。</div>
<h2>上线前的最小检查单</h2>
<table class="t"><thead><tr><th>检查</th><th>你要看到什么</th></tr></thead><tbody>
<tr><td>写入</td><td>新 SDK/OTel trace 能进入 events</td></tr>
<tr><td>读取</td><td>Observations v2 / Metrics v2 能及时看到同一数据</td></tr>
<tr><td>上下文</td><td>user/session/tags 在子 observations 上正确传播</td></tr>
<tr><td>评估</td><td>root observation 与局部 generation/tool score 都正常</td></tr>
<tr><td>成本</td><td>模型识别、token、price/cost 正常</td></tr>
<tr><td>恢复</td><td>备份已验证；不要假设 schema migration 后能靠降镜像自动回滚</td></tr>
</tbody></table>
<div class="card detail"><div class="tag">🔎 运维原则</div>生产环境不要把示例 Compose 当 HA 方案：数据库备份、ClickHouse 容量、Redis 持久性、对象存储、web/worker 副本、监控和升级顺序都要单独设计。版本也应 pin 到明确 release，而不是长期漂在浮动 tag。</div>
<div class="card key"><div class="tag">🎯 本课要点</div><ul>
<li>v4 自托管升级是<strong>数据迁移</strong>，不是镜像替换。</li>
<li>先基础设施，再 dual write/backfill，再迁 producer+reader，最后 events_only。</li>
<li>切换前验证一条完整业务链：trace → query → score → cost，而不只是“容器能启动”。</li>
</ul></div>"""
_EN61 = r"""<p class="lead">The biggest self-hosting mistake is treating v3 → v4 as “change the image tag from <code>:3</code> to <code>:4</code>”. V4 adds no new infrastructure service, but the <strong>ClickHouse data model and producer/consumer contracts are migrating</strong>, so this is a data-platform migration.</p>
<div class="card analogy"><div class="tag">📋 Analogy</div>This is not changing a mall sign; it is replacing warehouse shelves while the mall stays open. A safe rollout lets old and new shelves receive stock together (dual write), validates the new warehouse, then retires the old path.</div>
<h2>Upgrade the infrastructure foundation first</h2>
<table class="t"><thead><tr><th>Component</th><th>Migration baseline</th><th>Role</th></tr></thead><tbody>
<tr><td>PostgreSQL</td><td>15+ (16 recommended)</td><td>projects, users, prompts, datasets, config</td></tr>
<tr><td>ClickHouse</td><td>25.12+ (26.4 recommended)</td><td>events wide rows and analytics</td></tr>
<tr><td>Redis</td><td>7.0+ (7.2 recommended)</td><td>BullMQ queues, cache, locks/rate limits</td></tr>
<tr><td>S3 / MinIO</td><td>compatible object storage</td><td>media, blobs, exports and selected async payloads</td></tr>
<tr><td>web / worker</td><td>same v4 release</td><td>request/UI and background work</td></tr>
</tbody></table>
<h2>Do not jump in one step: legacy → dual → events_only</h2>
<div class="vflow">
<div class="step"><div class="num">1</div><div class="sc"><h4>Backup + infrastructure</h4><p>Back up PostgreSQL and ClickHouse, then move databases/Redis to supported versions.</p></div></div>
<div class="step"><div class="num">2</div><div class="sc"><h4>V4 server, preserve legacy/dual</h4><p>Upgrade the app while keeping old paths available and start writing the new events model.</p></div></div>
<div class="step"><div class="num">3</div><div class="sc"><h4>Backfill history</h4><p>Translate legacy traces/observations into events; large installations need substantial extra ClickHouse space.</p></div></div>
<div class="step"><div class="num">4</div><div class="sc"><h4>Migrate all producers and readers</h4><p>Move SDK/OTel producers, Observations/Metrics/Scores readers, evals and exports together.</p></div></div>
<div class="step"><div class="num">5</div><div class="sc"><h4>events_only</h4><p>Only stop legacy writes after checking coverage, latency, errors and history.</p></div></div>
</div>
<h2>Why can backfill need so much disk?</h2>
<p>During migration the old tables cannot disappear immediately while new events are being generated, so you temporarily carry <strong>old data + new data + merge/working space</strong>. The migration capacity guidance reaches roughly <strong>3× ClickHouse headroom</strong>. With very large history, a retention-window rollover can be safer than backfilling every old row at once.</p>
<h2>A useful third-party self-hosting failure</h2>
<div class="card warn"><div class="tag">⚠️ Field note</div>In a Langfuse 4.37.0 Docker Compose test, Jacar observed the <strong>worker starting before web migrations completed, model prices not loading correctly, and new generations missing cost</strong>; restarting the worker after migrations restored cost for subsequent data. This is not a protocol guarantee, but it is an excellent operational reminder: after an upgrade, inspect web/worker logs and run one real generation through token/cost calculation instead of checking only that containers are “Up”.</div>
<h2>Minimum pre-cutover checklist</h2>
<table class="t"><thead><tr><th>Check</th><th>What you should observe</th></tr></thead><tbody>
<tr><td>Write</td><td>new SDK/OTel traces arrive in events</td></tr>
<tr><td>Read</td><td>Observations v2 / Metrics v2 see the same data promptly</td></tr>
<tr><td>Context</td><td>user/session/tags propagate to child observations</td></tr>
<tr><td>Evaluation</td><td>root and local generation/tool scores work</td></tr>
<tr><td>Cost</td><td>model matching, tokens, pricing and cost are present</td></tr>
<tr><td>Recovery</td><td>backups are verified; do not assume a post-schema-migration image downgrade is rollback</td></tr>
</tbody></table>
<div class="card detail"><div class="tag">🔎 Operations principle</div>Do not mistake the example Compose for an HA production architecture. Backups, ClickHouse capacity, Redis durability, object storage, web/worker replicas, monitoring and upgrade ordering need explicit design. Pin releases rather than relying indefinitely on floating tags.</div>
<div class="card key"><div class="tag">🎯 Key points</div><ul>
<li>A self-hosted v4 upgrade is a <strong>data migration</strong>, not an image swap.</li>
<li>Upgrade infrastructure first, then dual-write/backfill, migrate producers + readers, and only then move to events_only.</li>
<li>Validate an end-to-end business path — trace → query → score → cost — not merely container startup.</li>
</ul></div>"""
LESSON_61 = {"zh": _ZH61, "en": _EN61}

