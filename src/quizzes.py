"""Per-lesson bilingual self-test (自测题): design-insight multiple-choice + open prompts.

Schema per lesson::

    "NN-file.html": {
        "mcq": [
            {
                "q":   {"zh": "...", "en": "..."},
                "opts": [{"zh": "...", "en": "..."}, ...],
                "answer": 1,                      # 0-based index into opts (as written)
                "why": {"zh": "...", "en": "..."},
            },
        ],
        "open": [{"zh": "...", "en": "..."}],
    }

``render(fname, lang)`` turns it into HTML that build.py appends to the bottom of
each language's lesson body. Options are deterministically shuffled per question
(same permutation for zh and en, so the correct letter matches across languages).

Quiz text (q/opts/why) is raw HTML in a text context (like the lesson body):
write literal ``<``/``&`` as ``&lt;``/``&amp;`` (or wrap code in ``<code>``).
"""
import hashlib

_HEAD = {"zh": "🧪 自测 · 想一想为什么这么设计", "en": "🧪 Self-test - think about the design"}
_SEE = {"zh": "看答案与解析", "en": "Show answer &amp; explanation"}
_CLICK = {"zh": "点击展开", "en": "click to expand"}
_ANS = {"zh": "答案：", "en": "Answer: "}
_SEP = {"zh": "。", "en": ". "}
_OPEN = {
    "zh": "💭 发散思考（没有标准答案，动手或动脑想想）",
    "en": "💭 Open questions (no single right answer - just think or try)",
}


def _shuffle(opts, answer, seed):
    """Deterministically permute opts (stable across builds); return
    (new_opts, new_answer_index) so the correct option lands in a varied slot."""
    order = sorted(
        range(len(opts)),
        key=lambda i: hashlib.md5(f"{seed}:{i}".encode("utf-8")).hexdigest(),
    )
    return [opts[i] for i in order], order.index(answer)


QUIZZES = {
    "01-what-is-langfuse.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 把 <code>observation</code>（而不是 trace）当作“主分析单元”。这个定位最主要带来什么不同？",
                    "en": "Langfuse treats the <code>observation</code> (not the trace) as the primary analytical unit. What is the main difference this brings?",
                },
                "opts": [
                    {
                        "zh": "每个 LLM 调用/检索步骤本身就是一条带丰富属性的宽事件，可独立切片聚合；trace 只是把它们关联起来的句柄",
                        "en": "Each LLM call/retrieval step is itself a richly-attributed wide event you can slice & aggregate; the trace is just a handle that correlates them",
                    },
                    {"zh": "它把所有数据压缩成一个 trace 大对象，查询时整体读出", "en": "It compresses everything into one big trace object read whole at query time"},
                    {"zh": "它取消了 trace 概念，只保留扁平日志", "en": "It removes the trace concept and keeps only flat logs"},
                    {"zh": "它要求每个 trace 只能有一个 observation", "en": "It requires each trace to have exactly one observation"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是“可观测性 2.0 / 宽事件”的核心：把高基数上下文留在每条 observation 上，用户就能在不预设问题的前提下任意切片、分组、过滤。trace 仍在，但它是关联句柄，不是唯一入口（见 <code>.agents/ARCHITECTURE_PRINCIPLES.md</code>）。",
                    "en": "This is the heart of 'Observability 2.0 / wide events': keep high-cardinality context on each observation so users can slice, group and filter without predefining questions. The trace still exists, but as a correlation handle, not the only entry point (see <code>.agents/ARCHITECTURE_PRINCIPLES.md</code>).",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 为什么要同时用 Postgres 和 ClickHouse 两套数据库，而不是只用一套？",
                    "en": "Why does Langfuse use both Postgres and ClickHouse instead of just one database?",
                },
                "opts": [
                    {
                        "zh": "事务性配置/元数据（项目、用户、prompt、配置）适合 Postgres；海量、可追加的宽事件（trace/observation/score）适合列存的 ClickHouse 做时间窗口扫描与聚合",
                        "en": "Transactional config/metadata (projects, users, prompts, settings) fits Postgres; high-volume append-oriented wide events (trace/observation/score) fit columnar ClickHouse for time-bounded scans & aggregation",
                    },
                    {"zh": "因为 Postgres 不能存字符串", "en": "Because Postgres cannot store strings"},
                    {"zh": "纯粹为了用更多技术显得复杂", "en": "Purely to look more complex by using more tech"},
                    {"zh": "ClickHouse 用来做用户登录，Postgres 用来跑 ML", "en": "ClickHouse handles logins while Postgres runs ML"},
                ],
                "answer": 0,
                "why": {
                    "zh": "两类负载的访问模式根本不同：元数据是小数据量、强一致、频繁更新——交给 Postgres；遥测是大数据量、写多于改、按时间和项目聚合——交给 ClickHouse（宽事件、列存、ReplacingMergeTree）。用对存储，热路径才不会被拖垮。",
                    "en": "The two workloads have fundamentally different access patterns: metadata is small, strongly-consistent and frequently updated — Postgres; telemetry is huge, write-mostly and aggregated by time/project — ClickHouse (wide events, columnar, ReplacingMergeTree). Matching storage to pattern keeps the hot path fast.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的摄取为什么走“SDK → 公共 API → 队列 → worker → ClickHouse”这条异步链路，而不是 API 直接写 ClickHouse？",
                    "en": "Why does ingestion go 'SDK → public API → queue → worker → ClickHouse' asynchronously instead of the API writing ClickHouse directly?",
                },
                "opts": [
                    {
                        "zh": "解耦与削峰：API 只需快速收下事件并入队，重活（合并、token/成本计算、批量写）交给 worker 异步处理，既抗流量尖峰又能批量高效写入",
                        "en": "Decoupling & smoothing: the API just accepts and enqueues fast, while the heavy work (merge, token/cost compute, batched writes) runs async in the worker — absorbing spikes and writing in efficient batches",
                    },
                    {"zh": "因为 ClickHouse 只接受来自 worker 的连接", "en": "Because ClickHouse only accepts connections from the worker"},
                    {"zh": "队列是用来加密数据的", "en": "The queue is there to encrypt the data"},
                    {"zh": "为了让写入更慢以节省成本", "en": "To make writes slower and save cost"},
                ],
                "answer": 0,
                "why": {
                    "zh": "把“接收”和“处理”分开，是高吞吐遥测系统的经典做法。API 端轻量、可水平扩展、对 SDK 低延迟；worker 端可重试、可批量、可分片（主/次队列隔离高吞吐项目）。代价是“最终一致”——数据有秒级处理延迟，这正是 §设计取舍要权衡的。",
                    "en": "Separating 'accept' from 'process' is the classic shape for high-throughput telemetry. The API stays lightweight, horizontally scalable and low-latency to the SDK; the worker can retry, batch and shard (primary/secondary queues isolate high-throughput projects). The cost is eventual consistency — a few seconds of processing lag, exactly the trade-off to weigh.",
                },
            },
        ],
        "open": [
            {
                "zh": "如果让你给一个自研的 LLM 应用加“可观测性”，你会先记录哪三类信息到每条 observation 上？为什么这三类最能帮你事后 debug？",
                "en": "If you were adding 'observability' to your own LLM app, which three kinds of data would you record on each observation first, and why would those three help you debug later?",
            },
        ],
    },
    "02-observability-2-and-wide-events.html": {
        "mcq": [
            {
                "q": {
                    "zh": "“可观测性 1.0（指标+日志+链路）”和“2.0（宽事件）”最本质的区别是什么？",
                    "en": "What is the most essential difference between Observability 1.0 (metrics+logs+traces) and 2.0 (wide events)?",
                },
                "opts": [
                    {
                        "zh": "1.0 把信息拆进三套分离的系统、回答跨维度问题前要人肉拼接；2.0 把一步的数字/结构/业务字段放进同一行，下钻与聚合都成了对同一张宽表的查询",
                        "en": "1.0 splits info across three separate systems and needs manual reassembly for cross-dimension questions; 2.0 puts numbers/structure/business fields of one step on one row, so drill-down and aggregation are both queries over one wide table",
                    },
                    {"zh": "2.0 不再存储任何数字指标", "en": "2.0 stops storing any numeric metrics"},
                    {"zh": "1.0 更快，因为数据更宽", "en": "1.0 is faster because the data is wider"},
                    {"zh": "2.0 要求每个 trace 只能有一条 observation", "en": "2.0 requires exactly one observation per trace"},
                ],
                "answer": 0,
                "why": {
                    "zh": "关键不在“用不用指标”，而在“分不分离”。1.0 的三件套各存一处，跨维度问题要在三套系统间对账；2.0 把高基数上下文整行留存，新问题只是换个查询。这正是 ARCHITECTURE_PRINCIPLES.md 第一条与第二条。",
                    "en": "The point isn't whether you use metrics, but whether things are separated. 1.0's three pillars live apart, forcing reconciliation across systems; 2.0 keeps high-cardinality context on the row, so a new question is just a new query. That's principles one and two in ARCHITECTURE_PRINCIPLES.md.",
                },
            },
            {
                "q": {
                    "zh": "为什么说宽事件能回答“unknown unknowns”，而预聚合指标不能？",
                    "en": "Why can wide events answer 'unknown unknowns' while pre-aggregated metrics cannot?",
                },
                "opts": [
                    {
                        "zh": "预聚合在上线前就把维度固定了，只能回答已建好的图；宽事件保留高基数整行，事后想到的新切法换个查询即可，无需改埋点或重新上线",
                        "en": "Pre-aggregation fixes dimensions before shipping, answering only charts you built; wide events keep the full high-cardinality row, so any slice thought of later is just a new query — no re-instrumenting or redeploy",
                    },
                    {"zh": "因为宽事件用了更贵的数据库", "en": "Because wide events use a more expensive database"},
                    {"zh": "因为预聚合指标不支持时间维度", "en": "Because pre-aggregated metrics don't support a time dimension"},
                    {"zh": "因为宽事件会自动猜测你想问的问题", "en": "Because wide events automatically guess your questions"},
                ],
                "answer": 0,
                "why": {
                    "zh": "“unknown unknowns”是你当初没想到要问的问题。预聚合把“能问什么”锁死在上线时；宽事件把上下文整行留下，于是定义新视图从“改埋点+重新上线”降级成“写一条新查询”——这是平台可扩展性的地基。",
                    "en": "'Unknown unknowns' are questions you didn't foresee. Pre-aggregation locks 'what you can ask' at ship time; wide events keep the context on the row, demoting 'define a new view' from 're-instrument + redeploy' to 'write a new query' — the foundation of platform extensibility.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 为什么把 model、usageDetails、costDetails 等<strong>内联</strong>到 observation 行上，而不是拆成多张表用外键关联？",
                    "en": "Why does Langfuse <strong>inline</strong> model, usageDetails, costDetails onto the observation row instead of splitting into normalized tables with foreign keys?",
                },
                "opts": [
                    {
                        "zh": "为了消除热路径上的 JOIN：可观测数据量极大，常用过滤/聚合若每次都要连表代价会爆炸；内联后“按模型/用户/时间”变成直接的列谓词",
                        "en": "To kill hot-path JOINs: observability data is huge, so joining for common filters/aggregations would explode in cost; inlining turns 'by model/user/time' into plain column predicates",
                    },
                    {"zh": "因为 ClickHouse 不支持多张表", "en": "Because ClickHouse doesn't support multiple tables"},
                    {"zh": "因为外键在任何数据库里都非法", "en": "Because foreign keys are illegal in any database"},
                    {"zh": "纯粹为了占用更多磁盘", "en": "Purely to use more disk"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这就是“谨慎反范式化”原则：用一点存储冗余换查询时不必连表。在上亿行规模下，把常用来过滤聚合的字段内联到行上，让高频查询变成直接列谓词，是把宽事件做快的关键一招（第 8 课展开）。",
                    "en": "This is the 'denormalize carefully' principle: trade a little storage redundancy for not joining at query time. At hundreds-of-millions-of-rows scale, inlining the fields used to filter/aggregate so hot queries become column predicates is key to making wide events fast (expanded in L08).",
                },
            },
        ],
        "open": [
            {
                "zh": "想象你维护一个公司内部的 LLM 网关，老板突然问“上周哪个部门、用哪个模型、花了最多钱”。如果你只有传统的“平均成本”指标，会卡在哪？换成宽事件后这个问题怎么变简单？",
                "en": "Imagine you run an internal LLM gateway and your boss asks 'which department, on which model, spent the most last week'. If you only had a traditional 'average cost' metric, where would you get stuck? How does a wide event make this easy?",
            },
        ],
    },
    "03-three-pillars-deep.html": {
        "mcq": [
            {
                "q": {
                    "zh": "为什么 Langfuse 把 model/token/cost/prompt 等“重”字段都放在 observation 上，而让 trace 只有身份与少数标记？",
                    "en": "Why does Langfuse put the 'heavy' fields (model/token/cost/prompt) on the observation while the trace has only identity and a few markers?",
                },
                "opts": [
                    {
                        "zh": "因为绝大多数查询发生在“步”这个粒度（按模型、按 prompt 版本聚合过滤），把这些维度放在 observation 上，常用查询就成了对宽表的直接列谓词；trace 只需负责关联",
                        "en": "Because most queries happen at the 'step' granularity (aggregate/filter by model, by prompt version); putting those dimensions on the observation makes common queries direct column predicates over the wide table, while the trace just correlates",
                    },
                    {"zh": "因为 trace 不允许有任何字段", "en": "Because a trace may not have any fields"},
                    {"zh": "因为 observation 存在 Postgres，trace 存在 ClickHouse", "en": "Because observations live in Postgres and traces in ClickHouse"},
                    {"zh": "因为这样能减少 SVG 数量", "en": "Because it reduces the number of SVGs"},
                ],
                "answer": 0,
                "why": {
                    "zh": "查询的粒度决定了字段的归属。把高频过滤/聚合维度放在 observation 上，热查询变成列谓词、无需 JOIN；trace 保持薄、只做关联。代价是 userId 等可能在两边冗余，这正是“谨慎反范式化”。",
                    "en": "Query granularity decides where fields belong. Put the hot filter/aggregate dimensions on the observation so hot queries become column predicates without JOINs; keep the trace thin for correlation. The cost is some redundancy (e.g. userId) — exactly 'denormalize carefully'.",
                },
            },
            {
                "q": {
                    "zh": "observation 之间的父子关系只用子节点上的一个 parentObservationId 指针表达。这个设计对“异步摄取”有什么关键好处？",
                    "en": "Parent-child links among observations are expressed only by a parentObservationId pointer on the child. What's the key benefit for async ingestion?",
                },
                "opts": [
                    {
                        "zh": "每个 observation 自带“我爸是谁”，于是它们能各自独立、乱序到达服务端；子节点先于父节点到也没关系，查询时 UI 再按指针拼出整棵树",
                        "en": "Each observation carries 'who my parent is', so they can arrive independently and out of order; a child arriving before its parent is fine, and the UI rebuilds the tree from pointers at query time",
                    },
                    {"zh": "它让父节点能实时统计自己有几个孩子", "en": "It lets the parent count its children in real time"},
                    {"zh": "它要求所有 observation 必须按顺序写入", "en": "It requires all observations to be written in order"},
                    {"zh": "它把树结构存成了一张额外的关系表", "en": "It stores the tree as an extra relational table"},
                ],
                "answer": 0,
                "why": {
                    "zh": "若反过来让父节点维护 children 列表，就得“等所有孩子到齐才能写父节点”，在高并发异步管线里是灾难。只存子节点的父指针，写入彻底解耦、可乱序，是摄取链路可行的关键（第 25 课拼树）。",
                    "en": "If the parent maintained a children list, you'd have to 'wait for all children before writing the parent' — a disaster in a high-concurrency async pipeline. Storing only the child's parent pointer fully decouples writes and allows any order, key to the ingestion path (tree rebuilt in L25).",
                },
            },
            {
                "q": {
                    "zh": "observation 上为什么同时有 providedUsageDetails 和 usageDetails（成本同理）两套字段？",
                    "en": "Why does an observation carry both providedUsageDetails and usageDetails (and similarly for cost)?",
                },
                "opts": [
                    {
                        "zh": "provided 是 SDK 上报时自带的，usage 是 Langfuse 摄取时按模型定价自己算的；“你报的我尊重、你没报的我兜底”",
                        "en": "'provided' is what the SDK reported, 'usage' is what Langfuse computed at ingestion from model pricing; 'respect what you sent, backfill what you didn't'",
                    },
                    {"zh": "两者完全相同，纯属冗余", "en": "They are identical, pure redundancy"},
                    {"zh": "provided 给前端用，usage 给后端用", "en": "'provided' is for the frontend, 'usage' for the backend"},
                    {"zh": "一个存 token，一个存金额", "en": "One stores tokens, the other money"},
                ],
                "answer": 0,
                "why": {
                    "zh": "两套并存兼顾“应用精确控制”和“平台兜底”：应用知道精确用量就直接报（provided），不报时 Langfuse 按 model 名匹配定价表算出来（computed）。这套“provided 优先、computed 兜底”在成本计算课（第 16 课）会展开。",
                    "en": "Having both balances 'app precision' and 'platform backfill': if the app knows exact usage it reports it (provided); if not, Langfuse computes it from the model pricing table (computed). This 'provided wins, computed backfills' is expanded in the cost lesson (L16).",
                },
            },
        ],
        "open": [
            {
                "zh": "如果让你设计 score 的“来源”枚举，你会不会也像 Langfuse 一样禁止外部 API 提交 EVAL 来源的分数？说说这么做在“信任谁打的分”上的意义。",
                "en": "If you designed the score 'source' enum, would you also forbid external API callers from submitting EVAL-sourced scores like Langfuse does? Discuss what this means for trusting 'who scored'.",
            },
        ],
    },
    "04-project-map-monorepo.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 规定依赖只能 web/worker/ee → shared，而 shared 不依赖任何一方。这条“窄腰”规则最主要的好处是什么？",
                    "en": "Langfuse mandates that dependencies go only web/worker/ee → shared, and shared depends on none. What's the main benefit of this 'narrow waist' rule?",
                },
                "opts": [
                    {
                        "zh": "两个容器各自独立演进/部署，却共用同一套领域模型与队列契约，契约集中在一处定义、不会漂移",
                        "en": "The two containers evolve/deploy independently yet share one set of domain models and queue contracts, defined in one place so they can't drift",
                    },
                    {"zh": "让 shared 包能直接调用 web 的 React 组件", "en": "It lets shared call web's React components directly"},
                    {"zh": "让构建变慢以便缓存", "en": "It slows builds so caching kicks in"},
                    {"zh": "强制 web 和 worker 跑在同一个进程里", "en": "It forces web and worker into one process"},
                ],
                "answer": 0,
                "why": {
                    "zh": "web（低延迟、面向用户）和 worker（重活、可重试）是两种负载；让它们互相直接依赖会彼此牵连。把共享内容收进谁都不反向依赖的 shared，并只许向下依赖，就在两容器间立了契约墙——队列传什么、表长什么样都由 shared 一处定义。",
                    "en": "web (low-latency, user-facing) and worker (heavy, retryable) are different workloads; letting them depend on each other entangles them. Collecting shared content into a shared that nothing depends on backwards, with only-downward deps, erects a contract wall — what goes through queues and what tables look like are defined in one place.",
                },
            },
            {
                "q": {
                    "zh": "turbo.json 里 build 任务写着 \"dependsOn\": [\"db:generate\", \"^build\"]。这表示什么？",
                    "en": "In turbo.json the build task says \"dependsOn\": [\"db:generate\", \"^build\"]. What does that mean?",
                },
                "opts": [
                    {
                        "zh": "构建任何包之前，先生成 Prisma 客户端，并先构建它依赖的上游包（^ 表示上游）；Turbo 据此算出顺序、并行、并跳过缓存命中的部分",
                        "en": "Before building any package, generate the Prisma client and first build its upstream deps (^ = upstream); Turbo computes order, parallelizes, and skips cache hits",
                    },
                    {"zh": "build 任务永远不能被缓存", "en": "The build task can never be cached"},
                    {"zh": "db:generate 必须手动在 build 之后运行", "en": "db:generate must be run manually after build"},
                    {"zh": "^build 表示构建下游的包", "en": "^build means build the downstream packages"},
                ],
                "answer": 0,
                "why": {
                    "zh": "dependsOn 声明任务依赖图：db:generate 先于 build（要先有 Prisma 类型），^build 表示先构建上游依赖包。于是一条 pnpm build 就能让 Turbo 自动排序、并行、并对没变的包命中缓存——大仓也能增量构建。",
                    "en": "dependsOn declares the task graph: db:generate before build (need Prisma types first), ^build means build upstream dep packages first. So one pnpm build lets Turbo order, parallelize, and cache-hit unchanged packages — incremental builds even in a big repo.",
                },
            },
            {
                "q": {
                    "zh": "给 trace 加一个字段，在 Langfuse 的 monorepo 里大致怎么落地？",
                    "en": "Adding a field to the trace in Langfuse's monorepo roughly takes what steps?",
                },
                "opts": [
                    {
                        "zh": "改 prisma/schema.prisma 与 domain/traces.ts，db:generate 后 web 和 worker 都从同一个 @langfuse/shared 拿到新类型，一个 PR、CI 一起验",
                        "en": "Edit prisma/schema.prisma and domain/traces.ts; after db:generate both web and worker pick up the new type from the same @langfuse/shared, in one PR verified together by CI",
                    },
                    {"zh": "在三个独立仓库各发一次版，再手动对版本", "en": "Release three separate repos and manually align versions"},
                    {"zh": "只能改 web，worker 不受影响", "en": "Only web changes; worker is unaffected"},
                    {"zh": "必须先删掉旧的 ClickHouse 表", "en": "You must first drop the old ClickHouse table"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这正是 monorepo + 窄腰的价值：共享结构改一处，web/worker 都从 @langfuse/shared 取，原子地在一个 PR 完成、一起过 CI。分仓则要跨仓发版对版本、易漂移。",
                    "en": "This is exactly the monorepo + narrow-waist payoff: change the shared structure once, both web/worker pull from @langfuse/shared, done atomically in one PR through CI together. Polyrepo would need cross-repo releases and version alignment, inviting drift.",
                },
            },
        ],
        "open": [
            {
                "zh": "你自己的项目如果同时有“面向用户的服务”和“后台 worker”，你会把它们放一个仓还是分仓？参考 Langfuse 的窄腰，你会把哪些东西抽进一个共享层？",
                "en": "If your own project had both a 'user-facing service' and a 'background worker', would you keep them in one repo or split? Borrowing Langfuse's narrow waist, what would you pull into a shared layer?",
            },
        ],
    },
    "05-life-of-a-trace.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的摄取为什么是异步的（API 收下就入队返回，由 worker 后台处理），而不是 API 同步写完 ClickHouse 才返回？",
                    "en": "Why is Langfuse ingestion async (the API enqueues and returns, the worker processes in the background) rather than the API synchronously writing ClickHouse before returning?",
                },
                "opts": [
                    {
                        "zh": "为了让 API 永远毫秒级返回、几乎不拖累你的应用，并能用队列做缓冲：洪峰先排队、worker 批量可重试地消费、扛不住就横向扩容",
                        "en": "So the API always returns in ms and barely drags your app, and the queue buffers: spikes queue up, the worker consumes in batches retryably, and you scale out when overwhelmed",
                    },
                    {"zh": "因为 ClickHouse 不支持同步写入", "en": "Because ClickHouse doesn't support synchronous writes"},
                    {"zh": "为了故意增加延迟以省钱", "en": "To deliberately add latency to save money"},
                    {"zh": "因为 API 不能访问数据库", "en": "Because the API cannot access the database"},
                ],
                "answer": 0,
                "why": {
                    "zh": "若 API 同步合并/算成本/写库，你每次 LLM 调用都被拖慢，且下游一抖动 API 就超时甚至把错误反弹给业务。异步把“收件”和“处理”解耦：API 极轻、几乎不可能慢；worker 批量、可重试、可扩容地消化洪峰。代价是秒级延迟（最终一致）。",
                    "en": "If the API synchronously merged/costed/wrote, every LLM call is slowed and a downstream hiccup times out the API or bounces errors into your business. Async decouples accept from process: the API is featherweight and rarely slow; the worker digests spikes in batches, retryably, scalably. The cost is seconds of lag (eventual consistency).",
                },
            },
            {
                "q": {
                    "zh": "worker 处理时为什么要回 S3 取“这个 id 的历史事件”再合并？",
                    "en": "Why does the worker re-read 'this id's prior events' from S3 and merge during processing?",
                },
                "opts": [
                    {
                        "zh": "因为一个 observation 常被分多次、可能乱序地上报（先 create 再 update），worker 必须把这些碎片合并成一条一致的最终记录",
                        "en": "Because one observation is often reported in multiple, possibly out-of-order events (create then update), and the worker must merge these fragments into one consistent final record",
                    },
                    {"zh": "因为 ClickHouse 会丢数据，要从 S3 恢复", "en": "Because ClickHouse loses data and must restore from S3"},
                    {"zh": "因为 S3 比队列快", "en": "Because S3 is faster than the queue"},
                    {"zh": "因为合并必须在前端做", "en": "Because merging must happen in the frontend"},
                ],
                "answer": 0,
                "why": {
                    "zh": "SDK 上报往往不是一次性的：先发 create（我开始了），调用返回后再发 update（输出/用量）。两条分别到达，worker 回 S3 取历史把碎片拼成完整一行。这也支撑了“事件可乱序到达、worker 收敛成最终态”，正是第 3 课 parentObservationId 设计的运行时体现。",
                    "en": "SDK reporting often isn't one-shot: a create ('I started') then an update ('output/usage') after the call returns. They arrive separately; the worker re-reads S3 to stitch the fragments into one row. This supports 'events arrive out of order, worker converges to final state' — the runtime realization of L03's parentObservationId design.",
                },
            },
            {
                "q": {
                    "zh": "“最终一致”对使用 Langfuse 意味着什么实践注意点？",
                    "en": "What practical caveat does 'eventual consistency' imply when using Langfuse?",
                },
                "opts": [
                    {
                        "zh": "刚埋点的数据可能要等一两秒才在 UI 出现；别把它当强一致业务库，写自动化测试验证埋点时要给摄取留处理时间",
                        "en": "Just-instrumented data may take a second or two to appear in the UI; don't treat it as a strongly-consistent business DB, and when testing instrumentation, allow ingestion time to process",
                    },
                    {"zh": "数据永远不会出现", "en": "Data will never appear"},
                    {"zh": "必须手动刷新数据库连接", "en": "You must manually refresh the DB connection"},
                    {"zh": "trace 会随机丢失", "en": "Traces are randomly lost"},
                ],
                "answer": 0,
                "why": {
                    "zh": "异步摄取有秒级处理延迟，对“事后排查/看板/评估”完全够用，但意味着“写完不一定立刻可读”。所以别拿它当强一致库；自动化验证埋点时要等摄取处理完，否则会误判“数据没上来”。",
                    "en": "Async ingestion has seconds of processing lag — fine for after-the-fact triage/dashboards/eval, but it means 'written isn't instantly readable'. So don't treat it as a strongly-consistent store; when verifying instrumentation in tests, wait for ingestion or you'll falsely conclude 'no data arrived'.",
                },
            },
        ],
        "open": [
            {
                "zh": "回顾第一部分：用你自己的话，把“一条 trace 的一生”讲给一个没用过 Langfuse 的同事听（从 SDK 到 UI）。你觉得哪一段最容易被忽略、但其实最关键？",
                "en": "Recap Part 1: in your own words, tell a colleague who's never used Langfuse the 'life of a trace' from SDK to UI. Which leg do you think is most overlooked yet most crucial?",
            },
        ],
    },
    "06-instrumenting-an-llm-app.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 为什么既支持自家 SDK 的“原生事件”，又支持 OpenTelemetry（OTLP）？",
                    "en": "Why does Langfuse support both its own SDK 'native events' and OpenTelemetry (OTLP)?",
                },
                "opts": [
                    {
                        "zh": "原生 SDK 表达力最强（精确报 prompt/用量/成本），OTel 则让已经用 OTel 的系统无缝接入、无需重写埋点；两者各服务一类用户",
                        "en": "The native SDK is most expressive (precise prompt/usage/cost), while OTel lets systems already on OTel plug in without rewriting instrumentation; each serves a different user",
                    },
                    {"zh": "因为原生 SDK 已经废弃，OTel 是唯一入口", "en": "Because the native SDK is deprecated and OTel is the only entry"},
                    {"zh": "因为 OTel 比原生事件携带更多 LLM 专有语义", "en": "Because OTel carries more LLM-specific semantics than native events"},
                    {"zh": "为了让数据走两条完全独立的存储", "en": "To route data into two completely separate stores"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是“拥抱标准 vs 发挥专长”的权衡：OTel 是云原生可观测的事实标准，支持它降低接入门槛；但其通用模型不天然懂 prompt 版本/token 用量，原生 SDK 更精确。Langfuse 两者都要——OTLP 降门槛，原生 SDK 给最佳体验。",
                    "en": "This is 'embrace the standard vs play to strengths': OTel is the de-facto cloud-native standard, so supporting it lowers the barrier; but its generic model doesn't natively grok prompt version/token usage, where the native SDK is more precise. Langfuse does both — OTLP for reach, native SDK for the best experience.",
                },
            },
            {
                "q": {
                    "zh": "一个 span 型 observation 常常先发 SPAN_CREATE、结束时再发 SPAN_UPDATE。这种“增量上报”的主要好处是什么？",
                    "en": "A span-type observation often sends SPAN_CREATE first, then SPAN_UPDATE at the end. What's the main benefit of this 'incremental reporting'?",
                },
                "opts": [
                    {
                        "zh": "能更早记下“它开始了”，即使后面崩溃/超时也知道卡在哪步——失败 case 不会因为“没等到结束”而彻底消失",
                        "en": "It records 'it started' earlier, so even if it later crashes/times out you know which step stalled — failure cases don't vanish just because 'the end never came'",
                    },
                    {"zh": "为了减少事件数量", "en": "To reduce the number of events"},
                    {"zh": "因为 ClickHouse 只接受两次写入", "en": "Because ClickHouse only accepts two writes"},
                    {"zh": "为了让 SDK 自己拼装最终状态", "en": "So the SDK assembles the final state itself"},
                ],
                "answer": 0,
                "why": {
                    "zh": "若等结束才发一条完整事件，一旦中途挂掉这一步就彻底消失，而失败恰恰最该被观测。增量上报 = “边发生边记录”，服务端再把 create+update 合并成一条（第 15 课）。",
                    "en": "Waiting to send one complete event means a mid-flight crash erases that step — yet failures are exactly what you most want to observe. Incremental reporting = 'record as it happens', and the server merges create+update into one row (L15).",
                },
            },
            {
                "q": {
                    "zh": "这套“事件增量上报 + 合并”的协议，把最复杂的合并逻辑放在哪一端？为什么？",
                    "en": "In this 'incremental events + merge' protocol, where does the most complex merge logic live, and why?",
                },
                "opts": [
                    {
                        "zh": "放在服务端（worker）：SDK 只管把小事件发出去，合并“可能乱序/重复的事件成一致一行”只在一处维护，避免每种语言 SDK 各写各错",
                        "en": "On the server (worker): SDKs just emit small events; merging 'possibly out-of-order/duplicate events into one consistent row' lives in one place, avoiding each language SDK re-implementing (and re-bugging) it",
                    },
                    {"zh": "放在 SDK：每个语言各自实现合并", "en": "In the SDK: each language implements merging itself"},
                    {"zh": "放在数据库触发器里", "en": "In database triggers"},
                    {"zh": "放在前端 UI 渲染时", "en": "In the frontend at render time"},
                ],
                "answer": 0,
                "why": {
                    "zh": "把复杂度收敛到一个能严格测试的地方（服务端）：SDK 因此轻、好移植、对应用影响小；合并这种最易错的逻辑只在 worker 维护一份，而不是散落在每个语言 SDK 里。",
                    "en": "Converge complexity to one strictly testable place (the server): SDKs stay light, portable and low-impact; the error-prone merge logic is maintained once in the worker rather than scattered across every language SDK.",
                },
            },
        ],
        "open": [
            {
                "zh": "如果你要给自己的应用加埋点，你会选 Langfuse 原生 SDK 还是 OpenTelemetry？你的系统现状（有没有已用 OTel、需不需要精确成本）会怎么影响这个选择？",
                "en": "If you were instrumenting your own app, would you pick the Langfuse native SDK or OpenTelemetry? How would your system's current state (already on OTel? need precise cost?) shape that choice?",
            },
        ],
    },
    "07-dual-store-architecture.html": {
        "mcq": [
            {
                "q": {
                    "zh": "为什么 Langfuse 把配置/元数据放 Postgres、把 trace/observation/score 放 ClickHouse，而不是统一用一个库？",
                    "en": "Why does Langfuse put config/metadata in Postgres and trace/observation/score in ClickHouse, rather than one database for all?",
                },
                "opts": [
                    {
                        "zh": "因为两者是相反的负载：配置是 OLTP（小、精确单条读写、强一致），遥测是 OLAP（海量、按时间窗口+维度聚合）；没有哪个库能把两头都做到极致",
                        "en": "Because they're opposite workloads: config is OLTP (small, precise single-row, strongly consistent), telemetry is OLAP (massive, time-window + dimensional aggregation); no single store nails both extremes",
                    },
                    {"zh": "因为 ClickHouse 不能存字符串", "en": "Because ClickHouse can't store strings"},
                    {"zh": "因为 Postgres 不支持索引", "en": "Because Postgres has no indexes"},
                    {"zh": "纯粹为了用更多技术", "en": "Purely to use more tech"},
                ],
                "answer": 0,
                "why": {
                    "zh": "配置要精确读写单条且强一致（创建即可用），是行存 Postgres 的主场；遥测海量、写多于改、按维度聚合，是列存 ClickHouse 的主场。硬塞进一个必然顾此失彼。这是“按访问模式选存储”。",
                    "en": "Config needs precise single-row read/write and strong consistency (instantly usable) — row-store Postgres's turf; telemetry is massive, write-mostly, dimensionally aggregated — columnar ClickHouse's turf. Forcing one store loses both ways. This is 'choose storage by access pattern'.",
                },
            },
            {
                "q": {
                    "zh": "在摄取链路里，S3 扮演的关键角色是什么？",
                    "en": "What key role does S3 play in the ingestion path?",
                },
                "opts": [
                    {
                        "zh": "事件的“真相之源/原始日志”：事件先落 S3，worker 合并时回 S3 取历史；ClickHouse 的宽事件相当于其合并后的派生表，理论上可从 S3 重放重建",
                        "en": "The events' 'source of truth / raw log': events land in S3 first, the worker re-reads S3 to merge; ClickHouse wide events are the merged derived table, in principle replayable from S3",
                    },
                    {"zh": "只是存上传的图片，和摄取无关", "en": "Just stores uploaded images, unrelated to ingestion"},
                    {"zh": "代替 Redis 做队列", "en": "Replaces Redis as the queue"},
                    {"zh": "存用户密码", "en": "Stores user passwords"},
                ],
                "answer": 0,
                "why": {
                    "zh": "S3 不只是大文件仓。事件先落 S3 作为不可变原始日志，worker 据此合并出 ClickHouse 宽事件（派生/物化）。这正是第 2 课“不可变/追加式事件”的体现，也让数据可重放重建。",
                    "en": "S3 isn't just a big-file store. Events land in S3 as an immutable raw log, from which the worker merges ClickHouse wide events (derived/materialized). This is L02's 'immutable/append-oriented events', and makes data replayable.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 用四种存储，但第 2 课又说“把运维简单性当约束”。怎么调和？判断“该不该再加一个存储”的标准是什么？",
                    "en": "Langfuse uses four stores, yet L02 says 'treat operational simplicity as a constraint'. How to reconcile? What's the test for 'should we add another store'?",
                },
                "opts": [
                    {
                        "zh": "每个存储都必须挣到自己的存在——它解决的硬问题是否值得它带来的长期运维成本（备份/监控/升级/容灾）",
                        "en": "Each store must earn its existence — does the hard problem it solves justify its long-term ops cost (backup/monitoring/upgrade/DR)",
                    },
                    {"zh": "存储越多越好，多多益善", "en": "More stores are always better"},
                    {"zh": "永远只能用一个数据库", "en": "You may only ever use one database"},
                    {"zh": "由前端框架决定", "en": "The frontend framework decides"},
                ],
                "answer": 0,
                "why": {
                    "zh": "四存储不是“想加就加”：ClickHouse 解决海量聚合、Redis 解决异步抗洪峰、S3 解决大字段+重放，各自解决单库做不到的硬问题，所以挣到了存在。这也正是判断要不要再加存储的标准。",
                    "en": "The four aren't 'add because we can': ClickHouse solves huge aggregation, Redis solves async spike absorption, S3 solves big fields + replay — each solving what one store can't, thus earning its place. That's exactly the test for adding another store.",
                },
            },
        ],
        "open": [
            {
                "zh": "想象你在设计一个新的日志/监控系统，预算有限。你会从一个 Postgres 起步，还是一开始就上 ClickHouse？在什么规模/查询模式下，引入列存才真正“挣到存在”？",
                "en": "Imagine designing a new logging/monitoring system on a tight budget. Would you start with one Postgres, or bring in ClickHouse from day one? At what scale/query pattern does a columnar store truly 'earn its existence'?",
            },
        ],
    },
    "08-clickhouse-wide-events.html": {
        "mcq": [
            {
                "q": {
                    "zh": "ReplacingMergeTree(event_ts, is_deleted) 的核心语义是什么？它怎么承接“一个 observation 先 create 后 update”？",
                    "en": "What's the core semantic of ReplacingMergeTree(event_ts, is_deleted)? How does it absorb 'an observation created then updated'?",
                },
                "opts": [
                    {
                        "zh": "排序键相同的多行会被替换成 event_ts 最大的那条（is_deleted 软删除）；create 与 update 是两次同 id 写入，后台合并时自动用 update 覆盖 create——只管追加，覆盖交给引擎",
                        "en": "Rows with the same ordering key collapse to the largest event_ts (is_deleted soft-deletes); create and update are two writes of the same id, and background merge auto-overwrites create with update — just append, the engine overwrites",
                    },
                    {"zh": "它会拒绝重复 id 的写入", "en": "It rejects writes with duplicate ids"},
                    {"zh": "它把两次写入都永久保留且都返回", "en": "It keeps both writes forever and returns both"},
                    {"zh": "它要求先删除旧行再写新行", "en": "It requires deleting the old row before writing the new one"},
                ],
                "answer": 0,
                "why": {
                    "zh": "ReplacingMergeTree 让“改一条”退化成“追加一条更大 event_ts 的记录”，无需读-改-写。这正好承接 create+update 的合并模型，也是第 2 课“不可变/追加式事件”能落地的存储基础。",
                    "en": "ReplacingMergeTree turns 'edit one' into 'append one with a larger event_ts', no read-modify-write. It absorbs the create+update merge model and is the storage basis for L02's 'immutable/append-oriented events'.",
                },
            },
            {
                "q": {
                    "zh": "为什么 observations 的 ORDER BY 以 project_id 打头、PARTITION BY 按月？这对“某项目最近 7 天”这类查询有什么用？",
                    "en": "Why does observations' ORDER BY start with project_id and PARTITION BY by month? What does that do for a 'project, last 7 days' query?",
                },
                "opts": [
                    {
                        "zh": "月分区让查询直接裁掉无关月份，project_id 打头让目标项目数据物理相邻成一段；于是只扫一小片、再列存只读所需列——“少扫”是海量下高效的关键",
                        "en": "Monthly partitions prune irrelevant months; project_id-first clusters the target project into a contiguous range; so only a small slice is scanned and columnar reads only needed columns — 'scan less' is the key at scale",
                    },
                    {"zh": "为了让写入更慢", "en": "To make writes slower"},
                    {"zh": "为了让所有项目的数据混在一起", "en": "To mix all projects' data together"},
                    {"zh": "因为 ClickHouse 不支持索引", "en": "Because ClickHouse has no indexes"},
                ],
                "answer": 0,
                "why": {
                    "zh": "分区裁剪 + 排序键定位 + 列存选列三者合力，让最高频的“按项目按时间”查询在上亿行里只碰一小片。这正是第 2 课“围绕列式访问设计：时间窗口+排序键+剪枝”。",
                    "en": "Partition pruning + ordering-key locating + columnar column-selection make the hottest 'by project, by time' query touch only a small slice across hundreds of millions of rows. This is L02's 'columnar access: time windows + ordering keys + pruning'.",
                },
            },
            {
                "q": {
                    "zh": "ReplacingMergeTree 的覆盖是“最终”的（后台合并需要时间）。这带来什么取舍，Langfuse 怎么应对？",
                    "en": "ReplacingMergeTree's overwrite is 'eventual' (background merge takes time). What trade-off does this bring, and how does Langfuse handle it?",
                },
                "opts": [
                    {
                        "zh": "未合并瞬间可能读到旧行；用 FINAL 或按 id 取最大 event_ts 的聚合保证最终态——把去重成本从“每次写入”挪到“查询时且可控”，换来写入飞快",
                        "en": "Before merge you might read an old row; use FINAL or aggregate (max event_ts per id) for the final state — moving dedup cost from 'every write' to 'query time, controllable', buying fast writes",
                    },
                    {"zh": "没有任何取舍，永远强一致", "en": "No trade-off at all, always strongly consistent"},
                    {"zh": "必须停机合并", "en": "You must take downtime to merge"},
                    {"zh": "只能每天查询一次", "en": "You may only query once a day"},
                ],
                "answer": 0,
                "why": {
                    "zh": "追加换吞吐的代价是“最终一致”。查询侧用 FINAL/聚合读到最终态，把去重从每次写入挪到查询时并显式优化——正是第 2 课“避免读时去重的隐藏开销”的实际做法。",
                    "en": "Append-for-throughput costs 'eventual consistency'. The read side uses FINAL/aggregation for the final state, moving dedup from every write to query time and optimizing it explicitly — exactly L02's 'avoid read-time dedup's hidden cost'.",
                },
            },
        ],
        "open": [
            {
                "zh": "ReplacingMergeTree 把“改”变成“追加 + 后台覆盖”。如果你自己的系统也常常“同一条记录被多次更新”，这种“只追加、读时取最新”的思路能怎么帮你？它的代价你能接受吗？",
                "en": "ReplacingMergeTree turns 'edit' into 'append + background overwrite'. If your own system also 'updates the same record many times', how could this 'append-only, read-the-latest' idea help you? Can you accept its cost?",
            },
        ],
    },
    "09-postgres-metadata-schema.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 为什么把配置/元数据（org/project/user、API key、prompt、定价…）放 Postgres，而不是和遥测一起放 ClickHouse？",
                    "en": "Why does Langfuse keep config/metadata (org/project/user, API keys, prompts, pricing…) in Postgres rather than in ClickHouse with telemetry?",
                },
                "opts": [
                    {
                        "zh": "配置要外键关系、事务、强一致（创建即可用），是关系型 Postgres 的强项；ClickHouse 弱事务、最终一致、不擅长频繁改单条，放配置是错配",
                        "en": "Config needs foreign keys, transactions and strong consistency (instantly usable) — relational Postgres's strength; ClickHouse has weak transactions, eventual consistency and dislikes frequent single-row edits, so config there is a mismatch",
                    },
                    {"zh": "因为 ClickHouse 容量太小", "en": "Because ClickHouse is too small"},
                    {"zh": "因为 Postgres 查询更慢，适合不常用的数据", "en": "Because Postgres is slower, fit for rarely-used data"},
                    {"zh": "纯粹历史原因，没有道理", "en": "Pure history, no reason"},
                ],
                "answer": 0,
                "why": {
                    "zh": "配置是 OLTP：量小、要精确单条读写、要强一致、有外键关系。这正是 Postgres 的主场；ClickHouse 适合海量追加+聚合（OLAP）。按职责分库，各做擅长的事——这是第 7 课的延续。",
                    "en": "Config is OLTP: small, precise single-row, strongly consistent, with foreign keys — Postgres's turf; ClickHouse fits massive append + aggregation (OLAP). Split by responsibility, each at its best — a continuation of L07.",
                },
            },
            {
                "q": {
                    "zh": "为什么说 Project 是控制面的“枢纽”，以及它为什么是多租户的“数据边界”？",
                    "en": "Why is Project the 'hub' of the control plane, and why is it the multi-tenant 'data boundary'?",
                },
                "opts": [
                    {
                        "zh": "Project 字段不多但挂着几十条 1:N 关系，几乎一切（key/成员/prompt/数据集/仪表盘/集成…）都属于某个 project；一把 API key 属于某 project，查询也被限定在该 project 内",
                        "en": "Project has few fields but dozens of 1:N relations; almost everything (keys/members/prompts/datasets/dashboards/integrations…) belongs to a project; an API key belongs to a project and queries are scoped to it",
                    },
                    {"zh": "因为 Project 表行数最多", "en": "Because the Project table has the most rows"},
                    {"zh": "因为 Project 存了所有 trace", "en": "Because Project stores all traces"},
                    {"zh": "因为它没有任何关系", "en": "Because it has no relations"},
                ],
                "answer": 0,
                "why": {
                    "zh": "几乎所有控制面对象都 1:N 挂在 project 下，所以它是中心；又因为 key、数据都按 project 划分，project 成了天然的隔离边界（也对应 ClickHouse 排序键以 project_id 打头）。多租户下一课展开。",
                    "en": "Almost all control-plane objects hang 1:N off a project, making it the center; and since keys and data are scoped by project, project is the natural isolation boundary (matching ClickHouse's project_id-first ordering key). Multi-tenancy next lesson.",
                },
            },
            {
                "q": {
                    "zh": "schema.prisma 里为什么还有 LegacyPrismaTrace/Observation/Score？API key 又是怎么存的？",
                    "en": "Why are there still LegacyPrismaTrace/Observation/Score in schema.prisma? And how are API keys stored?",
                },
                "opts": [
                    {
                        "zh": "Legacy 是早期把遥测存在 Postgres 的历史残留，分析数据已迁到 ClickHouse，仅为兼容/迁移保留；API key 的密钥只存哈希、不存明文",
                        "en": "Legacy models are historical remnants of storing telemetry in Postgres; analytical data moved to ClickHouse, kept only for compat/migration; API key secrets are stored hashed, never plaintext",
                    },
                    {"zh": "Legacy 是主力表；API key 明文存储", "en": "Legacy are the primary tables; API keys are stored in plaintext"},
                    {"zh": "Legacy 用于备份 ClickHouse；API key 不存储", "en": "Legacy back up ClickHouse; API keys aren't stored"},
                    {"zh": "两者都已从代码删除", "en": "Both have been removed from the code"},
                ],
                "answer": 0,
                "why": {
                    "zh": "带 Legacy 前缀=老路：遥测早已迁 ClickHouse（第 7、8 课的存在理由），这些只为兼容/迁移留着。API key 只存 hashedSecretKey 等哈希，即使库泄露也拿不到可用 key——安全细节，第 49/53 课展开。",
                    "en": "Legacy prefix = old way: telemetry long moved to ClickHouse (the reason for L07/L08); these remain for compat/migration. API keys store only hashedSecretKey etc., so a DB leak yields no usable key — a security detail expanded in L49/L53.",
                },
            },
        ],
        "open": [
            {
                "zh": "Langfuse 把“配置”和“数据”分到两个库。如果你自己的系统也有“少而关键的配置”+“海量的事件”，你会怎么划分？跨库读配置的代价你打算怎么压（提示：缓存）？",
                "en": "Langfuse splits 'config' and 'data' into two databases. If your system also had 'small critical config' + 'massive events', how would you divide them? How would you tame the cross-store config-read cost (hint: caching)?",
            },
        ],
    },
    "10-multi-tenancy.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的多租户隔离，project 和 environment 的本质区别是什么？",
                    "en": "In Langfuse multi-tenancy, what's the essential difference between project and environment?",
                },
                "opts": [
                    {
                        "zh": "project 是硬隔离（跨项目数据绝不可见，安全红线），environment 是软切片（同一项目内给 prod/staging/dev 贴标签，可分可合）",
                        "en": "project is hard isolation (data never visible across projects, a security red line); environment is a soft slice (tagging prod/staging/dev within one project, separable or combinable)",
                    },
                    {"zh": "两者完全一样，只是名字不同", "en": "They're identical, just different names"},
                    {"zh": "environment 比 project 隔离更强", "en": "environment isolates more strongly than project"},
                    {"zh": "project 是软的，environment 是硬的", "en": "project is soft, environment is hard"},
                ],
                "answer": 0,
                "why": {
                    "zh": "“不同团队数据绝不能串”是安全红线 → project 硬隔离；“线上 vs 测试”只是同团队的视图偏好 → environment 软切片。强度不同，待遇不同。",
                    "en": "'Different teams' data must never mix' is a security red line → project hard isolation; 'live vs test' is one team's view preference → environment soft slice. Different strengths, different treatment.",
                },
            },
            {
                "q": {
                    "zh": "为什么说 Langfuse 的租户隔离“不是事后加一个 WHERE project_id 过滤”？",
                    "en": "Why is Langfuse's tenant isolation 'not an afterthought WHERE project_id filter'?",
                },
                "opts": [
                    {
                        "zh": "因为 project_id 被焊进 ClickHouse 排序键最前面：同项目数据物理相邻，“只看我的项目”退化成扫一段连续区间——隔离与高效合一，且结构性地不可能看到别人",
                        "en": "Because project_id is welded into the front of the ClickHouse ordering key: one project's data is physically adjacent, so 'see only my project' becomes scanning a contiguous range — isolation and efficiency in one, and structurally impossible to see others",
                    },
                    {"zh": "因为 Langfuse 不支持过滤", "en": "Because Langfuse doesn't support filtering"},
                    {"zh": "因为每个项目用独立的数据库实例", "en": "Because each project uses a separate database instance"},
                    {"zh": "因为 project_id 是随机的", "en": "Because project_id is random"},
                ],
                "answer": 0,
                "why": {
                    "zh": "若 project_id 只是普通过滤列，海量下既慢又危险（写漏过滤就串租户）。放进排序键最前，隔离变成“定位连续区间”，又快又结构性安全。代价：排序键难改、查询须带 project_id。",
                    "en": "If project_id were an ordinary filter column, it'd be slow at scale and dangerous (miss the filter and you leak across tenants). Put it first in the ordering key and isolation becomes 'locate a contiguous range' — fast and structurally safe. Cost: hard-to-change ordering key, project_id required on queries.",
                },
            },
            {
                "q": {
                    "zh": "ClickHouse 里 environment 列定义为 LowCardinality(String) DEFAULT 'default' AFTER project_id。这三点各有什么用意？",
                    "en": "The ClickHouse environment column is LowCardinality(String) DEFAULT 'default' AFTER project_id. What's the intent of each?",
                },
                "opts": [
                    {
                        "zh": "低基数：环境名就那么几个，省空间快查询；默认 default：不指定时自动归类、向后兼容老数据；紧跟 project_id：与之构成“项目+环境”定位前缀",
                        "en": "Low-cardinality: few env names, saving space and speeding queries; default 'default': auto-classify when unspecified, backward-compatible with old data; right after project_id: forms a 'project+environment' locating prefix with it",
                    },
                    {"zh": "纯粹为了占位，没有用意", "en": "Pure placeholder, no intent"},
                    {"zh": "为了让环境名可以无限多", "en": "To allow infinitely many env names"},
                    {"zh": "为了删除 project_id", "en": "To remove project_id"},
                ],
                "answer": 0,
                "why": {
                    "zh": "LowCardinality 适合取值少的列（编码省空间、查得快）；DEFAULT 'default' 让老数据/未指定环境的数据天然归到 default（向后兼容）；AFTER project_id 让二者构成定位前缀，按“项目+环境”查同样高效。",
                    "en": "LowCardinality suits low-distinct columns (compact encoding, fast queries); DEFAULT 'default' makes old/unspecified-env data fall into default (backward compatible); AFTER project_id forms a locating prefix so 'project+environment' queries stay efficient.",
                },
            },
        ],
        "open": [
            {
                "zh": "“把多租户隔离做进存储结构，而不是一道可能写漏的过滤”——这条思路你能用到自己的系统吗？把租户键放进主键/排序键最前，会给你带来什么好处和什么约束？",
                "en": "'Bake multi-tenant isolation into the storage structure, not a filter you might forget' — can you apply this to your own system? What benefits and constraints come from putting the tenant key first in the primary/ordering key?",
            },
        ],
    },
    "11-deployment-topology.html": {
        "mcq": [
            {
                "q": {
                    "zh": "自托管一套 Langfuse，最小栈包含哪些容器？",
                    "en": "What containers make up the minimal stack to self-host Langfuse?",
                },
                "opts": [
                    {
                        "zh": "2 个应用（langfuse-web、langfuse-worker）+ 4 个基础设施（postgres、clickhouse、redis、minio/S3），全在 docker-compose.yml",
                        "en": "2 apps (langfuse-web, langfuse-worker) + 4 infra (postgres, clickhouse, redis, minio/S3), all in docker-compose.yml",
                    },
                    {"zh": "只要一个 langfuse 容器", "en": "Just one langfuse container"},
                    {"zh": "web + worker + 一个 SQLite 文件", "en": "web + worker + one SQLite file"},
                    {"zh": "只需要 ClickHouse", "en": "Only ClickHouse"},
                ],
                "answer": 0,
                "why": {
                    "zh": "docker-compose.yml 列出两个应用容器（web/worker）加四个基础设施（postgres:17、clickhouse-server、redis:7、minio）。这正是第 5、7 课架构图的实体版。",
                    "en": "docker-compose.yml lists two app containers (web/worker) plus four infra (postgres:17, clickhouse-server, redis:7, minio). It's the physical version of the architecture in L05/L07.",
                },
            },
            {
                "q": {
                    "zh": "web 和 worker 都连同一套存储，为什么还要拆成两个容器、还能分别扩容？",
                    "en": "web and worker connect the same storage — why split into two containers, and why scale them separately?",
                },
                "opts": [
                    {
                        "zh": "职责相反：web 面向用户、要低延迟、按 QPS 扩；worker 啃重活、可重试、按队列积压扩。靠 Redis 队列解耦，所以能各自独立扩容、互不阻塞",
                        "en": "Opposite duties: web is user-facing, low-latency, scales by QPS; worker chews heavy jobs, retryable, scales by queue backlog. Decoupled by the Redis queue, so each scales independently without blocking the other",
                    },
                    {"zh": "因为一个容器装不下代码", "en": "Because one container can't hold the code"},
                    {"zh": "因为它们用不同的数据库", "en": "Because they use different databases"},
                    {"zh": "纯粹为了多开机器", "en": "Just to run more machines"},
                ],
                "answer": 0,
                "why": {
                    "zh": "用户压力（QPS）和后台压力（队列积压）是两条独立的扩容信号。拆成两个容器、用队列解耦，就能“用户多了加 web、队列堵了加 worker”，互不牵连。这是第 4 课窄腰让两容器独立演进的部署体现。",
                    "en": "User pressure (QPS) and background pressure (queue backlog) are independent scaling signals. Splitting into two containers decoupled by a queue lets you 'add web for more users, add worker for a backed-up queue', without entanglement. It's the deployment-side expression of L04's narrow waist.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 用 Zod 在“启动时”校验环境变量。这条纪律的好处是什么？",
                    "en": "Langfuse validates env vars with Zod 'at startup'. What's the benefit of this discipline?",
                },
                "opts": [
                    {
                        "zh": "配错/漏填会让进程直接启动失败并指出哪个变量有问题——把“配置错误”从难查的运行时 bug 变成一眼可见的启动错误，而不是带病运行到半路才崩",
                        "en": "A misconfig/missing var makes the process fail to start and names the bad variable — turning 'config errors' from hard-to-find runtime bugs into obvious startup errors, instead of running sick and crashing midway",
                    },
                    {"zh": "让启动更慢以便检查", "en": "To make startup slower for checking"},
                    {"zh": "把环境变量加密", "en": "To encrypt env vars"},
                    {"zh": "自动修正错误的配置", "en": "To auto-fix wrong config"},
                ],
                "answer": 0,
                "why": {
                    "zh": "fail-fast：env.ts 用 Zod 在启动时校验类型与必填项，错了立刻报清楚。这比“带着错误配置跑半天、在某个边角功能才崩”可调试得多（第 51 课展开）。",
                    "en": "Fail-fast: env.ts uses Zod to validate types and required fields at startup, reporting clearly on error. Far more debuggable than 'running with bad config and crashing in some corner feature later' (expanded in L51).",
                },
            },
        ],
        "open": [
            {
                "zh": "Langfuse 的自托管需要 4 个基础设施，门槛比“一个二进制”高。如果你做一个开源工具，会怎么在“能扛规模”和“易自托管”之间取舍？docker-compose 一键编排算不算一个好答案？",
                "en": "Langfuse self-host needs 4 infra engines, a higher bar than 'one binary'. If you built an open-source tool, how would you trade off 'handles scale' vs 'easy to self-host'? Is one-command docker-compose orchestration a good answer?",
            },
        ],
    },
    "12-ingestion-api.html": {
        "mcq": [
            {
                "q": {
                    "zh": "摄取 API 收到一批事件后只做三件事就立即返回。是哪三件？为什么不在这里合并/算成本/写库？",
                    "en": "The ingestion API does only three things on a batch, then returns immediately. Which three, and why not merge/cost/write-DB here?",
                },
                "opts": [
                    {
                        "zh": "鉴权 + Zod 校验 + 入队；因为 API 直面你的应用，首要目标是“永远快、不拖累调用方”，重活放这里会增加每次埋点的延迟、还会因下游抖动而失败",
                        "en": "auth + Zod validation + enqueue; because the API faces your app directly, its top goal is 'always fast, never drag the caller'; heavy work here would add latency to every call and fail on downstream hiccups",
                    },
                    {"zh": "鉴权 + 合并 + 写库；因为这样最快", "en": "auth + merge + write-DB; because it's fastest"},
                    {"zh": "压缩 + 加密 + 入队", "en": "compress + encrypt + enqueue"},
                    {"zh": "只做入队，不鉴权也不校验", "en": "only enqueue, no auth or validation"},
                ],
                "answer": 0,
                "why": {
                    "zh": "入口只保留“必须当场做”的最小集合（鉴权防越权、校验拦脏数据、入队完成交接），能异步的全交给 worker。入口越薄越扛洪峰、越不可能拖垮你的业务，代价是最终一致（第 5 课）。",
                    "en": "The entry keeps only the must-do-now minimum (auth prevents unauthorized writes, validation blocks dirty data, enqueue hands off), deferring everything async to the worker. The thinner the entry, the better it survives spikes and the less it drags your business — at the cost of eventual consistency (L05).",
                },
            },
            {
                "q": {
                    "zh": "ingestion.ts 的 handler 把真正的活交给一个叫 processEventBatch 的共享函数，连单独提交 score 的接口也复用它。这么做的好处是？",
                    "en": "The ingestion.ts handler delegates the real work to a shared processEventBatch, reused even by the standalone score endpoint. The benefit?",
                },
                "opts": [
                    {
                        "zh": "“收一批、校验、入队”到处都用得上，抽成一处就不必每个端点各写一遍、各错一遍（复杂度收敛到一处，第 6 课）",
                        "en": "'accept a batch, validate, enqueue' is needed everywhere; factoring it into one place avoids re-implementing (and re-bugging) it per endpoint (converge complexity, L06)",
                    },
                    {"zh": "为了让 score 接口更慢", "en": "to make the score endpoint slower"},
                    {"zh": "因为 score 不能走队列", "en": "because scores can't use the queue"},
                    {"zh": "纯粹为了多写代码", "en": "just to write more code"},
                ],
                "answer": 0,
                "why": {
                    "zh": "多个端点共享同一套摄取逻辑，维护在一处、测试在一处，避免分散实现导致的不一致。这与第 6 课“把复杂度收敛到一个能严格测试的地方”一脉相承。",
                    "en": "Multiple endpoints share one ingestion routine, maintained and tested in one place, avoiding inconsistency from scattered implementations — in line with L06's 'converge complexity to one strictly testable place'.",
                },
            },
            {
                "q": {
                    "zh": "为什么说“在入口用 Zod 校验、越早拒绝坏数据越好”，而且 API 还能返回“部分成功”？",
                    "en": "Why 'validate with Zod at the entry, reject bad data as early as possible', and why can the API return 'partial success'?",
                },
                "opts": [
                    {
                        "zh": "摄取每天吞下各种 SDK/版本的数据，难免有脏事件；入口拦下并给清晰错误，比让它流进队列、到 worker 才崩好得多；一批里坏几条只拒那几条、其余照收",
                        "en": "Ingestion swallows data from many SDKs/versions daily, inevitably with dirty events; rejecting at the entry with a clear error beats letting them crash the worker; a few bad events in a batch get rejected while the rest are accepted",
                    },
                    {"zh": "因为 Zod 能加密数据", "en": "because Zod encrypts data"},
                    {"zh": "因为坏数据更快", "en": "because bad data is faster"},
                    {"zh": "因为部分成功能省钱", "en": "because partial success saves money"},
                ],
                "answer": 0,
                "why": {
                    "zh": "fail-fast + 容错：在门口用 schema 拦下脏数据，避免污染下游、避免 worker 崩；同时按事件粒度返回部分成功，不因个别坏事件牵连整批。这让海量异构来源的摄取既健壮又友好。",
                    "en": "Fail-fast + fault tolerance: a schema blocks dirty data at the door, sparing downstream and the worker; per-event partial success avoids letting a few bad events doom the whole batch. This keeps ingestion from massive heterogeneous sources both robust and friendly.",
                },
            },
        ],
        "open": [
            {
                "zh": "把“接收”和“处理”切开、入口只做最小集合——这条思路你能用到自己写的 API 上吗？哪些工作“必须当场做”，哪些可以丢给后台异步？切错了会怎样？",
                "en": "Splitting 'accept' from 'process' so the entry does the minimum — can you apply this to your own APIs? Which work 'must happen now', and which can be deferred to async background? What if you split it wrong?",
            },
        ],
    },
    "13-event-types-merge.html": {
        "mcq": [
            {
                "q": {
                    "zh": "一次 LLM 调用，SDK 先发 generation-create、后发 generation-update，最后却落成 ClickHouse 里同一行。靠的是什么？",
                    "en": "For one LLM call the SDK sends generation-create then generation-update, yet they land as the same row in ClickHouse. How?",
                },
                "opts": [
                    {
                        "zh": "两个事件共享同一个实体 id（body.id），服务端按 body.id 分组合并成一行；冲突字段以 timestamp 更晚者为准（last-write-wins）",
                        "en": "Both events share one entity id (body.id); the server groups by body.id and merges into one row, conflicts resolved by later timestamp (last-write-wins)",
                    },
                    {"zh": "靠事件 id 相同来合并", "en": "they merge because their event ids are equal"},
                    {"zh": "靠 SDK 在本地先合并好再发一条", "en": "the SDK merges locally and sends just one"},
                    {"zh": "靠 ClickHouse 随机挑一条保留", "en": "ClickHouse randomly keeps one of them"},
                ],
                "answer": 0,
                "why": {
                    "zh": "实体 id（body.id）是合并键：同 id 的 create/update 注定汇成一行；事件 id（信封 id）是去重键，成为 S3 文件名 <eventId>.json 保证幂等。合并冲突时按 timestamp 最新者胜，正是第 8 课 ReplacingMergeTree(event_ts) 在写入侧的镜像。",
                    "en": "The entity id (body.id) is the merge key: same-id create/update converge into one row; the event id (envelope id) is the dedup key, becoming the S3 filename <eventId>.json for idempotency. Conflicts resolve latest-timestamp-wins — the write-side mirror of L08's ReplacingMergeTree(event_ts).",
                },
            },
            {
                "q": {
                    "zh": "事件用 z.discriminatedUnion(\"type\", […]) 定义，而不是“一个所有字段都可选的大 schema”。这样做的核心好处是？",
                    "en": "Events are defined with z.discriminatedUnion(\"type\", […]) rather than 'one big schema with all fields optional'. The core benefit?",
                },
                "opts": [
                    {
                        "zh": "每种 type 配一套严格的 body 规则：发 generation-create 必须符合 CreateGenerationBody，缺字段/填错类型当场被 Zod 拦下，校验既精确又能给出清晰错误",
                        "en": "A strict body ruleset per type: generation-create must match CreateGenerationBody; missing/wrong fields are rejected by Zod on the spot — precise validation with clear errors",
                    },
                    {"zh": "让所有事件都能随便填字段", "en": "lets every event fill any field freely"},
                    {"zh": "让事件体积更小", "en": "makes events smaller on the wire"},
                    {"zh": "可以省掉 type 字段", "en": "lets you drop the type field"},
                ],
                "answer": 0,
                "why": {
                    "zh": "判别联合用 type 这一个字段决定该套哪套 body 规则，是“一个字段定身份、一套规则配一种身”。比“全字段可选”精确得多——后者无法在入口拦下结构性错误，脏数据会一路流到 worker 才崩。",
                    "en": "The discriminated union uses the single type field to pick the body ruleset — 'one field sets identity, one ruleset per identity'. Far more precise than 'all-optional', which can't catch structural errors at the entry and lets dirty data crash the worker downstream.",
                },
            },
            {
                "q": {
                    "zh": "getClickhouseEntityType 把 18 种事件 type 坍缩成 5 个实体类型，其中 span / generation / agent / tool 等都归到哪个，意味着什么？",
                    "en": "getClickhouseEntityType collapses 18 event types into 5 entity types; where do span/generation/agent/tool land among them, and what does that imply?",
                },
                "opts": [
                    {
                        "zh": "全归到 observation，进同一张 observations 表，靠行内 type 列区分；新增一种观测类型不必加表、不必改 schema——这正是第 8 课“宽事件”的威力",
                        "en": "all into observation, the same observations table, distinguished by the row's type column; adding a new observation kind needs no new table or schema change — the power of L08's 'wide events'",
                    },
                    {"zh": "各自进一张独立的表", "en": "each into its own separate table"},
                    {"zh": "归到 trace 表", "en": "into the trace table"},
                    {"zh": "归到 score 表", "en": "into the score table"},
                ],
                "answer": 0,
                "why": {
                    "zh": "5 个实体类型里，三个核心的 trace / observation / score 正好对应第 8 课的三张 ReplacingMergeTree 宽表（另两个 sdk_log、dataset_run_item 各自处理）。所有“像观测”的形态共用 observations 一张表、用 type 列区分，所以 Langfuse 能不断新增观测类型（AGENT/TOOL/CHAIN…）而无需迁移表结构。",
                    "en": "Among the 5 entity types, the three core ones trace / observation / score map onto L08's three ReplacingMergeTree wide tables (the other two, sdk_log & dataset_run_item, are handled separately). Every 'observation-like' shape shares the one observations table, distinguished by the type column, so Langfuse can keep adding observation kinds (AGENT/TOOL/CHAIN…) without schema migrations.",
                },
            },
        ],
        "open": [
            {
                "zh": "create/update 拆成两个事件，把“攒着整条记录”的状态从客户端推给了服务端。你自己的系统里，有没有类似“让边缘无状态、让中心兜底”的地方？这样做的代价和收益各是什么？",
                "en": "Splitting create/update into two events pushes the 'hold the whole record' state from client to server. In your own systems, is there a similar 'keep the edge stateless, let the center backstop' spot? What are its costs and benefits?",
            },
        ],
    },
    "14-ingestion-queue.html": {
        "mcq": [
            {
                "q": {
                    "zh": "摄取队列里到底放了什么？为什么不直接把事件本体塞进 Redis？",
                    "en": "What's actually in the ingestion queue, and why not stuff the event body straight into Redis?",
                },
                "opts": [
                    {
                        "zh": "只放含 fileKey 的轻量任务（指针）；事件本体先写进 S3 的 <eventId>.json，worker 再照 fileKey 回 S3 读回——队列轻则 Redis 内存省、入队快，本体留在 S3 当“真账本”，任务丢了也能重建",
                        "en": "only a lightweight job carrying fileKey (a pointer); the body is first written to S3 as <eventId>.json, the worker reads it back by fileKey — a light queue saves Redis memory and speeds enqueue, while the body stays in S3 as the 'real ledger', rebuildable if a job is lost",
                    },
                    {"zh": "放事件的完整内容，包括可能很大的 input/output", "en": "the full event content, including possibly huge input/output"},
                    {"zh": "什么都不放，worker 自己去数据库查", "en": "nothing; the worker queries the DB itself"},
                    {"zh": "放一份加密后的事件副本", "en": "an encrypted copy of the event"},
                ],
                "answer": 0,
                "why": {
                    "zh": "S3 存本体、队列递指针是这条链路最易误解的点。Redis 内存金贵，任务越小越快越扛积压；S3 既是合并要回读的历史事件源（第 15 课），也是任务失败时的可重放依据。这就买到了“轻队列 + 持久存储”两样好处。",
                    "en": "S3 holds the body, the queue passes a pointer — the most-misunderstood point of the path. Redis memory is precious, so smaller jobs are faster and survive backlog; S3 is both the historical event source the merge reads back (L15) and the replay basis on job failure. You get 'light queue + durable storage' at once.",
                },
            },
            {
                "q": {
                    "zh": "分片键为什么选 projectId-eventBodyId，而不是随机分配？",
                    "en": "Why is the shard key projectId-eventBodyId rather than a random assignment?",
                },
                "opts": [
                    {
                        "zh": "对实体 id 哈希取模能保证“同一实体永远落同一 shard”：一条记录的 create/update 始终在同一队列、被同一 worker 有序处理，合并无需跨队列协调；随机分会把它们打散、合并时复杂又可能乱序",
                        "en": "hashing the entity id guarantees 'same entity always on the same shard': a record's create/update stay in one queue, processed in order by one worker, no cross-queue coordination at merge; random scatter would split them, making merge complex and prone to disorder",
                    },
                    {"zh": "因为随机分配根本无法实现", "en": "because random assignment is impossible to implement"},
                    {"zh": "因为 projectId-eventBodyId 最短", "en": "because projectId-eventBodyId is the shortest string"},
                    {"zh": "为了让每个 shard 负载完全相等", "en": "to make every shard's load exactly equal"},
                ],
                "answer": 0,
                "why": {
                    "zh": "用一致性哈希（SHA-256 取模）把负载摊到多个 Redis 节点，同时用实体 id 当键，让“同一实体同一 shard”天然成立——这与第 8 课用 project_id 领头排序键、第 13 课用 body.id 当合并键，是同一种“让相关数据物理聚在一起”的思路。",
                    "en": "Consistent hashing (SHA-256 modulo) spreads load across Redis nodes, while using the entity id as key makes 'same entity, same shard' hold naturally — the same 'keep related data physically together' idea as L08 leading the ordering key with project_id and L13 using body.id as the merge key.",
                },
            },
            {
                "q": {
                    "zh": "主队列 vs 次队列的隔离机制解决了什么问题？worker 何时把任务改道次队列？",
                    "en": "What problem does primary-vs-secondary isolation solve, and when does the worker redirect a job to the secondary?",
                },
                "opts": [
                    {
                        "zh": "防止某个超高吞吐项目塞满主队列、饿死其他项目；命中 env 白名单（静态隔离已知大户）或 S3 限流标志（动态临时改道）就把该任务原样入次队列并 return，主队列立刻服务别人",
                        "en": "it prevents one ultra-high-throughput project from packing the primary and starving others; on hitting the env allowlist (statically isolating known heavy hitters) or the S3 slowdown flag (dynamic temporary redirect), the worker re-enqueues the job to the secondary and returns, freeing the primary to serve others",
                    },
                    {"zh": "让次队列处理得更慢以省钱", "en": "to make the secondary slower to save money"},
                    {"zh": "次队列只处理失败的任务", "en": "the secondary only handles failed jobs"},
                    {"zh": "主队列只处理 trace，次队列只处理 score", "en": "primary handles only traces, secondary only scores"},
                ],
                "answer": 0,
                "why": {
                    "zh": "次队列有独立的分片数和独立的 worker，把洪峰与日常物理隔离。两条判断：env 白名单（LANGFUSE_SECONDARY_INGESTION_QUEUE_ENABLED_PROJECT_IDS）做静态隔离，S3 SlowDown 标志做动态减压。这是典型的“吵闹邻居”隔离，保障多租户公平。",
                    "en": "The secondary has its own shard count and workers, physically isolating spike from steady-state. Two checks: the env allowlist (LANGFUSE_SECONDARY_INGESTION_QUEUE_ENABLED_PROJECT_IDS) for static isolation, the S3 SlowDown flag for dynamic relief. A classic 'noisy neighbor' isolation safeguarding multi-tenant fairness.",
                },
            },
        ],
        "open": [
            {
                "zh": "“队列 + S3 当真账本”换来了削峰、容错、可重放，代价是多一跳和最终一致的延迟。如果让你给一个高并发写入系统做选型，你会在“直接写库”和“队列缓冲 + 对象存储”之间怎么权衡？哪些信号会让你倒向后者？",
                "en": "'Queue + S3 as real ledger' buys spike absorption, fault tolerance and replayability, at the cost of an extra hop and eventual-consistency latency. Designing a high-concurrency write system, how would you weigh 'write the DB directly' against 'queue buffer + object storage'? What signals would tip you toward the latter?",
            },
        ],
    },
    "15-ingestion-service.html": {
        "mcq": [
            {
                "q": {
                    "zh": "一个 observation 先收到 create（带 startTime、input、model），后收到 update（带 endTime、output、usage）。mergeRecords 合并后，startTime 和 model 还在吗？为什么？",
                    "en": "An observation gets create (startTime, input, model) then update (endTime, output, usage). After mergeRecords, do startTime and model survive? Why?",
                },
                "opts": [
                    {
                        "zh": "都还在：update 没带这些字段（值为 undefined），overwriteObject 的“不覆盖”规则会保留旧值；startTime 还是 immutable 键，本就锁死",
                        "en": "both survive: update doesn't carry them (undefined), so overwriteObject's 'don't overwrite' rule keeps the old values; startTime is also an immutable key, locked anyway",
                    },
                    {"zh": "都被清空：后到的 update 整体覆盖了 create", "en": "both wiped: the later update wholly overwrites create"},
                    {"zh": "随机保留其一", "en": "one of them is randomly kept"},
                    {"zh": "只有 model 还在，startTime 被清空", "en": "only model survives, startTime is wiped"},
                ],
                "answer": 0,
                "why": {
                    "zh": "overwriteObject 用 lodash mergeWith，命中三条之一就保留旧值：① immutable 键（id/project_id/trace_id/start_time/created_at/environment）② 值为 undefined ③ 空对象。update 只带变化字段，没带的 input/model 是 undefined 故不被抹；start_time 更是 immutable。这正是 create/update 能正确合并的根本。",
                    "en": "overwriteObject uses lodash mergeWith and keeps the old value on any of three: ① immutable keys (id/project_id/trace_id/start_time/created_at/environment) ② undefined value ③ empty object. update carries only changed fields, so absent input/model are undefined and not wiped; start_time is immutable anyway. This is exactly why create/update merge correctly.",
                },
            },
            {
                "q": {
                    "zh": "合并时，mergeRecords 的输入数组里第一个元素总是 ClickHouse 已存在的那条记录。把它放第一位有什么用？",
                    "en": "In mergeRecords, the first element of the input array is always the existing ClickHouse record. What's the point of putting it first?",
                },
                "opts": [
                    {
                        "zh": "它当 immutable 字段的基线：左折叠从它开始，后续事件只能覆盖 mutable 字段；created_at、start_time 等锁死字段以它为准，保证身份/锚点稳定",
                        "en": "it's the baseline for immutable fields: the left-fold starts from it, later events can only overwrite mutable fields; locked fields like created_at, start_time take its value, keeping identity/anchors stable",
                    },
                    {"zh": "纯粹是数组顺序习惯，没有语义", "en": "purely an array-order habit, no semantics"},
                    {"zh": "为了让 ClickHouse 记录覆盖所有新事件", "en": "so the ClickHouse record overwrites all new events"},
                    {"zh": "为了先把它删掉", "en": "to delete it first"},
                ],
                "answer": 0,
                "why": {
                    "zh": "折叠从最左（CH 底稿）往右叠事件，后者覆盖前者。但 immutable 键不被覆盖，于是 created_at/start_time 等永远保留 CH 底稿（即第一次写定）的值。这让“读旧底稿 + 叠新修订”既纳新又不改旧，是合并正确性的关键。",
                    "en": "The fold goes left (CH base) to right (events), later overwriting earlier. But immutable keys aren't overwritten, so created_at/start_time keep the CH base's (first-written) value. This lets 'read old base + apply new revisions' absorb new while preserving old — key to merge correctness.",
                },
            },
            {
                "q": {
                    "zh": "既然第 8 课的 ReplacingMergeTree 会按 event_ts 自动去重，为什么 IngestionService 在写入侧还要预合并一遍？",
                    "en": "Since Lesson 8's ReplacingMergeTree auto-dedups by event_ts, why does IngestionService still pre-merge on the write side?",
                },
                "opts": [
                    {
                        "zh": "两层解决不同时刻的问题：写入侧预合并保证“写出的那一行当下就完整正确”，查询立即可读；ReplacingMergeTree 的后台去重是最终发生的，收拾并发竞态的尾巴。event_ts=now 让新行总能胜出，两层咬合成纵深防御",
                        "en": "the two layers solve problems at different moments: write-side pre-merge ensures 'the written row is complete and correct now', readable immediately; ReplacingMergeTree's background dedup is eventual, cleaning up concurrency races. event_ts=now lets the new row always win, meshing the layers into defense in depth",
                    },
                    {"zh": "因为 ReplacingMergeTree 其实不工作", "en": "because ReplacingMergeTree doesn't actually work"},
                    {"zh": "为了把数据写两遍更安全", "en": "to write the data twice for safety"},
                    {"zh": "纯粹是历史遗留代码", "en": "purely legacy code"},
                ],
                "answer": 0,
                "why": {
                    "zh": "写入侧求“即时正确”——不预合并的话，查询会读到半成品（只有 create 没有 update）；存储侧求“最终唯一”——收拾“同一记录被并发处理产生多行”的竞态。event_ts=now 这个版本戳把两层咬合：预合并产出的新行 event_ts 更大，必在 ReplacingMergeTree 去重里胜出。这是典型的纵深防御。",
                    "en": "The write side seeks 'immediate correctness' — without pre-merge, queries would read a half-baked row (create but no update); the storage side seeks 'eventual uniqueness', cleaning races that produce multiple rows for one record. The event_ts=now stamp meshes them: a pre-merged new row has a larger event_ts and always wins ReplacingMergeTree's dedup. Classic defense in depth.",
                },
            },
        ],
        "open": [
            {
                "zh": "IngestionService 把“合并”和“落盘”切成两层，又把“即时正确”和“最终唯一”分给写入侧与存储侧。这种“同一目标、两层各管一段、用一个版本戳咬合”的纵深防御，你在自己接触过的系统里见过类似设计吗？它的好处和复杂度代价你怎么看？",
                "en": "IngestionService splits 'merge' from 'persist', and assigns 'immediate correctness' to the write side and 'eventual uniqueness' to the storage side. Have you seen this 'one goal, two layers each owning a stretch, meshed by a version stamp' defense-in-depth elsewhere? How do you weigh its benefits against the added complexity?",
            },
        ],
    },
    "16-token-counting-cost.html": {
        "mcq": [
            {
                "q": {
                    "zh": "你的 SDK 上报了 usage={input:1000, output:500}，也报了 cost={total: 0.01}。Langfuse 会怎么处理 token 数和成本？",
                    "en": "Your SDK reported usage={input:1000, output:500} and cost={total: 0.01}. How does Langfuse handle the token counts and cost?",
                },
                "opts": [
                    {
                        "zh": "都直接采用你报的：token 跳过分词、用你的 1000/500；成本因为你给了至少一项，全用你的 0.01，连价目表都不查——provided 压倒 computed",
                        "en": "uses yours directly: tokens skip tokenization and use your 1000/500; since you gave at least one cost point, it uses your 0.01 wholesale and doesn't even consult the rate card — provided beats computed",
                    },
                    {"zh": "重新分词验证你的 token 数，再按价目表重算成本", "en": "re-tokenizes to verify your counts, then recomputes cost from the rate card"},
                    {"zh": "把你报的和系统估算的取平均", "en": "averages your reported values with the system's estimate"},
                    {"zh": "忽略你报的，一律自己算", "en": "ignores your values and computes everything itself"},
                ],
                "answer": 0,
                "why": {
                    "zh": "provided 压倒 computed 是贯穿 Langfuse 的原则。getUsageUnits 见有 provided_usage 就直接用；calculateUsageCosts 见“给了任一 cost 点”就全用 provided、不再算别的。系统从不把估算和你报的真实值混用，因为半真半估的账更危险。",
                    "en": "Provided beats computed runs through all of Langfuse. getUsageUnits uses provided_usage directly when present; calculateUsageCosts, seeing 'any cost point given', uses provided wholesale and computes nothing else. The system never mixes estimates with your real reported values, since a half-real, half-estimated bill is more dangerous.",
                },
            },
            {
                "q": {
                    "zh": "你用裸 HTTP 调了一个模型，埋点里没有任何 usage。什么情况下 Langfuse 会替你分词数 token？",
                    "en": "You called a model over raw HTTP with no usage in the event. When will Langfuse tokenize-count for you?",
                },
                "opts": [
                    {
                        "zh": "三条同时满足：模型名能正则匹配到一条 model 记录、observation 不是 ERROR、且你没提供 usage——这时用该模型的 tokenizerId 对 input/output 分词计数",
                        "en": "all three hold: the model name regex-matches a model row, the observation isn't ERROR, and you provided no usage — then it counts input/output tokens using that model's tokenizerId",
                    },
                    {"zh": "任何时候都会无条件分词", "en": "always, unconditionally"},
                    {"zh": "只有付费版才会分词", "en": "only on the paid plan"},
                    {"zh": "只有当 level=ERROR 时才分词", "en": "only when level=ERROR"},
                ],
                "answer": 0,
                "why": {
                    "zh": "computed 是有前提的兜底：匹配到模型（才知道用哪种 tokenizer、什么价）、非 ERROR（错误生成没必要算）、且无 provided。三者缺一就不分词。分词用 model.tokenizerId，在 worker/src/features/tokenisation 里、可走独立线程以免阻塞。",
                    "en": "Computed is a precondition-gated backstop: a matched model (so it knows which tokenizer and price), non-ERROR (no point counting a failed generation), and no provided usage. Missing any one, no tokenization. It counts via model.tokenizerId, in worker/src/features/tokenisation, optionally on a separate thread to avoid blocking.",
                },
            },
            {
                "q": {
                    "zh": "findModel 把模型名匹配到价目时，如果一个项目自定义了 gpt-4o 的价格，同时内置也有 gpt-4o，会用哪条？",
                    "en": "When findModel matches a model name to a price, if a project customized gpt-4o's price while a built-in gpt-4o also exists, which is used?",
                },
                "opts": [
                    {
                        "zh": "用项目自定义的：SQL 是 project_id = ? OR project_id IS NULL，再 ORDER BY project_id，项目模型排在全局(NULL)前面；同名下还按 start_date 最新取一条",
                        "en": "the project's custom one: the SQL is project_id = ? OR project_id IS NULL, then ORDER BY project_id so project rows rank before global (NULL); among those it also takes the latest start_date",
                    },
                    {"zh": "用内置的，自定义会被忽略", "en": "the built-in; the customization is ignored"},
                    {"zh": "随机选一条", "en": "picks one at random"},
                    {"zh": "两条价格相加", "en": "adds the two prices together"},
                ],
                "answer": 0,
                "why": {
                    "zh": "findModel 用 Postgres 正则 ~ match_pattern 匹配，WHERE 同时取项目模型与全局(project_id IS NULL)，ORDER BY project_id 让自定义优先、start_date DESC 取最新生效价、LIMIT 1。于是项目能覆盖默认定价或加自有模型，历史数据按当时价、新数据按新价。",
                    "en": "findModel matches via Postgres regex ~ match_pattern, the WHERE takes both project and global (project_id IS NULL) models, ORDER BY project_id prioritizes custom, start_date DESC takes the latest effective price, LIMIT 1. So projects can override defaults or add own models; history is priced at its time, new data at the new price.",
                },
            },
        ],
        "open": [
            {
                "zh": "“可信来源优先、估算只做兜底、两者严格隔离”——这条原则不止用于 token/成本。想想你自己的系统里，有没有“用户/上游给的权威数据”和“本地推断/估算”并存的场景？你会怎么设计它们的优先级与隔离，避免半真半估造成的误判？",
                "en": "'Trusted source first, estimation only as backup, the two strictly isolated' — this principle isn't only for tokens/cost. In your own systems, where do 'authoritative data from users/upstream' and 'local inference/estimates' coexist? How would you design their precedence and isolation to avoid the misjudgment of half-real, half-estimated data?",
            },
        ],
    },
    "17-clickhouse-writer.html": {
        "mcq": [
            {
                "q": {
                    "zh": "ClickhouseWriter 为什么要把单条记录攒成大批再写，而不是 IngestionService 算完一条就直接 INSERT 一条？",
                    "en": "Why does ClickhouseWriter batch single records before writing, instead of IngestionService INSERTing each record as soon as it's computed?",
                },
                "opts": [
                    {
                        "zh": "因为 ClickHouse 的 MergeTree 每次 INSERT 都落一个磁盘分片(part)，逐条写会产生海量小分片、后台合并追不上、查询变慢甚至触发 too-many-parts 拒写；攒成一批只生成一个大分片",
                        "en": "because ClickHouse's MergeTree drops a disk part per INSERT; row-by-row spawns a flood of tiny parts, background merges can't keep up, queries slow, even hitting the too-many-parts guard; one batch makes just one big part",
                    },
                    {"zh": "因为攒批能加密数据", "en": "because batching encrypts the data"},
                    {"zh": "因为 IngestionService 不能访问数据库", "en": "because IngestionService can't access the database"},
                    {"zh": "因为单条写会丢数据", "en": "because single writes lose data"},
                ],
                "answer": 0,
                "why": {
                    "zh": "第 8 课讲过 ClickHouse 偏爱大批量。MergeTree 每个 INSERT 生成一个数据分片，小分片越多、磁盘元数据和后台合并压力越大。把高频小写翻译成低频大写，是列式存储扛住高频摄取的必要前提，而非可有可无的优化。",
                    "en": "Lesson 8 noted ClickHouse prefers large batches. Each INSERT creates a MergeTree part; more tiny parts means heavier disk metadata and background merges. Translating high-frequency small writes into low-frequency large ones is a precondition for a columnar store to withstand high-frequency ingestion, not an optional optimization.",
                },
            },
            {
                "q": {
                    "zh": "ClickhouseWriter 的两个 flush 触发条件是什么？为什么需要两个而不是一个？",
                    "en": "What are ClickhouseWriter's two flush triggers, and why two rather than one?",
                },
                "opts": [
                    {
                        "zh": "① 某表队列 ≥ batchSize（按量）② 定时器每 writeInterval 触发 flushAll（按时）；谁先到算谁——高峰靠“坐满”保吞吐，低谷靠“到点”保延迟上限，缺一就会要么延迟失控、要么批永远凑不满",
                        "en": "① a table's queue ≥ batchSize (by size) ② a timer fires flushAll every writeInterval (by time); whichever first — rush hour uses 'full' for throughput, lulls use 'on time' to cap latency; with only one, either latency runs away or batches never fill",
                    },
                    {"zh": "① 内存满 ② 磁盘满", "en": "① memory full ② disk full"},
                    {"zh": "① 白天 ② 夜间", "en": "① daytime ② nighttime"},
                    {"zh": "只有一个：队列满才写", "en": "only one: write when the queue is full"},
                ],
                "answer": 0,
                "why": {
                    "zh": "只靠 batchSize：低谷期凑不满一批，记录会无限期滞留内存、延迟失控。只靠定时器：高峰期一个 interval 内涌入远超一批，仍可能积压。两者“谁先到算谁”互补：高吞吐批批写满拉高效率，低吞吐到点即发封顶延迟。关机时再 flushAll(true) 排空，不丢数据。",
                    "en": "batchSize alone: in a lull a batch never fills, so records linger in memory indefinitely with runaway latency. Timer alone: at peak far more than a batch floods in per interval, risking backlog. The two complement 'whichever first': high throughput writes full batches for efficiency, low throughput flushes on time to cap latency. On shutdown, flushAll(true) drains everything, losing nothing.",
                },
            },
            {
                "q": {
                    "zh": "记录攒在内存队列里，worker 崩溃这批就没了。Langfuse 为什么敢用这种“易失”的内存缓冲？",
                    "en": "Records sit in an in-memory queue, so a worker crash loses that batch. Why does Langfuse dare to use such 'volatile' in-memory buffering?",
                },
                "opts": [
                    {
                        "zh": "因为持久性由上游兜底：每个事件原原本本在 S3，队列任务写库成功前不会被确认；崩了任务会重投、从 S3 重读重合并重写，一条不丢——所以这层可放心用内存换吞吐",
                        "en": "because durability is backstopped upstream: every event sits verbatim in S3, and the queue job isn't acked until the DB write succeeds; on crash the job is redelivered, re-reads from S3, re-merges and re-writes, losing nothing — so this layer can trade memory for throughput",
                    },
                    {"zh": "因为 worker 永远不会崩", "en": "because the worker never crashes"},
                    {"zh": "因为内存比磁盘更可靠", "en": "because memory is more reliable than disk"},
                    {"zh": "因为丢一点数据无所谓", "en": "because losing some data is fine"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是典型的分层智慧：S3（第 14 课）负责“绝不丢”，ClickhouseWriter 负责“写得快”，谁也不为对方妥协。因为队列 + S3 已经保证了持久性与可重放，写入器才敢用易失内存缓冲去换吞吐——崩溃只是触发一次重投重算。",
                    "en": "Classic layered wisdom: S3 (Lesson 14) owns 'never lose', ClickhouseWriter owns 'write fast', neither compromising for the other. Because the queue + S3 already guarantee durability and replayability, the writer can trade volatile memory buffering for throughput — a crash merely triggers a redeliver-and-recompute.",
                },
            },
        ],
        "open": [
            {
                "zh": "ClickhouseWriter 把“持久”交给上游 S3、自己专注“高效”，于是敢用易失内存缓冲换吞吐。这种“把不同的质量目标分给不同层、各自做到极致”的思路，你在自己设计系统时会怎么运用？如果某一层既要快又要绝不丢，会带来哪些额外复杂度？",
                "en": "ClickhouseWriter delegates durability to upstream S3 and focuses on efficiency, so it dares to trade volatile memory buffering for throughput. How would you apply this 'assign different quality goals to different layers, each taken to the extreme' approach in your own designs? If one layer must be both fast and never-lose, what extra complexity does that bring?",
            },
        ],
    },
    "18-opentelemetry-ingestion.html": {
        "mcq": [
            {
                "q": {
                    "zh": "OTLP 数据从 /otel/v1/traces 进来后，OtelIngestionProcessor 把 span 翻译成什么？之后又如何处理？",
                    "en": "After OTLP data enters at /otel/v1/traces, what does OtelIngestionProcessor translate spans into, and what happens next?",
                },
                "opts": [
                    {
                        "zh": "翻译成原生的 IngestionEventType[]（第 13 课事件格式）：observation 交 IngestionService.mergeAndWrite，trace 走 processEventBatch——从此与原生 SDK 数据完全同路（合并/算钱/落盘共用一套）",
                        "en": "into native IngestionEventType[] (Lesson 13's format): observations go to IngestionService.mergeAndWrite, traces to processEventBatch — thereafter identical to native-SDK data (one shared merge/cost/write)",
                    },
                    {"zh": "直接写进一张专门的 otel 表，不经过合并", "en": "straight into a dedicated otel table, skipping merge"},
                    {"zh": "转成 SQL 语句执行", "en": "into SQL statements to execute"},
                    {"zh": "原样存进 S3 就结束了", "en": "just stored verbatim in S3 and done"},
                ],
                "answer": 0,
                "why": {
                    "zh": "OTel 摄取本质是“边缘适配、核心归一”。OtelIngestionProcessor.processToIngestionEvents 把 span 映射成原生事件格式，按实体类型分流后汇入第 15–17 课同一条管道。OTel 特异的只有最前端的映射，后端与原生完全共享。",
                    "en": "OTel ingestion is essentially 'adapt at the edge, unify at the core'. OtelIngestionProcessor.processToIngestionEvents maps spans into the native event format, splits by entity type, and converges into the same Lesson 15–17 pipeline. Only the front-end mapping is OTel-specific; the backend is fully shared with native.",
                },
            },
            {
                "q": {
                    "zh": "同一个“模型名”，OpenTelemetry 写在 gen_ai.response.model、Vercel AI SDK 写在 ai.model.id、OpenLLMetry 写在 llm.model_name。适配器怎么应对这种混乱？",
                    "en": "The same 'model name' is written to gen_ai.response.model by OpenTelemetry, ai.model.id by Vercel AI SDK, llm.model_name by OpenLLMetry. How does the adapter cope with this mess?",
                },
                "opts": [
                    {
                        "zh": "为每个字段准备一份优先级属性键列表，从上往下试，第一个有值的就采用；新约定出现只需往列表里加几个键，老数据不受影响、新数据立刻被认得",
                        "en": "it keeps a priority list of attribute keys per field, tries top to bottom, takes the first present; a new convention just needs a few keys added to the list — old data unaffected, new data instantly recognized",
                    },
                    {"zh": "要求所有用户统一改用一种约定", "en": "requires all users to standardize on one convention"},
                    {"zh": "随机选一个键", "en": "picks a key at random"},
                    {"zh": "只认 OpenTelemetry 官方约定，其他一律丢弃", "en": "only recognizes the official OpenTelemetry convention, discarding others"},
                ],
                "answer": 0,
                "why": {
                    "zh": "extractModelName 依次尝试 langfuse 原生 → gen_ai.response.model → ai.model.id → gen_ai.request.model → llm.* → 通用 model，第一个命中即用。usage、input/output 同理。这种“加键即兼容”的优先级回退，让 Langfuse 不必强迫用户改约定，也能跟着生态演进。",
                    "en": "extractModelName tries in turn langfuse-native → gen_ai.response.model → ai.model.id → gen_ai.request.model → llm.* → generic model, using the first hit. usage and input/output likewise. This 'add a key, gain compatibility' priority fallback lets Langfuse avoid forcing users to change conventions while evolving with the ecosystem.",
                },
            },
            {
                "q": {
                    "zh": "原生摄取比 OTel 更精确，为什么 Langfuse 还要支持 OpenTelemetry？这个取舍的本质是什么？",
                    "en": "Native ingestion is more precise than OTel — so why does Langfuse still support OpenTelemetry, and what's the essence of the trade-off?",
                },
                "opts": [
                    {
                        "zh": "为了“去用户所在的地方接住他们”：OTel 是事实标准，无数应用早已埋好点；支持 OTLP 意味着用户不用改一行埋点就能接入。代价是一个满是回退的适配器+推断的语义损耗，但适配器只在最前端，翻完即汇入共享核心",
                        "en": "to 'meet users where they are': OTel is the de facto standard and countless apps are already instrumented; supporting OTLP means users onboard without changing a line of instrumentation. The cost is a fallback-laden adapter + inference's semantic loss, but the adapter is only at the front, converging into the shared core after translation",
                    },
                    {"zh": "因为 OTel 比原生更快", "en": "because OTel is faster than native"},
                    {"zh": "因为原生 SDK 即将废弃", "en": "because the native SDK is being deprecated"},
                    {"zh": "纯粹为了营销噱头", "en": "purely a marketing gimmick"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是经典的适配器模式：把脏活、特例（追各家约定、处理语义落差）收敛到边缘的一层适配器，让核心（合并/算钱/落盘）保持纯净统一。降低接入门槛换来更广的用户覆盖，而复杂度被限制在最前端一层，不污染后端。",
                    "en": "A classic adapter pattern: confine the grunt work and special cases (chasing conventions, handling the semantic gap) to one edge adapter, keeping the core (merge/cost/write) pure and unified. Lowering the onboarding barrier buys broader user coverage, while complexity is confined to the front layer without polluting the backend.",
                },
            },
        ],
        "open": [
            {
                "zh": "“把适配各种外部格式的脏活收敛到边缘一层适配器，核心只认一种统一格式”——这条原则你在自己的系统里能用上吗？如果要同时支持多种输入协议/数据源，你会在哪里画那条“适配器 vs 核心”的边界？画错了会怎样？",
                "en": "'Confine the grunt work of adapting various external formats to one edge adapter, and let the core know only one unified format' — can you apply this in your own systems? If you must support multiple input protocols/data sources, where would you draw the 'adapter vs core' boundary? What goes wrong if you draw it wrong?",
            },
        ],
    },
    "19-media-blob-storage.html": {
        "mcq": [
            {
                "q": {
                    "zh": "一次多模态调用的 input 里有一张 3MB 的图。Langfuse 是怎么处理它的，ClickHouse 里最终存了什么？",
                    "en": "A multimodal call's input has a 3MB image. How does Langfuse handle it, and what ends up in ClickHouse?",
                },
                "opts": [
                    {
                        "zh": "图片本体存进 S3 媒体桶，事件里那张图被替换成一个小引用串 @@@langfuseMedia:…@@@；ClickHouse 只存这个几十字节的引用，绝不存 3MB 二进制",
                        "en": "the image body goes into the S3 media bucket, and in the event the image is replaced by a small reference @@@langfuseMedia:…@@@; ClickHouse stores only that few-dozen-byte reference, never the 3MB binary",
                    },
                    {"zh": "把 3MB base64 直接存进 ClickHouse 的 input 列", "en": "stores the 3MB base64 straight into ClickHouse's input column"},
                    {"zh": "把图片丢弃，只留文字", "en": "discards the image, keeping only text"},
                    {"zh": "把图片压缩后存进 Postgres", "en": "compresses the image into Postgres"},
                ],
                "answer": 0,
                "why": {
                    "zh": "大块二进制绝不能进 ClickHouse 宽表，否则 input/output 列暴涨、拖慢所有查询。Langfuse 把 blob 与引用分离：本体进 S3 媒体桶，事件里只留 MEDIA_REFERENCE_PATTERN 匹配的小引用串，ClickHouse 始终精瘦。",
                    "en": "Large binaries must never enter ClickHouse wide tables, or input/output columns balloon and slow every query. Langfuse splits blob from reference: the body to the S3 media bucket, the event keeping only a small reference matched by MEDIA_REFERENCE_PATTERN, keeping ClickHouse lean.",
                },
            },
            {
                "q": {
                    "zh": "媒体上传时，SDK 先把 sha256 报给服务端、而不是直接把文件 POST 过去。这个“先报指纹”的设计带来哪两个好处？",
                    "en": "On media upload, the SDK first reports the sha256 to the server instead of POSTing the file directly. What two benefits does this 'fingerprint first' design bring?",
                },
                "opts": [
                    {
                        "zh": "① 去重：按 (projectId, sha256) 查 prisma.media，已传过就回 uploadUrl=null 跳过，同一文件只存一份；② 直传：未命中则返回 presigned URL，SDK 把本体直接 PUT 进 S3，绕开应用服务器省带宽",
                        "en": "① dedup: look up prisma.media by (projectId, sha256), if already uploaded return uploadUrl=null to skip, storing the same file once; ② direct upload: on miss return a presigned URL so the SDK PUTs the body straight to S3, bypassing app servers and saving bandwidth",
                    },
                    {"zh": "① 加密文件 ② 压缩文件", "en": "① encrypt the file ② compress the file"},
                    {"zh": "① 给文件改名 ② 给文件分类", "en": "① rename the file ② categorize it"},
                    {"zh": "① 让上传更慢 ② 让 API 更忙", "en": "① slow the upload ② busy the API"},
                ],
                "answer": 0,
                "why": {
                    "zh": "先报指纹让服务端能在传输前就判断“是否已有同一文件”，实现内容寻址去重；命中则秒过，未命中才发 presigned URL 让 SDK 直传 S3。本体全程不经 Langfuse 应用层，既省带宽又不堵 API——这是把大文件挡在热路径之外的关键一招。",
                    "en": "Reporting the fingerprint first lets the server decide 'do we already have this file' before any transfer, achieving content-addressed dedup; on hit it passes instantly, on miss it issues a presigned URL for the SDK to upload directly to S3. The body never passes through Langfuse's app layer, saving bandwidth and not clogging the API — key to keeping big files off the hot path.",
                },
            },
            {
                "q": {
                    "zh": "为什么 Langfuse 要把遥测数据放 ClickHouse、媒体 blob 放 S3，而不是图省事都放一处？背后的核心原则是什么？",
                    "en": "Why does Langfuse put telemetry in ClickHouse and media blobs in S3, rather than everything in one place? What's the core principle?",
                },
                "opts": [
                    {
                        "zh": "因为两者“体质”不同：遥测小、结构化、要高频查询聚合（适合 ClickHouse 宽表）；媒体大、是不透明二进制、几乎只按 id 整取（适合对象存储）。让每种数据待在最适合它的存储里，互不拖累",
                        "en": "because their 'constitutions' differ: telemetry is small, structured, frequently queried/aggregated (fits ClickHouse wide tables); media is large, opaque binary, almost only fetched whole by id (fits object storage). Let each kind of data live in the storage that fits it best, neither dragging the other",
                    },
                    {"zh": "因为 S3 比 ClickHouse 更快查询", "en": "because S3 queries faster than ClickHouse"},
                    {"zh": "因为 ClickHouse 不能存文本", "en": "because ClickHouse can't store text"},
                    {"zh": "纯粹是历史原因", "en": "purely historical reasons"},
                ],
                "answer": 0,
                "why": {
                    "zh": "把几 MB 图片塞进 ClickHouse 会同时毁两件事：宽表撑爆、连不碰图的查询也被拖慢，又用昂贵分析库干对象存储的活。各按本性安置——结构化进 ClickHouse、二进制进 S3、引用串牵线、sha256 去重——这条“让每种数据待在最适合的存储里”正是第 7 课双存储分工的延续，也为第三部分收尾。",
                    "en": "Stuffing a multi-MB image into ClickHouse ruins two things: the wide table bloats and even image-free queries slow, and you waste a pricey analytical store on object storage's job. Placing each by its nature — structured to ClickHouse, binary to S3, linked by a reference, deduped by sha256 — extends Lesson 7's dual-store division of labor and closes out Part 3.",
                },
            },
        ],
        "open": [
            {
                "zh": "“让每种数据待在最适合它的存储里，用一个小引用把它们牵起来”——这条原则在你做过的系统里有没有类似场景（比如大文件、日志、缩略图）？你会怎么决定“什么放主库、什么放对象存储/外部存储”，那条边界怎么画？内容寻址去重又能帮你省下什么？",
                "en": "'Let each kind of data live in the storage that fits it best, linked by a small reference' — is there a similar scenario in systems you've built (large files, logs, thumbnails)? How would you decide 'what goes in the main DB vs object/external storage', and where to draw that line? What could content-addressed dedup save you?",
            },
        ],
    },
    "20-web-app-architecture.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的 web 应用为什么并存三种 API 风格（tRPC、公共 REST、App-Router/SSE），而不是统一成一种？",
                    "en": "Why does Langfuse's web app run three API styles (tRPC, public REST, App-Router/SSE) rather than unifying into one?",
                },
                "opts": [
                    {
                        "zh": "因为对内和对外是两类需求：UI 要类型安全、改得快（tRPC，前后端共享类型）；SDK 要契约稳定、带版本（REST + Fern）；少数流式/webhook 要原始 Request 语义（App-Router）。硬统一会牺牲其一",
                        "en": "because internal and external are two needs: the UI wants type-safety and fast change (tRPC, shared types front-to-back); SDKs want a stable, versioned contract (REST + Fern); a few streaming/webhook cases need raw Request semantics (App-Router). Forcing unity sacrifices one of them",
                    },
                    {"zh": "因为开发者忘了删旧代码", "en": "because developers forgot to delete old code"},
                    {"zh": "因为三种 API 各自更快", "en": "because each API is individually faster"},
                    {"zh": "因为 Next.js 强制要求三种都用", "en": "because Next.js mandates all three"},
                ],
                "answer": 0,
                "why": {
                    "zh": "核心边界是“对内求类型安全与迭代速度、对外求契约稳定与版本可控”。UI 和后端同仓同队，tRPC 把类型贯穿、重构即时报错；SDK 面向外部用户，接口发布后不能随意改，需 REST+版本+Fern。同一批数据、两种对外姿态——按受众分而治之，比强求统一更合适。",
                    "en": "The core boundary: internally seek type-safety and iteration speed, externally seek a stable, versioned contract. UI and backend share one repo/team, so tRPC threads types and errors instantly on refactor; the SDK faces external users where published interfaces can't change freely, needing REST+versions+Fern. Same data, two external postures — dividing by audience fits better than forced uniformity.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 几乎全用老的 Pages Router，App Router 下只有 4 个文件。这说明了什么？",
                    "en": "Langfuse uses the old Pages Router for almost everything, with only 4 files under App Router. What does this show?",
                },
                "opts": [
                    {
                        "zh": "务实的取舍：Pages Router + tRPC 是 App Router 成熟前就立的稳固根基，贸然迁移收益小风险大；App Router 只保留给需要原始 Request/流式/webhook 这类 Pages Router 不擅长的语义",
                        "en": "a pragmatic choice: Pages Router + tRPC is a solid foundation laid before App Router matured, so a rash migration is low-reward/high-risk; App Router is kept only for raw Request/streaming/webhook semantics Pages Router handles awkwardly",
                    },
                    {"zh": "代码库已经过时、无人维护", "en": "the codebase is outdated and unmaintained"},
                    {"zh": "App Router 完全不能用", "en": "App Router is completely unusable"},
                    {"zh": "团队不知道 App Router 存在", "en": "the team doesn't know App Router exists"},
                ],
                "answer": 0,
                "why": {
                    "zh": "架构选择服务于团队现实而非追新。tRPC 让前后端共享类型，是全栈团队快速迭代的关键；迁移成本高、收益小。App Router 的 4 个文件（layout + stripe-webhook/chatCompletion/in-app-agent）正是那些需要原始 Request、流式或 webhook 语义的特例——合适比统一更重要。",
                    "en": "Architecture serves team reality, not novelty. tRPC's shared types are key to fast full-stack iteration; migration is costly and low-reward. App Router's 4 files (layout + stripe-webhook/chatCompletion/in-app-agent) are exactly the cases needing raw Request, streaming, or webhook semantics — fit matters more than uniformity.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的 web/src 用 features/ 按“功能”切分（约 80 个纵向模块），而不是按“技术层”（全部页面/全部组件/全部接口各一目录）。这样组织的主要好处是？",
                    "en": "Langfuse's web/src cuts by 'feature' under features/ (~80 vertical modules) rather than by 'technical layer' (all pages/all components/all APIs each in one dir). The main benefit?",
                },
                "opts": [
                    {
                        "zh": "每个功能是自包含的竖切片，把它的组件、状态、server 逻辑收在一处；读懂或改一个功能主要只看一个目录，功能之间边界清晰、不易牵连",
                        "en": "each feature is a self-contained vertical slice gathering its components, state, and server logic in one place; to understand or change a feature you mostly read one directory, with clear boundaries that don't entangle",
                    },
                    {"zh": "让目录数量更少", "en": "to have fewer directories"},
                    {"zh": "强制所有功能共享代码", "en": "to force all features to share code"},
                    {"zh": "让构建更快", "en": "to make builds faster"},
                ],
                "answer": 0,
                "why": {
                    "zh": "按功能切分（vertical slice）让一个功能的全部代码聚在 features/<功能>/ 一处，避免在 pages/components/api 三四个目录间来回跳。修改局部化、边界清晰，是大型前端可维护性的关键——这也是为什么后面每课几乎都能指向一个 features/ 子目录。",
                    "en": "By-feature (vertical-slice) organization gathers a feature's whole code under features/<feature>/, avoiding hops across pages/components/api. Localized changes and clear boundaries are key to large-frontend maintainability — which is why nearly every later lesson points at a features/ subfolder.",
                },
            },
        ],
        "open": [
            {
                "zh": "“对内类型安全、对外契约稳定”——同一批数据用两种 API 姿态对待。你做过的系统里，内部调用和对外接口是混在一起还是分开的？如果分开，你会怎么划界？tRPC 这种“前后端共享类型”的收益，在什么规模/团队结构下最划算？",
                "en": "'Internal type-safety, external stable contract' — the same data treated with two API postures. In systems you've built, are internal calls and external interfaces mixed or separated? If separated, how would you draw the line? At what scale/team structure does tRPC's 'shared types front-to-back' pay off most?",
            },
        ],
    },
    "21-trpc-backbone.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 用 procedure 构建器（publicProcedure / authenticatedProcedure / protectedProjectProcedure）来定义 tRPC 接口。这种「分层中间件栈」的本质是什么？",
                    "en": "Langfuse defines tRPC endpoints with procedure builders (publicProcedure / authenticatedProcedure / protectedProjectProcedure). What's the essence of this 'layered middleware stack'?",
                },
                "opts": [
                    {
                        "zh": "procedure 是一摞中间件按 .use() 叠出来的；公开门只过 OTel+错误处理，受保护门再叠登录、项目成员校验。中间件定义一次，每个路由按需挑选——RBAC 不必各写一遍",
                        "en": "a procedure is a stack of middleware chained by .use(); a public door passes only OTel+error handling, a protected door adds login and project-member checks. Middleware is defined once and each router picks what it needs — RBAC isn't rewritten per router",
                    },
                    {"zh": "每个路由都必须手写完整的鉴权逻辑", "en": "every router must hand-write full auth logic"},
                    {"zh": "procedure 只是给接口起个名字，无实际作用", "en": "procedures just name endpoints, with no real effect"},
                    {"zh": "中间件只能用一个，不能叠加", "en": "only one middleware is allowed, no stacking"},
                ],
                "answer": 0,
                "why": {
                    "zh": "tRPC 的精髓是 procedure = 可叠加的中间件栈。withOtelTracingProcedure 叠 OTel，再 .use(withErrorHandling) 得 publicProcedure，再 .use(enforceUserIsAuthed) 得 authenticatedProcedure，再换成 enforceUserIsAuthedAndProjectMember 得 protectedProjectProcedure。声明式组合让安全检查写一次、处处复用。",
                    "en": "tRPC's essence is procedure = stackable middleware. withOtelTracingProcedure adds OTel, then .use(withErrorHandling) gives publicProcedure, then .use(enforceUserIsAuthed) gives authenticatedProcedure, then swapping in enforceUserIsAuthedAndProjectMember gives protectedProjectProcedure. Declarative composition lets a security check be written once and reused everywhere.",
                },
            },
            {
                "q": {
                    "zh": "protectedProjectProcedure 的 RBAC 中间件做了一件关键的事：它在 resolver 跑之前就从请求输入里取出 projectId。为什么这一招重要？",
                    "en": "protectedProjectProcedure's RBAC middleware does one key thing: it pulls projectId from the request input before the resolver runs. Why does this matter?",
                },
                "opts": [
                    {
                        "zh": "校验先于业务逻辑发生：任何受保护路由都不可能在没核验「你是这个 project 成员」之前碰到数据，租户隔离由结构保证，而非靠每个路由作者自觉",
                        "en": "the check happens before business logic: no protected router can ever touch data before verifying 'you're a member of this project', so tenant isolation is guaranteed by structure, not by each router author's diligence",
                    },
                    {"zh": "为了让请求更快返回", "en": "to make requests return faster"},
                    {"zh": "为了节省数据库连接", "en": "to save database connections"},
                    {"zh": "projectId 只是用来打日志", "en": "projectId is only used for logging"},
                ],
                "answer": 0,
                "why": {
                    "zh": "enforceUserIsAuthedAndProjectMember 用 getRawInput() 取出 projectId，再去 session 的「组织→项目」树里查成员资格，不通过就抛 FORBIDDEN。这让每个受保护路由自动获得统一、前置的租户校验——正是第 10 课「project_id 是隔离键」在 API 层的落地，安全靠结构而非靠人。",
                    "en": "enforceUserIsAuthedAndProjectMember pulls projectId via getRawInput(), then checks membership in the session's 'org→project' tree, throwing FORBIDDEN otherwise. This gives every protected router uniform, up-front tenant checking — Lesson 10's 'project_id is the isolation key' landing at the API layer, security by structure not by people.",
                },
            },
            {
                "q": {
                    "zh": "所有 procedure 最底层都叠了 withErrorHandling 这一中间件。它对 ClickHouse 的资源类错误（内存超限、超时）做了什么特殊处理？",
                    "en": "All procedures stack withErrorHandling at the base. What special handling does it give ClickHouse resource errors (out-of-memory, timeout)?",
                },
                "opts": [
                    {
                        "zh": "把它们映射成 UNPROCESSABLE_CONTENT 并附上「换个更小的时间范围」之类可操作建议；同时隐藏 5xx 内部细节与堆栈，防止泄露",
                        "en": "maps them to UNPROCESSABLE_CONTENT with actionable advice like 'try a smaller time range'; and hides 5xx internal detail and stacks to prevent leaks",
                    },
                    {"zh": "直接把原始堆栈和 SQL 返回给前端", "en": "returns the raw stack and SQL straight to the frontend"},
                    {"zh": "忽略错误，返回空结果", "en": "ignores the error and returns empty results"},
                    {"zh": "自动重试一百次", "en": "automatically retries a hundred times"},
                ],
                "answer": 0,
                "why": {
                    "zh": "withErrorHandling 统一翻译异常：5xx 隐藏内部细节防泄露；ClickHouse 资源错误（如内存/超时）被特判为 UNPROCESSABLE_CONTENT，并给出「缩小时间范围」等用户能照做的建议。于是无论哪个路由查崩了什么，用户看到的都是一致、可读、不暴露内幕的错误。",
                    "en": "withErrorHandling uniformly translates exceptions: 5xx hides internal detail to prevent leaks; ClickHouse resource errors (memory/timeout) are special-cased to UNPROCESSABLE_CONTENT with actionable advice like 'narrow the time range'. So whatever router blew up, the user sees a consistent, readable error that doesn't expose internals.",
                },
            },
        ],
        "open": [
            {
                "zh": "「把安全检查收敛成中间件、用声明式 procedure 组合，而不是每个接口各写一遍」——这条原则你能用到自己的系统吗？如果你的 API 有几十个端点都要做同一种权限校验，你会怎么设计，才能让「新增端点几乎不可能漏掉校验」？",
                "en": "'Converge security checks into middleware and compose via declarative procedures, rather than hand-writing per endpoint' — can you apply this to your systems? If your API has dozens of endpoints all needing the same permission check, how would you design it so 'a new endpoint can hardly miss the check'?",
            },
        ],
    },
    "22-repository-layer.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 让所有 ClickHouse 读取都经过一个 queryClickhouse() 执行器，而不是各处直接写查询。这样做最核心的收益是？",
                    "en": "Langfuse routes all ClickHouse reads through one queryClickhouse() executor rather than writing queries everywhere. The core benefit?",
                },
                "opts": [
                    {
                        "zh": "横切关注（OTel 追踪、查询标签、退避重试、资源错误包装）一次实现、处处生效；加一项能力全平台查询一起获得，不会有的写有的漏、写法不一",
                        "en": "cross-cutting concerns (OTel tracing, query tags, backoff retry, resource-error wrapping) are implemented once and apply everywhere; add a capability and every query gains it, with no some-write-some-omit inconsistency",
                    },
                    {"zh": "让查询语法更简单", "en": "to make query syntax simpler"},
                    {"zh": "因为 ClickHouse 只接受一个连接", "en": "because ClickHouse accepts only one connection"},
                    {"zh": "为了隐藏 SQL 不让人看", "en": "to hide the SQL from view"},
                ],
                "answer": 0,
                "why": {
                    "zh": "可观测性、追责、重试、资源保护都和「业务查什么」无关却每条查询都需要。收敛到一个执行器，它们一次实现、处处复用；散落各处的裸查询必然写法不一、漏东漏西。这与第 6 课「把复杂度收敛到一处」一脉相承。",
                    "en": "Observability, accountability, retry, resource protection are unrelated to 'what business queries' yet needed by every query. Converged into one executor they're implemented once and reused; scattered raw queries inevitably drift and omit. In line with L06's 'converge complexity to one place'.",
                },
            },
            {
                "q": {
                    "zh": "queryClickhouse 通过 log_comment 给每条 SQL 打上 project/面/路由标签。这个标签的实际用处是？",
                    "en": "queryClickhouse tags every SQL via log_comment with project/surface/route. What's the practical use?",
                },
                "opts": [
                    {
                        "zh": "标签随查询进入 ClickHouse 的查询日志；当某条慢查询拖垮集群时，运维能直接在日志里按标签定位是哪个 project/面/路由的元凶——把可观测性焊进数据访问层",
                        "en": "the tags enter ClickHouse's query log with the query; when a slow query drags the cluster down, operators can locate the culprit project/surface/route by tag right in the log — observability welded into the data-access layer",
                    },
                    {"zh": "标签用来加密查询", "en": "the tags encrypt the query"},
                    {"zh": "标签让查询更快", "en": "the tags speed up the query"},
                    {"zh": "标签替代了 WHERE 条件", "en": "the tags replace the WHERE clause"},
                ],
                "answer": 0,
                "why": {
                    "zh": "sendClickhouseQuery 把标签塞进 clickhouse_settings.log_comment，于是每条打到 CH 的 SQL 都自带「谁/哪个面/哪个路由发起」。出现慢查询或资源耗尽时，可在 CH 自己的查询日志里按标签追责——这是散落各处的裸查询永远做不到的。",
                    "en": "sendClickhouseQuery stuffs tags into clickhouse_settings.log_comment, so every SQL hitting CH carries 'who/which surface/which route initiated it'. On a slow query or resource exhaustion, you can trace the culprit by tag in CH's own query log — impossible for scattered raw queries.",
                },
            },
            {
                "q": {
                    "zh": "把一条 trace 的观测拼起来时，Langfuse 不全表扫 observations，而是只在 trace 时间戳前后一个有界窗口（如 2 天）内找。为什么能、且为什么要这样？",
                    "en": "To stitch a trace's observations, Langfuse doesn't full-scan observations but searches only a bounded window (e.g. 2 days) around the trace timestamp. Why can it, and why must it?",
                },
                "opts": [
                    {
                        "zh": "能：trace/observation/score 是三张独立宽表、靠时间关联，且一条 trace 的观测几乎都集中在它发生后很短时间内；要：否则跨表 JOIN 要扫几个月上亿行，把分析库当事务库用必然拖垮集群",
                        "en": "can: trace/observation/score are three independent wide tables correlated by time, and a trace's observations almost all cluster shortly after it; must: otherwise the cross-table JOIN scans months and billions of rows, crashing the cluster by using an analytical store like a transactional one",
                    },
                    {"zh": "因为 2 天前的数据会被自动删除", "en": "because data older than 2 days is auto-deleted"},
                    {"zh": "因为 ClickHouse 不支持大于 2 天的查询", "en": "because ClickHouse can't query beyond 2 days"},
                    {"zh": "纯粹是随便定的限制", "en": "an arbitrary limit"},
                ],
                "answer": 0,
                "why": {
                    "zh": "第 8 课让三表独立、靠时间关联，JOIN 没有外键可走。回看时间窗（OBSERVATIONS_TO_TRACE_INTERVAL=2 天、SCORE=1 小时）注入 WHERE，配合按月分区只扫几个相关分区。代价是极长尾观测可能漏（源码 README 记录约 96% 在 2 分钟内开始，长尾很长，2 天留足裕量）——用极小正确性换巨大成本节省。",
                    "en": "L08 made the three tables independent and time-correlated, so JOINs have no FK to follow. Look-back windows (OBSERVATIONS_TO_TRACE_INTERVAL=2 days, SCORE=1 hour) injected into WHERE, with monthly partitioning, scan only a few relevant partitions. The cost is missing extreme-long-tail observations (~96% start within 2 min per the repo README, with a long tail; 2 days leaves margin) — a tiny correctness trade for huge cost savings.",
                },
            },
        ],
        "open": [
            {
                "zh": "「把所有数据访问收敛到一个执行器，统一加上追踪、标签、重试、资源保护」——这条原则你能用到自己的系统吗？如果你的代码里到处是裸 SQL/裸 HTTP 调用，把它们收敛到一个执行器，你最想先统一加上哪三样能力？为什么？",
                "en": "'Converge all data access into one executor, uniformly adding tracing, tags, retry, resource protection' — can you apply this to your systems? If your code is full of raw SQL/raw HTTP calls, converging them into one executor, which three capabilities would you add first, and why?",
            },
        ],
    },
    "23-filtering-search-bar.html": {
        "mcq": [
            {
                "q": {
                    "zh": "用户的过滤来自侧栏、搜索栏、AI 三种入口，后端又有 ClickHouse 和 Postgres 两套。Langfuse 让它们都先汇成一个 FilterState 再编译成 SQL，最大的好处是？",
                    "en": "Filters come from three entries (sidebar, search bar, AI), and there are two backends (ClickHouse, Postgres). Langfuse converges them into one FilterState before compiling to SQL. The biggest benefit?",
                },
                "opts": [
                    {
                        "zh": "把 N×M 的直连组合降成 N+M：每个输入只管译成 FilterState、每个后端只管从 FilterState 译出 SQL；校验与参数化只在中间做一次，新增输入白嫖所有后端与全部安全",
                        "en": "it cuts the N×M direct-wiring combinatorics to N+M: each input only translates to FilterState, each backend only translates FilterState to SQL; validation and parameterization happen once in the middle, and a new input freeloads all backends and all the safety",
                    },
                    {"zh": "让查询变快", "en": "it makes queries faster"},
                    {"zh": "可以不用 WHERE 条件", "en": "it removes the need for WHERE clauses"},
                    {"zh": "让前端不用写代码", "en": "the frontend needs no code"},
                ],
                "answer": 0,
                "why": {
                    "zh": "若每个输入直连每个后端，是 N×M 套翻译 + N×M 处注入风险，新增输入要为每个后端重写。收敛到一个 FilterState 中间契约后变 N+M：输入只译入、后端只译出，校验/参数化集中一次。这是「单一中间表示」的核心收益。",
                    "en": "Wiring each input to each backend is N×M translations + N×M injection risks, and a new input means rewriting for every backend. Converging to one FilterState contract makes it N+M: inputs only translate in, backends only translate out, validation/parameterization centralized once. The core gain of a single intermediate representation.",
                },
            },
            {
                "q": {
                    "zh": "FilterState 编译成 ClickHouse SQL 时，每个过滤器的 apply() 用随机命名的占位符（如 stringFilter_xY9z）传值，而不是把值拼进 SQL 字符串。这防住了什么？",
                    "en": "When FilterState compiles to ClickHouse SQL, each filter's apply() passes values via randomly-named placeholders (e.g. stringFilter_xY9z) rather than splicing values into the SQL string. What does this prevent?",
                },
                "opts": [
                    {
                        "zh": "SQL 注入：用户输入的值永远是被绑定的参数、不进 SQL 文本，哪怕写 '; DROP TABLE… 也只当普通字符串匹配；加上工厂校验列存在/类型兼容，脏输入编译期就被挡下",
                        "en": "SQL injection: user values are always bound parameters, never in the SQL text, so even '; DROP TABLE… is matched as a plain string; plus the factory's column-existence/type checks stop dirty input at compile time",
                    },
                    {"zh": "防止查询太慢", "en": "prevents slow queries"},
                    {"zh": "防止结果太多", "en": "prevents too many results"},
                    {"zh": "防止用户看到数据", "en": "prevents users from seeing data"},
                ],
                "answer": 0,
                "why": {
                    "zh": "参数化查询是防注入的根本：值绑定到占位符、由驱动安全代入，绝不与 SQL 文本拼接。随机参数名进一步避免命名冲突。工厂还前置校验列是否在 schema、类型是否兼容，并注入强制 project_id（第 10 课）——多道防线叠加。",
                    "en": "Parameterized queries are the root of injection defense: values bind to placeholders and are safely substituted by the driver, never spliced into SQL text. Random param names avoid collisions. The factory also pre-checks column existence, type compatibility, and injects the mandatory project_id (L10) — layered defenses.",
                },
            },
            {
                "q": {
                    "zh": "AI filter 用大模型从自然语言生成过滤，可大模型可能编造不存在的列。Langfuse 怎么保证幻觉列绝不被应用？",
                    "en": "The AI filter uses an LLM to generate filters from natural language, but the model may hallucinate nonexistent columns. How does Langfuse ensure hallucinated columns are never applied?",
                },
                "opts": [
                    {
                        "zh": "把模型输出往返一遍：用 filterStateToQueryText 转回搜索栏语法、再解析回 FilterState，只保留能干净往返的；还原不了的（幻觉/非法列）直接丢弃。能表达才能进——构造即合法",
                        "en": "it round-trips the model output: convert back to search-bar grammar via filterStateToQueryText and re-parse to FilterState, keeping only what cleanly round-trips; un-restorable ones (hallucinated/illegal columns) are dropped. Only the expressible passes — valid by construction",
                    },
                    {"zh": "人工逐条审核模型输出", "en": "a human reviews each model output"},
                    {"zh": "信任模型，直接应用", "en": "trusts the model and applies directly"},
                    {"zh": "让模型自己检查", "en": "asks the model to check itself"},
                ],
                "answer": 0,
                "why": {
                    "zh": "generateFilter 调 Bedrock 生成候选，再通过 filterStateToQueryText 往返：只有能还原成合法搜索栏语法（即能降解成 FilterState 能表达的过滤）的才被采纳，其余 droppedCount++ 丢弃。因为输出必须能被 FilterState 表达，幻觉列从结构上就进不来——安全靠表示边界而非事后检查。",
                    "en": "generateFilter calls Bedrock for candidates, then round-trips via filterStateToQueryText: only filters that restore to valid search-bar grammar (i.e. lower to what FilterState expresses) are accepted, the rest droppedCount++. Because the output must be expressible by FilterState, hallucinated columns can't enter structurally — safety from the representation's boundaries, not after-checks.",
                },
            },
        ],
        "open": [
            {
                "zh": "「让 AI 的输出必须能还原成一个受限中间表示，不能表达的就进不来」——这种『构造即合法』的护栏，比『生成后再用规则检查』强在哪？你能想到把它用到自己系统里哪个『让 LLM 生成结构化指令』的场景吗？",
                "en": "'Make the AI output have to restore to a constrained intermediate representation, and the inexpressible can't enter' — how is this 'valid by construction' guardrail stronger than 'generate then check with rules'? Can you think of a 'let an LLM generate structured commands' scenario in your own systems where you'd apply it?",
            },
        ],
    },
    "24-lists-and-tables.html": {
        "mcq": [
            {
                "q": {
                    "zh": "打开 trace 列表时，Langfuse 并行发 traces.all（行）和 traces.metrics（指标）两路，而不是一次查全。这样设计为了什么？",
                    "en": "Opening the trace list, Langfuse fires traces.all (rows) and traces.metrics (metrics) in parallel rather than one combined query. Why?",
                },
                "opts": [
                    {
                        "zh": "紧凑行便宜、立刻就到，先把表画出来；成本/延迟/评分等指标要 JOIN 两张表、较慢，作为附加信息后到再按 id 合并。感知延迟从「最慢一路」降到「最快一路」",
                        "en": "compact rows are cheap and arrive instantly so the table paints first; cost/latency/score metrics need 2 JOINs and are slower, merged in by id later as extra info. Perceived latency drops from 'slowest call' to 'fastest call'",
                    },
                    {"zh": "为了多发请求把服务器压垮", "en": "to flood the server with more requests"},
                    {"zh": "因为 ClickHouse 不能一次查两类数据", "en": "because ClickHouse can't query two kinds at once"},
                    {"zh": "为了让指标更准确", "en": "to make metrics more accurate"},
                ],
                "answer": 0,
                "why": {
                    "zh": "列表的体验目标是秒开，而指标天生昂贵（2 JOIN）。把便宜的行和昂贵的指标拆开，joinTableCoreAndMetrics 按 id 合并、指标缺席也返回 success，于是表格先用行渲染、指标后到补入。这是「紧凑列表模型」——能立刻给的先给，要算的边算边补。",
                    "en": "The list's goal is instant open, but metrics are inherently expensive (2 JOINs). Splitting cheap rows from costly metrics, joinTableCoreAndMetrics merges by id and returns success even without metrics, so the table renders from rows first and fills metrics later. The 'compact list model' — give what you can instantly, fill in what you compute as it comes.",
                },
            },
            {
                "q": {
                    "zh": "traces 是 ReplacingMergeTree（同 id 可能多行）。默认按时间排序时，Langfuse 不用 FINAL，而是 ORDER BY toDate(timestamp),event_ts DESC + LIMIT 1 BY id。为什么这样更好？",
                    "en": "traces is a ReplacingMergeTree (one id may have multiple rows). For default time ordering, Langfuse skips FINAL and uses ORDER BY toDate(timestamp),event_ts DESC + LIMIT 1 BY id. Why is this better?",
                },
                "opts": [
                    {
                        "zh": "FINAL 会当场读全部分区去重、很慢；而按时间排序 + LIMIT 1 BY id 让 CH 只从磁盘读最新那天的分区、在内存里取每个 id 的最新行——既对又快，不必为去重捞一个月的数据",
                        "en": "FINAL reads all partitions and dedups on the spot, slow; time ordering + LIMIT 1 BY id lets CH read only the latest day's partition from disk and take each id's latest row in memory — correct and fast, no pulling a month of data just to dedup",
                    },
                    {"zh": "因为 FINAL 会返回错误结果", "en": "because FINAL returns wrong results"},
                    {"zh": "因为 LIMIT 1 BY id 更省内存", "en": "because LIMIT 1 BY id saves memory"},
                    {"zh": "因为默认排序不需要去重", "en": "because default ordering needs no dedup"},
                ],
                "answer": 0,
                "why": {
                    "zh": "FINAL 正确但慢（读全量去重）。默认按时间排序时，用 event_ts DESC + LIMIT 1 BY id 在内存里取每个 id 最新行，CH 只读最新分区。只有按非时间列（如成本）排序时才退回 FROM traces FINAL 全量去重——按需付费，常见路径不被拖累。",
                    "en": "FINAL is correct but slow (reads all to dedup). For default time ordering, event_ts DESC + LIMIT 1 BY id takes each id's latest row in memory, CH reading only the latest partition. Only sorting by a non-time column (e.g. cost) falls back to FROM traces FINAL full dedup — pay on demand, the common path unburdened.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的表格状态（过滤、排序、列设置、视图预设）分三层存储，以 URL 为真源。这样分层最直接的好处是？",
                    "en": "Langfuse stores table state (filters, sort, column settings, view presets) in three layers, with the URL as the source of truth. The most direct benefit?",
                },
                "opts": [
                    {
                        "zh": "URL 编码当前视图 → 把链接发给同事，他看到的和你一模一样（可分享/可深链）；session 记导航间状态不丢；DB 存永久预设、可跨设备共享，失效列优雅降级",
                        "en": "the URL encodes the current view → send a colleague the link and they see exactly what you do (shareable/deep-linkable); session preserves state across navigation; DB stores permanent presets, cross-device shareable, with graceful degradation for invalid columns",
                    },
                    {"zh": "让表格渲染更快", "en": "to render the table faster"},
                    {"zh": "为了减少数据库查询", "en": "to reduce database queries"},
                    {"zh": "为了隐藏过滤条件", "en": "to hide filter conditions"},
                ],
                "answer": 0,
                "why": {
                    "zh": "三层各管一段时效：URL「此刻可分享」（深链、一个链接复现全貌，呼应第 23 课 FilterState）、session「这次导航」（跳转间不丢列宽/可见列）、DB「永久」（saved view 跨设备团队共享，失效部分丢弃+提示不白屏）。这让大表格既快又稳又可分享。",
                    "en": "Three layers each own a timescale: URL 'shareable now' (deep links, one link reproduces the whole view, echoing L23's FilterState), session 'this navigation' (column widths/visible columns survive hops), DB 'permanent' (saved views shared cross-device/team, invalid parts dropped+warned, no blank screen). This makes big tables fast, stable, and shareable.",
                },
            },
        ],
        "open": [
            {
                "zh": "「为最常见路径极致优化，把复杂度/代价推迟到真的要了才引入」——紧凑行 vs 指标、按需 JOIN、按需 FINAL 都是这条原则。你做过的列表/详情界面里，有没有「为了 1% 的高级需求，拖慢了 99% 的日常浏览」的地方？你会怎么拆？",
                "en": "'Optimize for the most common path, defer complexity/cost until actually asked' — compact rows vs metrics, conditional JOIN, conditional FINAL all follow it. In your own list/detail UIs, is there a place where 'the 1% advanced need slows the 99% daily browse'? How would you split it?",
            },
        ],
    },
    "25-trace-detail-tree.html": {
        "mcq": [
            {
                "q": {
                    "zh": "详情页要看一条 trace 的整棵观测树，可 byIdWithObservationsAndScores 取观测时却传 includeIO:false（不带 input/output）。为什么？",
                    "en": "The detail page shows a trace's whole observation tree, yet byIdWithObservationsAndScores fetches observations with includeIO:false (no input/output). Why?",
                },
                "opts": [
                    {
                        "zh": "树查询只带结构与时序（轻、快），整棵树立刻可见；某个观测的 IO 可能是几 MB JSON、几百个叠起来会爆，所以点开哪个节点才懒加载那一个的 IO——按需付费，不为没看的节点买单",
                        "en": "the tree query carries only structure and timing (light, fast) so the whole tree shows instantly; one observation's IO can be a multi-MB JSON and hundreds explode, so only opening a node lazy-loads that one's IO — pay on demand, never for nodes you didn't look at",
                    },
                    {"zh": "因为观测没有 IO 字段", "en": "because observations have no IO fields"},
                    {"zh": "为了隐藏 IO 不让用户看", "en": "to hide IO from users"},
                    {"zh": "因为 IO 存在另一个数据库", "en": "because IO lives in another database"},
                ],
                "answer": 0,
                "why": {
                    "zh": "一条 agent trace 可能有几百个观测，每个 IO 是不短的 JSON。开树就拉全部 IO 会是几十 MB、好几秒，而你大多数节点根本不展开——白拉。Langfuse 让树先到（结构+时序）、IO 点开懒加载，于是超大 trace 详情也能秒开。",
                    "en": "An agent trace may have hundreds of observations, each IO a sizeable JSON. Loading all IO when opening the tree would be tens of MB and seconds, yet you won't expand most nodes — wasted. Langfuse sends the tree first (structure+timing) and lazy-loads IO on click, so even a huge trace's detail opens instantly.",
                },
            },
            {
                "q": {
                    "zh": "第 24 课列表「极力推迟」、第 25 课详情「一次取全树」，看似相反。它们其实遵循同一条原则，是哪条？",
                    "en": "Lesson 24's list 'defers aggressively' while Lesson 25's detail 'fetches the whole tree' — seemingly opposite. What single principle do they share?",
                },
                "opts": [
                    {
                        "zh": "先取有界的维度、推迟无界的维度：列表面对无界行数→连稍贵的列都推迟；详情面对一条 trace（观测数有界）→结构取全，但树内单个观测 IO 仍是无界维度→懒加载。只急着取你扛得住的那部分",
                        "en": "fetch the bounded dimension first, defer the unbounded one: the list faces unbounded rows → defer even slightly pricey columns; the detail faces one trace (bounded observation count) → fetch structure in full, but a single observation's IO is still an unbounded dimension within → lazy-load. Only rush to fetch the part you can bear",
                    },
                    {"zh": "都尽量多取数据", "en": "both fetch as much data as possible"},
                    {"zh": "都尽量少取数据", "en": "both fetch as little data as possible"},
                    {"zh": "列表用 ClickHouse、详情用 Postgres", "en": "list uses ClickHouse, detail uses Postgres"},
                ],
                "answer": 0,
                "why": {
                    "zh": "关键是有界性。列表的行数无界（几千几万），故连一行里稍贵的指标都推迟；详情面对一条 trace，观测数虽多但有界，且看全这一条正是详情价值，故结构与时序一次取全。但有界实体内仍藏无界维度（单观测 IO），于是同一纪律下沉到树内：树取全、IO 缓取、verbosity 封顶。",
                    "en": "The key is boundedness. The list's row count is unbounded (thousands+), so even per-row metrics are deferred; the detail faces one trace whose observation count, though large, is bounded, and seeing this one in full is the detail's value, so structure and timing are fetched at once. But a bounded entity hides an unbounded dimension (per-observation IO), so the same discipline descends into the tree: fetch the tree, defer IO, cap with verbosity.",
                },
            },
            {
                "q": {
                    "zh": "byId 接口带一个 verbosity 参数（compact/truncated/full），在服务端决定 trace 自身 IO 是否解析/截断。为什么要在服务端而不是前端做这个截断？",
                    "en": "byId carries a verbosity param (compact/truncated/full) deciding server-side whether the trace's own IO is parsed/truncated. Why truncate server-side rather than on the frontend?",
                },
                "opts": [
                    {
                        "zh": "等数据传到前端再裁已经晚了——那几 MB 已从 ClickHouse 读出、序列化、走完网络。verbosity 让裁剪发生在最靠近数据源处：compact 压根不取、truncated 序列化前截短、full 才完整返回",
                        "en": "trimming after data reaches the frontend is too late — those MB already got read from ClickHouse, serialized, crossed the network. verbosity puts trimming closest to the source: compact doesn't fetch, truncated cuts before serialization, only full returns it whole",
                    },
                    {"zh": "前端不能截断字符串", "en": "the frontend can't truncate strings"},
                    {"zh": "为了让前端代码更简单", "en": "to simplify frontend code"},
                    {"zh": "因为服务端更安全", "en": "because the server is more secure"},
                ],
                "answer": 0,
                "why": {
                    "zh": "截断的目的是省「读取+序列化+传输」的成本；这些成本在数据离开 ClickHouse 时就已发生，到前端再裁只是徒劳。verbosity 在服务端、最靠近数据源处定档：compact 不取 IO、truncated 序列化前截短、full 完整。于是同一个 byId 既能给列表轻量预览、又能给详情看全文。",
                    "en": "Truncation aims to save 'read+serialize+transfer' cost; those costs already happen as data leaves ClickHouse, so trimming at the frontend is futile. verbosity tiers server-side, closest to the source: compact fetches no IO, truncated cuts before serialization, full returns whole. So one byId serves both a list's lightweight preview and a detail's full text.",
                },
            },
        ],
        "open": [
            {
                "zh": "「圈定有界维度先取、推迟无界维度」——这条原则你能用到自己做的「列表 + 详情」界面吗？想想你的实体里哪些维度是有界的（适合一次取）、哪些是无界的（该懒加载或封顶）？你会在哪一层、用什么手段给无界维度封顶？",
                "en": "'Fence the bounded dimension and fetch it first, defer the unbounded one' — can you apply this to your own 'list + detail' UIs? Which dimensions of your entities are bounded (fetch at once) and which unbounded (lazy-load or cap)? At which layer and by what means would you cap the unbounded ones?",
            },
        ],
    },
    "26-sessions.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的 session（会话，比如一段多轮对话）的「指标与列表」在存储上是怎么回事？",
                    "en": "How do a Langfuse session's metrics and listing (e.g. a multi-turn conversation) exist in storage?",
                },
                "opts": [
                    {
                        "zh": "它们不单独存，而是 traces 按 session_id 的 GROUP BY 现算出来——session_id 只是第 8 课宽表上的一列，分组即得各项聚合指标（仅有一个轻量元数据存根 trace_sessions 在摄取时落 Postgres）",
                        "en": "they aren't stored separately but computed on the fly by GROUP BY of traces on session_id — session_id is just a column on Lesson 8's wide table, grouping yields all the aggregate metrics (only a lightweight metadata stub, trace_sessions, is persisted to Postgres on ingestion)",
                    },
                    {"zh": "每个会话的全部指标（计数/成本/时长）都预先算好、存进一张表，每条 trace 进来都更新它", "en": "every session's full metrics (count/cost/duration) are pre-computed and stored in a table, updated by each incoming trace"},
                    {"zh": "session 的指标全存在 Redis 里", "en": "session metrics all live in Redis"},
                    {"zh": "session 是前端临时拼出来的，后端完全不参与", "en": "sessions are assembled ad-hoc on the frontend, with no backend involvement"},
                ],
                "answer": 0,
                "why": {
                    "zh": "session_id 本就是 traces 宽表的一列，按它 GROUP BY 就能现算出会话的全部指标：user_ids（去重）、trace_count（计数）、duration（最晚−最早）、session_total_cost（求和）。这些聚合不预存——避免每条 trace 都要同步更新。摄取时只往 Postgres trace_sessions 落一个极轻的存根（id/project/environment + 元数据如收藏/公开），登记会话存在，但不存指标。",
                    "en": "session_id is already a column on the traces wide table, so GROUP BY on it computes all the session's metrics on the fly: user_ids (distinct), trace_count (count), duration (latest−earliest), session_total_cost (sum). These aggregates aren't pre-stored — avoiding a sync update per trace. On ingestion only a tiny stub goes into Postgres trace_sessions (id/project/environment + metadata like bookmarked/public), registering the session's existence but storing no metrics.",
                },
            },
            {
                "q": {
                    "zh": "把 session 的「指标」靠 GROUP BY 现算、而不是预先算好存进一张表，最大的好处是？",
                    "en": "Computing a session's metrics on the fly by GROUP BY rather than pre-computing them into a table — the biggest benefit?",
                },
                "opts": [
                    {
                        "zh": "指标永远和底层 traces 一致 + 零额外聚合写入：新来一条带某 session_id 的 trace 自动被算进那个会话的统计，不需要「更新会话聚合」的同步，也就不会出现「trace 写了、会话计数忘了加」的不一致",
                        "en": "metrics always consistent with the underlying traces + zero extra aggregate writes: a new trace with some session_id is automatically counted into that session's stats, no 'update the session aggregates' sync, so no 'trace written but session count forgotten' inconsistency",
                    },
                    {"zh": "让 session 查询更快", "en": "makes session queries faster"},
                    {"zh": "节省 trace 的存储空间", "en": "saves trace storage space"},
                    {"zh": "让 session 能被单独删除", "en": "lets sessions be deleted independently"},
                ],
                "answer": 0,
                "why": {
                    "zh": "现算的聚合天然和底层一致：会话指标从 traces 现场 GROUP BY 得出，新 trace 自动算入，无需同步聚合值，杜绝了「双写不一致」bug。若反过来把每个会话的计数/成本/时长预存进表，每条 trace 都要更新它——多一条写入链路、多一份要操心同步的状态。会话仍会落一个轻量元数据存根（trace_sessions），但昂贵的聚合一律现算、不预存。",
                    "en": "On-the-fly aggregates are inherently consistent with the underlying data: session metrics come from a live GROUP BY over traces, a new trace is auto-counted, no aggregate to sync, eliminating 'dual-write inconsistency' bugs. Conversely pre-storing each session's count/cost/duration makes every trace update it — an extra write path and state to sync. A lightweight metadata stub (trace_sessions) is still persisted, but the expensive aggregates are always computed, never pre-stored.",
                },
            },
            {
                "q": {
                    "zh": "sessions-ui-table-service 的 getSessionsTableGeneric 和第 24 课 traces 的 getTracesTableGeneric「几乎一个模子」（同样四形状、同样紧凑行 vs 指标拆分）。这说明了什么设计价值？",
                    "en": "getSessionsTableGeneric mirrors Lesson 24's getTracesTableGeneric (same four shapes, same compact-rows-vs-metrics split). What design value does this show?",
                },
                "opts": [
                    {
                        "zh": "把表格系统做成「实体无关的通用件」：会话表白白继承第 24 课的分页、回看窗、按需聚合、URL 状态等全部能力，一行新代码不用写；再来一个「按某维度聚合的列表」也能套同一模子",
                        "en": "making the table system an 'entity-agnostic generic part': the sessions table inherits all of Lesson 24's pagination, look-back windows, on-demand aggregation, URL state etc. without a line of new code; any new 'list aggregated by some dimension' fits the same mold",
                    },
                    {"zh": "说明代码重复、应该合并", "en": "it shows duplicated code that should be merged"},
                    {"zh": "说明 session 和 trace 是同一种东西", "en": "it shows sessions and traces are the same thing"},
                    {"zh": "纯属巧合", "en": "pure coincidence"},
                ],
                "answer": 0,
                "why": {
                    "zh": "把通用表格机制（四形状、紧凑行 vs 指标、按需聚合、URL 状态、列预设）抽象成实体无关的通用件后，会话表只需提供「按 session_id 分组」的查询，就免费获得全部性能与体验。这就是正交设计的红利：一个看似实在的新功能，本质是一句 GROUP BY + 复用已有机制。",
                    "en": "Abstracting the generic table machinery (four shapes, compact-vs-metrics, on-demand aggregation, URL state, column presets) into an entity-agnostic part means the sessions table only supplies a 'GROUP BY session_id' query to get all the performance and UX free. The dividend of orthogonal design: a seemingly substantial feature is essentially one GROUP BY plus reusing existing machinery.",
                },
            },
        ],
        "open": [
            {
                "zh": "「能从已有数据现算的，就别再单独存一份」——session 用 GROUP BY 从 traces 派生，省掉了一套写入与同步。你做过的系统里，有没有「为了方便而冗余存了一份、结果要操心同步一致性」的地方？哪些适合改成派生视图？派生的代价（每次查都要现算）你怎么权衡？",
                "en": "'What you can compute from existing data, don't store again' — sessions derive from traces by GROUP BY, sparing a write-and-sync path. In your systems, is there a place where 'you stored a redundant copy for convenience and then had to worry about sync consistency'? Which would suit a derived view? How do you weigh the cost of deriving (computing on every query)?",
            },
        ],
    },
    "27-public-rest-api.html": {
        "mcq": [
            {
                "q": {
                    "zh": "公共 REST API 用一个路由工厂 createAuthedProjectAPIRoute 统一所有端点。和第 21 课 tRPC 的 procedure 构建器相比，它额外多了哪些「面向公众」的关卡？",
                    "en": "The public REST API unifies all endpoints with one route factory createAuthedProjectAPIRoute. Compared to Lesson 21's tRPC procedure builders, what 'public-facing' gates does it add?",
                },
                "opts": [
                    {
                        "zh": "限流（防外部滥用）、响应校验（防对外契约漂移）、访问级别（如 Bearer 只读 score）——都是对内 tRPC 不需要、对外才必须的关卡",
                        "en": "rate limiting (against external abuse), response validation (against external contract drift), access levels (e.g. Bearer read-only scores) — gates the internal tRPC doesn't need but the external API must have",
                    },
                    {"zh": "更复杂的类型检查", "en": "more complex type checking"},
                    {"zh": "更快的数据库连接", "en": "faster database connections"},
                    {"zh": "去掉了鉴权", "en": "it removes auth"},
                ],
                "answer": 0,
                "why": {
                    "zh": "两套都用「工厂/构建器把横切关注收敛到一处」的同一模式，但优先级不同：tRPC 对内求速度，REST 对外求稳定与扛量，故多了限流、响应校验、访问级别。鉴权、Zod 校验则是两者共有——都不靠端点作者自觉，由工厂强制跑。",
                    "en": "Both use the same 'factory/builder converges cross-cutting concerns' pattern, but with different priorities: tRPC seeks internal speed, REST external stability and scale, hence the added rate-limit, response validation, access levels. Auth and Zod validation are common to both — neither relies on endpoint-author diligence; the factory forces them.",
                },
            },
            {
                "q": {
                    "zh": "对外 API 每个请求都要验 key，SDK 可能每秒上万条。Langfuse 的鉴权除了用 Redis 缓存命中的 key，还特意「负缓存」不存在的 key。负缓存防的是什么？",
                    "en": "An external API verifies a key per request, and SDKs may send tens of thousands per second. Besides caching valid keys in Redis, Langfuse deliberately 'negatively caches' nonexistent keys. What does negative caching prevent?",
                },
                "opts": [
                    {
                        "zh": "暴力打库：攻击者拿大量假 key 来刷，若不缓存「不存在」，每个假 key 都会回 Postgres 查一遍；负缓存（API_KEY_NON_EXISTENT）让第二次起就被 Redis 挡回，保护数据库",
                        "en": "brute-forcing the DB: attackers flood with many fake keys; without caching 'nonexistent', each fake key would hit Postgres; negative caching (API_KEY_NON_EXISTENT) blocks them at Redis from the 2nd hit, shielding the database",
                    },
                    {"zh": "防止 key 泄露", "en": "prevents key leakage"},
                    {"zh": "防止响应太大", "en": "prevents oversized responses"},
                    {"zh": "防止版本不一致", "en": "prevents version mismatch"},
                ],
                "answer": 0,
                "why": {
                    "zh": "只缓存有效 key 时，攻击者用海量不存在的 key 仍能让每次都穿透到 Postgres。负缓存把「这个 key 不存在」也记进 Redis，于是无论正常流量还是恶意刷量，数据库都被保护在缓存后面，只在真正缓存未命中时才被惊动。这是「缓存正例也缓存反例」的安全考量。",
                    "en": "Caching only valid keys still lets attackers with floods of nonexistent keys punch through to Postgres each time. Negative caching records 'this key doesn't exist' in Redis too, so whether normal traffic or malicious flooding, the DB stays shielded behind the cache, disturbed only on a true miss. A 'cache the positives and the negatives' security consideration.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 用「文件夹做版本」（v1 在根、v2/、v3/）+「Fern 契约生成 SDK」来管理对外 API。这套组合解决的核心矛盾是？",
                    "en": "Langfuse manages the external API with 'versioning by folder' (v1 at root, v2/, v3/) + 'Fern contract generates SDKs'. What core tension does this combo resolve?",
                },
                "opts": [
                    {
                        "zh": "「需求要演进」与「发布后不能破坏老用户」的矛盾：文件夹版本让老路径永不改（旧集成照跑）、新版可显式切换甚至做减法；Fern 一份契约生成多语言 SDK、保证一致，开发期响应校验防实现与契约漂移",
                        "en": "the tension between 'needs evolve' and 'can't break existing users after release': folder versions keep old paths unchanged (old integrations run) while new versions opt-in and can even subtract; Fern's one contract generates multi-language SDKs ensuring consistency, with dev-time response validation against drift",
                    },
                    {"zh": "让 API 响应更快", "en": "makes API responses faster"},
                    {"zh": "减少端点数量", "en": "reduces the number of endpoints"},
                    {"zh": "让前端不用写代码", "en": "lets the frontend skip code"},
                ],
                "answer": 0,
                "why": {
                    "zh": "对外契约一旦发布就不能随意改，但需求总在变。文件夹版本让 v1 永不破、新能力进 v2/v3（甚至砍掉昂贵旧设计，如 v3 scores 去掉需 JOIN 的过滤、改游标分页）；Fern 用一份手写 YAML 生成 Python/TS SDK + OpenAPI，一处定义处处一致。这正是第 20 课「对外求契约稳定」的落地。",
                    "en": "An external contract can't change freely once published, yet needs keep evolving. Folder versions keep v1 unbroken and put new capability in v2/v3 (even cutting costly old designs, e.g. v3 scores dropping JOIN-needing filters for cursor pagination); Fern generates Python/TS SDKs + OpenAPI from one hand-written YAML, define-once consistent everywhere. This realizes Lesson 20's 'externally seek contract stability'.",
                },
            },
        ],
        "open": [
            {
                "zh": "「对内优化『改得快』、对外优化『不破坏』」——同一份数据，UI 用 tRPC、SDK 用版本化 REST。你做过或用过的系统里，内部接口和对外 API 是怎么处理这对矛盾的？如果让你给一个对外 API 设计「演进而不破坏」的机制，你会怎么做版本、怎么防契约漂移？",
                "en": "'Internally optimize fast-to-change, externally optimize don't-break' — same data, UI via tRPC, SDK via versioned REST. In systems you've built or used, how were internal interfaces and external APIs handled against this tension? Designing an 'evolve without breaking' mechanism for an external API, how would you do versioning and prevent contract drift?",
            },
        ],
    },
    "28-scoring-model.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse score config 有三种可比刻度：NUMERIC、CATEGORICAL、BOOLEAN。但源码里 BOOLEAN 并不是独立的一套校验逻辑，而是被实现成什么？",
                    "en": "A Langfuse score config has three comparable scales: NUMERIC, CATEGORICAL, BOOLEAN. But in the source, BOOLEAN is not its own independent validation logic — what is it implemented as?",
                },
                "opts": [
                    {
                        "zh": "一个「恰好两档、且锁死为 True=1 / False=0」的特殊 CATEGORICAL——底层只需处理数值与分类两套逻辑，布尔复用分类的存储与聚合",
                        "en": "a special CATEGORICAL with 'exactly two categories, locked to True=1 / False=0' — the core only handles numeric and categorical, and boolean reuses categorical storage and aggregation",
                    },
                    {"zh": "一个独立的布尔表", "en": "a separate boolean table"},
                    {"zh": "一个 NUMERIC 的别名", "en": "an alias of NUMERIC"},
                    {"zh": "一段前端专用的校验", "en": "a frontend-only validation"},
                ],
                "answer": 0,
                "why": {
                    "zh": "BooleanConfigFields 强制 categories 长度为 2、且锁死 {True:1, False:0}（score-configs.ts）。这样就不必为布尔新造一套存储/聚合，它顺着分类的路走——少一套特例、多一分一致。这正呼应第 8 课「能用通用机制表达的，就别新造一个」。",
                    "en": "BooleanConfigFields forces categories length 2, locked to {True:1, False:0} (score-configs.ts). So boolean needs no new storage/aggregation; it rides the categorical path — one fewer special case, more consistency. This echoes Lesson 8's 'if a general mechanism expresses it, don't invent a new one'.",
                },
            },
            {
                "q": {
                    "zh": "「有用性」这个分数，A 团队打 0–1、B 团队用百分制、C 用「好/差」。score config 要解决的核心问题是？",
                    "en": "For the score 'helpfulness', team A rates 0–1, team B uses a percentage, C uses 'good/bad'. What core problem does a score config solve?",
                },
                "opts": [
                    {
                        "zh": "可比性：config 是某个 name 的 schema，把「这个名字=这种刻度」固定并强制校验，于是同名分数永远同一把尺——求平均、画趋势、做对比才有意义",
                        "en": "comparability: a config is the schema of a name, fixing and enforcing 'this name = this scale', so same-named scores always use one ruler — only then are averaging, trending, and comparison meaningful",
                    },
                    {"zh": "让评分速度更快", "en": "makes scoring faster"},
                    {"zh": "减少数据库存储", "en": "reduces database storage"},
                    {"zh": "自动生成分数", "en": "auto-generates scores"},
                ],
                "answer": 0,
                "why": {
                    "zh": "「能比较」是评估的全部价值。若同名分数刻度各异，放一起求平均/画趋势/对比全是错的。score config 显式声明 dataType 与约束（区间/类别）并前置校验，使同名分数恒可比。这和第 8 课 provided/computed、第 16 课定价 schema 是同一种「把数据该长什么样显式建模」的工程信念。",
                    "en": "'Being comparable' is the whole value of evaluation. If same-named scores use different scales, averaging/trending/comparing them is all wrong. A score config explicitly declares dataType and constraints (bounds/categories) and validates up front, keeping same-named scores forever comparable. Same belief as Lesson 8's provided/computed and Lesson 16's pricing schema: model 'what the data should look like' explicitly.",
                },
            },
            {
                "q": {
                    "zh": "score 有三种 source：API、EVAL、ANNOTATION（scores.ts 的 ScoreSourceArray）。关于这三者的关系，下列哪句最准确？",
                    "en": "A score has three sources: API, EVAL, ANNOTATION (ScoreSourceArray in scores.ts). Which statement about them is most accurate?",
                },
                "opts": [
                    {
                        "zh": "三者殊途同归：AI 评判(EVAL)、人工标注(ANNOTATION)、亲手提交(API)最终都按同一 config 校验、写进同一张 scores 表——评估不是独立管道，而是 score 的生产者",
                        "en": "all three converge: AI judging (EVAL), human annotation (ANNOTATION), and direct submission (API) are all validated by the same config and written to the same scores table — evaluation isn't a separate pipeline but a producer of scores",
                    },
                    {"zh": "三种 source 各有独立的表和聚合逻辑", "en": "each source has its own table and aggregation logic"},
                    {"zh": "只有 API 来源会被存储", "en": "only the API source gets stored"},
                    {"zh": "EVAL 分数不经过摄取链路", "en": "EVAL scores bypass the ingestion path"},
                ],
                "answer": 0,
                "why": {
                    "zh": "ScoreSourceArray=[\"API\",\"EVAL\",\"ANNOTATION\"] 只是给同一张 scores 表的一行标注「这分谁打的」。LLM-as-a-judge、代码 eval、人工标注算出的分都走回同一条摄取链路、按同一 config 校验。这就是 Part 5 后续每课的共同终点：用不同方式生产可比的 score。",
                    "en": "ScoreSourceArray=[\"API\",\"EVAL\",\"ANNOTATION\"] merely labels a row in the same scores table with 'who scored this'. Scores from LLM-as-a-judge, code eval, and human annotation all flow back through the same ingestion path, validated by the same config. This is the shared destination of every remaining Part 5 lesson: producing comparable scores in different ways.",
                },
            },
        ],
        "open": [
            {
                "zh": "Langfuse 把「AI 评的、人审的、API 报的」分数统一成一种 score、一张表、一套 config，只用 source 字段区分来源。在你做过或设想的系统里，如果要把「多种来源的质量信号」统一成一个可比的指标，你会怎么设计它的数据模型？需要一个像 score config 那样的「schema 守门人」吗，为什么？",
                "en": "Langfuse unifies 'AI-judged, human-reviewed, API-reported' scores into one score type, one table, one config, distinguishing origin only by a source field. In a system you've built or imagined, if you had to unify 'quality signals from many sources' into one comparable metric, how would you design its data model? Would you want a 'schema gatekeeper' like a score config — and why?",
            },
        ],
    },
    "29-llm-as-a-judge.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的 LLM-as-a-judge 强制裁判 LLM 用「结构化输出」返回 {score, reasoning}，而不是让它自由写一段评语。这么做的核心原因是？",
                    "en": "Langfuse's LLM-as-a-judge forces the judge LLM to return {score, reasoning} via 'structured output' rather than free prose. The core reason is?",
                },
                "opts": [
                    {
                        "zh": "评估的产物要能录入、聚合、比较：分必须能进 scores 表跨千条 trace 求平均，理由留在 comment 里可追溯——散文两样都做不到",
                        "en": "the product of evaluation must be recordable, aggregatable, comparable: the score must enter the scores table to average across thousands of traces, with the reasoning kept in comment for traceability — prose does neither",
                    },
                    {"zh": "结构化输出让 LLM 调用更便宜", "en": "structured output makes the LLM call cheaper"},
                    {"zh": "可以不调用 LLM", "en": "it avoids calling the LLM"},
                    {"zh": "让裁判模型必须用 GPT-4", "en": "it forces the judge to use GPT-4"},
                ],
                "answer": 0,
                "why": {
                    "zh": "若裁判回一段散文，既没法可靠抽出一个数值分、也没法跨大量 trace 聚合。强制 {score, reasoning} 的 schema 让 value 进 scores 表（可聚合）、reasoning 进 comment（可追溯），两全。toNormalizedScores 正是据此把输出归一成 score（value=分，comment=理由）。",
                    "en": "If the judge returns prose, you can't reliably extract a numeric score nor aggregate across many traces. Forcing a {score, reasoning} schema puts value into the scores table (aggregatable) and reasoning into comment (traceable) — both at once. toNormalizedScores normalizes the output into a score exactly this way (value=score, comment=reasoning).",
                },
            },
            {
                "q": {
                    "zh": "裁判 LLM 评出的分，最终是怎么变成数据库里一条可查询的 score 的？",
                    "en": "How does the judge LLM's verdict ultimately become a queryable score in the database?",
                },
                "opts": [
                    {
                        "zh": "包成 source=EVAL 的 SCORE_CREATE 事件，走第 12 课那条和手写 score 完全相同的摄取链路——评估是摄取管道的又一个生产者，不是独立系统",
                        "en": "wrapped as a source=EVAL SCORE_CREATE event through the exact same Lesson-12 ingestion path as a hand-written score — evaluation is another producer for the ingestion pipeline, not a separate system",
                    },
                    {"zh": "直接 INSERT 进 ClickHouse，绕过摄取链路", "en": "directly INSERTed into ClickHouse, bypassing ingestion"},
                    {"zh": "存进一张专门的 eval 结果表", "en": "stored in a dedicated eval-results table"},
                    {"zh": "只存在内存里供仪表盘读取", "en": "kept in memory only for dashboards"},
                ],
                "answer": 0,
                "why": {
                    "zh": "evalScoreEvent.ts 把归一后的结果包成 eventTypes.SCORE_CREATE、标 source=ScoreSourceEnum.EVAL，再走摄取链路。于是去重、合并、落 ClickHouse 的逻辑只写一遍、对 API/EVAL/ANNOTATION 三来源一致。这正是「一个入口，多个生产者」的体现，也让裁判分天然与其它来源同表可比。",
                    "en": "evalScoreEvent.ts wraps the normalized result as eventTypes.SCORE_CREATE tagged source=ScoreSourceEnum.EVAL, then runs the ingestion path. So dedup/merge/ClickHouse-persist are written once and consistent across API/EVAL/ANNOTATION. This is 'one entry, many producers', and makes judge scores inherently comparable in the same table.",
                },
            },
            {
                "q": {
                    "zh": "模板里写的是 {{question}}、{{answer}} 这样的占位符。执行时它们怎么变成真实内容？",
                    "en": "The template holds placeholders like {{question}}, {{answer}}. How do they become real content at execution?",
                },
                "opts": [
                    {
                        "zh": "靠变量映射：每个模板变量声明来自 trace/observation/dataset_item 的哪一列，extractVariablesFromTracingData 去真实数据取值，compileEvalPrompt 再填进占位符",
                        "en": "via variable mapping: each template variable declares which column of trace/observation/dataset_item it comes from; extractVariablesFromTracingData fetches real values, then compileEvalPrompt fills the placeholders",
                    },
                    {"zh": "裁判 LLM 自己去数据库查", "en": "the judge LLM queries the database itself"},
                    {"zh": "用固定的示例数据", "en": "with fixed sample data"},
                    {"zh": "前端把内容硬编码进模板", "en": "the frontend hardcodes content into the template"},
                ],
                "answer": 0,
                "why": {
                    "zh": "每条映射是 {templateVariable, langfuseObject, selectedColumnId}。执行时按映射从真实 trace/observation/dataset_item 取那一列的值，得到 {var, value}；compileEvalPrompt 在「喂给 LLM」的边界用 parseUnknownToString 拍平成字符串再填进 {{占位符}}。提取阶段保留原始形状（给代码 eval 用），只在边界处转换。",
                    "en": "Each mapping is {templateVariable, langfuseObject, selectedColumnId}. At run it pulls that column's value from the real trace/observation/dataset_item into {var, value}; compileEvalPrompt flattens to a string via parseUnknownToString at the 'feed-to-LLM' boundary before filling {{placeholders}}. Extraction keeps original shapes (for code eval), converting only at the boundary.",
                },
            },
        ],
        "open": [
            {
                "zh": "LLM-as-a-judge 用一个 LLM 评判另一个 LLM——但裁判自己也会犯错、也有偏好。你会怎么验证「裁判本身是否可靠」？（提示：Langfuse 把裁判的每次调用也记成一条 trace，且评出的分能和人工标注的分同表比较。）这对「用 AI 评 AI」的可信度建设意味着什么？",
                "en": "LLM-as-a-judge uses one LLM to judge another — but the judge itself errs and has biases. How would you validate 'whether the judge itself is reliable'? (Hint: Langfuse records each judge call as a trace, and judge scores sit in the same table as human-annotation scores for comparison.) What does this imply for building trust in 'AI judging AI'?",
            },
        ],
    },
    "30-eval-execution-pipeline.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的评估调度把工作拆成「创建」和「执行」两级队列。这种分离最核心的好处是？",
                    "en": "Langfuse's eval scheduling splits work into 'creation' and 'execution' two-stage queues. The core benefit of this separation is?",
                },
                "opts": [
                    {
                        "zh": "两件事性质不同：创建是轻快的纯数据库匹配，执行是慢、花钱、会限流的 LLM 调用——分开后各自独立扩容、采样、重试，慢的不拖死快的",
                        "en": "the two differ in nature: creation is light pure-DB matching, execution is slow, costly, rate-limited LLM calls — split apart they scale/sample/retry independently, and the slow doesn't drag down the fast",
                    },
                    {"zh": "让评估结果更准确", "en": "makes eval results more accurate"},
                    {"zh": "减少数据库表的数量", "en": "reduces the number of DB tables"},
                    {"zh": "省掉 LLM 调用", "en": "avoids the LLM call"},
                ],
                "answer": 0,
                "why": {
                    "zh": "创建（匹配、去重、采样）轻快、失败重跑代价小；执行（调 LLM）慢、贵、会被限流、可能超时。混在一起则慢拖快、贵的没法单独采样、失败没法独立重试。两级队列让第一级高吞吐决定「该评谁」，第二级带延迟/采样/重试/分流地慢慢消化——正是第 14 课「队列解耦」在评估域的复刻。",
                    "en": "Creation (match, dedup, sample) is light and cheap to re-run; execution (LLM call) is slow, costly, rate-limited, may time out. Mixed, the slow drags the fast, the costly can't be sampled alone, failures can't retry independently. Two-stage queues let stage one decide 'whom' at high throughput and stage two digest slowly with delay/sampling/retry/offload — Lesson 14's queue decoupling in the eval domain.",
                },
            },
            {
                "q": {
                    "zh": "评估本身要调 LLM，而 Langfuse 会把每次 LLM 调用记成一条 trace。createEvalJobs 里有一段「如果 trace 环境以 langfuse 开头就直接 return」的代码。它防的是什么？",
                    "en": "Evaluation calls the LLM, and Langfuse records each LLM call as a trace. createEvalJobs has code that 'returns immediately if the trace environment starts with langfuse'. What does it prevent?",
                },
                "opts": [
                    {
                        "zh": "无限循环：用户 trace 触发评估 → 评估的 LLM 调用又成一条 trace → 又触发评估 → 无限套娃；给内部 trace 打 langfuse- 前缀并在入口挡掉即可斩断",
                        "en": "an infinite loop: a user trace triggers eval → the eval's LLM call becomes a trace → triggers eval again → nesting forever; tagging internal traces with a langfuse- prefix and blocking them at the entry breaks the cycle",
                    },
                    {"zh": "防止内部 trace 被用户看到", "en": "hides internal traces from users"},
                    {"zh": "加快内部 trace 的写入", "en": "speeds up writing internal traces"},
                    {"zh": "防止重复计费", "en": "prevents double billing"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是自指系统的经典陷阱：一个能观测一切的系统，会把自己的评估调用也观测成 trace，从而触发对自己的评估。Langfuse 让内部 trace 用 LangfuseInternalTraceEnvironment（langfuse- 前缀），并在 createEvalJobs 入口对 trace-upsert 来源的这类 trace 直接 return，斩断递归。fetchLLMCompletion 还强制内部 trace 必须带该前缀，形成双重保险。",
                    "en": "A classic self-reference trap: a system that observes everything observes its own eval call as a trace, triggering eval on itself. Langfuse marks internal traces with LangfuseInternalTraceEnvironment (langfuse- prefix) and returns early at createEvalJobs for such trace-upsert-sourced traces, cutting the recursion. fetchLLMCompletion also enforces that internal traces carry the prefix — a dual safeguard.",
                },
            },
            {
                "q": {
                    "zh": "一行 JobExecution 落在 Postgres 里，而不只是一条「阅后即焚」的队列消息。为什么评估系统需要这样一个有状态、可更新的工单？",
                    "en": "A JobExecution row lives in Postgres, not just a 'read-once' queue message. Why does the eval system need such a stateful, updatable ticket?",
                },
                "opts": [
                    {
                        "zh": "它要支持去重、取消、追溯：能回答「这条 trace 被哪些评估器评过、成功没、产出哪条分」，并通过 jobOutputScoreId/executionTraceId 双向链到产出的分与裁判自己的 trace",
                        "en": "it must support dedup, cancellation, and audit: answering 'which evaluators evaluated this trace, did it succeed, which score did it produce', and via jobOutputScoreId/executionTraceId bidirectionally linking to the produced score and the judge's own trace",
                    },
                    {"zh": "Postgres 比队列快", "en": "Postgres is faster than a queue"},
                    {"zh": "为了不用 Redis", "en": "to avoid using Redis"},
                    {"zh": "队列不能存 JSON", "en": "queues can't store JSON"},
                ],
                "answer": 0,
                "why": {
                    "zh": "队列消息消费即逝，无法回答「评过没、结果如何」。JobExecution 是落库的状态机（PENDING→COMPLETED/ERROR/CANCELLED/DELAYED），支持：去重（已有工单就不重复建）、取消（trace 被后续事件踢出目标集合则标 CANCELLED）、追溯（jobOutputScoreId 链到评出的分、executionTraceId 链到裁判的 trace），全链路可审计。",
                    "en": "A queue message is gone on consume, unable to answer 'evaluated yet, what outcome'. JobExecution is a persisted state machine (PENDING→COMPLETED/ERROR/CANCELLED/DELAYED) supporting: dedup (don't recreate an existing ticket), cancel (mark CANCELLED if a later event kicks the trace out of the target set), and audit (jobOutputScoreId links to the score, executionTraceId links to the judge's trace) — auditable end to end.",
                },
            },
        ],
        "open": [
            {
                "zh": "评估系统给了三道闸：去重、采样、延迟。假设你的生产流量每天一百万条 trace，每条评估要调一次 GPT-4 花约 ¥0.05。你会怎么配置这三道闸（采样率、延迟）来平衡「成本」与「质量信号的及时性/代表性」？延迟设太短、采样设太低分别会带来什么问题？",
                "en": "The eval system offers three gates: dedup, sampling, delay. Suppose your production handles a million traces/day, each eval calling GPT-4 at ~$0.007. How would you configure these gates (sample rate, delay) to balance 'cost' against 'timeliness/representativeness of the quality signal'? What problems arise from setting delay too short or sampling too low?",
            },
        ],
    },
    "31-code-based-evaluation.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 同时有 LLM-as-judge（第 29 课）和代码 eval（本课）两种评估。下面哪种说法最准确地刻画了它们的关系？",
                    "en": "Langfuse has both LLM-as-judge (Lesson 29) and code eval (this lesson). Which statement most accurately characterizes their relationship?",
                },
                "opts": [
                    {
                        "zh": "互补：代码 eval 确定、适合客观/规则信号（合法 JSON、含 PII、长度）；LLM-as-judge 概率、适合主观/语义信号（有用性、语气）。两者都接同一条调度流水线，只是「执行」步不同",
                        "en": "complementary: code eval is deterministic, for objective/rule signals (valid JSON, has PII, length); LLM-as-judge is probabilistic, for subjective/semantic signals (helpfulness, tone). Both attach to the same scheduling pipeline, differing only at the 'execution' step",
                    },
                    {"zh": "代码 eval 是 LLM-as-judge 的升级替代品", "en": "code eval is an upgraded replacement for LLM-as-judge"},
                    {"zh": "两者用完全独立的调度与存储", "en": "they use entirely separate scheduling and storage"},
                    {"zh": "代码 eval 只能产出布尔分", "en": "code eval can only produce boolean scores"},
                ],
                "answer": 0,
                "why": {
                    "zh": "两者是同一个 score 的两种生产方式，都挂在第 30 课调度流水线后，区别只在「执行」那一步：LLM-as-judge 调模型、代码 eval 跑函数。结果都归一成 source=EVAL 的 score 回流同一张表、走同一个 JobExecution 状态机。能用规则说清的交给代码 eval（确定、免费），要语义理解的交给 LLM-as-judge。",
                    "en": "Both are two ways of producing the same score, hanging off Lesson 30's pipeline, differing only at the 'execution' step: LLM-as-judge calls a model, code eval runs a function. Both normalize into source=EVAL scores flowing into the same table via the same JobExecution state machine. Rule-expressible goes to code eval (deterministic, free); semantic goes to LLM-as-judge.",
                },
            },
            {
                "q": {
                    "zh": "代码 eval 要执行用户写的代码。Langfuse 的本地派发器在源码里直接命名为 \"insecure-local\"。这个命名透露了什么？",
                    "en": "Code eval executes user-written code. Langfuse's local dispatcher is named \"insecure-local\" right in the source. What does this naming reveal?",
                },
                "opts": [
                    {
                        "zh": "诚实的警告：它用 node 的 vm 模块，而 vm 不是真正的安全沙箱（可被逃逸）；命名即文档，明示这条路只配本地开发，生产要用 Lambda 那种真隔离",
                        "en": "an honest warning: it uses node's vm module, and vm is not a real security sandbox (escapable); naming as documentation, signaling this path is for local dev only, with production needing real isolation like Lambda",
                    },
                    {"zh": "本地运行速度慢", "en": "local execution is slow"},
                    {"zh": "本地只支持 Python", "en": "local only supports Python"},
                    {"zh": "它会泄露环境变量", "en": "it leaks environment variables"},
                ],
                "answer": 0,
                "why": {
                    "zh": "node 的 vm 模块能创建隔离 context 跑代码，但业界共识是它不足以安全运行不可信代码（有已知逃逸手法）。Langfuse 不粉饰，把 insecure 写进 dispatcher 的 name，相当于在源码里贴警告条：本地开发可用，生产请切到 AwsLambdaCodeEvalDispatcher（ephemeral、强隔离、按语言调 python/node 函数）。",
                    "en": "Node's vm can create an isolated context to run code, but the consensus is it's insufficient for safely running untrusted code (known escapes exist). Langfuse doesn't gloss over it—writing insecure into the dispatcher's name is a source-level warning: fine for local dev, switch to AwsLambdaCodeEvalDispatcher (ephemeral, strong isolation, per-language python/node functions) in production.",
                },
            },
            {
                "q": {
                    "zh": "代码 eval 的沙箱有一条铁律：评估器代码不准发任何网络请求。为什么这条「禁网络」被认为一箭双雕？",
                    "en": "The code-eval sandbox has an iron rule: evaluator code may make no network requests. Why is this 'no network' considered to kill two birds?",
                },
                "opts": [
                    {
                        "zh": "既保安全（用户代码联网就能外泄你递进去的 trace 数据、或拿沙箱打内网 SSRF），又保确定性（网络天生不确定、会抖会超时甚至可能永不返回，破坏「同输入恒同分」）",
                        "en": "it preserves security (networked user code could exfiltrate the trace data you fed it, or use the sandbox for SSRF into your internal network) and determinism (network is inherently nondeterministic—flaky, timing out, even may-never-return, breaking 'same input, same score')",
                    },
                    {"zh": "只是为了省带宽", "en": "just to save bandwidth"},
                    {"zh": "让评估跑得更快", "en": "to make eval run faster"},
                    {"zh": "防止评估器调用 LLM", "en": "to stop the evaluator from calling an LLM"},
                ],
                "answer": 0,
                "why": {
                    "zh": "安全上：一旦能联网，用户代码可把含敏感信息的 trace 数据偷传出去，或以沙箱为跳板访问内网服务（SSRF）。确定性上：评估的灵魂是「同输入恒同分」，而网络请求会抖、超时、返回不同结果，源码原话甚至说「可能永不返回」。掐断网络同时焊死了安全口子和不确定性源头——一条约束，两重收益。",
                    "en": "Security: once networked, user code can smuggle out sensitive trace data or use the sandbox as a springboard to internal services (SSRF). Determinism: the soul of eval is 'same input, same score', yet network requests flake, time out, return different results—the source even says 'may never return'. Cutting the network welds shut both the security hole and the nondeterminism source — one constraint, two payoffs.",
                },
            },
        ],
        "open": [
            {
                "zh": "想象你要给一个客服机器人写 5 个评估器。哪些你会用代码 eval（确定/规则），哪些用 LLM-as-judge（概率/语义）？请各举几个，并说说为什么——以及如果某个信号「看起来客观但其实有灰区」（比如「回答是否礼貌」），你会怎么权衡？",
                "en": "Imagine writing 5 evaluators for a customer-service bot. Which would you do with code eval (deterministic/rule) and which with LLM-as-judge (probabilistic/semantic)? Give a few of each and say why—and if a signal 'looks objective but has a gray zone' (e.g. 'is the reply polite'), how would you weigh it?",
            },
        ],
    },
    "32-human-annotation.html": {
        "mcq": [
            {
                "q": {
                    "zh": "人工标注是第 28 课三种 score 来源里的 ANNOTATION。除了「人比机器更准」，它在评估体系里还扮演一个独特角色，是什么？",
                    "en": "Human annotation is the ANNOTATION of Lesson 28's three score sources. Beyond 'humans are more accurate than machines', it plays a unique role in the evaluation system. What is it?",
                },
                "opts": [
                    {
                        "zh": "充当 ground truth / 校准 AI 裁判：把人评的「金标准」和 AI 裁判分放在同一批 trace 上对照，量出裁判哪里偏了——这正是第 29 课「怎么信任 AI 裁判」的答案",
                        "en": "serving as ground truth / calibrating the AI judge: laying the human 'gold standard' against AI-judge scores on the same traces measures where the judge is biased — the answer to Lesson 29's 'how to trust the AI judge'",
                    },
                    {"zh": "让评估跑得更快", "en": "makes evaluation run faster"},
                    {"zh": "替代 LLM-as-judge", "en": "replaces LLM-as-judge"},
                    {"zh": "降低标注成本", "en": "lowers annotation cost"},
                ],
                "answer": 0,
                "why": {
                    "zh": "人工分又慢又贵，通常只评一小撮关键样本，但这一小撮是衡量 AI 裁判的金标准。因为三来源同表同 config（ScoreSourceArray=[API,EVAL,ANNOTATION]），人评分和 AI 裁判分可在同一批对象上直接对照；不一致处正是裁判要改 prompt/换模型的地方。这把「人工标注当裁判的标尺」，正是评估可信度的基石。",
                    "en": "Human scores are slow and costly, usually only on a small key sample—but that sample is the gold standard for the AI judge. Because the three sources share one table and config (ScoreSourceArray=[API,EVAL,ANNOTATION]), human and AI-judge scores compare directly on the same objects; disagreements are where the judge must fix its prompt/model. Using human annotation as the judge's yardstick is the bedrock of evaluation trust.",
                },
            },
            {
                "q": {
                    "zh": "多个评审员同时盯着一个标注队列。Langfuse 用一个「5 分钟时间软锁」防止两人评到同一份。相比数据库事务锁或永久占用标记，软锁的关键好处是？",
                    "en": "Several reviewers eye one annotation queue at once. Langfuse uses a '5-minute time-based soft lock' to stop two from annotating the same item. Versus a DB transaction lock or a permanent-hold marker, the soft lock's key benefit is?",
                },
                "opts": [
                    {
                        "zh": "匹配人的节奏且永不死锁：5 分钟够看完一份、避免撞车；又因自动过期，关浏览器/断网都只会让锁自愈，绝不会把 item 永久占死",
                        "en": "fits the human rhythm and never deadlocks: 5 minutes suffices to finish one item and avoid collisions; and because it auto-expires, closing the browser/losing network just lets the lock self-heal, never holding an item forever",
                    },
                    {"zh": "比事务锁查询更快", "en": "queries faster than a transaction lock"},
                    {"zh": "能锁住整个队列", "en": "can lock the whole queue"},
                    {"zh": "不需要数据库字段", "en": "needs no database fields"},
                ],
                "answer": 0,
                "why": {
                    "zh": "isItemLocked 只认 lockedAt 在最近 5 分钟内的锁。数据库事务锁是毫秒级、占连接，扛不住人看几分钟；永久标记一旦评审员关页面就把 item 占死。时间软锁两头讨好：5 分钟避免并发撞车，又因自动过期而自愈、永不死锁。这是「乐观并发 + 租约」用在人类工作流上——锁的粒度匹配被锁者的节奏。",
                    "en": "isItemLocked only counts a lock whose lockedAt is within the last 5 minutes. A DB transaction lock is millisecond-scale and ties up a connection, unfit for minutes of human reading; a permanent marker holds the item forever once a reviewer closes the tab. The time-based soft lock pleases both: 5 minutes avoids collisions, and auto-expiry self-heals, never deadlocking. It's 'optimistic concurrency + a lease' applied to a human workflow — lock granularity matching the locked party's rhythm.",
                },
            },
            {
                "q": {
                    "zh": "一个 AnnotationQueue 上绑了一组 scoreConfigIds。这个绑定起什么作用？",
                    "en": "An AnnotationQueue binds a set of scoreConfigIds. What does this binding do?",
                },
                "opts": [
                    {
                        "zh": "它是这个队列的「统一评分表」：规定所有评审员要按同一组 score config 评分（同名同刻度），分数才可比、才能聚合——直接复用第 28 课的 config",
                        "en": "it's the queue's 'uniform scoring sheet': all reviewers must score by the same set of score configs (same name, same scale) so scores are comparable and aggregatable — directly reusing Lesson 28's configs",
                    },
                    {"zh": "决定队列指派给哪些评审员", "en": "decides which reviewers the queue is assigned to"},
                    {"zh": "决定评哪些 trace", "en": "decides which traces to review"},
                    {"zh": "控制 5 分钟锁的时长", "en": "controls the 5-minute lock duration"},
                ],
                "answer": 0,
                "why": {
                    "zh": "scoreConfigIds 绑定第 28 课的 score config，规定这个队列里每位评审员要填哪几项分、每项什么刻度（NUMERIC/CATEGORICAL/BOOLEAN）。统一了尺，不同评审员、不同 item 的分才可比可聚合。指派给谁是另一个模型 AnnotationQueueAssignment 的事，评哪些对象是 AnnotationQueueItem 的事——三者各司其职。",
                    "en": "scoreConfigIds bind Lesson 28's score configs, dictating which scores each reviewer in this queue fills and on what scale (NUMERIC/CATEGORICAL/BOOLEAN). With a unified ruler, scores across reviewers and items are comparable and aggregatable. Who it's assigned to is the separate AnnotationQueueAssignment model; which objects to review is AnnotationQueueItem — each with its own job.",
                },
            },
        ],
        "open": [
            {
                "zh": "Part 5 走到这里，三种 score 来源（API/EVAL/ANNOTATION）全部汇入同一张 scores 表、同一套 config。回头看这条主线：为什么 Langfuse 不为「AI 评的分」和「人评的分」分别建表，而是执意让它们同表同尺？这种「统一数据模型」的设计，在可信度、可维护性、未来扩展上分别带来了什么？你能想到它的代价或局限吗？",
                "en": "By this point in Part 5, all three score sources (API/EVAL/ANNOTATION) flow into one scores table, one set of configs. Looking back at this through-line: why does Langfuse refuse to build separate tables for 'AI-judged' and 'human-judged' scores, insisting on one table and one ruler? What does this 'unified data model' buy in trust, maintainability, and future extension? Can you think of its costs or limits?",
            },
        ],
    },
    "33-monitors-and-alerting.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的 monitor（监控器）和 dashboard（仪表盘）有什么本质关系？",
                    "en": "What is the essential relationship between a Langfuse monitor and a dashboard?",
                },
                "opts": [
                    {
                        "zh": "monitor 复用仪表盘组件的查询形状（view/filters/metric，源码注释 mirrors DashboardWidget），区别在于它由调度器定时算、并拿去比阈值——pull（你看）变 push（它喊）",
                        "en": "a monitor reuses the dashboard widget's query shape (view/filters/metric, the source comment says mirrors DashboardWidget), differing in that a scheduler computes it on a cadence and compares against thresholds — pull (you look) becomes push (it calls you)",
                    },
                    {"zh": "monitor 是 dashboard 的只读快照", "en": "a monitor is a read-only snapshot of a dashboard"},
                    {"zh": "两者用完全不同的查询引擎", "en": "they use entirely different query engines"},
                    {"zh": "dashboard 是 monitor 的告警历史", "en": "a dashboard is a monitor's alert history"},
                ],
                "answer": 0,
                "why": {
                    "zh": "Monitor 的 view/filters/metric 直接 mirror DashboardWidget——能在仪表盘画出的曲线，都能一键变成会自己盯着的告警，底层 ClickHouse 查询机制只写一遍。区别只在 monitor 多了①调度（按 cadenceMs 定时）+③④阈值与状态机。pull 与 push 共享同一个指标定义，既省代码又顺直觉。",
                    "en": "Monitor's view/filters/metric directly mirror DashboardWidget—any curve you can draw on a dashboard becomes a self-watching alert in one click, with the ClickHouse query machinery written once. The difference is only that a monitor adds ① scheduling (per cadenceMs) + ③④ thresholds and a state machine. Pull and push share one metric definition: saves code and matches intuition.",
                },
            },
            {
                "q": {
                    "zh": "一个 monitor 持续处于 ALERT 状态。它每 5 分钟算一次，但并不会每 5 分钟都发一条告警。这种克制由什么实现，解决什么问题？",
                    "en": "A monitor stays in ALERT. It computes every 5 minutes but does not send an alert every 5 minutes. What implements this restraint, and what problem does it solve?",
                },
                "opts": [
                    {
                        "zh": "applyStateMachine：原则上只在严重度「变化」时 emit（OK→ALERT 发、ALERT→ALERT 不发），持续异常按 renotify 周期补发——根治告警疲劳",
                        "en": "applyStateMachine: as a rule emit only on a severity 'change' (OK→ALERT sends, ALERT→ALERT doesn't), topping up persistent anomalies per the renotify period — curing alert fatigue",
                    },
                    {"zh": "每次都发，靠 Slack 自己去重", "en": "it sends every time, relying on Slack to dedupe"},
                    {"zh": "随机丢弃一部分告警", "en": "it randomly drops some alerts"},
                    {"zh": "只在工作时间发", "en": "it only sends during work hours"},
                ],
                "answer": 0,
                "why": {
                    "zh": "告警疲劳是监控系统头号杀手：持续 ALERT 每 5 分钟一条，工程师会把频道静音，真问题也被淹没。applyStateMachine 对比 prev/next 严重度，severityChanged 才考虑 emit，并按 renotify 决定是否补发；PAUSED 直接跳过不覆盖用户意图。把 severity 做成状态机而非瞬时值，正是为了能问「和上次比变了吗」。",
                    "en": "Alert fatigue is a monitoring system's top killer: a persistent ALERT pinging every 5 minutes makes engineers mute the channel and bury real issues. applyStateMachine compares prev/next severity, considering emit only when severityChanged, and tops up per renotify; PAUSED is skipped to not overwrite user intent. Making severity a state machine rather than an instantaneous value is exactly to ask 'did it change from last time'.",
                },
            },
            {
                "q": {
                    "zh": "monitor 判定要告警后，并不直接调 Slack API，而是把告警发布到 WebhookQueue，再由自动化系统转投递。为什么这样设计？",
                    "en": "After deciding to alert, a monitor doesn't call the Slack API directly but publishes the alert to the WebhookQueue, with the automation system forwarding it. Why this design?",
                },
                "opts": [
                    {
                        "zh": "判断与投递分离（解耦）：monitor 只管「要不要告警」，不必认识每种投递渠道；投递方式可独立演进/重试/接新渠道，monitor 一行不改——呼应第30课创建/执行分离",
                        "en": "decision separate from delivery (decoupling): the monitor only decides 'whether to alert' and needn't know each delivery channel; delivery can evolve/retry/add channels independently with the monitor unchanged — echoing Lesson 30's create/execute split",
                    },
                    {"zh": "WebhookQueue 比直接调 Slack 快", "en": "the WebhookQueue is faster than calling Slack directly"},
                    {"zh": "为了把告警存档", "en": "to archive the alerts"},
                    {"zh": "Slack 不支持直接调用", "en": "Slack can't be called directly"},
                ],
                "answer": 0,
                "why": {
                    "zh": "monitor 的职责是判断是否越线告警，不该耦合「告警怎么送到人手里」（Slack/webhook/邮件/值班）。发布到统一 WebhookQueue，由自动化（第44课 Trigger→Action）决定渠道，于是投递可独立演进、可重试、可接任意新渠道，monitor 不变。这与第30课创建/执行分离、第12课一个入口多生产者，是同一种「解耦」品味。",
                    "en": "A monitor's job is deciding whether a line is crossed, not coupling to 'how the alert reaches a human' (Slack/webhook/email/on-call). Publishing to one WebhookQueue, with automation (Lesson 44's Trigger→Action) choosing the channel, lets delivery evolve/retry/add channels independently while the monitor stays put. Same decoupling taste as Lesson 30's create/execute split and Lesson 12's one-entry-many-producers.",
                },
            },
        ],
        "open": [
            {
                "zh": "Part 5 到此完整：score 模型（28）→ 四种生产 score 的方式（29–32）→ 主动监控告警（33）。回顾整个第五部分，Langfuse 让「评估」从一个静态的「能评分、能查」系统，变成一个动态的「能自动评、能主动告警、还能用人工分校准 AI」的闭环。如果让你为自己的 LLM 应用设计一套评估体系，你会怎么组合这五种能力（人工/LLM裁判/代码/监控）？哪些质量信号你会持续监控并告警，为什么？",
                "en": "Part 5 is now complete: the score model (28) → four ways to produce scores (29–32) → active monitoring and alerting (33). Reviewing the whole part, Langfuse turns 'evaluation' from a static 'can score, can query' system into a dynamic closed loop that 'auto-evaluates, alerts actively, and calibrates AI with human scores'. If you designed an evaluation system for your own LLM app, how would you combine these five capabilities (human/LLM-judge/code/monitoring)? Which quality signals would you continuously monitor and alert on, and why?",
            },
        ],
    },
    "34-datasets-and-items.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的数据项（DatasetItem）有 sourceTraceId / sourceObservationId 字段。它们让数据集获得了什么独特能力？",
                    "en": "Langfuse's DatasetItem has sourceTraceId / sourceObservationId fields. What unique capability do they give datasets?",
                },
                "opts": [
                    {
                        "zh": "把真实生产 trace「提拔」成测试用例：在线上发现应用答砸的难题，一键收录成回归题，让测试集紧贴真实流量分布而非凭空臆造",
                        "en": "promoting a real production trace into a test case: spot a botched hard case in production, capture it as a regression question in one click, keeping the test set close to the real traffic distribution rather than imagined",
                    },
                    {"zh": "让数据项自动评分", "en": "auto-scoring dataset items"},
                    {"zh": "把数据项存进 ClickHouse", "en": "storing items in ClickHouse"},
                    {"zh": "给数据项加密", "en": "encrypting items"},
                ],
                "answer": 0,
                "why": {
                    "zh": "sourceTraceId/sourceObservationId 记下「这道题从哪条真实 trace 来」。凭空想象的测试用例覆盖不到真实长尾输入，而线上每次答砸的 trace 都是现成好题。于是「发现问题→收录成回归题→改进后验证」闭环——观测平台顺手把生产问题变成防复发的疫苗。",
                    "en": "sourceTraceId/sourceObservationId record which real trace a question came from. Imagined test cases miss real long-tail inputs, while every botched production trace is a ready-made question. This closes the loop 'find a problem → capture as regression question → verify after improving'—the platform turns production problems into vaccines against recurrence.",
                },
            },
            {
                "q": {
                    "zh": "DatasetItem 的主键是 (id, projectId, validFrom)，每行还有一个 validTo。当你修订一道题时，系统怎么做？",
                    "en": "A DatasetItem's primary key is (id, projectId, validFrom), and each row has a validTo. When you revise a question, what does the system do?",
                },
                "opts": [
                    {
                        "zh": "在一个事务里：给旧版盖上 validTo（关闭其有效区间），再插入一行新版（新 validFrom、validTo 为空成为当前版）——缓慢变化维 / 双时态，不抹改历史",
                        "en": "in a transaction: stamp the old version with validTo (close its validity interval), then insert a new version row (new validFrom, validTo null becoming current)—slowly-changing dimension / bitemporal, not erasing history",
                    },
                    {"zh": "原地更新那一行", "en": "updates that row in place"},
                    {"zh": "删除旧行再建新行", "en": "deletes the old row then creates a new one"},
                    {"zh": "只改 updatedAt 时间戳", "en": "only changes the updatedAt timestamp"},
                ],
                "answer": 0,
                "why": {
                    "zh": "dataset-items.ts 的 VERSIONED 写入：事务里先找当前版（validTo IS NULL），给它盖 validTo=newValidFrom 关闭区间，再 create 一行新版 validFrom=newValidFrom（validTo 默认 null）。于是同一道题多版本共存、当前版 = validTo 为空那行。这是经典的不可变历史 + 可移动当前指针。",
                    "en": "dataset-items.ts VERSIONED write: in a transaction, find the current version (validTo IS NULL), stamp it with validTo=newValidFrom to close its interval, then create a new row with validFrom=newValidFrom (validTo defaults null). So many versions of one question coexist, the current being the validTo-null row. Classic immutable history + a movable current pointer.",
                },
            },
            {
                "q": {
                    "zh": "为什么数据项要这样版本化，而不是简单地原地更新？",
                    "en": "Why version dataset items this way rather than simply updating in place?",
                },
                "opts": [
                    {
                        "zh": "为了实验可复现：一次 run 钉住某个 validFrom，永远看到「当时那版题」；否则历史实验的分数会失去语境，两次实验无法公平对比（第30课 eval 正是用 datasetItemValidFrom 精确回放）",
                        "en": "for reproducibility: a run pins a validFrom and always sees 'that version of the question'; otherwise historical scores lose their context and two experiments can't be fairly compared (Lesson 30's eval replays exactly via datasetItemValidFrom)",
                    },
                    {"zh": "为了节省存储", "en": "to save storage"},
                    {"zh": "为了加快查询", "en": "to speed up queries"},
                    {"zh": "为了支持并发写", "en": "to support concurrent writes"},
                ],
                "answer": 0,
                "why": {
                    "zh": "评估的价值在比较。若题被原地改，「上次」的分就失去语境——不知道当时考的是什么，没法和「这次」公平比。版本化给每道题每版钉上时间区间，让每次 run 钉死它用的那版（第30课 eval 带 datasetItemValidFrom 精确回放）。这和第37课 prompt 版本、git commit 同一种「真相记录后不抹改」的信念。",
                    "en": "Evaluation's value is comparison. If a question is edited in place, 'last time'\\'s score loses context—you don't know what it tested, can't fairly compare with 'this time'. Versioning pins a time interval on every version, letting each run pin the version it used (Lesson 30's eval replays via datasetItemValidFrom). Same 'record truth without erasing' belief as Lesson 37's prompt versions and git commits.",
                },
            },
        ],
        "open": [
            {
                "zh": "数据集把「生产 trace」和「测试用例」用 sourceTraceId 连了起来，又用版本化保证实验可复现。设想你在维护一个客服机器人：你会怎么用这两个机制构建一套「持续改进」的回归测试流程？哪些线上 case 值得提拔成数据集？什么时候该给一道题升新版而不是新建一道题？",
                "en": "Datasets link 'production traces' and 'test cases' via sourceTraceId, and use versioning to keep experiments reproducible. Imagine maintaining a customer-service bot: how would you use these two mechanisms to build a 'continuous improvement' regression-test flow? Which production cases are worth promoting into a dataset? When should you version-up a question rather than create a new one?",
            },
        ],
    },
    "35-dataset-runs.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 用 DatasetRunItem 把 datasetRunId + datasetItemId 连到一个 traceId。为什么要专门建这个连接表，而不是直接给 trace 打个「属于哪场实验」的标签？",
                    "en": "Langfuse's DatasetRunItem links datasetRunId + datasetItemId to a traceId. Why a dedicated junction table rather than just tagging a trace with 'which experiment it belongs to'?",
                },
                "opts": [
                    {
                        "zh": "因为这是多对多关系且要支撑高效聚合：run/item/trace 各自独立演化，专门的连接表让三者解耦，又给了干净的聚合入口（扫这表 JOIN score 即可算「这场平均分」，不用在 trace 海里捞带标签的针）",
                        "en": "because it's a many-to-many relation needing efficient aggregation: run/item/trace evolve independently, a dedicated junction table decouples them and gives a clean aggregation entry (scan it and JOIN scores to compute 'this run's average', not fish tagged needles in a trace ocean)",
                    },
                    {"zh": "因为 trace 不能加字段", "en": "because traces can't take extra fields"},
                    {"zh": "为了把实验数据和生产数据隔离", "en": "to isolate experiment data from production data"},
                    {"zh": "为了加密实验结果", "en": "to encrypt experiment results"},
                ],
                "answer": 0,
                "why": {
                    "zh": "一条 trace 概念上属于「某场 run 的某道题」，但 run、item、trace 都是独立演化的实体（题会改版、run 会重跑、trace 有完整生命周期）。用连接表承载三元关系，既让三者解耦，又给了聚合入口：算「这场考了哪些题、平均分多少」只需扫这表 JOIN score。关系独立建模是高效查询/聚合的前提。",
                    "en": "A trace conceptually belongs to 'some question of some run', but run, item, and trace evolve independently (questions versioned, runs re-run, traces have full lifecycles). A junction table carrying the three-way relation decouples them and gives an aggregation entry: computing 'which questions this exam covered, what the average' just scans it and JOINs scores. Modeling the relation independently is the precondition for efficient query/aggregation.",
                },
            },
            {
                "q": {
                    "zh": "ClickHouse 的 dataset_run_items_rmt 镜像表里，除了 id/run/item/trace 的关系，还反范式地内联了 run 名、并把数据项的 input/expectedOutput「快照」了进去。快照题面解决了什么独特问题？",
                    "en": "In ClickHouse's dataset_run_items_rmt mirror table, besides the id/run/item/trace relations it denormalizes the run name and 'snapshots' the item's input/expectedOutput. What unique problem does snapshotting the question text solve?",
                },
                "opts": [
                    {
                        "zh": "记忆：题目会改版(第34课)，但快照让一场三月的实验永远记得当时考的是哪版题面——即便原题后来面目全非，实验语境分毫不失，给「可复现」再上一道保险",
                        "en": "memory: questions get versioned (L34), but the snapshot lets a March experiment forever remember the question text it tested then—even if the original later changes beyond recognition, the experiment's context is preserved, doubly insuring reproducibility",
                    },
                    {"zh": "压缩存储空间", "en": "compressing storage"},
                    {"zh": "加密题面", "en": "encrypting the question"},
                    {"zh": "防止题目被删除", "en": "preventing question deletion"},
                ],
                "answer": 0,
                "why": {
                    "zh": "反范式有两重收益。聚合速度：内联 run 名/题面，省回表 JOIN（OLAP 老主题）。更微妙的是记忆：题会改版，但三月的实验理应永远记得三月那版题面。把 input/expectedOutput 在 run 时快照进 run item，即便原题后来变了，这场实验的语境也不失——第34课「可复现」的再加保险。快照不是冗余，是固化「当时的真相」。",
                    "en": "Denormalization has two payoffs. Aggregation speed: inlining run name/question saves back-to-table JOINs (the OLAP theme). Subtler is memory: questions get versioned, but a March experiment should forever remember March's question text. Snapshotting input/expectedOutput into the run item at run time preserves the experiment's context even if the original later changes—doubly insuring L34's reproducibility. The snapshot isn't redundancy but freezing 'the truth as of then'.",
                },
            },
            {
                "q": {
                    "zh": "在 Langfuse 里「跑一场 dataset run，分数会自动评出来」。这个自动评分是怎么被触发的？",
                    "en": "In Langfuse, 'running a dataset run computes scores automatically'. How is this auto-scoring triggered?",
                },
                "opts": [
                    {
                        "zh": "创建 run item 会发出 dataset-run-item-upsert 事件，触发第30课的 createEvalJobs 给这条 run 的 trace 排评估工单；评分回流后 dataset-run-items.ts JOIN scores 按名求平均(agg_scores_avg)",
                        "en": "creating a run item emits a dataset-run-item-upsert event, triggering Lesson 30's createEvalJobs to queue eval for this run's trace; once scores flow back, dataset-run-items.ts JOINs scores and averages by name (agg_scores_avg)",
                    },
                    {"zh": "前端每秒轮询评分", "en": "the frontend polls and scores every second"},
                    {"zh": "run 结束时手动点击评分", "en": "manually clicking score when the run finishes"},
                    {"zh": "ClickHouse 自动计算", "en": "ClickHouse computes it automatically"},
                ],
                "answer": 0,
                "why": {
                    "zh": "回想第30课：createEvalJobs 有三个触发源，其一就是 dataset-run-item-upsert。建 run item 发此事件 → 评估器按 filter 匹配这条 run 的 trace → 排 JobExecution → 裁判/代码/人工评出 score 经摄取链路挂回 trace。最后 dataset-run-items.ts JOIN scores 按 score 名求平均得 agg_scores_avg（这场总评），交第36课对比。整条链全自动。",
                    "en": "Recall Lesson 30: createEvalJobs has three trigger sources, one being dataset-run-item-upsert. Creating a run item emits this event → evaluators filter-match this run's trace → queue a JobExecution → judge/code/human produce scores attached back via ingestion. Finally dataset-run-items.ts JOINs scores and averages by name into agg_scores_avg (the run's grade), handed to Lesson 36. The whole chain is automatic.",
                },
            },
        ],
        "open": [
            {
                "zh": "一次 dataset run 产生的 trace 和生产 trace「毫无二致」——同样的观测树、同样能挂 score、同样走摄取链路。这种「实验复用生产基础设施」的设计有什么好处？设想如果实验数据走一套完全独立的存储与查询栈，会带来哪些重复建设和不一致风险？",
                "en": "The traces a dataset run produces are 'indistinguishable' from production traces—same observation tree, same scores, same ingestion path. What are the benefits of this 'experiments reuse production infrastructure' design? Imagine if experiment data went through a completely separate storage and query stack—what duplication and inconsistency risks would that bring?",
            },
        ],
    },
    "36-experiments-and-comparison.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的服务端实验（createExperimentJobClickhouse）对数据集的每道题做什么？",
                    "en": "What does Langfuse's server-side experiment (createExperimentJobClickhouse) do for each dataset question?",
                },
                "opts": [
                    {
                        "zh": "replaceVariablesInPrompt 把这道题的 input 填进 prompt 的变量空格，用选定 provider/model 调一次 LLM，写成一条 trace（标 PromptExperiments 环境、链接被考 prompt、钉住 item 版本）+ run item",
                        "en": "replaceVariablesInPrompt fills this question's input into the prompt's variable blanks, calls the LLM once with the chosen provider/model, writing a trace (tagged PromptExperiments env, linking the prompt under test, pinning the item version) + run item",
                    },
                    {"zh": "只把数据项复制到一张新表", "en": "just copies the item to a new table"},
                    {"zh": "在前端用 JavaScript 跑模型", "en": "runs the model in the frontend via JavaScript"},
                    {"zh": "直接给数据项评分，不调 LLM", "en": "scores the item directly without calling an LLM"},
                ],
                "answer": 0,
                "why": {
                    "zh": "processLLMCall 三步：① replaceVariablesInPrompt 用 item.input 填 prompt 变量得完整 messages；② 组 trace，环境标 PromptExperiments、链接 config.prompt、metadata 钉 itemVersion=validFrom（第34/35课版本回放）；③ 用 config.provider/model 调 LLM。这是「服务端零代码跑实验」——产品经理也能在 UI 点跑，平台统一变量替换/版本钉定/评分调度。",
                    "en": "processLLMCall's three steps: ① replaceVariablesInPrompt fills the prompt's variables with item.input into full messages; ② build the trace, tagging env PromptExperiments, linking config.prompt, metadata pinning itemVersion=validFrom (L34/35 version replay); ③ call the LLM with config.provider/model. This is 'zero-code server-side experiments'—a PM can click run in the UI, with the platform unifying variable substitution/version pinning/eval scheduling.",
                },
            },
            {
                "q": {
                    "zh": "实验对比页用「baseline + 增量」展示结果，而不是直接列绝对分。为什么这种设计更利于决策？",
                    "en": "The experiment comparison page shows results via 'baseline + deltas' rather than listing absolute scores. Why does this aid decisions?",
                },
                "opts": [
                    {
                        "zh": "绝对分几乎没意义（「有用性 0.78」是好是坏说不清），相对变化才有（「比现役高 0.07」可据以决策）；且质量常是多维权衡，并排增量让「准度提升值不值延迟代价」这种取舍一目了然",
                        "en": "absolute scores mean almost nothing ('helpfulness 0.78' good or bad?), relative change does ('0.07 above active' is actionable); and quality is often a multi-dimensional trade-off, with side-by-side deltas making 'is the accuracy gain worth the latency cost' obvious",
                    },
                    {"zh": "增量计算更省 CPU", "en": "deltas use less CPU"},
                    {"zh": "绝对分会泄露隐私", "en": "absolute scores leak privacy"},
                    {"zh": "baseline 能加密结果", "en": "a baseline encrypts results"},
                ],
                "answer": 0,
                "why": {
                    "zh": "「有用性 0.78」没有参照根本判不了好坏，但「比现役配置高 0.07」是能决策的事实。更重要的是质量常是多维权衡（B 更准但更慢更贵），把每维增量并排，决策者才能清醒取舍而非被单一指标牵着走。这呼应第33课监控「只在变化时告警」——有信息量的永远是变化，不是绝对值。ExperimentBaselineControls/ComparisonSelector/ChartsGrid 实现这套对比。",
                    "en": "'Helpfulness 0.78' can't be judged without a reference, but '0.07 above the active config' is an actionable fact. More importantly quality is often a multi-dimensional trade-off (B more accurate but slower/costlier); laying each dimension's delta side by side lets decision-makers trade off clearly rather than be led by one metric. This echoes Lesson 33's 'alert only on change'—information lives in change, not absolutes. ExperimentBaselineControls/ComparisonSelector/ChartsGrid implement this.",
                },
            },
            {
                "q": {
                    "zh": "把 Part 6 三课串起来，Langfuse 提供的「数据集→实验→评分→对比→决策」回路，本质上把第 5 部分的能力升级成了什么？",
                    "en": "Stringing Part 6's three lessons together, the 'dataset→experiment→score→compare→decide' loop essentially upgrades Part 5's capability into what?",
                },
                "opts": [
                    {
                        "zh": "从「能给质量评分」升级成「能用分数做决策」：改 prompt/换模型前先在固定测试集上验证，用数据而非感觉判断改动好坏——LLM 工程里最接近科学方法的一环",
                        "en": "from 'can score quality' into 'can make decisions with scores': verify on a fixed test set before changing a prompt/model, judging by data not feeling—the closest thing to the scientific method in LLM engineering",
                    },
                    {"zh": "升级成自动写 prompt", "en": "into auto-writing prompts"},
                    {"zh": "升级成实时监控", "en": "into real-time monitoring"},
                    {"zh": "升级成更快的数据库", "en": "into a faster database"},
                ],
                "answer": 0,
                "why": {
                    "zh": "第5部分让你「能看见、能评分」；Part 6 让你「能据此决策」。数据集是固定考卷、实验是一次对照试验、对比是带增量的成绩单——于是「这个改动到底好不好」从拍脑袋变成有数据。回路还自我强化：上线遇新难 case 再提拔成题，飞轮越转应用越稳。被反复考的 prompt 正是下一部分主角。",
                    "en": "Part 5 lets you 'see and score'; Part 6 lets you 'decide on that basis'. The dataset is a fixed exam, an experiment is a controlled trial, comparison is a report card with deltas—so 'is this change good' goes from gut feeling to data. The loop self-reinforces: post-ship hard cases get promoted into questions, the flywheel steadies the app. The repeatedly-tested prompt is the next part's protagonist.",
                },
            },
        ],
        "open": [
            {
                "zh": "实验把「改 prompt 前先验证」变成了科学方法。但它依赖一个前提：你的数据集能代表真实流量、你的评分能反映真实质量。设想这两个前提其中之一不成立（比如数据集偏窄、或 LLM 裁判有系统性偏差），实验对比的结论会怎样误导你？你会怎么防范这种「评估体系本身不可靠」的风险？（提示：回顾第32课人工标注当 ground truth。）",
                "en": "Experiments turn 'verify before changing a prompt' into a scientific method. But it rests on premises: your dataset represents real traffic, and your scoring reflects real quality. Imagine one premise fails (e.g. a narrow dataset, or an LLM judge with systematic bias)—how would the comparison's conclusions mislead you? How would you guard against this 'the evaluation system itself is unreliable' risk? (Hint: revisit Lesson 32's human annotation as ground truth.)",
            },
        ],
    },
    "37-prompt-management.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 把 prompt 的 version 设计成不可变（自增、内容不再改），而 label（如 production）设计成可移动指针。这种「不可变实体 + 可移动指针」组合的核心好处是？",
                    "en": "Langfuse designs a prompt's version as immutable (auto-incrementing, content never changed) and a label (like production) as a movable pointer. The core benefit of this 'immutable entity + movable pointer' combo is?",
                },
                "opts": [
                    {
                        "zh": "同时获得「可复现」与「可演进」：不可变版本让任意历史版精确复盘，可移动 label 让 production 这个稳定名字平滑切换/回滚——把矛盾干净分配到两个概念上",
                        "en": "getting both 'reproducibility' and 'evolvability': immutable versions let any historical version be replayed exactly, movable labels let a stable name like production switch/roll back smoothly—cleanly assigning the tension to two concepts",
                    },
                    {"zh": "节省数据库空间", "en": "saving database space"},
                    {"zh": "让 prompt 自动优化", "en": "auto-optimizing prompts"},
                    {"zh": "加密 prompt 内容", "en": "encrypting prompt content"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是版本控制的精髓，git、第34课数据项、prompt 皆然。不可变保证可复现：v5 永远是 v5，三个月前生产那版今天一字不差可复盘。可移动 label 提供可演进：现实需要 production 这个稳定名字指代「当前现役」，而现役会变。两者结合既能大胆迭代（每版安全留存）又能安心运营（label 平滑切换/秒回滚）。",
                    "en": "This is the essence of version control—git, Lesson 34's items, prompts alike. Immutability guarantees reproducibility: v5 is forever v5, the version in production three months ago is replayable word-for-word today. Movable labels provide evolvability: reality needs a stable name like production for 'the current active', which changes. Together you iterate boldly (each version preserved) and operate calmly (smooth switch/instant rollback via labels).",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 推荐生产代码用 get(label=\"production\") 而不是 get(version=5) 来取 prompt。这么做最大的运营价值是？",
                    "en": "Langfuse recommends production code fetch a prompt via get(label=\"production\") rather than get(version=5). The biggest operational value of this is?",
                },
                "opts": [
                    {
                        "zh": "把「用哪一版」从代码里搬走：换版本变成运营在 UI 移指针——秒级生效、可回滚、非工程师也能做，无需改代码/过CI/重新部署（配置与代码分离）",
                        "en": "lifting 'which version' out of code: switching versions becomes operations moving a pointer in the UI—second-scale, rollback-able, doable by non-engineers, no code change/CI/redeploy (config-code separation)",
                    },
                    {"zh": "按 label 取更快", "en": "fetching by label is faster"},
                    {"zh": "按 label 取更省 token", "en": "fetching by label saves tokens"},
                    {"zh": "version 取不到旧版", "en": "fetching by version can't get old versions"},
                ],
                "answer": 0,
                "why": {
                    "zh": "若应用写死 version=5，换 prompt 就得改代码、过 CI、重新部署——慢重且要工程师在场。写 label=\"production\"，换版本就是运营在 UI 点一下移指针：秒级、可回滚、非工程师可做。这把变化频繁的东西(prompt 内容)从变化缓慢的东西(应用代码)里剥离，各自用最适合的节奏演进。protected labels 再给关键 label 加权限门。",
                    "en": "If the app hardcodes version=5, switching means changing code, passing CI, redeploying—slow, heavy, needs an engineer. With label=\"production\", switching is operations clicking a pointer-move in the UI: second-scale, rollback-able, non-engineer-doable. This lifts the frequently-changing thing (prompt content) out of the slowly-changing thing (app code), each evolving at its own pace. Protected labels then gate key labels.",
                },
            },
            {
                "q": {
                    "zh": "PromptDependency 让一个父 prompt 引用子 prompt，可以按 childLabel（如 production）浮动，也可以按 childVersion（如 3）钉死。这两种引用方式分别适合什么？",
                    "en": "PromptDependency lets a parent prompt reference a child, either floating by childLabel (e.g. production) or pinned by childVersion (e.g. 3). What does each reference style suit?",
                },
                "opts": [
                    {
                        "zh": "浮动(label)：子 prompt 升级时父自动获得更新，适合「公共片段一改处处生效」；钉死(version)：父永远用那一版、不受子升级影响，适合需要稳定的场景——和按 label/version 取 prompt 同一种取舍",
                        "en": "floating (label): the parent auto-gets updates when the child upgrades, suiting 'edit the shared snippet once, effective everywhere'; pinned (version): the parent always uses that version, unaffected by child upgrades, suiting stability—the same trade-off as fetching prompts by label/version",
                    },
                    {"zh": "浮动更安全，钉死有风险", "en": "floating is safer, pinning is risky"},
                    {"zh": "两者完全等价", "en": "the two are equivalent"},
                    {"zh": "钉死会自动升级", "en": "pinning auto-upgrades"},
                ],
                "answer": 0,
                "why": {
                    "zh": "PromptDependency 用 childLabel 或 childVersion 二选一描述引用。浮动(childLabel)：跟着 label 走，子升级父自动获得新内容——适合公共开场白这种「改一次处处更新」。钉死(childVersion)：锁定具体版本，父不受子升级影响——适合要绝对稳定/可复现。这和第一节「按 label 取 vs 按 version 取」是同一种「浮动求便利、钉定求稳定」的取舍，一脉相承。",
                    "en": "PromptDependency describes a reference by either childLabel or childVersion. Floating (childLabel): follows the label, the parent auto-gets new content on child upgrade—suiting a shared preamble's 'edit once, update everywhere'. Pinned (childVersion): locks a specific version, the parent unaffected by upgrades—suiting absolute stability/reproducibility. This mirrors the first section's 'fetch by label vs version': float for convenience, pin for stability.",
                },
            },
        ],
        "open": [
            {
                "zh": "prompt 管理把「软件版本控制」的思想（不可变版本、可移动 label、依赖、commit message）整套搬到了 prompt 上。回想你用 git 的经验：哪些 git 工作流（如分支策略、code review、回滚演练）你觉得也值得搬到 prompt 管理上？反过来，prompt 和代码有什么本质不同，使得某些 git 实践未必适用？",
                "en": "Prompt management ports the whole idea of 'software version control' (immutable versions, movable labels, dependencies, commit messages) onto prompts. Recall your git experience: which git workflows (branch strategy, code review, rollback drills) do you think are worth porting to prompt management? Conversely, how do prompts differ fundamentally from code, making some git practices not necessarily applicable?",
            },
        ],
    },
    "38-prompt-serving-caching.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的 PromptService 用 Redis 做 read-through 缓存。「read-through」具体指什么流程？",
                    "en": "Langfuse's PromptService uses Redis as a read-through cache. What flow does 'read-through' specifically mean?",
                },
                "opts": [
                    {
                        "zh": "getPrompt 先查 Redis，命中即返回（不碰库）；未命中才查 Postgres，并把结果回填进 Redis（SET EX ttl），于是下次同请求走缓存——绝大多数请求毫秒级、不压数据库",
                        "en": "getPrompt checks Redis first, returns on a hit (no DB); only on a miss queries Postgres and backfills the result into Redis (SET EX ttl), so the next identical request hits the cache—the vast majority are millisecond and don't load the DB",
                    },
                    {"zh": "每次都查 Postgres，再顺便更新 Redis", "en": "queries Postgres every time, then updates Redis on the side"},
                    {"zh": "只读 Redis，从不回库", "en": "reads only Redis, never the DB"},
                    {"zh": "先写 Redis 再异步落库", "en": "writes Redis first, then async to the DB"},
                ],
                "answer": 0,
                "why": {
                    "zh": "read-through：缓存命中走捷径，未命中才穿透到权威库并回填。getPrompt 先 getCachedPrompt，命中返回；未命中 findPrompt(DB)→cachePrompt(redis.set EX ttlSeconds)。生产可能每次 LLM 调用都取 prompt，这层缓存把数据库压力挡在前面，只有缓存冷/失效后第一笔才回库。开关 LANGFUSE_CACHE_PROMPT_ENABLED、时长 _TTL_SECONDS。",
                    "en": "Read-through: a hit takes the shortcut, only a miss penetrates to the authoritative DB and backfills. getPrompt first getCachedPrompt, returns on hit; on miss findPrompt(DB)→cachePrompt(redis.set EX ttlSeconds). Production may fetch a prompt every LLM call; this cache shields the DB, with only the first request after a cold/invalidated cache hitting the DB. Toggle LANGFUSE_CACHE_PROMPT_ENABLED, duration _TTL_SECONDS.",
                },
            },
            {
                "q": {
                    "zh": "prompt 改动后要让缓存失效。Langfuse 不去逐个删旧 key，而是在缓存 key 里嵌一个项目级 epoch 令牌、失效时只把它转成新随机值。为什么这样做？",
                    "en": "After a prompt change the cache must be invalidated. Langfuse doesn't delete old keys one by one but embeds a project-scoped epoch token in the cache key, rotating it to a new random value on invalidation. Why?",
                },
                "opts": [
                    {
                        "zh": "因为 resolved prompt 可能内联多个别的 prompt（依赖），精确反查「哪些 key 受牵连」几乎不可行、漏一个就读到陈旧；转 epoch 等于直接换一片干净命名空间，旧 key 失联按 TTL 过期——O(1)、绝不漏",
                        "en": "because a resolved prompt may inline several other prompts (dependencies), precisely reverse-looking-up 'which keys are affected' is nearly infeasible and one miss serves stale data; rotating the epoch swaps to a fresh namespace, old keys orphaned and expiring by TTL—O(1), never misses",
                    },
                    {"zh": "因为 Redis 不支持 DEL", "en": "because Redis doesn't support DEL"},
                    {"zh": "为了节省 Redis 内存", "en": "to save Redis memory"},
                    {"zh": "为了让缓存永不过期", "en": "to make the cache never expire"},
                ],
                "answer": 0,
                "why": {
                    "zh": "服务的 prompt 是解析后的成品，可能内联多个 child（第37课）。改一个 child，所有间接依赖它的 resolved 成品都该失效，但你很难反查受影响的 key、它们还散落在不同名字下，逐个删既慢又漏。invalidateCache 只对项目级 epoch 键 SET 新令牌，缓存 key 含该 epoch，于是旧 key 全部失联、按 TTL 自然过期。用一点内存浪费换失效的简单与正确。",
                    "en": "A served prompt is a resolved product that may inline several children (L37). Changing one child should invalidate all resolved products indirectly depending on it, but you can barely reverse-lookup the affected keys, scattered across names—deleting one by one is slow and miss-prone. invalidateCache just SETs a new token on the project-scoped epoch key; cache keys embed that epoch, so old keys are all orphaned and expire by TTL. Trade a little wasted memory for simple, correct invalidation.",
                },
            },
            {
                "q": {
                    "zh": "为什么 Langfuse 的缓存 epoch 是「项目级」（prompt_cache_epoch:{projectId}），而不是按单个 prompt 名字隔离？",
                    "en": "Why is Langfuse's cache epoch 'project-scoped' (prompt_cache_epoch:{projectId}) rather than isolated per prompt name?",
                },
                "opts": [
                    {
                        "zh": "因为 resolved prompt 跨多个名字（依赖），若按 prompt 名隔离 epoch，改 child 时又得追踪「哪些 parent 依赖它」；项目级 epoch 用「偶尔多失效一点」换「彻底不必追踪依赖 + 永不读到陈旧」",
                        "en": "because a resolved prompt spans multiple names (dependencies); if the epoch were per prompt name, changing a child would again require tracking 'which parents depend on it'; a project-scoped epoch trades 'occasionally over-invalidating' for 'no dependency tracking at all + never stale'",
                    },
                    {"zh": "项目级 key 更短更省内存", "en": "project-scoped keys are shorter, saving memory"},
                    {"zh": "为了跨项目共享缓存", "en": "to share cache across projects"},
                    {"zh": "prompt 级 epoch 不被 Redis 支持", "en": "prompt-scoped epochs aren't supported by Redis"},
                ],
                "answer": 0,
                "why": {
                    "zh": "源码注释明说：epoch 项目级是因为 resolved prompt 可含跨多个 prompt 名字的传递依赖。若按 prompt 名隔离，改 child 又要回到「哪些 parent 受影响」的依赖追踪难题。项目级粒度意味着「项目内任一 prompt 变动，整片 prompt 缓存翻篇」——粗一点、偶尔多失效，但换来彻底不必追踪依赖的确定性。对 prompt 这种正确性远比命中率重要的数据，这个取舍正确。",
                    "en": "The source comment states: the epoch is project-scoped because a resolved prompt can include transitive dependencies across multiple prompt names. Per-name isolation would revive the 'which parents are affected' dependency-tracking problem on a child change. Project granularity means 'any prompt change in the project turns the whole prompt cache's page'—coarser, occasionally over-invalidating, but buying certainty of no dependency tracking. Right for prompts, where correctness beats hit rate.",
                },
            },
        ],
        "open": [
            {
                "zh": "epoch 失效这一招——「改命名空间而非删 key」——本质上是「用空间换正确性与简单性」。回想你做过或设想的缓存系统，哪些场景的失效逻辑曾让你头疼（关联失效、依赖追踪、惊群）？这种 epoch/版本号命名空间的思路能不能套上去？它的代价（内存、TTL 选择、冷启动惊群）你会怎么权衡？",
                "en": "The epoch-invalidation move—'change the namespace, not delete keys'—is essentially 'trade space for correctness and simplicity'. Recall caching systems you've built or imagined: which invalidation scenarios gave you headaches (cascading invalidation, dependency tracking, thundering herd)? Could this epoch/version-namespace idea apply? How would you weigh its costs (memory, TTL choice, cold-start thundering herd)?",
            },
        ],
    },
    "39-playground-llm-connections.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的 Playground、LLM 裁判（第29课）、prompt 实验（第36课）三者在底层有什么关系？",
                    "en": "What's the underlying relationship among Langfuse's Playground, LLM judge (Lesson 29), and prompt experiment (Lesson 36)?",
                },
                "opts": [
                    {
                        "zh": "三者共用同一个 fetchLLMCompletion 核心——一台引擎、三个消费者；凭证解密、provider 适配、结构化输出、工具调用都只写一遍",
                        "en": "all three share the same fetchLLMCompletion core—one engine, three consumers; credential decryption, provider adaptation, structured output, tool calls all written once",
                    },
                    {"zh": "三者各有独立的 LLM 调用实现", "en": "each has its own independent LLM-call implementation"},
                    {"zh": "Playground 只能调 OpenAI", "en": "the Playground can only call OpenAI"},
                    {"zh": "实验不调真实 LLM", "en": "experiments don't call a real LLM"},
                ],
                "answer": 0,
                "why": {
                    "zh": "playground 的 chatCompletionHandler 直接 import 并调用 fetchLLMCompletion，传 tools 和 structuredOutputSchema——和第29课裁判的 callLLM、第36课实验的模型调用是同一台引擎。Playground 不过是这台引擎的「交互式前台」。一处封装、三处复用，避免重复造轮子，也保证三处行为一致。",
                    "en": "The playground's chatCompletionHandler directly imports and calls fetchLLMCompletion, passing tools and structuredOutputSchema—the same engine as Lesson 29's judge callLLM and Lesson 36's experiment model call. The Playground is just this engine's 'interactive front desk'. One encapsulation, three reuses, avoiding reinvention and ensuring consistent behavior across all three.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 用 AES-256-GCM（而非普通对称加密）来加密 provider 的 API key。GCM 模式的 authTag 在这里起什么独特作用？",
                    "en": "Langfuse uses AES-256-GCM (not plain symmetric encryption) to encrypt a provider's API key. What unique role does GCM mode's authTag play here?",
                },
                "opts": [
                    {
                        "zh": "防篡改/完整性保证：解密时校验 authTag，密文哪怕被改一个比特都会校验失败、直接拒绝——保证拿到的明文要么和当初存的一模一样、要么报错，绝不是被悄悄改过的版本",
                        "en": "anti-tamper / integrity guarantee: decryption verifies the authTag, so flipping even one bit of the ciphertext fails verification and is rejected—ensuring the plaintext is either exactly what was stored or an error, never a silently-altered version",
                    },
                    {"zh": "让加密更快", "en": "makes encryption faster"},
                    {"zh": "压缩密文体积", "en": "compresses the ciphertext"},
                    {"zh": "允许多人共享密钥", "en": "lets multiple people share the key"},
                ],
                "answer": 0,
                "why": {
                    "zh": "对 API key 这种数据，光保密不够、还要防篡改。普通加密（如 AES-CBC）挡不住有人偷改几字节、解出另一串看似合法的乱码而悄悄出错。GCM 在加密时算 authTag，解密一并校验：密文动一个比特就失败。于是你得到「完整性保证」——明文要么和存入时一模一样、要么直接报错。对凭证这种错一点就酿大祸的数据，认证加密是底线。",
                    "en": "For data like an API key, confidentiality alone isn't enough—you need anti-tampering. Plain encryption (e.g. AES-CBC) can't stop someone altering a few bytes and decrypting to another seemingly-valid garbage, failing silently. GCM computes an authTag during encryption, verified on decrypt: flip one bit and it fails. So you get an 'integrity guarantee'—plaintext is either exactly as stored or an outright error. For credentials where a small error brews disaster, authenticated encryption is the floor.",
                },
            },
            {
                "q": {
                    "zh": "LlmApiKeys 表既存加密的 secretKey，又单独存一个脱敏的 displaySecretKey（如 sk-…xyz）。为什么要多存这个脱敏串？",
                    "en": "The LlmApiKeys table stores both the encrypted secretKey and a separate masked displaySecretKey (like sk-…xyz). Why store this masked string too?",
                },
                "opts": [
                    {
                        "zh": "为了在 UI 上能认出「这是哪把 key」，又不必为了显示就解密暴露整把 key——展示用脱敏版、调用才解密真版，安全与可用两头兼顾",
                        "en": "so the UI can recognize 'which key this is' without decrypting and exposing the whole key just to display it—show the masked version, decrypt only to call, covering both security and usability",
                    },
                    {"zh": "脱敏串是加密的备份", "en": "the masked string is a backup of the encryption"},
                    {"zh": "用来加速解密", "en": "to speed up decryption"},
                    {"zh": "脱敏串才是真正调用用的", "en": "the masked string is what's actually used to call"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是「明文只在存入和点火瞬间存在」纪律下的实用设计：你在 UI 上得能认出是哪把 key，但不该为了显示就把整把 key 解密暴露。于是单存一个只露末尾几位的脱敏串供展示，真正调 provider 前一刻才 decrypt 出 secretKey 的明文、用完即弃。展示脱敏、调用解密——安全与体验都照顾到。这套纪律是处理一切敏感凭证的范式。",
                    "en": "It's a practical design under the discipline 'plaintext exists only at storing and ignition': in the UI you must recognize which key it is, but shouldn't decrypt and expose the whole key just to display. So a masked string showing only the last few digits is stored for display, with secretKey's plaintext decrypted only just before calling the provider and discarded after. Show masked, decrypt to call—security and UX both covered. This discipline is the paradigm for any sensitive credential.",
                },
            },
        ],
        "open": [
            {
                "zh": "Part 7 到此，整条「开发者工作流」闭环合拢：Playground 试 → 版本化 → 实验对比 → label 发布 → 观测/评估/告警。回顾这条闭环，它和你熟悉的「软件开发生命周期」（写代码→测试→CI→发布→监控）有哪些惊人相似、又有哪些因为 LLM 的「不确定性」而独有的环节？如果让你给团队推广这套 prompt 工程流程，最难落地的是哪一步，为什么？",
                "en": "By the end of Part 7, the whole 'developer workflow' loop closes: try in the Playground → version → experiment-compare → label release → observe/evaluate/alert. Reviewing this loop, how does it strikingly resemble the familiar 'software development lifecycle' (write code→test→CI→release→monitor), and which links are unique due to LLMs' 'non-determinism'? If you rolled out this prompt-engineering process to a team, which step would be hardest to adopt, and why?",
            },
        ],
    },
    "40-dashboards-and-widgets.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的 DashboardWidget 把 view+dimensions+metrics+filters（查询）和 chartType+chartConfig（图表）分开建模。这种「查询/呈现分离」最大的好处是？",
                    "en": "Langfuse's DashboardWidget models view+dimensions+metrics+filters (query) separately from chartType+chartConfig (chart). The biggest benefit of this 'query/presentation separation' is?",
                },
                "opts": [
                    {
                        "zh": "查询与图表正交、各自自由演化：同查询换 chartType 即换图、同图换 metric 即换量；更关键的是纯粹的「算什么」声明不掺展示逻辑，才能被监控器/查询引擎原样复用",
                        "en": "query and chart are orthogonal and evolve freely: same query swaps chartType to change the chart, same chart swaps metric to change the quantity; crucially the pure 'what to compute' declaration, untainted by presentation, can be reused verbatim by the monitor/query engine",
                    },
                    {"zh": "让图表渲染更快", "en": "makes charts render faster"},
                    {"zh": "减少数据库表数量", "en": "reduces the number of DB tables"},
                    {"zh": "自动选择最优图表", "en": "auto-selects the best chart"},
                ],
                "answer": 0,
                "why": {
                    "zh": "查询(算什么)与图表(怎么画)是两个正交维度，强耦合两头受限。分开后：同查询换 chartType 从折线变柱状、同图换 metric 从看成本变看延迟；更关键的是那份纯粹「算什么」声明不掺展示逻辑，才能被第33课监控器、第41课查询引擎原样借走。声明式描述意图而非步骤——和第23课 FilterState、第21课 tRPC 契约同一种信念。",
                    "en": "Query (what to compute) and chart (how to draw) are two orthogonal dimensions; tight coupling limits both. Split: same query swaps chartType from line to bar, same chart swaps metric from cost to latency; crucially that pure 'what to compute' declaration, untainted by presentation, can be borrowed verbatim by Lesson 33's monitor and Lesson 41's query engine. Declarative describes intent not steps—same belief as Lesson 23's FilterState and Lesson 21's tRPC contract.",
                },
            },
            {
                "q": {
                    "zh": "第 33 课的监控器源码注释说它「mirrors DashboardWidget, minus TRACES」，且 MonitorView 恰好是 DashboardWidgetViews 去掉 TRACES。这个复用透露了什么设计意图？",
                    "en": "Lesson 33's monitor source comment says it 'mirrors DashboardWidget, minus TRACES', and MonitorView is exactly DashboardWidgetViews minus TRACES. What design intent does this reuse reveal?",
                },
                "opts": [
                    {
                        "zh": "「指标」全公司只有一种算法：仪表盘画图、监控比阈值、查询引擎编 SQL 共享同一份查询形状，于是图上看到的、告警依据的、API 取到的永远是同一个数——一致性靠架构从根上保证而非靠纪律",
                        "en": "a metric has exactly one algorithm company-wide: dashboard charts, monitor thresholds, and the query engine's SQL share one query shape, so what you see on the chart, what alerts on, and what the API returns are always the same number—consistency guaranteed at the root by architecture, not discipline",
                    },
                    {"zh": "监控器是仪表盘的子集功能", "en": "the monitor is a subset feature of dashboards"},
                    {"zh": "TRACES 数据不能被监控", "en": "TRACES data can't be monitored"},
                    {"zh": "为了节省存储", "en": "to save storage"},
                ],
                "answer": 0,
                "why": {
                    "zh": "若仪表盘的「平均有用性」和监控器的「平均有用性」各写一套实现，迟早算出不同的数——口径漂移是数据产品的慢性毒药。让三处共享同一份 view+dimensions+metrics+filters 声明、同一个查询引擎，等于钉死「这个指标全公司只有一种算法」。pull(看图)与 push(告警)永远同一个数。一致性靠架构保证，不靠纪律维持。",
                    "en": "If the dashboard's and the monitor's 'average helpfulness' were separate implementations, they'd eventually compute different numbers—definition drift is a slow poison for data products. Having three places share one view+dimensions+metrics+filters declaration and one query engine nails down 'this metric has one algorithm company-wide'. Pull (chart) and push (alert) are always the same number. Consistency is guaranteed by architecture, not maintained by discipline.",
                },
            },
            {
                "q": {
                    "zh": "DashboardWidget 的 view 字段取自 DashboardWidgetViews 枚举。它有哪四个值？",
                    "en": "A DashboardWidget's view field comes from the DashboardWidgetViews enum. What are its four values?",
                },
                "opts": [
                    {
                        "zh": "TRACES、OBSERVATIONS、SCORES_NUMERIC、SCORES_CATEGORICAL——即一个 widget 能聚合 trace、观测、数值分或分类分这四种数据源之一",
                        "en": "TRACES, OBSERVATIONS, SCORES_NUMERIC, SCORES_CATEGORICAL—i.e. a widget can aggregate one of these four data sources: traces, observations, numeric scores, or categorical scores",
                    },
                    {"zh": "LINE、BAR、PIE、NUMBER", "en": "LINE, BAR, PIE, NUMBER"},
                    {"zh": "DAY、WEEK、MONTH、YEAR", "en": "DAY, WEEK, MONTH, YEAR"},
                    {"zh": "SUM、AVG、COUNT、MAX", "en": "SUM, AVG, COUNT, MAX"},
                ],
                "answer": 0,
                "why": {
                    "zh": "DashboardWidgetViews = { TRACES, OBSERVATIONS, SCORES_NUMERIC, SCORES_CATEGORICAL }，决定 widget 聚合哪种数据源。LINE/BAR/PIE/NUMBER 那些是另一个枚举 DashboardWidgetChartType（怎么画，9 种）。view 管「看什么数据」、chartType 管「画成什么图」——正是查询与呈现分离的体现。监控器的 MonitorView 则是这个去掉 TRACES。",
                    "en": "DashboardWidgetViews = { TRACES, OBSERVATIONS, SCORES_NUMERIC, SCORES_CATEGORICAL }, deciding which data source a widget aggregates. LINE/BAR/PIE/NUMBER belong to a different enum, DashboardWidgetChartType (how to draw, 9 types). view governs 'what data', chartType 'what chart'—exactly the query/presentation split. The monitor's MonitorView is this minus TRACES.",
                },
            },
        ],
        "open": [
            {
                "zh": "「一份查询形状，三处复用」是 Langfuse 保证指标口径一致的核心招式。回想你做过或用过的数据产品：是否遇到过「同一个指标在不同页面/报表/告警里算出不同数」的口径漂移？如果让你设计一套机制根治它，你会怎么做？声明式查询 + 统一引擎的代价（灵活性受限、引擎要支持所有需求）你怎么权衡？",
                "en": "'One query shape, three reuses' is Langfuse's core move for guaranteeing metric-definition consistency. Recall data products you've built or used: have you hit 'the same metric computes different numbers on different pages/reports/alerts' definition drift? If you designed a mechanism to cure it, how would you? How would you weigh the costs of declarative-query + unified-engine (limited flexibility, the engine must support all needs)?",
            },
        ],
    },
    "41-query-engine.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的查询引擎有一个「语义层」（data model）。它的核心作用是什么？",
                    "en": "Langfuse's query engine has a 'semantic layer' (data model). What is its core role?",
                },
                "opts": [
                    {
                        "zh": "把友好的逻辑名（如维度 name、度量 totalCost）映射到真实的 ClickHouse 列/表达式（traces.name、sum(total_cost)），让上层永不直接碰物理列——物理 schema 改名换表只需改字典",
                        "en": "mapping friendly logical names (e.g. dimension name, measure totalCost) to real ClickHouse columns/expressions (traces.name, sum(total_cost)), so the upper layer never touches physical columns—a physical rename/restructure only changes the dictionary",
                    },
                    {"zh": "缓存查询结果", "en": "caching query results"},
                    {"zh": "把 SQL 翻译成自然语言", "en": "translating SQL into natural language"},
                    {"zh": "压缩 ClickHouse 数据", "en": "compressing ClickHouse data"},
                ],
                "answer": 0,
                "why": {
                    "zh": "dataModel.ts 为每个 view 声明 dimensions/measures，每项形如 { sql: \"traces.name\", alias: \"name\" }，把逻辑名映射到真实 SQL（甚至是 formatDateTime 这样的表达式）。widget 只引用逻辑名，永不碰物理列。于是物理列改名/换表只需改字典，成百上千张 widget 不动——这是「想要什么」与「怎么存」的解耦。",
                    "en": "dataModel.ts declares dimensions/measures per view, each shaped like { sql: \"traces.name\", alias: \"name\" }, mapping logical names to real SQL (even expressions like formatDateTime). A widget only references logical names, never physical columns. So a physical rename/restructure only touches the dictionary, leaving hundreds of widgets unmoved—decoupling 'what you want' from 'how it's stored'.",
                },
            },
            {
                "q": {
                    "zh": "QueryBuilder.build() 把过滤条件编译进 SQL 时，用户填的具体值（如 environment=\"production\"）是怎么处理的？",
                    "en": "When QueryBuilder.build() compiles filter conditions into SQL, how are user-filled concrete values (e.g. environment=\"production\") handled?",
                },
                "opts": [
                    {
                        "zh": "绑成 parameters、绝不拼进 SQL 正文（SQL 里只放 {占位符}，值随调用绑定）——和第23课 FilterState 同款，从结构上根除 SQL 注入",
                        "en": "bound as parameters, never spliced into the SQL body (the SQL holds only {placeholders}, values bound per call)—same as Lesson 23's FilterState, rooting out SQL injection structurally",
                    },
                    {"zh": "直接字符串拼接进 SQL", "en": "directly string-concatenated into the SQL"},
                    {"zh": "先做 HTML 转义再拼接", "en": "HTML-escaped then concatenated"},
                    {"zh": "存进 Redis 再引用", "en": "stored in Redis then referenced"},
                ],
                "answer": 0,
                "why": {
                    "zh": "mapFilters/buildWhereClause 用 FilterList 的 apply() 产出 SQL+参数：SQL 模板里是 {占位符}，用户值放进 parameters 字典，由 ClickHouse 驱动安全绑定。SQL 与值分离，模板可缓存/审计，恶意输入串改不了结构。这正是第23课把 FilterState 编译成过滤 SQL 的同一种防注入纪律，在聚合查询里同样贯彻——注入安全靠结构兜底，不靠每个开发者自觉。",
                    "en": "mapFilters/buildWhereClause use FilterList's apply() to produce SQL+parameters: the SQL template has {placeholders}, user values go into a parameters dict, safely bound by the ClickHouse driver. SQL separate from values, the template cacheable/auditable, malicious input can't alter the structure. This is the same injection-prevention discipline as Lesson 23 compiling FilterState into filter SQL, carried into aggregation—injection safety backstopped by structure, not each developer's diligence.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的 view 带有 v1/v2 版本。为什么查询引擎要给「视图」也引入版本？",
                    "en": "Langfuse's views carry v1/v2 versions. Why does the query engine introduce versions to 'views' too?",
                },
                "opts": [
                    {
                        "zh": "因为物理 schema 会演进（表重构、列拆分、加物化视图），但历史查询不该因此失效；一个 v1 查询永远按 v1 字典编译，底层迁到 v2 也不破坏——和第34/37课「不可变+演进」同一信念",
                        "en": "because the physical schema evolves (table refactors, column splits, materialized views), yet historical queries shouldn't break for it; a v1 query forever compiles against the v1 dictionary even after the underlying migrates to v2—same belief as Lessons 34/37's 'immutable + evolving'",
                    },
                    {"zh": "为了支持多个 ClickHouse 实例", "en": "to support multiple ClickHouse instances"},
                    {"zh": "v2 比 v1 查询更快", "en": "v2 queries are faster than v1"},
                    {"zh": "版本号用于计费", "en": "version numbers are used for billing"},
                ],
                "answer": 0,
                "why": {
                    "zh": "ClickHouse 表会重构、列会拆分合并、为性能加物化视图——底层正常演化。若查询绑死当前物理结构，每次底层一动，所有保存的 widget/monitor/API 查询都可能算错或报错。给 view 引入 v1/v2，等于给「语义」也加了不可变快照：v1 查询永远按 v1 编译。这和第34课数据项版本、第37课 prompt 版本同一信念——底层敢大胆演进，因为上层被稳定的版本化语义保护。",
                    "en": "ClickHouse tables get refactored, columns split/merge, materialized views added for performance—normal underlying evolution. If a query binds to the current physical structure, every underlying move risks miscomputing/erroring every saved widget/monitor/API query. Versioning a view gives semantics an immutable snapshot: a v1 query forever compiles against v1. Same belief as Lesson 34's dataset-item versions and Lesson 37's prompt versions—the underlying evolves boldly because the upper layer is protected by stable versioned semantics.",
                },
            },
        ],
        "open": [
            {
                "zh": "查询引擎本质是一个「语义层 + 编译器」——这模式在业界很常见（Cube、LookML、Malloy 等）。它用「声明式 + 物理无关 + 注入安全」换取了什么？又付出了什么代价（引擎得支持所有需要的查询形状，逃逸到原生 SQL 受限）？如果你的团队要做内部分析平台，你会选「人人写 SQL」还是「统一语义层」，为什么？两者能并存吗？",
                "en": "The query engine is essentially a 'semantic layer + compiler'—a common industry pattern (Cube, LookML, Malloy). What does 'declarative + physical-agnostic + injection-safe' buy, and at what cost (the engine must support every needed query shape, escaping to raw SQL is limited)? If your team built an internal analytics platform, would you choose 'everyone writes SQL' or 'a unified semantic layer', and why? Can the two coexist?",
            },
        ],
    },
    "42-models-and-pricing.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 给每个模型配一条 matchPattern 正则（如 gpt-4o 的 (?i)^(openai/)?(gpt-4o)$），而不是用精确字符串匹配模型名。为什么？",
                    "en": "Langfuse gives each model a matchPattern regex (e.g. gpt-4o's (?i)^(openai/)?(gpt-4o)$) instead of exact string matching. Why?",
                },
                "opts": [
                    {
                        "zh": "模型命名极度碎片化：同一模型在 OpenAI/Bedrock/Vertex 有 provider 前缀、us./eu. 区域前缀、-v1:0/@date 版本等十几种合法写法；一条正则把这些同义写法收敛成一个意图，精确匹配则要为每种写法各存一条、维护爆炸",
                        "en": "model naming is highly fragmented: the same model has provider prefixes, us./eu. region prefixes, -v1:0/@date versions—a dozen valid spellings across OpenAI/Bedrock/Vertex; one regex converges these synonyms into one intent, whereas exact matching needs one entry per spelling, exploding maintenance",
                    },
                    {"zh": "正则匹配更快", "en": "regex matching is faster"},
                    {"zh": "为了支持模糊搜索", "en": "to support fuzzy search"},
                    {"zh": "正则能加密模型名", "en": "regex can encrypt model names"},
                ],
                "answer": 0,
                "why": {
                    "zh": "同一个 Claude 在 OpenAI 风格叫 claude-3-5-sonnet、Bedrock 叫 us.anthropic.claude-3-5-sonnet-v1:0、Vertex 叫 claude-...@20240620，加大小写和 provider/ 前缀排列，轻松十几种写法。精确匹配要为每种各存一条价目，加区域/改版本就全表翻新、极易漏。一条 (?i)^…$ 全串正则把同义写法收敛成「无论你怎么称呼，我都认得这是 gpt-4o」——对抗命名碎片化的必需品。",
                    "en": "The same Claude is claude-3-5-sonnet in OpenAI style, us.anthropic.claude-3-5-sonnet-v1:0 on Bedrock, claude-...@20240620 on Vertex, plus casing and provider/ prefix permutations—easily a dozen spellings. Exact matching needs one price entry per spelling; adding a region or bumping a version overhauls the table and misses abound. One (?i)^…$ full-string regex converges synonyms into 'however you call it, I know this is gpt-4o'—a necessity against naming fragmentation.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的 pricingTiers 把定价分成「恰一个默认档 + 任意条件档」。matchPricingTier 是怎么选出该用哪个档的？",
                    "en": "Langfuse's pricingTiers splits pricing into 'exactly one default tier + any conditional tiers'. How does matchPricingTier pick which tier to use?",
                },
                "opts": [
                    {
                        "zh": "滤掉默认档，把条件档按 priority 升序逐个评估（每档 conditions 是 AND 逻辑、全满足才中），第一个全满足的胜出；都不满足就回落默认档——保证任何用量都能算出价",
                        "en": "filter out the default tier, evaluate conditional tiers in ascending priority (each tier's conditions are AND logic, all must hold), the first all-holding wins; if none hold, fall back to the default tier—guaranteeing any usage gets a price",
                    },
                    {"zh": "总是用最便宜的档", "en": "always uses the cheapest tier"},
                    {"zh": "随机选一个档", "en": "picks a random tier"},
                    {"zh": "用 priority 最高的档", "en": "uses the highest-priority tier"},
                ],
                "answer": 0,
                "why": {
                    "zh": "matchPricingTier(matcher.ts:88)：① 滤掉 isDefault 档、按 priority 升序排序非默认档；② 逐个评估其 conditions（evaluateConditions 用 AND——全部 operator(gt/gte/lt/lte/eq/neq) 比较通过才算中）；③ 返回第一个全满足的档；④ 都不中则返回默认档。默认档永远存在、永远兜底，保证任何用量都落进某个价、绝不漏算。这把「分级定价策略」表达成数据而非 if-else。",
                    "en": "matchPricingTier (matcher.ts:88): ① filter out the isDefault tier, sort non-default tiers by ascending priority; ② evaluate each one's conditions (evaluateConditions uses AND—all operator(gt/gte/lt/lte/eq/neq) comparisons must pass to match); ③ return the first all-holding tier; ④ if none, return the default. The default always exists and backstops, guaranteeing any usage lands in a price. This expresses 'tiered pricing policy' as data, not if-else.",
                },
            },
            {
                "q": {
                    "zh": "default-model-prices.json 里有 158 条模型价目，但一个项目用了自研模型、谈了折扣价。Langfuse 怎么兼顾「开箱即用」和「贴合真实账单」？",
                    "en": "default-model-prices.json has 158 model prices, but a project uses a self-built model with a negotiated discount. How does Langfuse balance 'ready out of the box' with 'fits the real bill'?",
                },
                "opts": [
                    {
                        "zh": "158 条是 projectId 为空的全局默认价（upsert 进 Model/Price 表，开箱即用）；项目可新增带 projectId 的 Model 条目覆盖（自研/私有/折扣价优先）——默认 + 项目覆盖两全",
                        "en": "the 158 are global defaults with empty projectId (upserted into Model/Price tables, ready out of the box); a project can add projectId-scoped Model entries to override (self-built/private/discount prices take priority)—defaults + project override, both covered",
                    },
                    {"zh": "只能用内置的 158 个模型", "en": "only the built-in 158 models can be used"},
                    {"zh": "必须改 JSON 文件重新部署", "en": "you must edit the JSON and redeploy"},
                    {"zh": "折扣价不支持", "en": "discount prices aren't supported"},
                ],
                "answer": 0,
                "why": {
                    "zh": "default-model-prices.json 的 158 条是 Langfuse 内置默认价，由 upsertDefaultModelPrices 灌进 DB 的 Model/Price 表（projectId 为空=全局）。项目可在自己项目下新增带 projectId 的 Model 条目，优先于全局默认——于是主流模型价开箱即备好，自研/私有/折扣场景又能精确覆盖。add-model-price 仓库技能管的就是怎么安全往种子价里增改条目。",
                    "en": "The 158 in default-model-prices.json are Langfuse's built-in defaults, loaded into the DB's Model/Price tables by upsertDefaultModelPrices (empty projectId = global). A project can add projectId-scoped Model entries that take priority over global defaults—so mainstream prices are preloaded while self-built/private/discount cases override precisely. The add-model-price repo skill governs how to safely add/edit entries in the seed file.",
                },
            },
        ],
        "open": [
            {
                "zh": "模型定价把「分级策略」表达成数据（带 conditions 的 tier）而非代码里的 if-else，这是第 16/28 课「规则即数据」的又一次回响。回想你做过的系统：哪些「业务规则」其实更适合放进数据/配置而非硬编码？「规则即数据」带来灵活，但也有代价（要设计一套表达规则的 schema、要写解释器、调试更绕）。你会用什么标准判断一条规则该进代码还是进数据？",
                "en": "Model pricing expresses 'tiering policy' as data (tiers with conditions) rather than if-else in code—another echo of Lessons 16/28's 'rules as data'. Recall systems you've built: which 'business rules' are actually better as data/config than hardcoded? 'Rules as data' brings flexibility but also costs (designing a schema to express rules, writing an interpreter, harder debugging). By what criteria would you decide whether a rule goes into code or into data?",
            },
        ],
    },
    "43-cloud-usage-metering.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse Cloud 的用量计量任务用一张 cronJobs 表，做整点对齐 + Processing 互斥 + 20分钟兜底接管。这套设计要解决的核心问题是？",
                    "en": "Langfuse Cloud's usage-metering job uses a cronJobs table for hour alignment + Processing mutex + 20-minute fallback takeover. What core problem does this design solve?",
                },
                "opts": [
                    {
                        "zh": "计费的「恰好一次」：重复上报会双倍收费、漏报则平台亏损；用数据库行锁堵死重复执行(互斥)、任务崩溃(20分钟兜底)、区间错位(整点对齐)，让每小时用量不重不漏",
                        "en": "billing's 'exactly once': a duplicate report double-charges, a miss loses money for the platform; a DB row lock plugs duplicate execution (mutex), task crash (20-min fallback), and interval misalignment (hour alignment), so each hour's usage is no-dup, no-miss",
                    },
                    {"zh": "加快计量速度", "en": "speeding up metering"},
                    {"zh": "压缩 ClickHouse 存储", "en": "compressing ClickHouse storage"},
                    {"zh": "支持多种货币", "en": "supporting multiple currencies"},
                ],
                "answer": 0,
                "why": {
                    "zh": "前面链路偶尔多算一条 trace 大多无伤、下次自愈，但计费对错误零容忍：多报一小时用量，客户信用卡被多刷、上投诉；少报是平台亏损。普通任务「最终一致」不够，计量须「精确一次」(exactly-once，分布式难题)。Langfuse 务实地用 cronJobs 行锁把三种威胁逐一堵死：重复执行(Processing 互斥)、崩溃(jobStartedAt>20分钟强制接管)、错位(lastRun%3600000===0 整点对齐)。",
                    "en": "Earlier chains can over-count a trace harmlessly and self-heal, but billing tolerates no error: over-report an hour and a customer's card is overcharged with a complaint; under-report is a platform loss. Normal 'eventual consistency' isn't enough; metering must be 'exactly once' (a hard distributed problem). Langfuse pragmatically uses a cronJobs row lock to plug three threats: duplicate execution (Processing mutex), crash (jobStartedAt>20min forced takeover), misalignment (lastRun%3600000===0 hour alignment).",
                },
            },
            {
                "q": {
                    "zh": "Langfuse Cloud 按「用量事件」（可观测操作的细颗粒度）计费，而不是按 token 数。为什么这种细颗粒度单位比 token 更合适？",
                    "en": "Langfuse Cloud bills by 'usage events' (a fine-grained per-observable-operation unit) rather than token count. Why is this fine-grained unit more suitable than token?",
                },
                "opts": [
                    {
                        "zh": "它最对齐平台提供的价值：token 绑模型(贵模型token多，与记录分析的价值无关)、trace 太粗(一个trace可能1步也可能上百步观测)；观测是「一次可观测操作」的原子单位，让客户付的钱正比于「Langfuse帮你记录分析了多少」",
                        "en": "it best aligns with the platform's value: token is model-bound (pricey models burn more, unrelated to record/analysis value), trace is too coarse (one trace may be 1 step or hundreds of observations); the observation is the atomic unit of 'one observable operation', making what the customer pays proportional to 'how much Langfuse recorded/analyzed'",
                    },
                    {"zh": "观测数最容易统计", "en": "observation count is easiest to count"},
                    {"zh": "Stripe 只支持观测计费", "en": "Stripe only supports observation billing"},
                    {"zh": "观测数最小，收费最低", "en": "observation count is smallest, lowest charge"},
                ],
                "answer": 0,
                "why": {
                    "zh": "按 token 计费和你用的模型强绑定(贵模型 token 多)，且和 Langfuse 的价值(记录与分析，不是替你跑模型)不直接相关。按 trace 太粗：一个 trace 可能含一步或上百步观测，复杂 agent 和简单问答同价不公平。观测恰好是「一次可观测操作」的原子计量单位，最对得上「Langfuse 帮你存了、分析了多少」——复杂应用观测多付得多、简单少付。好的计费单位让客户付的钱正比于得到的价值。（计量上报两个 meter：tracing_observations 为 legacy、tracing_events=trace+score+observation 之和，为当前口径。）",
                    "en": "Billing by token couples tightly to your model (pricey models burn more) and isn't directly tied to Langfuse's value (record and analysis, not running the model). Billing by trace is too coarse: one trace may hold one step or hundreds of observations, charging complex agents and simple Q&A the same is unfair. The observation is exactly the atomic metering unit of 'one observable operation', best matching 'how much Langfuse stored and analyzed'—complex apps pay more, simple less. A good billing unit makes what the customer pays proportional to value received. (Metering reports two meters: tracing_observations legacy, and tracing_events = trace+score+observation, the current unit.)",
                },
            },
            {
                "q": {
                    "zh": "Part 8 里出现了两种「钱」：cloudUsageMetering 和 cloudSpendAlert。它们的区别是？",
                    "en": "Part 8 features two kinds of 'money': cloudUsageMetering and cloudSpendAlert. What's the difference?",
                },
                "opts": [
                    {
                        "zh": "方向相反：计量是「平台向你收费」(按用量事件报Stripe，Cloud专属)；花费告警是「帮你管你自己的LLM花费」(盯你在各provider的成本越阈值就提醒)——一个收你的钱、一个帮你看你的钱",
                        "en": "opposite directions: metering is 'the platform charging you' (reports usage events to Stripe, Cloud-exclusive); spend alert is 'helping you manage your own LLM spend' (watches your cost across providers, alerts on threshold)—one charges you, one helps you watch your money",
                    },
                    {"zh": "完全一样，只是名字不同", "en": "identical, just different names"},
                    {"zh": "都是平台向你收费", "en": "both are the platform charging you"},
                    {"zh": "都只在自托管版生效", "en": "both only work in self-host"},
                ],
                "answer": 0,
                "why": {
                    "zh": "两笔账方向相反。cloudUsageMetering：平台→收你的费，按观测数每小时报 Stripe，是 Cloud 商业层、自托管不收费。cloudSpendAlert：帮你→管你自己在 OpenAI/Anthropic 等的 LLM 开销，越过你设的阈值就提醒——和第16/42课算你的成本一脉相承。前者是「Langfuse 怎么收你钱」，后者是「帮你看你花了多少钱」，别混淆。",
                    "en": "Two opposite ledgers. cloudUsageMetering: platform → charges you, reporting observation count to Stripe hourly, the Cloud commercial layer, self-host charges nothing. cloudSpendAlert: helps you → manage your own LLM spend on OpenAI/Anthropic etc., alerting when crossing your threshold—in the lineage of Lessons 16/42 computing your cost. The former is 'how Langfuse charges you', the latter 'helping you watch what you spent'; don't conflate them.",
                },
            },
        ],
        "open": [
            {
                "zh": "「计费必须恰好一次」是分布式系统里出了名难的 exactly-once 问题，而 Langfuse 没有追求理论完美，而是用一张数据库行锁把「防重复+防崩溃+防错位」三种现实威胁逐一堵死。回想你做过或设想的系统：哪些场景对「不重不漏」有类似的硬要求（支付、库存、发券）？你会怎么权衡「理论上的精确一次」与「工程上够用的几道具体防护」？后者有什么风险？",
                "en": "'Billing must be exactly once' is the notoriously hard exactly-once problem in distributed systems, yet Langfuse doesn't chase theoretical perfection but uses a DB row lock to plug three real threats: anti-duplicate + anti-crash + anti-misalignment. Recall systems you've built or imagined: which scenarios have a similar hard 'no-dup-no-miss' requirement (payments, inventory, coupon issuance)? How would you weigh 'theoretical exactly-once' against 'a few good-enough concrete engineering defenses'? What are the latter's risks?",
            },
        ],
    },
    "44-automations-webhooks.html": {
        "mcq": [
            {
                "q": {
                    "zh": "webhook 这个 Action 让 Langfuse 的服务器去请求「用户填写的任意 URL」。这为什么是个危险的安全面，攻击者会怎么利用？",
                    "en": "The webhook Action makes Langfuse's server fetch 'any user-supplied URL'. Why is this a dangerous attack surface, and how would an attacker exploit it?",
                },
                "opts": [
                    {
                        "zh": "SSRF（服务端请求伪造）：攻击者把 URL 填成内网地址或 169.254.169.254（云元数据接口），借你服务器之手够到它本不该够到的内部资源——尤其能偷到这台机器的临时云凭证(AK/SK)，进而接管整个云账号",
                        "en": "SSRF (Server-Side Request Forgery): the attacker sets the URL to an internal address or 169.254.169.254 (the cloud metadata endpoint), reaching—through your server's hands—internal resources it should never reach, especially stealing this machine's temporary cloud credentials (AK/SK) and from there taking over the whole cloud account",
                    },
                    {"zh": "webhook 会拖慢页面加载速度", "en": "webhooks slow down page load"},
                    {"zh": "用户填的 URL 可能拼错，导致 404", "en": "the user's URL may be mistyped, causing 404"},
                    {"zh": "webhook 消耗的带宽太大", "en": "webhooks consume too much bandwidth"},
                ],
                "answer": 0,
                "why": {
                    "zh": "「用户给一个 URL、我们去请求它」是所有 Web 系统里最危险的功能之一。攻击者不在乎对方返回什么页面，而是借你的服务器当跳板：请求 169.254.169.254（AWS/GCP 实例元数据接口）拿临时云凭证、请求 localhost:6379 打你的内部 Redis、请求内部管理后台……这些资源往往因为「反正在内网」而不设防。SSRF 的可怕在于它绕过了所有边界：防火墙挡外面进来的，SSRF 是从你内部往外打。",
                    "en": "'A user gives a URL and we fetch it' is one of the most dangerous features in any web system. The attacker doesn't care what page comes back; they use your server as a springboard: fetch 169.254.169.254 (the AWS/GCP instance metadata endpoint) for temporary cloud credentials, fetch localhost:6379 to hit your internal Redis, fetch internal admin panels… these are often undefended on the assumption 'it's internal anyway'. SSRF is terrifying because it bypasses every boundary: a firewall blocks what comes in, SSRF attacks outward from inside you.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的 IP 黑名单校验有两个值得注意的设计：解析失败时默认「拦截」，而且校验放在「真正发请求那一刻」对解析出的真实 IP 做。这两点各防住了什么？",
                    "en": "Langfuse's IP-blocklist check has two notable designs: it defaults to 'block' when resolution fails, and it runs 'at the moment the request is actually sent' on the resolved real IP. What does each guard against?",
                },
                "opts": [
                    {
                        "zh": "fail-closed(拿不准就拦)防的是「校验代码本身出错或遇到怪输入时悄悄放行」；请求时校验真实 IP 防的是 DNS-rebinding——攻击者创建时把域名解析到合法 IP 过审、请求时再切换解析到内网 IP",
                        "en": "fail-closed (block when uncertain) guards against 'silently letting through when the check code errors or hits weird input'; checking the real IP at request time guards against DNS-rebinding—the attacker resolves the domain to a legit IP at creation to pass review, then flips it to an internal IP at request time",
                    },
                    {"zh": "都是为了让校验跑得更快", "en": "both are to make the check run faster"},
                    {"zh": "都是为了节省内存", "en": "both are to save memory"},
                    {"zh": "都是为了兼容 IPv6", "en": "both are for IPv6 compatibility"},
                ],
                "answer": 0,
                "why": {
                    "zh": "fail-closed 是安全代码的默认信条：拿不准的、解析不了的，一律当危险处理——默认答案是「拒绝」不是「放行」（ipBlocking.ts:88 注释 'block it to be safe'）。DNS-rebinding 则是个阴险攻击：只在创建时校验就会被骗，因为域名解析结果可以临门一脚切换。Langfuse 把 IP 校验下沉到实际发请求那一刻、对当时真正解析出的 IP 判定，攻击者再切 DNS 也逃不过。安全检查必须贴着「危险动作真正发生的那一刻」做。",
                    "en": "fail-closed is the default creed of secure code: anything uncertain or unparseable is treated as dangerous—the default answer is 'deny', not 'allow' (ipBlocking.ts:88 comment 'block it to be safe'). DNS-rebinding is insidious: validating only at creation is fooled because DNS resolution can flip at the last second. Langfuse pushes the IP check down to the moment the request is sent, judging the IP actually resolved then, so swapping DNS can't slip past. Security checks must hug 'the moment the dangerous action actually happens'.",
                },
            },
            {
                "q": {
                    "zh": "自动化的数据模型是 Trigger → Action，每次执行还落一条 AutomationExecution 记录。这个 AutomationExecution 和前面哪些课的设计是「同一种东西」？",
                    "en": "The automation data model is Trigger → Action, and each run writes an AutomationExecution record. AutomationExecution is 'the same kind of thing' as designs from which earlier lessons?",
                },
                "opts": [
                    {
                        "zh": "和第30课 eval 的 JobExecution、第32课人工标注的 queue item 是同一种「落库的、有状态的、可追溯的执行记录」——状态机 PENDING→COMPLETED/ERROR，连 input/output/error 一并存，便于排查与重试",
                        "en": "the same 'persisted, stateful, traceable execution record' as Lesson 30's eval JobExecution and Lesson 32's annotation queue item—a state machine PENDING→COMPLETED/ERROR, storing input/output/error too, for debugging and retry",
                    },
                    {"zh": "和 ClickHouse 的 trace 表是同一种东西", "en": "the same as the ClickHouse trace table"},
                    {"zh": "和 Redis 缓存是同一种东西", "en": "the same as the Redis cache"},
                    {"zh": "和 Prompt 的版本号是同一种东西", "en": "the same as a Prompt's version number"},
                ],
                "answer": 0,
                "why": {
                    "zh": "Langfuse 反复用同一个模式：凡是「异步执行、可能失败、要能排查」的动作，就给它一张表、一个状态机、一份 input/output/error 留痕。eval 的 JobExecution（第30课）、标注 item（第32课）、这里的 AutomationExecution，本质都是「有状态、可追溯的执行记录」。认出这个反复出现的骨架，新功能就不再陌生：先问『它的执行记录长什么样、状态机怎么流转』。",
                    "en": "Langfuse reuses the same pattern: any 'async, possibly-failing, must-be-debuggable' action gets a table, a state machine, and an input/output/error trail. eval's JobExecution (Lesson 30), the annotation item (Lesson 32), and AutomationExecution here are all 'stateful, traceable execution records'. Recognizing this recurring skeleton makes new features unsurprising: first ask 'what does its execution record look like, how does the state machine flow'.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课的 webhook SSRF 防御是「纵深防御」的范本：协议白名单、端口白名单、主机名黑名单、IP CIDR 黑名单、fail-closed、请求时校验……一道接一道，而不是一道大墙。请结合你自己的经验谈谈：为什么安全设计偏爱「多道独立的闸」而不是「一道完美的墙」？这种思路除了 SSRF，还能迁移到哪些场景（鉴权、输入校验、限流）？多道防护各自独立又有什么维护成本？",
                "en": "This lesson's webhook SSRF defense is a model of 'defense in depth': protocol allowlist, port allowlist, hostname blocklist, IP CIDR blocklist, fail-closed, request-time check… gate after gate, not one big wall. Drawing on your own experience: why does security design favor 'many independent gates' over 'one perfect wall'? Beyond SSRF, where else does this idea transfer (auth, input validation, rate limiting)? What maintenance cost do independent layered defenses carry?",
            },
        ],
    },
    "45-slack-and-notifications.html": {
        "mcq": [
            {
                "q": {
                    "zh": "同样是「通知投递」，第 44 课的 webhook 只要填一个 URL，而 Slack 集成却要走完整 OAuth 安装、把 bot 令牌加密入库。为什么 Slack 需要这么重的流程？",
                    "en": "Both are 'notification delivery', yet Lesson 44's webhook just needs a URL, while the Slack integration goes through a full OAuth install and stores the bot token encrypted. Why does Slack need such a heavy flow?",
                },
                "opts": [
                    {
                        "zh": "信任模型不同：webhook 是 Langfuse 作为发起方把数据推给你的端点，不需要你的任何凭据(填URL即可)；Slack 要「以你的身份在你工作区发消息」，必须由 Slack 授予一把代表你的钥匙(bot令牌)——这把钥匙泄露=别人能冒充你，所以必须加密保管",
                        "en": "different trust models: a webhook has Langfuse as initiator pushing data to your endpoint, needing none of your credentials (a URL suffices); Slack must 'post as you in your workspace', so Slack must grant a key representing you (bot token)—leaking it = someone can impersonate you, so it must be encrypted at rest",
                    },
                    {"zh": "Slack 的服务器比较慢，需要预先建立连接", "en": "Slack's servers are slow, needing a pre-established connection"},
                    {"zh": "OAuth 只是为了好看，技术上 URL 也能实现", "en": "OAuth is just cosmetic; a URL could do it technically"},
                    {"zh": "Slack 收费，所以要走付费授权", "en": "Slack charges money, so it needs paid authorization"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是「能力越大、保管越严」的体现。webhook 是 Langfuse 主动往外推，自己不持有对方任何凭据，所以风险集中在「URL 会不会指向危险目标」(SSRF，第44课用 URL 校验解决)。Slack 则要拿到一把「代表你」的 bot 令牌，凭它能往你的频道发消息、读频道列表——这是被授予的、可冒充你的权力，所以必须像第 39 课保管 LLM API Key 一样，用 AES-256-GCM 加密入库。两种集成的「重」与「轻」，直接由它们的信任模型决定。",
                    "en": "This embodies 'the greater the capability, the stricter the safekeeping'. A webhook is Langfuse actively pushing out, holding none of the peer's credentials, so risk concentrates on 'does the URL point somewhere dangerous' (SSRF, solved by URL validation in Lesson 44). Slack must obtain a bot token that 'represents you', wielding which it can post to your channels and read channel lists—a granted, impersonating power, so it must be encrypted at rest with AES-256-GCM like Lesson 39's LLM API key safekeeping. Each integration's 'heavy' or 'light' is set directly by its trust model.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 每次给 Slack 发消息，都重新从数据库取出加密令牌、解密、构造 WebClient，而不是缓存一个 WebClient 长期复用。这个选择的主要好处是？",
                    "en": "Each time Langfuse sends a Slack message, it re-fetches the encrypted token from the DB, decrypts it, and builds a WebClient, rather than caching a long-lived WebClient. The main benefit of this choice is?",
                },
                "opts": [
                    {
                        "zh": "保证永远用「当前最新」的令牌：用户可能在 Slack 侧卸载应用、重装到别的工作区、或令牌被轮换——每次解密取最新令牌就不会用到已失效的凭据，和第38课prompt缓存读时校验新鲜度、第44课请求时校验真实IP同理",
                        "en": "guarantees always using the 'currently latest' token: the user may uninstall the app on Slack's side, reinstall to another workspace, or the token may be rotated—decrypting the latest token each time avoids using a stale credential, same as Lesson 38's prompt cache validating freshness on read and Lesson 44's checking the real IP at request time",
                    },
                    {"zh": "解密比缓存更快", "en": "decrypting is faster than caching"},
                    {"zh": "为了让数据库有更多读负载", "en": "to give the database more read load"},
                    {"zh": "WebClient 不能被缓存", "en": "WebClient cannot be cached"},
                ],
                "answer": 0,
                "why": {
                    "zh": "缓存一个长生命周期、握着敏感令牌的客户端，省下的开销很小，却带来「用了过期/已撤销凭据」的真实风险：令牌可能因卸载、重装、轮换而失效。每次发送都 fetchInstallation→decrypt 取当前令牌，就总用最新最有效的凭据。这和第 38 课 prompt「读时校验是否被改」、第 44 课「请求那一刻才校验真实 IP」是同一种智慧——贴着「使用的那一刻」取最新状态，而不是依赖一个可能过期的快照。",
                    "en": "Caching a long-lived client clutching a sensitive token saves little, yet brings the real risk of 'using an expired/revoked credential': the token may invalidate via uninstall, reinstall, or rotation. Fetching the current token via fetchInstallation→decrypt each send always uses the freshest, most-valid credential. This is the same wisdom as Lesson 38's prompt 'validate-on-read whether it changed' and Lesson 44's 'check the real IP only at request time'—fetch the latest state right at the moment of use, not rely on a possibly-stale snapshot.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 给 Slack 发的告警不是一行纯文本，而是 Block Kit 富消息，且 buildMonitorAlertSlackMessage 会按 severity 给消息染色。这个「染色」的设计意图是？",
                    "en": "Langfuse's Slack alerts aren't plain text but Block Kit rich messages, and buildMonitorAlertSlackMessage tints them by severity. What's the design intent of this 'tinting'?",
                },
                "opts": [
                    {
                        "zh": "让人一眼看出严重度：ALERT 红、WARNING 黄、OK 绿——颜色是比文字更快的信号，频道里一片消息中红色告警最先抓住注意力，这是把「告警可读性/可操作性」做进投递层",
                        "en": "let people gauge severity at a glance: ALERT red, WARNING amber, OK green—color is a faster signal than text; among many channel messages a red alert grabs attention first, baking 'alert readability/actionability' into the delivery layer",
                    },
                    {"zh": "Slack 要求所有消息必须带颜色", "en": "Slack requires every message to have a color"},
                    {"zh": "颜色能压缩消息体积", "en": "color compresses message size"},
                    {"zh": "随机染色防止消息被折叠", "en": "random tinting prevents message collapsing"},
                ],
                "answer": 0,
                "why": {
                    "zh": "告警的价值不只在「送达」，更在「被快速正确地理解和响应」。同样的文字，配上红/黄/绿的颜色条，严重度一目了然——这是人因工程：颜色是比阅读文字更快的感知通道。Block Kit 还能加「在 Langfuse 中查看」按钮，让人一键跳到现场。把这些做进投递层，体现的是「通知不是把信息倒出去就完事，而是要让收信人最省力地行动」。这也是 Slack 相比裸 webhook「精致」的地方。",
                    "en": "An alert's value isn't only 'delivered' but 'quickly and correctly understood and acted on'. The same text with a red/amber/green color bar makes severity obvious at a glance—human-factors engineering: color is a faster perceptual channel than reading text. Block Kit also adds a 'View in Langfuse' button for one-click jump to the scene. Baking these into the delivery layer reflects 'a notification isn't done by dumping info out, but by making the recipient act with least effort'. This is also where Slack is 'refined' versus a naked webhook.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课指出：L45 几乎没有全新的基础设施，而是把前面攒下的加密(L39)、单例、游标分页、自动重试、BullMQ 队列这些零件，组装成一个体面的 Slack 集成。请回想你做过的项目：有没有哪个「看起来很新」的功能，其实是已有能力的重新组合？识别出这种「可复用的骨架」对一个工程团队意味着什么？过度追求复用又可能带来什么问题（错误的抽象、强行套用）？",
                "en": "This lesson notes: L45 has almost no brand-new infrastructure but assembles parts accumulated earlier—encryption (L39), singleton, cursor pagination, auto-retry, BullMQ queue—into a respectable Slack integration. Recall your own projects: was there a 'seemingly new' feature that was actually a recombination of existing capabilities? What does recognizing such 'reusable skeletons' mean for an engineering team? And what problems can over-pursuing reuse bring (wrong abstractions, forced fits)?",
            },
        ],
    },
    "46-analytics-integrations.html": {
        "mcq": [
            {
                "q": {
                    "zh": "分析集成把数据导出去，用的是「调度队列 + 处理队列」两级 fan-out，而不是「一个定时任务里 for 循环处理所有项目」。这样拆的主要好处是？",
                    "en": "Analytics integration exports data via a two-level fan-out of 'scheduling queue + processing queue', rather than 'a for-loop over all projects in one cron task'. The main benefit of this split is?",
                },
                "opts": [
                    {
                        "zh": "隔离+并行+可观测：项目A的导出失败/卡死不连累B/C(各自removeOnFail)；N个项目任务可被多worker并行消费而非串行；每项目instrumentAsync各开一条trace，出问题能精确定位到哪个项目哪一步",
                        "en": "isolation + parallelism + observability: project A's export failing/hanging doesn't drag down B/C (each removeOnFail itself); N project tasks can be consumed by multiple workers in parallel rather than serially; each project's instrumentAsync opens its own trace, so problems pinpoint which project, which step",
                    },
                    {"zh": "两级队列比一级队列省内存", "en": "two-level queues use less memory than one-level"},
                    {"zh": "Slack 要求所有导出都走两级队列", "en": "Slack requires all exports to use two-level queues"},
                    {"zh": "处理队列能自动加密数据", "en": "the processing queue auto-encrypts data"},
                ],
                "answer": 0,
                "why": {
                    "zh": "一个大任务串行处理所有项目，有三个致命问题：① 某项目报错或超慢，整个批次都受影响；② 无法利用多 worker 并行，项目一多就越拖越久；③ 所有项目混在一条执行流里，出问题难定位。拆成「调度清点 + 逐项目处理」后：失败的任务 removeOnFail 自己清掉、不挡别人；处理任务可被多 worker 并行抢；每个项目 instrumentAsync 各开一条 trace 独立观测。这套 fan-out 在第30课 eval、第43课计量里反复出现，是「对一批对象各做一遍」的标准答案。",
                    "en": "One big task serially processing all projects has three fatal problems: ① one project erroring or being very slow affects the whole batch; ② can't leverage multiple workers in parallel, so it drags on as projects grow; ③ all projects mixed in one execution flow, hard to pinpoint problems. Split into 'schedule-tally + per-project process': a failed task removeOnFails itself without blocking others; processing tasks are grabbed by multiple workers in parallel; each project's instrumentAsync opens its own trace for isolated observability. This fan-out recurs in Lesson 30 eval and Lesson 43 metering—the standard answer for 'do one pass over a batch of objects'.",
                },
            },
            {
                "q": {
                    "zh": "增量同步时，maxTimestamp 不取「当前时刻」，而是取 min(下一个UTC日界, 当前−30分钟)。这「退30分钟」和「按日切块」分别是为了解决什么？",
                    "en": "In incremental sync, maxTimestamp isn't 'now' but min(next UTC day boundary, now−30min). What do the 'back off 30 minutes' and 'chunk by day' each solve?",
                },
                "opts": [
                    {
                        "zh": "退30分钟：数据是陆续到达的(摄取有批处理/延迟)，取一个相对稳定的水位避免漏掉还在路上的在途事件；按日切块：给异常兜底——某集成停很久/老项目回填时 lastSyncAt 落后很多，一次性扫超大窗口会每次重扫巨量数据永远追不上，按天切既限单次工作量又对齐CH按天分区裁剪",
                        "en": "back off 30min: data arrives gradually (ingestion has batching/lag), so take a relatively stable watermark to avoid missing in-flight events still on the way; chunk by day: a safety net for anomalies—if an integration stopped long or backfills an old project, lastSyncAt lags far, scanning one giant window re-scans massive data each retry and never catches up; day-slicing bounds per-run work and aligns CH day-partition pruning",
                    },
                    {"zh": "都是为了让导出的数据更少", "en": "both are to export less data"},
                    {"zh": "都是 Mixpanel API 的硬性要求", "en": "both are hard requirements of the Mixpanel API"},
                    {"zh": "退30分钟是为了避开服务器高峰", "en": "backing off 30min avoids server peak hours"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这两个细节体现了增量同步的工程现实。「退30分钟」对应「数据不是瞬间齐的」：摄取链路有缓冲和延迟，紧贴此刻去查会漏掉马上要落库的事件，宁可慢一点也要不漏。「按日切块」对应「异常恢复要可控」：如果一个集成停了一周、或在一个老项目上首次全量，lastSyncAt 和现在差很远，若一次扫完这超大窗口，每小时重试都在啃巨量数据、可能永远追不上、还撑爆资源；切成一天一段后，每次只推进一天、工作量有上界，且正好命中 ClickHouse 按天分区，查得快。增量同步追求的是「稳稳推进一小步」，不是「一步到最新」。",
                    "en": "These two details reflect incremental sync's engineering reality. 'Back off 30min' addresses 'data isn't instantly complete': the ingestion path has buffering and lag; querying right up to now misses events about to land, so rather slower than miss. 'Chunk by day' addresses 'recovery must be controlled': if an integration stopped for a week, or first full-export on an old project, lastSyncAt is far from now; scanning that giant window at once means each hourly retry gnaws massive data, may never catch up, and blows resources; sliced into one-day chunks, each run advances one day with a bounded workload, and hits ClickHouse's day partitions for fast queries. Incremental sync aims for 'advance one small step steadily', not 'jump to the latest in one step'.",
                },
            },
            {
                "q": {
                    "zh": "Blob Storage 导出（可能导出海量历史数据到 S3）用的是 Node stream pipeline，一行行查、一行行转格式、流式写出，而不是先把整个结果集查进内存再写。这个选择最关键的原因是？",
                    "en": "Blob Storage export (possibly exporting massive history to S3) uses a Node stream pipeline—query row by row, transform row by row, write streaming—rather than loading the whole result set into memory first. The most critical reason for this choice is?",
                },
                "opts": [
                    {
                        "zh": "内存安全：导出量可能远超内存(几百万行)，若全装进内存会OOM崩溃；流式「翻一页处理一页、处理完即走」让内存占用恒定，无论导10行还是1亿行都不会撑爆",
                        "en": "memory safety: the export volume may far exceed memory (millions of rows); loading it all would OOM-crash; streaming 'process a page, move on' keeps memory constant, so whether exporting 10 rows or 100 million it won't blow up",
                    },
                    {"zh": "流式导出的数据更准确", "en": "streaming export produces more accurate data"},
                    {"zh": "S3 只接受流式上传", "en": "S3 only accepts streaming uploads"},
                    {"zh": "流式能自动去重数据", "en": "streaming auto-deduplicates data"},
                ],
                "answer": 0,
                "why": {
                    "zh": "「把整个结果集装进内存再处理」在数据量小时没问题，但导出场景的数据量可能是几百万、上亿行——一次性查进内存会直接 OOM 把进程打挂。流式处理（stream pipeline/Transform）的精髓是「数据像水一样流过」：查一行、转一行格式(CSV/JSON/JSONL)、写一行到 S3，处理完的行立即释放，内存占用与数据总量无关、恒定在一个小水平。这和第24课列表用游标分页、第38课不一次性加载所有 prompt 是同一种「面对不确定规模时，不要把全部装进内存」的工程纪律。",
                    "en": "'Load the whole result set into memory then process' is fine when small, but export volumes can be millions or hundreds of millions of rows—loading at once directly OOM-kills the process. The essence of streaming (stream pipeline/Transform) is 'data flows like water': query a row, transform a row's format (CSV/JSON/JSONL), write a row to S3, releasing processed rows immediately, so memory is independent of total volume, constant at a small level. This is the same 'when facing uncertain scale, don't load everything into memory' discipline as Lesson 24's cursor pagination and Lesson 38's not loading all prompts at once.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课的分析集成体现了「往外导数据」的三件套：两级 fan-out（隔离+并行+可观测）、lastSyncAt 增量水位（只导新数据、留缓冲、按日切块）、流式导出（内存安全）。请设想：如果让你给一个系统设计「定期把数据同步到外部」的功能，这三条你会怎么取舍和组合？哪些场景可以省掉其中一两条（比如数据量很小、或要求强实时）？增量水位若遇到「数据可能被回溯修改」（不只是追加）又会带来什么新难题？",
                "en": "This lesson's analytics integration embodies the trio for 'exporting data out': two-level fan-out (isolation+parallelism+observability), lastSyncAt incremental watermark (only new data, leave buffer, chunk by day), streaming export (memory safety). Imagine: if you designed a 'periodically sync data to external' feature for a system, how would you weigh and combine these three? Which scenarios let you drop one or two (e.g. tiny data volume, or strong real-time requirement)? And if the incremental watermark meets 'data may be retroactively modified' (not just appended), what new difficulty arises?",
            },
        ],
    },
    "47-batch-exports-and-actions.html": {
        "mcq": [
            {
                "q": {
                    "zh": "批量导出和批量操作看着很不同（一个产文件、一个改数据），但这一课强调它们共享同一套工程骨架。这套共同骨架是什么？",
                    "en": "Batch export and batch action look quite different (one produces a file, one mutates data), yet this lesson stresses they share one engineering skeleton. What is that shared skeleton?",
                },
                "opts": [
                    {
                        "zh": "都基于一个可能命中海量行的过滤条件、都因耗时长而走队列异步(有状态机可追踪)、都用流式+分块避免一次性把几万行装进内存——区别只在『只读产文件』vs『改数据』",
                        "en": "both build on a filter that may match massive rows, both go async via queue for being slow (with a trackable state machine), both use streaming + chunking to avoid loading tens of thousands of rows into memory at once—the only difference is 'read-only produces a file' vs 'mutates data'",
                    },
                    {"zh": "都把数据加密后存储", "en": "both encrypt data before storing"},
                    {"zh": "都只能在自托管版使用", "en": "both only work in self-host"},
                    {"zh": "都需要用户付费解锁", "en": "both require paid unlock"},
                ],
                "answer": 0,
                "why": {
                    "zh": "识别「不同功能的共同骨架」是这一课的核心。批量导出（只读）和批量操作（改数据）表面差异大，但都面对同样两个工程现实：① 数据量可能极大（命中几万行）→ 必须流式 + 分块，不能全装内存；② 处理耗时长 → 不能卡在 HTTP 请求里，必须扔进队列异步跑，并用状态机（BatchExportStatus / BatchActionStatus）让用户能追踪进度。看穿这层共性，你就知道：凡是『对一大票数据整体做一件事』的需求，都该往这个骨架上套。",
                    "en": "Recognizing 'the shared skeleton of different features' is this lesson's core. Batch export (read-only) and batch action (mutating) look very different but face the same two engineering realities: ① data volume may be enormous (matching tens of thousands of rows) → must stream + chunk, not all-in-memory; ② processing is slow → can't block an HTTP request, must run async on a queue, with a state machine (BatchExportStatus / BatchActionStatus) so users can track progress. See through this commonality and you know: any 'do one thing to a whole batch of data' need should map onto this skeleton.",
                },
            },
            {
                "q": {
                    "zh": "批量操作的源码在 processActionChunk 上方顶着一句醒目注释：「所有操作必须幂等。任务失败会重试，重试时已处理过的块可能被再处理一遍。」为什么幂等在这里是「硬约束」而非「最好做到」？",
                    "en": "The batch action source pins a conspicuous comment atop processActionChunk: 'All operations must be idempotent. The job retries on failure, and on retry chunks already processed may be processed again.' Why is idempotency a 'hard constraint' here, not 'nice to have'?",
                },
                "opts": [
                    {
                        "zh": "因为它和「队列会重试」正面相撞：删5万行分50块，跑到第30块崩了，BullMQ 会重发整个任务(它不知道内部跑到第几块)，前29块会被再执行一遍——若删除/加队列不幂等，要么重试直接失败任务卡死，要么同批数据被加两次",
                        "en": "because it collides head-on with 'queues retry': deleting 50k rows in 50 chunks, crash at chunk 30, BullMQ re-dispatches the whole job (it doesn't know which chunk you reached), the first 29 rerun—if delete/add-to-queue isn't idempotent, either the retry fails outright and the job sticks, or the same batch gets added twice",
                    },
                    {"zh": "因为幂等能让任务跑得更快", "en": "because idempotency makes the job run faster"},
                    {"zh": "因为数据库要求所有写操作幂等", "en": "because the database requires all writes to be idempotent"},
                    {"zh": "因为幂等能节省存储空间", "en": "because idempotency saves storage space"},
                ],
                "answer": 0,
                "why": {
                    "zh": "队列的「失败重试」是可靠性的来源，但它和「批量改数据」相遇时产生一个尖锐后果：重试是把整个任务重发，而任务内部已经跑完的块，队列并不知道、也会跟着重跑。于是每个 action 都活在「可能被重复调用」的世界里。如果不幂等：删一个已删的 id 抛异常 → 重试永远失败、任务卡死；把一批 trace 重复加进标注队列 → 数据被污染。所以幂等是「在会重试的系统里保证正确」的前提，不是可选项。这与第43课计量「恰好一次」、第30课 eval 去重，都是对『分布式不可靠』的同一种清醒。",
                    "en": "A queue's 'retry on failure' is the source of reliability, but meeting 'bulk data mutation' yields a sharp consequence: a retry re-dispatches the whole job, and the chunks already done inside it—the queue doesn't know, and reruns them too. So every action lives in a world where 'it may be called again.' Without idempotency: deleting an already-deleted id throws → the retry fails forever, job stuck; re-adding a batch of traces to the annotation queue → data polluted. So idempotency is the precondition for 'correctness in a retrying system', not optional. Same clarity about 'distributed unreliability' as Lesson 43's 'exactly once' and Lesson 30's eval dedup.",
                },
            },
            {
                "q": {
                    "zh": "批量导出完成后，给用户的是一个带过期时间的「签名 URL」，而不是一个永久公开的下载地址。这个设计主要在防什么？",
                    "en": "After a batch export completes, the user gets a time-limited 'signed URL' rather than a permanently-public download address. What does this design mainly guard against?",
                },
                "opts": [
                    {
                        "zh": "防敏感数据被永久泄露：导出文件常含用户trace/输入输出/PII，永久公开链接一旦被转发/记日志/缓存，就等于把数据永久敞开给任何拿到链接的人；签名URL是带加密签名和过期时间的临时授权，expiresAt一到自动失效",
                        "en": "guards against permanent leakage of sensitive data: export files often contain users' traces/inputs-outputs/PII; a permanent public link, once forwarded/logged/cached, opens the data forever to anyone with the link; a signed URL is temporary authorization with a cryptographic signature and expiry, auto-invalidating once expiresAt passes",
                    },
                    {"zh": "防止文件占用太多存储", "en": "prevents files from using too much storage"},
                    {"zh": "防止下载速度太慢", "en": "prevents slow download speed"},
                    {"zh": "防止用户重复下载", "en": "prevents users downloading repeatedly"},
                ],
                "answer": 0,
                "why": {
                    "zh": "导出的本质是把一批（往往敏感的）数据打包成一个可下载文件。如果给的是永久公开 URL，这个链接就成了数据的「长期后门」：它可能被贴进聊天、写进日志、被代理缓存，之后任何拿到它的人都能下载——相当于把这批数据永久泄露。签名 URL 的设计是「临时、可收回的授权」：URL 里嵌入加密签名和 expiresAt，过期即失效，BatchExport 记录也存着 expiresAt 备查。背后的安全原则是：对敏感数据的访问，默认应该是有时限、可收回的，而不是一次给出、永久敞开。",
                    "en": "An export essentially packages a batch of (often sensitive) data into a downloadable file. A permanent public URL becomes a 'long-term backdoor' to that data: it may be pasted into chats, written to logs, cached by proxies, and anyone who later gets it can download—effectively a permanent leak. A signed URL is 'temporary, revocable authorization': the URL embeds a cryptographic signature and expiresAt, invalidating on expiry, and the BatchExport record stores expiresAt for audit. The security principle: access to sensitive data should default to time-bound and revocable, not given-once and open-forever.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课是第九部分（自动化与集成）的收官：从 webhook/SSRF（L44）、Slack（L45）、分析集成（L46）到批量导出与操作（L47），主线是「把平台数据安全、可靠、可控地与外部世界连接」。回看这四课，你能总结出几条反复出现的『与外部世界打交道』的工程原则吗（如：不可信输入要纵深防御、敏感凭据/数据要加密与限时、耗时大活要队列+流式、会重试就必须幂等）？这些原则在你自己做过的『对接外部系统』里，哪些被遵守了、哪些被忽略并酿成过问题？",
                "en": "This lesson closes Part 9 (Automation & Integrations): from webhook/SSRF (L44), Slack (L45), analytics integrations (L46) to batch export & actions (L47), the through-line is 'connecting platform data to the outside world securely, reliably, controllably.' Reviewing these four lessons, can you distill a few recurring engineering principles for 'dealing with the outside world' (e.g.: untrusted input needs defense-in-depth, sensitive credentials/data need encryption and time-limits, slow big jobs need queue+streaming, anything that retries must be idempotent)? In your own 'integrate with external systems' work, which were honored, and which were ignored and caused problems?",
            },
        ],
    },
    "48-auth-and-sessions.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的密码登录里有一段「看似浪费」的代码：当用户邮箱在库里查不到时，仍然照样调用一次 hashPassword 再返回「Invalid credentials」。这段代码的目的是？",
                    "en": "Langfuse's password login has a 'seemingly wasteful' bit: when the email isn't found in the DB, it still calls hashPassword once before returning 'Invalid credentials'. What's the purpose?",
                },
                "opts": [
                    {
                        "zh": "防时序攻击下的用户枚举：bcrypt故意慢，若「用户不存在」秒回而「密码错」要慢慢算，两条失败路径耗时差异会让攻击者靠响应快慢判断某邮箱是否注册过；让两路耗时相近就堵住了这个旁路",
                        "en": "defeats user enumeration via timing attack: bcrypt is deliberately slow; if 'user absent' returns instantly while 'wrong password' runs the slow hash, the time difference lets an attacker tell whether an email is registered by response speed; making both paths take similar time closes this side channel",
                    },
                    {"zh": "为了给数据库预热缓存", "en": "to warm up the database cache"},
                    {"zh": "为了记录登录失败日志", "en": "to record a login-failure log"},
                    {"zh": "为了兼容旧版密码格式", "en": "for compatibility with the legacy password format"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是安全工程里「错误也要长得一样、慢得一样」的经典实践。bcrypt 被设计成计算慢（12 轮）以抵抗暴力破解。但这个「慢」会泄露信息：如果只有「用户存在」时才走 bcrypt，攻击者拿一批邮箱来登，响应明显慢的就是已注册的——不费密码就能枚举出「谁在你这注册过」，既是隐私泄露也是撞库弹药。对策是让「用户不存在」这条路也白算一遍 hash，使两条失败路径耗时相近，时序侧信道就被堵死。许多登录实现忽略了这一点。",
                    "en": "This is the classic 'errors should look the same and take the same time' practice in security engineering. bcrypt is designed slow (12 rounds) to resist brute force. But that slowness leaks info: if only 'user exists' runs bcrypt, an attacker logging in with a batch of emails sees the noticeably-slow ones as registered—enumerating 'who's registered here' without any password, a privacy leak and credential-stuffing ammo. The countermeasure is to run a throwaway hash on the 'user absent' path too, making both failure paths take similar time and closing the timing side channel. Many login implementations miss this.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的会话用 JWT（session.strategy:\"jwt\"）而不是把 session 存在数据库里。在多实例水平扩展的部署下，JWT 的核心优势是？",
                    "en": "Langfuse's session uses JWT (session.strategy:\"jwt\") rather than storing sessions in a database. Under a multi-instance horizontally-scaled deployment, JWT's core advantage is?",
                },
                "opts": [
                    {
                        "zh": "无状态：身份信息直接印在凭证里并用密钥签名防篡改，任一web实例本地验签即可确认「你是谁」，无需每次请求都回头查共享session存储——后者在多实例下会成为瓶颈和单点",
                        "en": "stateless: identity info is printed on the credential and key-signed against tampering, so any web instance can verify locally to confirm 'who you are' without a per-request lookup to shared session storage—which under multi-instance becomes a bottleneck and single point",
                    },
                    {"zh": "JWT 永远不会过期，更省心", "en": "JWT never expires, more convenient"},
                    {"zh": "JWT 能存更多数据", "en": "JWT can store more data"},
                    {"zh": "JWT 比数据库查询更安全", "en": "JWT is more secure than a database query"},
                ],
                "answer": 0,
                "why": {
                    "zh": "数据库 session 的做法是发个随机 id、把「id→用户」存库，每次请求都拿 id 回库查。单机没问题，但 Langfuse 跑多个 web 实例横向扩展时，这个共享 session 存储就成了每请求都要访问的瓶颈和单点。JWT 把身份直接写进凭证、用密钥签名防篡改，任一实例本地验签就能确认身份，无需查库——这正是无状态架构能水平扩展的关键。代价是即时吊销变难（凭证发出后在有效期内一直有效），所以配一个不长的 maxAge 折中。这是一个典型的「用一点可控性换取扩展性」的权衡。",
                    "en": "A DB session issues a random id, stores 'id→user' in the DB, and queries the DB by id on every request. Fine on one machine, but when Langfuse runs multiple web instances for horizontal scaling, that shared session store becomes a per-request bottleneck and single point. JWT writes identity into the credential and signs it against tampering, so any instance verifies locally to confirm identity without a DB lookup—the key to a stateless, horizontally-scalable architecture. The cost is harder instant revocation (an issued credential stays valid through its window), so a not-too-long maxAge splits the difference. A classic 'trade a bit of control for scalability'.",
                },
            },
            {
                "q": {
                    "zh": "NextAuth 的 session 回调在每次构建会话时，会查出用户的 organizationMemberships→projects 和 ProjectMemberships 并塞进 session 对象。这一步在整个鉴权/授权体系里扮演什么角色？",
                    "en": "NextAuth's session callback, on each session build, queries the user's organizationMemberships→projects and ProjectMemberships and stuffs them into the session object. What role does this step play in the whole authn/authz system?",
                },
                "opts": [
                    {
                        "zh": "它是把「你是谁」(鉴权)接到「你能干什么」(授权/RBAC)的那根线：把用户的组织/项目成员关系和角色注入会话，下一课的 throwIfNoProjectAccess 正是读这里注入的角色来判断 scope 权限",
                        "en": "it's the wire connecting 'who you are' (authn) to 'what you can do' (authz/RBAC): it injects the user's org/project memberships and roles into the session, and the next lesson's throwIfNoProjectAccess reads exactly these injected roles to judge scope permissions",
                    },
                    {"zh": "它只是为了在页面上显示用户名", "en": "it's just to display the username on the page"},
                    {"zh": "它负责给用户的密码加密", "en": "it's responsible for encrypting the user's password"},
                    {"zh": "它决定用户能用哪些 SSO 提供商", "en": "it decides which SSO providers the user can use"},
                ],
                "answer": 0,
                "why": {
                    "zh": "鉴权（authentication）回答「你是谁」，授权（authorization/RBAC）回答「你能干什么」，两者需要一座桥把前者的结果交给后者。Langfuse 的这座桥就是 session 回调：登录确认身份后，它顺手把「该用户属于哪些组织、哪些项目、在每处是什么角色」查出来注入会话。于是后续任何一次权限判断（下一课的 throwIfNoProjectAccess / useHasProjectAccess）都能直接从会话里读到角色，再据角色→scope 映射判定能否执行某操作。没有这一步注入，RBAC 就拿不到判断所需的输入。",
                    "en": "Authentication answers 'who you are', authorization/RBAC answers 'what you can do', and a bridge must hand the former's result to the latter. Langfuse's bridge is the session callback: after login confirms identity, it conveniently queries 'which orgs, which projects, what role in each' and injects them into the session. So any later permission check (next lesson's throwIfNoProjectAccess / useHasProjectAccess) reads the role straight from the session, then judges via the role→scope map whether an action is allowed. Without this injection step, RBAC wouldn't have the input it needs.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课展示了 Langfuse 对「邮箱密码登录」这条最朴素的路堆了一圈安全护栏：SSO 强制、时序攻击防护、SSO 用户拦截、bcrypt 加盐慢哈希。请结合你的经验谈谈：为什么「自己实现密码登录」常被认为是危险且容易出错的？这一课的哪些细节是你以前没意识到要做的？如果让你在「自建密码体系」与「全部交给 SSO/IdP」之间为一个新产品做选择，你会怎么权衡（安全、合规、用户体验、实现成本）？",
                "en": "This lesson shows Langfuse piling a ring of guardrails on the plainest 'email-password login' path: SSO enforcement, timing-attack defense, SSO-user interception, bcrypt salted slow hashing. Drawing on your experience: why is 'rolling your own password login' often considered dangerous and error-prone? Which details here had you not realized were needed? If choosing for a new product between 'building your own password system' and 'delegating entirely to SSO/IdP', how would you weigh it (security, compliance, UX, implementation cost)?",
            },
        ],
    },
    "49-rbac-apikeys-scim.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 的 RBAC 把权限判断写成「你的角色里有没有这个 scope」（如 traces:delete），而不是「你是不是 OWNER/ADMIN」。这种「角色→scope」间接层的主要好处是？",
                    "en": "Langfuse's RBAC writes the permission check as 'does your role contain this scope' (e.g. traces:delete), rather than 'are you OWNER/ADMIN'. The main benefit of this 'role→scope' indirection is?",
                },
                "opts": [
                    {
                        "zh": "解耦与可维护：功能代码只问「有没有某 scope」，加新功能只需在角色定义里给相关角色添一个 scope，不必到处去改散落的「if 角色==X」判断；权限模型集中在一张 Record<Role,Scope[]> 表里，清晰可审计",
                        "en": "decoupling and maintainability: feature code only asks 'has this scope', adding a feature just adds a scope to relevant roles in the role definition, no editing scattered 'if role==X' checks everywhere; the permission model is centralized in one Record<Role,Scope[]> table, clear and auditable",
                    },
                    {"zh": "scope 比角色判断运行更快", "en": "scope checks run faster than role checks"},
                    {"zh": "这样可以不需要角色了", "en": "this eliminates the need for roles"},
                    {"zh": "scope 字符串能压缩存储", "en": "scope strings compress storage"},
                ],
                "answer": 0,
                "why": {
                    "zh": "如果到处写「if (role === 'OWNER' || role === 'ADMIN')」，每加一个功能、每调一次权限，都要翻遍代码找这些散落的判断，极易漏改、错配。引入 scope 间接层后：每个功能只关心一个细粒度权限点（traces:delete），而「哪个角色拥有哪些 scope」集中在 projectRoleAccessRights 一张表里维护。加功能=给角色添 scope，调权限=改这张表，判断逻辑（hasProjectAccess）则完全通用。这是「用一层间接换取可维护性与可审计性」的经典做法——也让「这个角色到底能干什么」一目了然。",
                    "en": "If you write 'if (role === OWNER || role === ADMIN)' everywhere, every new feature and every permission tweak means combing the code for these scattered checks—easy to miss or misconfigure. With the scope indirection: each feature cares about one fine-grained point (traces:delete), while 'which role has which scopes' is maintained centrally in the projectRoleAccessRights table. Add a feature = add a scope to a role; tweak permissions = edit the table; the check logic (hasProjectAccess) stays fully generic. A classic 'a layer of indirection for maintainability and auditability'—and it makes 'what exactly can this role do' obvious at a glance.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 为每个 API key 存了两种哈希：fastHashedSecretKey（sha256）和 hashedSecretKey（bcrypt）。为什么不能只用 bcrypt 一种？",
                    "en": "Langfuse stores two hashes per API key: fastHashedSecretKey (sha256) and hashedSecretKey (bcrypt). Why not just use bcrypt alone?",
                },
                "opts": [
                    {
                        "zh": "因为bcrypt每次加随机盐、结果不确定，没法当数据库查找键(只能逐行compare，O(n))，而API认证极高频必须O(1)查到；sha256确定性、同key恒定值，能直接当索引/缓存键一步查到，且哈希的是密钥本身+盐故泄露也反推不出——两者分工：sha查得快、bcrypt存得安全",
                        "en": "because bcrypt adds a random salt each time with a nondeterministic result, unusable as a DB lookup key (only row-by-row compare, O(n)), while API auth is extremely high-frequency and must find it in O(1); sha256 is deterministic, same key→constant value, usable directly as an index/cache key for one-step lookup, and it hashes the secret itself + salt so a leak can't reverse it — the two divide labor: sha for fast lookup, bcrypt for secure storage",
                    },
                    {"zh": "bcrypt 已经过时，必须配 sha256", "en": "bcrypt is obsolete and must be paired with sha256"},
                    {"zh": "两种哈希是为了双重加密更安全", "en": "two hashes double-encrypt for more security"},
                    {"zh": "sha256 用于公钥、bcrypt 用于私钥", "en": "sha256 for the public key, bcrypt for the secret key"},
                ],
                "answer": 0,
                "why": {
                    "zh": "「快查」和「抗暴破」是一对矛盾。bcrypt 为抗暴破刻意慢、且每次盐不同，导致同一 key 的 bcrypt 值不固定——你无法拿它做 WHERE 查找，只能扫全表逐行 compare，而 API 认证每条 trace 都要验一次 key，O(n) 扫表是灾难。sha256(key,SALT) 是确定性的：同一 key 永远同一值，能直接建索引、当 Redis 缓存键，O(1) 命中；又因为算的是「密钥本身」（高熵、不可枚举）加盐，库泄露也无法反推原 key。于是分工：sha256 负责「在海量 key 里快速定位是哪把」，bcrypt 负责老格式 key 的加盐慢验证。这正是「当快与安全冲突时，用两种工具各管一段」。",
                    "en": "'Fast lookup' and 'brute-force resistance' conflict. bcrypt is deliberately slow for brute-force resistance and salted differently each time, so a key's bcrypt value isn't fixed—you can't use it in a WHERE lookup, only a full-table row-by-row compare, and since API auth verifies a key per trace, an O(n) scan is a disaster. sha256(key,SALT) is deterministic: same key→same value, usable as an index or Redis cache key for an O(1) hit; and since it hashes 'the secret itself' (high-entropy, non-enumerable) plus salt, a store leak can't reverse the key. So they divide labor: sha256 quickly locates which key among millions, bcrypt does salted slow verification for legacy keys. Exactly 'when fast and secure conflict, use two tools each owning a segment'.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的同一个权限点（如「删除 trace」）在前端用 useHasProjectAccess、后端用 throwIfNoProjectAccess 各查一遍。关于这两道校验，哪种说法正确？",
                    "en": "Langfuse checks the same permission point (e.g. 'delete trace') in both front end (useHasProjectAccess) and back end (throwIfNoProjectAccess). Which statement about these two checks is correct?",
                },
                "opts": [
                    {
                        "zh": "后端那道是真正不可绕过的安全闸(跑在服务器上)，前端那道只是体验优化(隐藏没权限的按钮)；前端校验绝不能当安全，因为前端代码在用户浏览器里可被改、可直接构造请求绕过UI——前端隐藏必须始终有后端强制兜底",
                        "en": "the back-end check is the truly un-bypassable security gate (runs on the server), the front-end check is only UX (hide buttons without access); a front-end check is never security because front-end code runs in the user's browser, can be modified, and requests can be crafted to bypass the UI — front-end hiding must always have back-end enforcement behind it",
                    },
                    {"zh": "两道校验完全重复，可以删掉后端那道省性能", "en": "the two checks are fully redundant; drop the back-end one to save performance"},
                    {"zh": "前端那道是安全闸，后端只是辅助", "en": "the front-end check is the security gate, the back end is auxiliary"},
                    {"zh": "只要前端隐藏了按钮，接口就自动安全了", "en": "once the front end hides the button, the endpoint is automatically secure"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是 Web 安全里最常见也最致命的误区之一。前端代码（包括权限判断）整个运行在用户的浏览器里，用户可以打开开发者工具改它、可以绕过 UI 直接对后端接口构造请求。所以前端的 useHasProjectAccess「隐藏按钮」只是体验优化（让你看不到点不了的功能、不吃无谓的报错），绝不构成安全边界。真正挡住越权的，是后端每个 tRPC resolver 里的 throwIfNoProjectAccess——它跑在你控制的服务器上、不可绕过。许多越权漏洞正源于「只在前端藏了按钮，后端却忘了校验」，以为按钮没了就进不去，实则接口裸奔。原则：前端隐藏是礼貌，后端强制才是安全，两者必须同时在。",
                    "en": "This is one of the most common and fatal misconceptions in web security. Front-end code (including permission checks) runs entirely in the user's browser; the user can open dev tools to modify it or bypass the UI to craft requests straight to the back end. So the front-end useHasProjectAccess 'hide button' is only UX (you don't see unusable features or eat pointless errors), never a security boundary. What truly blocks escalation is throwIfNoProjectAccess in every back-end tRPC resolver—it runs on your controlled server and is un-bypassable. Many escalation bugs come precisely from 'hiding a button on the front end but forgetting the back-end check', thinking no button means no entry while the endpoint runs naked. Principle: front-end hiding is politeness, back-end enforcement is security, both must be present.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课把授权拆成两类对象（人走 RBAC、机器走 API key）外加 SCIM，背后是「最小权限 + 纵深防御」两条信条。请结合你做过的系统想一想：你的权限模型是「角色→scope」这种细粒度的，还是粗放的「管理员/普通用户」两档？两层哈希这种「为不同目的存同一秘密的多种派生物」的思路，在你别的场景里（如缓存、去重、索引）有没有类似的影子？如果要给一个新系统设计 API key 体系，你会怎么平衡安全、查询性能和可吊销性？",
                "en": "This lesson splits authorization into two subjects (humans via RBAC, machines via API keys) plus SCIM, underpinned by 'least privilege + defense in depth'. Reflect on systems you've built: is your permission model fine-grained 'role→scope', or coarse 'admin/regular user' two-tier? Does the two-tier-hash idea of 'storing multiple derivatives of the same secret for different purposes' echo elsewhere in your work (caching, dedup, indexing)? If designing an API key system for a new product, how would you balance security, query performance, and revocability?",
            },
        ],
    },
    "50-open-core-and-entitlements.html": {
        "mcq": [
            {
                "q": {
                    "zh": "关于 Langfuse 的 open-core 模式，下面哪种理解是正确的？",
                    "en": "Regarding Langfuse's open-core model, which understanding is correct?",
                },
                "opts": [
                    {
                        "zh": "整个仓库的代码全是开源的（包括审计日志、数据保留等企业功能），免费与付费的区别只在「运行时这个组织的 plan 能不能启用某功能」，而不在「代码是否公开」——能不能用与有没有代码彻底解耦",
                        "en": "the entire repo's code is all open source (including enterprise features like audit logs, data retention); free vs paid lies only in 'whether this org's plan can enable a feature at runtime', not in 'whether the code is public'—can-use and has-code are fully decoupled",
                    },
                    {"zh": "企业功能的代码是闭源的，开源的只有核心部分", "en": "enterprise-feature code is closed; only the core is open"},
                    {"zh": "所有功能都免费，Langfuse 靠捐赠盈利", "en": "all features are free; Langfuse profits from donations"},
                    {"zh": "付费功能在编译时被移除，开源版没有这些代码", "en": "paid features are stripped at compile time; the open-source version lacks the code"},
                ],
                "answer": 0,
                "why": {
                    "zh": "open-core 常被误解为「一半开源一半闭源」，但 Langfuse 不是：连审计日志、数据保留、多租户 SSO 这些企业功能的代码都在公开仓库里（ee/ 与 shared/.../ee/），你能读、能学、能自己改。真正划出商业边界的，是一层轻薄的运行时门控——组织挂的 plan + hasEntitlement 闸。所以「能不能用」取决于你的 plan，而非「代码在不在」。这种把代码透明性与商业可持续性同时拿到的设计，正是 open-core 的精巧之处：100% 公开 + 一层 entitlement 门控。",
                    "en": "Open-core is often misread as 'half open, half closed', but Langfuse isn't: even audit logs, data retention, multi-tenant SSO code is in the public repo (ee/ and shared/.../ee/)—you can read, learn, modify it. What actually draws the commercial boundary is a thin runtime gate—the org's plan + hasEntitlement. So 'can use' depends on your plan, not 'does the code exist'. This design—getting code transparency and commercial sustainability at once—is open-core's elegance: 100% public + a layer of entitlement gating.",
                },
            },
            {
                "q": {
                    "zh": "hasEntitlement 在找不到组织的 plan 时，用 `org?.plan ?? \"oss\"` 兜底成免费的 oss，而不是默认报错或默认给最高权限。这个默认值的选择体现了什么原则？",
                    "en": "When hasEntitlement can't find an org's plan, it falls back to free oss via `org?.plan ?? \"oss\"`, rather than erroring or defaulting to highest privileges. What principle does this default reflect?",
                },
                "opts": [
                    {
                        "zh": "fail-safe（失败安全）默认：默认值应是「权限最小、影响最轻」的那个。若默认给最高权限，plan 因 bug/迁移读不到时会意外解锁所有付费功能(漏损+越权)；兜底到 oss 则开源用户开箱即用、付费功能默认关——与登录默认拒、IP解析失败默认拦同源",
                        "en": "fail-safe default: the default should be 'least privilege, lightest impact'. Defaulting to highest privileges would accidentally unlock all paid features when plan can't be read due to a bug/migration (leak + overreach); falling back to oss lets open-source users work out of the box with paid features off by default—same lineage as login-defaults-deny, IP-resolution-failure-defaults-block",
                    },
                    {"zh": "为了让代码更短", "en": "to make the code shorter"},
                    {"zh": "oss 查询比其他 plan 快", "en": "oss queries are faster than other plans"},
                    {"zh": "为了兼容老版本数据库", "en": "for compatibility with old database versions"},
                ],
                "answer": 0,
                "why": {
                    "zh": "默认值的方向是个安全决策。设想 plan 字段因某个 bug、数据迁移、或字段缺失而读不到：若默认给最高权限，这个组织会瞬间解锁所有付费功能——商业上是漏损、安全上是越权；若默认报错，又会让绝大多数本就是 oss 的自托管开源用户用不了。兜底到 oss 两全：开源用户(最常见路径)开箱即用，付费功能默认关、必须由明确 plan/license 主动打开。这与第44课「IP 解析失败默认拦截」、第48课「登录默认拒绝」是同一条 fail-safe 原则——拿不准时，选权限最小、影响最轻的那个默认。",
                    "en": "The direction of a default is a security decision. Suppose the plan field can't be read due to a bug, data migration, or missing field: defaulting to highest privileges instantly unlocks all paid features for that org—a commercial leak and a privilege overreach; defaulting to error stalls the vast majority of self-hosted open-source users who are oss anyway. Falling back to oss gets both: open-source users (the common path) work out of the box, paid features off by default, opened only by an explicit plan/license. Same fail-safe principle as Lesson 44's 'IP-resolution failure defaults to block' and Lesson 48's 'login defaults to deny'—when unsure, pick the least-privilege, lightest-impact default.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 把「哪个 plan 能用哪些功能」收进一张声明式的 entitlementAccess 总表，所有功能门口只调同一个 hasEntitlement 闸，而不是在各功能里散写「if plan==pro」。这样做最大的好处是？",
                    "en": "Langfuse folds 'which plan can use which features' into one declarative entitlementAccess master table, with every feature calling the same hasEntitlement gate, rather than scattering 'if plan==pro' across features. The biggest benefit is?",
                },
                "opts": [
                    {
                        "zh": "把易变的商业规则从稳定的功能逻辑里抽出、集中声明：加套餐/调额度/把功能从pro下放到core，只需改总表一行，功能代码不动；想知道某plan包含什么，读表一行即可——便于演进与审计，避免散落判断改漏改错",
                        "en": "extracting volatile commercial rules from stable feature logic and declaring them centrally: adding a tier/adjusting a quota/demoting a feature from pro to core needs editing one table row, feature code untouched; to know what a plan includes, read one row—easing evolution and auditing, avoiding scattered checks being missed or mis-edited",
                    },
                    {"zh": "总表查询比散落的 if 判断运行更快", "en": "the master table runs faster than scattered if checks"},
                    {"zh": "这样就不需要 plan 概念了", "en": "this eliminates the need for the plan concept"},
                    {"zh": "总表能自动生成计费账单", "en": "the master table auto-generates billing invoices"},
                ],
                "answer": 0,
                "why": {
                    "zh": "商业 plan 是会频繁变动的：加一档套餐、调一次额度、把某功能从 pro 下放到 core，都很常见。如果「pro 才能用 X」散落在几十处功能代码里，每次调整都要全仓搜改，极易漏、易错、还难复盘「到底哪个 plan 能用什么」。收进一张声明式总表后：改商业策略=改表的一行，功能代码完全不动；查「pro 包含什么」=读表一行。这与第49课 RBAC 用「角色→scope」总表是同一种智慧——把易变规则从稳定逻辑里抽出、集中声明，让系统能跟上商业节奏，也让权限/权益一目了然、可审计。",
                    "en": "Commercial plans change frequently: adding a tier, adjusting a quota, demoting a feature from pro to core are all common. If 'only pro can use X' is scattered across dozens of feature sites, every change means a repo-wide search-and-edit—easy to miss, error-prone, hard to review 'which plan can use what'. Folded into one declarative master table: change strategy = edit one row, feature code untouched; check 'what pro includes' = read one row. Same wisdom as Lesson 49's RBAC 'role→scope' table—extract volatile rules from stable logic and declare centrally, keeping the system in step with the business and making permissions/entitlements auditable at a glance.",
                },
            },
        ],
        "open": [
            {
                "zh": "open-core 让 Langfuse「代码全公开 + 商业可持续」两者兼得：100% 开源，靠一层轻薄的运行时门控（plan + entitlement + license）划出商业边界。请谈谈你的看法：相比「纯开源（全免费）」和「纯闭源（全收费）」，open-core 在商业与社区之间的取舍是什么？它对使用者（能读到全部代码、能自托管、但企业功能要授权）是更友好还是更受限？如果你要把一个项目商业化，会选哪种模式，为什么？",
                "en": "Open-core lets Langfuse have both 'fully public code + commercial sustainability': 100% open source, with a thin runtime gate (plan + entitlement + license) drawing the commercial boundary. Share your view: versus 'pure open source (all free)' and 'pure closed (all paid)', what trade-off does open-core strike between business and community? For users (can read all the code, can self-host, but enterprise features need a license), is it friendlier or more restrictive? If commercializing a project of your own, which model would you choose, and why?",
            },
        ],
    },
    "51-self-observability-and-config.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 本身就是一个 LLM 可观测性平台，但它内部还到处用 OpenTelemetry（instrumentAsync 等）观测自己。关于这种「dogfooding（吃自己的狗粮）」，下面哪种说法最准确？",
                    "en": "Langfuse is itself an LLM observability platform, yet internally it uses OpenTelemetry (instrumentAsync etc.) to observe itself everywhere. Which statement about this 'dogfooding' is most accurate?",
                },
                "opts": [
                    {
                        "zh": "它既是最严苛的自测(每天用自己产品扛自己负载，毛病第一个最痛地暴露)，技术上又极顺滑(本就讲OTel这门语言、能摄取OTel，观测自己复用同一套trace/span概念近零额外成本)，还逼着把instrumentAsync打磨成包一下就行的薄包装",
                        "en": "it's both the most rigorous self-test (running its own product under its own load daily, flaws surface first and most painfully) and technically seamless (it already speaks OTel and can ingest OTel, so observing itself reuses the same trace/span concepts at near-zero extra cost), and it forces instrumentAsync to be polished into a thin wrap-once wrapper",
                    },
                    {"zh": "只是为了营销，技术上没有实际意义", "en": "purely for marketing, with no real technical meaning"},
                    {"zh": "因为 OTel 是唯一能用的可观测方案", "en": "because OTel is the only available observability option"},
                    {"zh": "为了让代码看起来更复杂、更专业", "en": "to make the code look more complex and professional"},
                ],
                "answer": 0,
                "why": {
                    "zh": "dogfooding 在 Langfuse 这里有三重价值。其一，最真实的自测：当团队每天用自己的产品扛自己的生产流量，产品的卡顿、缺陷、难用之处，开发者会第一个、最切肤地感受到，反馈比任何外部调研都快都真。其二，技术自洽：Langfuse 本就讲 OTel 这门通用语言（它能摄取你应用的 OTel 数据），所以观测自己时复用同一套 trace/span 概念，发出去的 span 和收进来的 span 是同构的，几乎没有额外认知负担。其三，它逼着把可观测能力做得「随手可用」——正因为内部处处要用，instrumentAsync 才被打磨成「包一下就行」的薄包装，而非每处手写 OTel 样板。一个工具最好的背书，是它自己离不开它。",
                    "en": "Dogfooding has triple value at Langfuse. First, the truest self-test: when the team runs its own product under its own production traffic daily, the product's jank, defects, and rough edges are felt first and most acutely by developers—feedback faster and truer than any external research. Second, technical self-consistency: Langfuse already speaks the universal OTel language (it can ingest your app's OTel data), so observing itself reuses the same trace/span concepts, with emitted and ingested spans isomorphic, at near-zero extra cognitive load. Third, it forces observability to be 'ready at hand'—precisely because it's needed internally everywhere, instrumentAsync got polished into a 'wrap once' thin wrapper rather than hand-written OTel boilerplate everywhere. A tool's best endorsement is that it can't live without itself.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的 winston 日志里有个 tracingFormat 格式器：每写一行日志，就把当前活跃 OTel span 的 trace_id/span_id 自动注入这行。这个设计解决了什么排查痛点？",
                    "en": "Langfuse's winston logging has a tracingFormat formatter: every log line auto-injects the current active OTel span's trace_id/span_id. What debugging pain point does this solve?",
                },
                "opts": [
                    {
                        "zh": "让「日志」和「链路追踪」自动对上号：从一条报错日志顺trace_id一键跳到该请求的完整链路(看清走了哪些服务、每步耗时、错在第几跳)，反向也能从慢链路捞出沿途所有日志——否则两者是孤岛，排查只能手工对时间戳",
                        "en": "auto-reconciles 'logs' and 'distributed traces': from one error log follow trace_id to jump to that request's full trace (which services, each step's latency, which hop errored) in one click, and in reverse scoop all logs from a slow trace—otherwise the two are isolated islands and debugging means manually matching timestamps",
                    },
                    {"zh": "让日志文件更小", "en": "makes log files smaller"},
                    {"zh": "给日志加密", "en": "encrypts the logs"},
                    {"zh": "让日志写入更快", "en": "makes log writes faster"},
                ],
                "answer": 0,
                "why": {
                    "zh": "可观测性常说「三支柱」：traces（链路）、logs（日志）、metrics（指标）。但三者若彼此孤立，价值大打折扣——最典型的痛点就是：你在海量日志里看到一条报错，却不知道它属于哪次请求、那次请求前后发生了什么；或者你盯着一条慢链路，却捞不出它沿途打了哪些日志。tracingFormat 用一行「自动注入 trace_id/span_id」把这两座岛连了起来：日志带着链路 id，于是日志↔链路可以一键互跳，前因后果一目了然。没有它，排查就退化成「手工对齐时间戳」，又慢又易错。这就是「让可观测三支柱协同」的关键一招。",
                    "en": "Observability often speaks of 'three pillars': traces, logs, metrics. But if the three are isolated, their value drops sharply—the classic pain: you see an error among a sea of logs but don't know which request it belongs to or what happened around it; or you eye a slow trace but can't scoop the logs it emitted along the way. tracingFormat connects these two islands with one line of 'auto-inject trace_id/span_id': logs carry the trace id, so logs↔traces jump in one click, cause and effect clear at a glance. Without it, debugging degrades to 'manually aligning timestamps', slow and error-prone. This is the key move of 'making the observability pillars work together'.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 不直接到处读 process.env.XXX，而是把所有环境变量过一遍 Zod 校验（共享 EnvSchema、web 用 createEnv 分 server/client）。这样做的好处不包括下面哪一项？",
                    "en": "Rather than reading process.env.XXX everywhere, Langfuse runs all env vars through Zod validation (shared EnvSchema, web createEnv splitting server/client). Which of the following is NOT a benefit of this?",
                },
                "opts": [
                    {
                        "zh": "让程序运行时占用更少的内存",
                        "en": "makes the program use less memory at runtime",
                    },
                    {"zh": "fail-fast：配置不合法时启动当场就报清晰的错，而非带病运行到半路神秘崩溃", "en": "fail-fast: invalid config errors clearly at startup, rather than running impaired and crashing mysteriously mid-run"},
                    {"zh": "类型安全：z.coerce 把端口字符串转数字、z.enum 限定取值，不再人人都是 string|undefined", "en": "type-safe: z.coerce turns a port string into a number, z.enum limits values, no longer all string|undefined"},
                    {"zh": "server/client 边界：createEnv 强制隔离仅服务端密钥与可进前端的公开配置，防止密钥泄露进浏览器包", "en": "server/client boundary: createEnv enforces isolating server-only secrets from public config, preventing secrets leaking into the browser bundle"},
                ],
                "answer": 0,
                "why": {
                    "zh": "Zod 校验 env 的三大好处是 fail-fast、类型安全、server/client 边界，但「省内存」不在其列——校验本身在启动时跑一次，对运行时内存占用没有实质影响，选它为「好处」是不对的。逐一看真正的好处：① fail-fast——错配在启动那一刻就当场报清晰的错（如 DATABASE_URL 非法），而不是跑到第一次用才崩、错误信息还离根因很远；② 类型安全——z.coerce/z.enum 把「永远是 string|undefined」的裸 env 变成有确定类型和取值约束的值；③ server/client 边界——createEnv 从机制上区分「只能服务端用的密钥」与「能打进前端的公开配置」，防止手滑把数据库密码泄露给所有访问者。核心理念：把配置当成「需要校验的输入」，而非「随便读的全局字符串」。",
                    "en": "Zod-validating env has three main benefits—fail-fast, type-safety, server/client boundary—but 'saving memory' isn't one: validation runs once at startup with no real impact on runtime memory, so choosing it as a 'benefit' is wrong. The real benefits: ① fail-fast—misconfig errors clearly the moment of startup (e.g. invalid DATABASE_URL), not crashing on first use with an error far from the root cause; ② type-safety—z.coerce/z.enum turn 'always string|undefined' raw env into values with definite types and value constraints; ③ server/client boundary—createEnv mechanically separates 'server-only secrets' from 'public config that can ship to the front end', preventing a fat-fingered DB password from leaking to every visitor. Core idea: treat config as 'input needing validation', not 'freely-readable global strings'.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课把「可观测性」（运行时透明：trace/log/metric 三支柱协同）和「配置校验」（启动时堵错：Zod fail-fast）放在一起，因为它们都服务于「让系统对运维者透明、可预期、早暴露问题」。请回想你运维或开发过的系统：你是怎么把 trace、log、metric 关联起来的（还是它们各自为政）？你吃过「配置错了却跑到半路才崩」的亏吗？如果让你给一个新服务定「最低限度的可运维性」清单，你会列哪几条？",
                "en": "This lesson pairs 'observability' (runtime transparency: the trace/log/metric three pillars working together) with 'config validation' (boot-time error-plugging: Zod fail-fast), because both serve 'making the system transparent, predictable, and early-surfacing to operators'. Recall systems you've operated or built: how did you correlate traces, logs, and metrics (or did they each go their own way)? Have you been burned by 'misconfig that only crashed mid-run'? If defining a 'minimum operability' checklist for a new service, which items would you list?",
            },
        ],
    },
    "52-data-lifecycle-and-deletion.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Langfuse 删除一个项目时，projectDelete 的顺序是「先并行清 ClickHouse 和 S3，最后才删 Postgres」。为什么 Postgres 要留到最后删？",
                    "en": "When Langfuse deletes a project, projectDelete's order is 'clean ClickHouse and S3 in parallel first, delete Postgres last'. Why is Postgres kept for last?",
                },
                "opts": [
                    {
                        "zh": "PG里的项目记录是「这次删除还没完成」的重试锚点：跨存储删除不是原子的，中途可能崩。只要PG记录还在，重试就知道「还得继续清CH/S3残留」；若先删PG，剩下的CH/S3数据就成了没人认领、再也对不上的孤儿，永久占空间",
                        "en": "the project record in PG is the retry anchor for 'this deletion isn't done': cross-store deletion isn't atomic and may crash mid-way; as long as the PG record exists, a retry knows 'keep cleaning the CH/S3 residue'; delete PG first and the remaining CH/S3 data becomes unclaimed, unmatchable orphans permanently taking space",
                    },
                    {"zh": "Postgres 删除最慢，放最后省时间", "en": "Postgres deletion is slowest, last saves time"},
                    {"zh": "ClickHouse 必须在 Postgres 之前初始化", "en": "ClickHouse must be initialized before Postgres"},
                    {"zh": "这只是代码书写的习惯，没有实际意义", "en": "it's just a coding habit with no real meaning"},
                ],
                "answer": 0,
                "why": {
                    "zh": "一次删除要跨 Postgres + ClickHouse + S3 三个存储，这不是一个原子事务——它是多步操作，任何一步都可能因崩溃/超时/网络抖动中断。核心问题是：中断之后，系统还知不知道「这事没做完、得回来接着做」？PG 里的项目记录恰好是这个「待办凭据」：留着它，删除任务重试时就知道该项目还没清干净，继续扫 CH/S3 残留；而一旦先删了 PG，这个凭据没了，若 CH/S3 还有残留，系统再也无从知道它们的存在，它们就成了永久孤儿。所以「锚点/源真相最后删」是分布式删除的通用纪律——先清外围、后清锚点，让「未完成」始终可发现、可重试。这与第47课「快照边界/幂等」一脉相承。",
                    "en": "A deletion spans three stores—Postgres + ClickHouse + S3—and this isn't an atomic transaction; it's multi-step, any step interruptible by crash/timeout/network blip. The key question: after interruption, does the system still know 'this isn't done, come back and finish'? The PG project record is exactly that 'to-do proof': keep it and a retry knows the project isn't fully cleaned, continuing to sweep CH/S3 residue; delete PG first and that proof is gone—if CH/S3 still have residue, the system can no longer know it exists, and it becomes a permanent orphan. So 'delete the anchor/source-of-truth last' is the universal discipline of distributed deletion—clean the periphery first, the anchor last, so 'unfinished' stays discoverable and retryable. Of one lineage with Lesson 47's 'snapshot boundary/idempotency'.",
                },
            },
            {
                "q": {
                    "zh": "在 Langfuse 里，删除一条 trace 不是「删一行数据库记录」那么简单。最根本的原因是？",
                    "en": "In Langfuse, deleting a trace isn't as simple as 'delete one database row'. The most fundamental reason is?",
                },
                "opts": [
                    {
                        "zh": "一条trace的数据散在三个存储里：元数据在Postgres、海量事件明细在ClickHouse、大块输入输出/媒体在对象存储S3。要真正删干净必须跨三处协调一致地删，漏删任何一处都是数据残留——既占空间，更是合规与隐私隐患(如GDPR的被遗忘权)",
                        "en": "a trace's data is scattered across three stores: metadata in Postgres, massive event detail in ClickHouse, bulky inputs/outputs/media in object storage S3. To truly delete it you must delete consistently across all three; missing any one is data residue—wasting space and, worse, a compliance and privacy hazard (e.g. GDPR's right to be forgotten)",
                    },
                    {"zh": "因为 trace 数据是加密的，删除前要先解密", "en": "because trace data is encrypted and must be decrypted before deletion"},
                    {"zh": "因为删除需要管理员审批", "en": "because deletion needs admin approval"},
                    {"zh": "因为 trace 太大，一次删不完", "en": "because a trace is too big to delete at once"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这是 Langfuse 存储架构的直接后果。为了让读写各得其所，一条 trace 被拆成三份存：Postgres 放结构化元数据、ClickHouse 放海量可分析的事件明细（列存，第3-4部分讲过）、S3 放体积过大的原始负载（完整输入输出、媒体）。这套分工对性能很好，但对删除提出了要求：必须三处同时清。只删 PG 那行「索引」，CH 的明细和 S3 的附件还在，就是数据残留——不仅白占存储，在隐私合规上更要命：用户行使「删除我的数据」的权利时，残留意味着没真正删除。所以 Langfuse 的每种删除（保留期清理、trace 删除、项目删除）都是跨存储操作。",
                    "en": "This is a direct consequence of Langfuse's storage architecture. To serve reads and writes well, a trace is split into three: Postgres for structured metadata, ClickHouse for massive analyzable event detail (columnar, Parts 3-4), S3 for oversized raw payloads (full I/O, media). This division is great for performance but demands of deletion: clean all three at once. Delete only the PG 'index' row and the CH detail and S3 attachments remain—data residue—not just wasted storage but, worse, a privacy-compliance problem: when a user exercises 'delete my data', residue means it wasn't truly deleted. So each Langfuse deletion (retention cleaning, trace delete, project delete) is a cross-store operation.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 的 BackgroundMigration（后台迁移）模型有 state、lockedAt/workerId、心跳等机制。它要解决的核心问题是？",
                    "en": "Langfuse's BackgroundMigration model has state, lockedAt/workerId, heartbeat mechanisms. What core problem does it solve?",
                },
                "opts": [
                    {
                        "zh": "给生产环境亿万行的表做变更(回填新字段/重组布局)，同时撞上不能停机、会被部署/崩溃中断、有多个worker三个约束：state记进度可断点续传(同第46课水位)、lockedAt/workerId锁保证同一迁移只一个worker跑、心跳续约——让几小时的大手术在后台不停机完成",
                        "en": "changing a billion-row production table (backfill a field/reorganize layout) hits three constraints at once—no downtime, interruptible by deploy/crash, multiple workers: state records progress for checkpoint resume (like Lesson 46's watermark), lockedAt/workerId lock ensures only one worker runs a given migration, heartbeat renewal—letting hours-long big surgery complete in the background without downtime",
                    },
                    {"zh": "让数据库迁移跑得更快", "en": "makes database migrations run faster"},
                    {"zh": "自动生成迁移脚本", "en": "auto-generates migration scripts"},
                    {"zh": "压缩迁移后的数据", "en": "compresses data after migration"},
                ],
                "answer": 0,
                "why": {
                    "zh": "普通迁移（加列、改约束）部署时几秒跑完即可，不需要这套重型机制。但当你要给 ClickHouse 里几十亿行回填一个新字段、或重组数据布局，任务可能跑几小时，这就同时撞上三个硬约束：① 不能停机——业务得持续服务，不可能锁表几小时；② 会中断——几小时里必然遇到部署、重启、崩溃，必须能从断点续跑而非从头来（靠把进度存进 state，和第46课增量同步的 lastSyncAt 同一招）；③ 多 worker——生产多实例，必须保证同一迁移只被一个 worker 执行，否则重复跑改乱数据（靠 lockedAt 分布式锁 + 心跳续约）。一次性脚本三条都占不住。BackgroundMigration 把这些共性沉淀成框架，每个迁移只实现 validate/run/abort，复杂的续传/加锁/留痕由框架统一保证。",
                    "en": "An ordinary migration (add column, change constraint) runs in seconds at deploy and needs none of this heavy machinery. But backfilling a new field across billions of ClickHouse rows or reorganizing layout may run for hours, hitting three hard constraints at once: ① no downtime—the business must keep serving, can't lock the table for hours; ② will be interrupted—over hours you'll surely meet a deploy, restart, crash, so it must resume from a checkpoint not start over (by persisting progress into state, the same trick as Lesson 46's incremental lastSyncAt); ③ multi-worker—production has many instances, so a given migration must run on only one worker, else duplicate runs corrupt data (via the lockedAt distributed lock + heartbeat renewal). A one-off script meets none of the three. BackgroundMigration distills these commonalities into a framework; each migration just implements validate/run/abort, while resume/lock/audit is guaranteed by the framework.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课反复出现一个主题：在分布式系统里「安全地做有副作用的大事」要靠几招——删除留重试锚点、迁移用 state 可恢复、用锁保证单 worker 执行。请结合你的经验谈谈：你做过的「跨多个系统/存储的批量删除或数据迁移」遇到过哪些坑（中途失败、孤儿数据、重复执行）？你是怎么保证「不重不漏、可恢复」的？如果数据还涉及合规删除（如 GDPR 被遗忘权），又会带来哪些额外要求？",
                "en": "This lesson recurs on a theme: in distributed systems, 'safely doing big side-effectful things' relies on a few moves — deletion keeps a retry anchor, migrations use state for resumability, locks ensure single-worker execution. Drawing on your experience: what pitfalls have you hit in 'bulk deletion or data migration across multiple systems/stores' (mid-way failure, orphan data, duplicate execution)? How did you ensure 'no-dup-no-miss, resumable'? And if the data also involves compliant deletion (e.g. GDPR right to be forgotten), what additional requirements arise?",
            },
        ],
    },
    "53-build-test-dev-workflow.html": {
        "mcq": [
            {
                "q": {
                    "zh": "Turborepo 的内容哈希缓存让 Langfuse 的多包构建变快。它的核心机制是？",
                    "en": "Turborepo's content-hash cache makes Langfuse's multi-package builds fast. What's its core mechanism?",
                },
                "opts": [
                    {
                        "zh": "把每个任务的输入(源码+依赖+环境变量)算一个哈希；只要哈希和上次一模一样，就直接重放上次缓存的outputs(dist/.next)、跳过真正构建。于是改了web、shared没动时，shared缓存秒重放，只重建web——「只重建真正改了的包」",
                        "en": "hash each task's inputs (source+deps+env vars); if the hash is identical to last time, directly replay the previously-cached outputs (dist/.next) and skip the real build. So when web changed but shared didn't, shared's cache replays in seconds and only web rebuilds — 'rebuild only what actually changed'",
                    },
                    {"zh": "把所有包压缩成一个文件来加速", "en": "compresses all packages into one file to speed up"},
                    {"zh": "并行编译所有包，不管有没有改", "en": "compiles all packages in parallel regardless of changes"},
                    {"zh": "缓存数据库查询结果", "en": "caches database query results"},
                ],
                "answer": 0,
                "why": {
                    "zh": "几十个包若每次都全量构建，会慢到无法忍受。Turbo 的关键洞察是：一个构建任务本质是「输入→输出」的纯函数，只要输入没变，输出就一定一样，那就没必要重算。它把每个任务的全部输入（该包源码 + 它依赖的包 + 相关环境变量）算成一个内容哈希；下次跑时先比哈希，命中就把上次存下的 outputs（turbo.json 里声明的 dist/、.next/）原样吐出，完全跳过编译。于是你只改了 web 的一个文件、shared 纹丝未动时，shared 的输入哈希不变、缓存秒重放，Turbo 只老实重建 web。这让「增量构建」名副其实，CI 上大部分包没变、缓存全中，几十个包可能几秒就过。",
                    "en": "With dozens of packages, building everything every time would be unbearably slow. Turbo's key insight: a build task is essentially a pure function 'inputs→outputs', so if inputs are unchanged the output must be identical, no need to recompute. It hashes each task's full inputs (that package's source + the packages it depends on + relevant env vars) into a content hash; next run it compares hashes first, and on a hit spits back the previously-stored outputs (the dist/, .next/ declared in turbo.json) verbatim, fully skipping compilation. So when you changed one web file and shared is untouched, shared's input hash is unchanged, its cache replays in seconds, and Turbo dutifully rebuilds only web. This makes 'incremental build' live up to its name; on CI most packages unchanged, all cache hits, dozens of packages may pass in seconds.",
                },
            },
            {
                "q": {
                    "zh": "turbo.json 里，build/lint/test 都是 cache:true，但 dev 和 db:generate 故意设了 cache:false。这个区分背后的判断标准是？",
                    "en": "In turbo.json, build/lint/test are cache:true, but dev and db:generate deliberately set cache:false. What's the criterion behind this distinction?",
                },
                "opts": [
                    {
                        "zh": "一个任务能否缓存，取决于它的全部效果是否都体现在可声明的outputs里。build/lint产出确定的文件可缓存；但dev是常驻服务(没有最终产物)、db:generate把Prisma类型写进node_modules(缓存只重放日志、恢复不了这个副作用)——凡有「藏在别处的副作用」的任务必须cache:false",
                        "en": "whether a task can be cached depends on whether all its effects are captured in declarable outputs. build/lint produce definite files and are cacheable; but dev is a long-running service (no final product), db:generate writes Prisma types into node_modules (the cache only replays logs and can't restore this side effect) — any task with 'side effects hidden elsewhere' must be cache:false",
                    },
                    {"zh": "dev 和 db:generate 运行太快，缓存没意义", "en": "dev and db:generate run too fast for caching to matter"},
                    {"zh": "只有构建产物才值得缓存，其他都不缓存", "en": "only build artifacts are worth caching, nothing else"},
                    {"zh": "cache:false 是为了节省磁盘空间", "en": "cache:false is to save disk space"},
                ],
                "answer": 0,
                "why": {
                    "zh": "缓存的前提是「纯函数式」：同样输入必然产生同样的、能被完整重放的输出。build 满足——给定源码+依赖，产物就是 dist/、.next/ 那些文件，存下来下次原样吐出即可。但 dev 是 persistent 常驻服务，它的「输出」是一个一直跑着的进程，根本没有可缓存的「最终产物」。db:generate 更隐蔽：它真正的效果是把 Prisma 生成的类型写进 node_modules，而 Turbo 缓存命中只会重放当时的日志、并不会真的把文件再写进 node_modules（turbo.json 专门有注释点破），于是在干净的 CI 机器上若缓存它，会出现「日志显示成功、类型却没生成」的诡异故障。所以普适判据是：任务的全部效果是否都落在可声明的 outputs 里？凡有起进程、写 node_modules、改外部状态这类「藏在别处的副作用」，就必须 cache:false。",
                    "en": "Caching presupposes 'pure-functional': the same inputs necessarily produce the same, fully-replayable output. build qualifies — given source+deps, the products are those dist/, .next/ files, stored and spat back verbatim. But dev is a persistent long-running service; its 'output' is a continuously-running process with no cacheable 'final product'. db:generate is subtler: its real effect is writing Prisma-generated types into node_modules, and a Turbo cache hit only replays the logs of that time, not actually re-writing the files into node_modules (turbo.json has a comment pointing this out), so caching it on a clean CI runner causes the weird failure of 'logs say success but types weren't generated'. So the universal criterion: are all of a task's effects captured in declarable outputs? Any task with 'side effects hidden elsewhere' — starting a process, writing node_modules, changing external state — must be cache:false.",
                },
            },
            {
                "q": {
                    "zh": "Langfuse 把 web/worker/shared/ee 放进同一个 monorepo，而不是每个包一个独立仓库（polyrepo）。monorepo 最突出的好处是？",
                    "en": "Langfuse puts web/worker/shared/ee in one monorepo rather than one repo per package (polyrepo). The most prominent benefit of a monorepo is?",
                },
                "opts": [
                    {
                        "zh": "跨包改动的原子性：改一个shared接口并同时更新所有调用它的web/worker代码，可以一个commit、一个PR、一次CI全搞定，永远不出现「shared发了新版但web还没升级」的中间断裂态；外加代码共享零摩擦、统一工具链",
                        "en": "atomicity of cross-package changes: changing a shared interface and updating all the web/worker code calling it can be done in one commit, one PR, one CI run, never an intermediate broken state of 'shared released a new version but web hasn't upgraded'; plus frictionless code sharing and a unified toolchain",
                    },
                    {"zh": "monorepo 让每个包的代码量更少", "en": "a monorepo makes each package's code smaller"},
                    {"zh": "monorepo 不需要任何构建工具", "en": "a monorepo needs no build tools at all"},
                    {"zh": "monorepo 自动让代码运行更快", "en": "a monorepo automatically makes code run faster"},
                ],
                "answer": 0,
                "why": {
                    "zh": "polyrepo（一包一仓库）下，改一个被多处依赖的 shared 接口是件痛事：你得先在 shared 仓库改完、发版，再到 web、worker 仓库分别升级依赖、改调用、各自发版——这期间必然存在「shared 已是新版、web 还是旧版」的不一致窗口，跨仓库的原子性根本无法保证。monorepo 把它们放一起后，这种改动就是一个 commit、一个 PR、一次 CI 的事，要么全过要么全不过，永远一致。此外还有代码直接 import（不必发包）、一套 lint/test/构建配置管全部等好处。代价是仓库变大、构建变重——但这恰恰由 Turbo 的缓存来摊平。所以「monorepo + Turbo」往往绑定出现：前者给协作的原子性，后者还构建的速度。",
                    "en": "Under polyrepo (one repo per package), changing a widely-depended-on shared interface is painful: you must change and release in the shared repo first, then upgrade deps, fix calls, and release separately in the web and worker repos — during which there's inevitably an inconsistency window of 'shared is new, web is still old', and cross-repo atomicity simply can't be guaranteed. With a monorepo, such a change is one commit, one PR, one CI run, all-pass-or-all-fail, always consistent. Plus direct imports (no publishing), one lint/test/build config ruling all. The cost is a larger repo and heavier builds — which is exactly amortized by Turbo's cache. So 'monorepo + Turbo' often appear bundled: the former gives collaborative atomicity, the latter returns build speed.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课（也是「平台与运维」的收尾）讲的是「开发者每天的循环」——monorepo 让跨包改动原子化、Turbo 让重建只花在改了的地方、dx 让新人一条命令上手、seed 让 bug 可廉价复现。请回想你参与过的项目：从 clone 代码到能跑起来要几步、花多久？哪些「隐形的工程基建」最影响你的开发幸福感？如果让你为一个新项目投资「开发者体验」，你会优先做哪三件事，为什么？",
                "en": "This lesson (also the close of 'Platform & Operations') is about the developer's daily loop — the monorepo makes cross-package changes atomic, Turbo spends rebuild effort only where it changed, dx gets newcomers productive in one command, seed makes bugs cheaply reproducible. Recall projects you've joined: from cloning the code to getting it running, how many steps and how long? Which 'invisible engineering infrastructure' most affects your development happiness? If investing in 'developer experience' for a new project, which three things would you prioritize, and why?",
            },
        ],
    },
    "54-design-themes-synthesis.html": {
        "mcq": [
            {
                "q": {
                    "zh": "这一课把 Langfuse 反复出现的设计归纳为六个主题（宽事件、不可变、异步、双存储、多租户、成本）。这一课的核心论点是？",
                    "en": "This lesson distills Langfuse's recurring design into six themes (wide events, immutability, async, dual storage, multi-tenancy, cost). What's the lesson's central argument?",
                },
                "opts": [
                    {
                        "zh": "这六个不是互不相干的技巧，而是同一套世界观的六个切面——全都从「为宽的、结构化的事件数据做高吞吐、探索式可观测」这个目标推导而来；它们彼此印证、共同服务一个目标，这正是「架构」区别于「一堆技术选型」之处",
                        "en": "the six aren't unrelated tricks but six facets of one worldview — all derived from the goal 'high-throughput, exploratory observability on wide, structured event data'; they mutually corroborate and jointly serve one goal, which is exactly what distinguishes 'architecture' from 'a pile of tech choices'",
                    },
                    {"zh": "这六个主题应该照搬到任何系统里", "en": "these six themes should be copied verbatim into any system"},
                    {"zh": "Langfuse 的设计是六个独立团队各自决定的", "en": "Langfuse's design was decided independently by six separate teams"},
                    {"zh": "这六个主题互相冲突，需要权衡取舍", "en": "the six themes conflict and require trade-offs against each other"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这一课的关键不在于列出六个名词，而在于揭示它们的「同源性」。把目标「为宽的结构化事件数据做高吞吐、探索式可观测」拆开：探索式→要保住高基数（宽事件）、不能预揉成固定指标；高吞吐→写要便宜（不可变避读时去重）、活要削峰（异步）、存要按访问形状分（双存储）；平台→要服务多租户（隔离）、要长期可维护（成本约束）。每个主题都是从「目标+规模」逼出来的必然，而非孤立偏好。这就是架构与「技术选型清单」的根本区别：架构是一组彼此印证、共同指向同一目标的取舍，拆掉任何一个，其余都会显得别扭。",
                    "en": "This lesson's key isn't listing six nouns but revealing their common origin. Unpack the goal 'high-throughput, exploratory observability on wide structured event data': exploratory→preserve high cardinality (wide events), don't pre-mash into fixed metrics; high-throughput→cheap writes (immutability avoids read-time dedup), peak-shaving work (async), storage split by access shape (dual storage); platform→serve many tenants (isolation), maintainable long-term (cost constraint). Each theme is a necessity forced from 'goal+scale', not an isolated preference. That's the fundamental difference between architecture and a 'tech-choice checklist': architecture is a set of mutually-corroborating trade-offs pointing at one goal; remove any and the rest look awkward.",
                },
            },
            {
                "q": {
                    "zh": "「宽事件」与「不可变」这两个主题是怎么互相配合的？",
                    "en": "How do the 'wide events' and 'immutability' themes reinforce each other?",
                },
                "opts": [
                    {
                        "zh": "宽事件主张把一次操作的全部上下文塞进一条又宽又富、写完基本不动的事件里；不可变则用「追加而非更新」承接这种高吞吐写入——改用「追加新行+查时去重保留最新」(ClickHouse ReplacingMergeTree(event_ts,is_deleted)+FINAL)替代原地更新，避免更新逼出的读时去重隐藏成本",
                        "en": "wide events advocate packing an operation's full context into one wide, rich event that basically doesn't move after writing; immutability handles this high-throughput write via 'append not update' — using 'append new rows + dedup at query keeping latest' (ClickHouse ReplacingMergeTree(event_ts,is_deleted)+FINAL) instead of in-place update, avoiding the read-time-dedup hidden cost updates would force",
                    },
                    {"zh": "宽事件和不可变其实是同一件事的两个名字", "en": "wide events and immutability are really two names for the same thing"},
                    {"zh": "不可变要求事件越窄越好，与宽事件矛盾", "en": "immutability requires the narrowest events, conflicting with wide events"},
                    {"zh": "它们没有关系，只是凑在一节里讲", "en": "they're unrelated, just discussed in one section"},
                ],
                "answer": 0,
                "why": {
                    "zh": "宽事件决定「数据长什么样」——以 observation 为单位、把全部上下文（输入输出模型用量耗时+高基数自定义属性）装进一条事件，trace 只是关联句柄。这种又宽又富、海量产生的事件，写入方式必须便宜且可扩展，于是不可变接力：写完就不动、只追加。为什么不更新？因为在几十亿行规模上，更新会逼着查询做读时去重，凭空增加隐藏成本。ClickHouse 的 ReplacingMergeTree(event_ts, is_deleted) 正是这个主题的落地——同一实体多次写入不原地改，而是追加新行、查询时用 FINAL 按 event_ts 保留最新版本(读时去重)。所以两者是共谋：宽事件定义了数据形状，不可变让这种形状的海量写入扛得住。",
                    "en": "Wide events decide 'what the data looks like'—per observation, packing all context (input/output/model/usage/latency + high-cardinality custom attributes) into one event, with the trace as just a correlation handle. Such wide, rich, massively-produced events need a write path that's cheap and scalable, so immutability takes over: written stays put, only append. Why not update? Because at billions of rows, updates force read-time dedup, conjuring hidden cost. ClickHouse's ReplacingMergeTree(event_ts, is_deleted) is this theme landing—the same entity written multiple times isn't modified in place but appended as new rows, with FINAL keeping the latest version by event_ts at query (read-time deduplication). So the two conspire: wide events define the data shape, immutability makes that shape's massive writes survivable.",
                },
            },
            {
                "q": {
                    "zh": "架构原则文档里有一句反复被引用的话：「额外的数据库、队列、物化视图、迁移，都必须挣回它们的长期运维负担」。这句话体现的「成本」主题，对设计决策意味着什么？",
                    "en": "The architecture principles doc has an oft-cited line: 'extra databases, queues, materialized views, and migrations must earn their long-term operational burden.' What does this 'cost' theme mean for design decisions?",
                },
                "opts": [
                    {
                        "zh": "把成本与运维简单性当作硬约束，而非「能加就加」：每个新增的活动部件都要先证明自己值这份长期维护成本。它解释了很多克制的选择(API契约要时间窗/字段选择/token分页、不给能扫全历史的危险默认)——能用更少部件达成目标几乎永远是更好的架构",
                        "en": "treating cost and operational simplicity as hard constraints, not 'add it because you can': every new moving part must first prove it's worth its long-term maintenance cost. It explains many restrained choices (API contracts require time windows/field selection/token pagination, no dangerous scan-all-history defaults) — achieving the goal with fewer parts is almost always the better architecture",
                    },
                    {"zh": "意思是要尽量用最便宜的云服务", "en": "it means using the cheapest cloud services possible"},
                    {"zh": "意思是不应该有任何数据库或队列", "en": "it means there should be no databases or queues at all"},
                    {"zh": "意思是性能比一切都重要", "en": "it means performance matters more than anything"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这句话把「成本」从「钱」上升为「架构约束」。它针对的不是云账单，而是每个活动部件带来的长期运维负担——多一个数据库要备份/监控/升级、多一个队列要保活/排障、多一个物化视图要维护一致性、多一个迁移要小心演进。所以默认姿态是减法：加任何东西之前先问「它配不配」。这解释了 Langfuse 一系列克制选择：公共 API 强制时间窗口、暴露字段选择、用 token 分页、拒绝「默认扫全部历史」这种危险便利。其底层智慧是：能用更少的活动部件达成同样目标，几乎永远是更可维护、更不容易出事的架构。复杂度是要还的债，成本主题就是那把催你少借债的尺子。",
                    "en": "This line elevates 'cost' from 'money' to an 'architectural constraint'. It targets not the cloud bill but the long-term operational burden of each moving part—an extra database to back up/monitor/upgrade, an extra queue to keep alive/debug, an extra materialized view to keep consistent, an extra migration to evolve carefully. So the default stance is subtraction: before adding anything, ask 'does it deserve to be here'. This explains Langfuse's restrained choices: the public API forces time windows, exposes field selection, uses token pagination, refuses the dangerous convenience of 'scan all history by default'. The underlying wisdom: achieving the same goal with fewer moving parts is almost always a more maintainable, less failure-prone architecture. Complexity is debt to be repaid; the cost theme is the ruler nudging you to borrow less.",
                },
            },
        ],
        "open": [
            {
                "zh": "这一课点出：迁移 Langfuse 的设计智慧，关键不是照搬具体选型（ClickHouse、fan-out 队列），而是学它的推导方式——先钉死「目标+规模」前提（探索式还是已知问题？写多还是读多？一个还是多个租户？容忍多大延迟？），再用「每个活动部件都要挣回运维负担」做减法。请挑一个你熟悉或正在做的系统，试着走一遍这个推导：它的目标+规模前提是什么？据此，六个主题里哪些适用、哪些不必要？你现有架构里有没有「没挣回运维负担」的部件？",
                "en": "This lesson notes: transferring Langfuse's design wisdom isn't about copying specific choices (ClickHouse, fan-out queues) but learning its way of deriving — first nail the 'goal+scale' premises (exploratory or known questions? write-heavy or read-heavy? one tenant or many? how much latency tolerable?), then subtract via 'every moving part must earn its burden'. Pick a system you know or are building, and walk this derivation: what are its goal+scale premises? Given those, which of the six themes apply and which are unnecessary? Does your current architecture have any parts that 'haven't earned their operational burden'?",
            },
        ],
    },
    "55-capstone-trace-life.html": {
        "mcq": [
            {
                "q": {
                    "zh": "这一课跟着一条 trace 走完它的「七个驿站」（出生→摄取→落库→被读→被评估→被作用→退场）。在「摄取」这一站，Langfuse 怎么做到既扛住高吞吐又不丢数据？",
                    "en": "This lesson follows a trace through its 'seven stations' (born→ingested→stored→read→evaluated→acted on→retired). At the 'ingested' station, how does Langfuse withstand high throughput without losing data?",
                },
                "opts": [
                    {
                        "zh": "「快接收、异步处理」：API 用 API key(两层哈希)认证后，把原始事件落进 S3、任务塞进 Redis 队列就立刻 207 返回(请求路径极薄)，真正的校验解析合并由 worker 从队列取出后在后台做、upsert 进 ClickHouse——异步削峰，请求不被重活拖住",
                        "en": "'receive fast, process async': after the API authenticates by API key (two-tier hash), it lands the raw event in S3, pushes the task to a Redis queue, and returns 207 immediately (a very thin request path); the real validation/parsing/merging is done by the worker pulling from the queue in the background, upserting into ClickHouse — async peak-shaving, the request isn't dragged by heavy work",
                    },
                    {"zh": "把所有数据直接同步写进 ClickHouse 并等待确认", "en": "synchronously write all data straight into ClickHouse and wait for confirmation"},
                    {"zh": "丢弃超过阈值的数据以保证不卡", "en": "drop data over a threshold to stay responsive"},
                    {"zh": "让 SDK 重试直到数据库有空", "en": "make the SDK retry until the database is free"},
                ],
                "answer": 0,
                "why": {
                    "zh": "摄取这一站是「异步」主题的典范。如果请求路径上同步把数据写进 ClickHouse 并等确认，高峰时数据库一慢，整条上报链路就堵死、SDK 侧超时丢数据。Langfuse 的做法是把请求路径做到极薄：认证 + 把原始事件落进 S3(持久化，不丢) + 把任务塞进 Redis 队列，就立刻返回 207。真正耗时的校验、解析、合并、写 ClickHouse，全交给 worker 异步在后台慢慢做。这样请求侧永远快、永远不被重活拖住(削峰)，而数据因为先落了 S3 + 进了队列，即使 worker 一时处理不过来也不会丢(解耦 + 可重试)。这正是第12-19课摄取链路的精髓，也是第54课「异步」主题的第一次亮相。",
                    "en": "The ingested station is a paragon of the 'async' theme. If the request path synchronously wrote data into ClickHouse and waited for confirmation, then at peak when the DB slows, the whole report chain jams and the SDK side times out and loses data. Langfuse makes the request path razor-thin: authenticate + land the raw event in S3 (persisted, not lost) + push the task to a Redis queue, then return 207 immediately. The truly time-consuming validation, parsing, merging, and ClickHouse writes are all handed to the worker to do slowly in the background. So the request side is always fast, never dragged by heavy work (peak-shaving), and since data first landed in S3 + entered the queue, even if the worker can't keep up momentarily nothing is lost (decoupling + retryable). This is the essence of Lessons 12-19's ingestion path and the 'async' theme's first appearance from Lesson 54.",
                },
            },
            {
                "q": {
                    "zh": "这一课指出 trace 一生中有一个「优雅的闭环」。这个闭环指的是什么？",
                    "en": "This lesson points out an 'elegant closed loop' in a trace's life. What does this loop refer to?",
                },
                "opts": [
                    {
                        "zh": "trace 被评估产生 score，而 score 又反过来驱动监控告警与实验对比，进而改进 prompt/模型/应用——「观测的产物反哺应用」，观测→评估→改进形成闭环，这正是「LLM 工程平台」(而不只是被动日志收集器)的灵魂",
                        "en": "the trace is evaluated to produce a score, and the score in turn drives monitoring alerts and experiment comparisons, thereby improving the prompt/model/app — 'observation products feed the app', observe→evaluate→improve forms a loop, which is the soul of an 'LLM engineering platform' (not just a passive log collector)",
                    },
                    {"zh": "trace 被删除后又被自动重建", "en": "the trace is automatically rebuilt after deletion"},
                    {"zh": "trace 在三个存储之间不断循环复制", "en": "the trace continuously cycles and replicates among the three stores"},
                    {"zh": "trace 每次被读都会触发一次重新摄取", "en": "every read of the trace triggers a re-ingestion"},
                ],
                "answer": 0,
                "why": {
                    "zh": "这个闭环是 Langfuse 之所以叫「LLM 工程平台」而非「日志收集器」的关键。被动的观测系统只是把数据记下来给你看；Langfuse 更进一步：trace 被 LLM 裁判或人工标注评估、产生 score(第28-32课)；score 不是终点，它被监控盯着聚合、越阈值发告警(第33课)，也被用来在数据集/实验里对比不同 prompt 与模型的优劣(第34-36课)；这些反馈最终指导你改进应用——而改进后的应用又产生新的 trace，循环往复。于是「观测」的产物(score)反过来成了「改进」的驱动力，形成 观测→评估→改进→再观测 的闭环。这正是把 AI 应用从「黑盒撞运气」变成「可度量、可迭代」的核心机制。",
                    "en": "This loop is the key to why Langfuse is an 'LLM engineering platform' not a 'log collector'. A passive observability system just records data for you to view; Langfuse goes further: a trace is evaluated by an LLM judge or human annotation, producing a score (Lessons 28-32); the score isn't the end — it's watched by a monitor's aggregate, alerting on threshold (Lesson 33), and used in datasets/experiments to compare different prompts and models (Lessons 34-36); this feedback ultimately guides you to improve the app — and the improved app produces new traces, round and round. So the 'observation' product (score) in turn becomes the driver of 'improvement', forming an observe→evaluate→improve→observe-again loop. This is the core mechanism turning an AI app from 'black-box luck' into 'measurable, iterable'.",
                },
            },
            {
                "q": {
                    "zh": "这一课作为全书终章，反复强调「真正该带走的不是某段源码」。那么按这一课，读完 55 课最该获得的是什么？",
                    "en": "As the whole guide's finale, this lesson repeatedly stresses 'what you should truly carry away isn't a snippet of source'. So per this lesson, what's the most important thing to gain from the 55 lessons?",
                },
                "opts": [
                    {
                        "zh": "一种「看系统」的眼光：面对任何复杂系统，会追问它的目标+规模前提、数据从哪来到哪去、什么该同步什么该异步、什么要强一致什么可最终一致、怎么隔离租户控成本观测自己——用「目标+规模→彼此印证的取舍」的架构师视角去理解系统，而非只问「这函数干嘛」",
                        "en": "a way of 'seeing systems': facing any complex system, you probe its goal+scale premises, where data comes from and goes, what should be sync vs async, what needs strong vs eventual consistency, how it isolates tenants/controls cost/observes itself — understanding systems with an architect's 'goal+scale→mutually-corroborating trade-offs' lens, not just asking 'what does this function do'",
                    },
                    {"zh": "把 Langfuse 的源码全部背下来", "en": "memorizing all of Langfuse's source code"},
                    {"zh": "学会照搬 ClickHouse 和 fan-out 队列到任何项目", "en": "learning to copy ClickHouse and fan-out queues into any project"},
                    {"zh": "记住 55 课每一课的标题", "en": "remembering every one of the 55 lesson titles"},
                ],
                "answer": 0,
                "why": {
                    "zh": "全书的终极意图，不是让你成为「Langfuse 源码专家」，而是借由这一个足够真实、足够完整的范本，训练出一种可迁移的架构思维。具体的选型(ClickHouse、BullMQ、fan-out)会过时、会因场景而异，照搬往往是错的；但那套推导方式是通用的：先想清目标与规模前提，再据此推导该用什么数据模型、哪些活儿同步/异步、哪些状态强/最终一致、怎么隔离与控成本。这正是第54课「钉死前提再做减法」、和这一课「用架构师的眼睛看见表象下彼此印证的取舍」想传递的。所以读完 55 课，最该带走的是这双眼睛——下次面对任何陌生系统，你都能穿过实现细节，看见它背后那套自洽的设计逻辑。这趟旅程结束了，但用这双眼睛读代码的旅程才刚开始。",
                    "en": "The guide's ultimate intent isn't to make you a 'Langfuse source expert' but, through this real-enough, complete-enough specimen, to train a transferable architectural mindset. Specific choices (ClickHouse, BullMQ, fan-out) date and vary by context; copying them is often wrong. But the way of deriving is universal: first get clear on goal and scale premises, then derive what data model to use, what work is sync/async, what state is strong/eventually consistent, how to isolate and control cost. This is exactly what Lesson 54's 'nail premises then subtract' and this lesson's 'use an architect's eyes to see the mutually-corroborating trade-offs beneath the surface' aim to convey. So after 55 lessons, what you should most carry away is these eyes — next time you face any unfamiliar system, you can see past the implementation details to the self-consistent design logic behind it. This journey ends, but the journey of reading code with these eyes has only just begun.",
                },
            },
        ],
        "open": [
            {
                "zh": "这是全书的最后一道思考题。回望这条 trace 的一生——出生、摄取、落库、被读、被评估、被作用、退场——它回答的大问题是「把 AI 应用的不可观测，变回可观测」。请你合上这本指南，试着不看答案、用自己的话讲一遍：一条 trace 从你的应用出发，到最终被删除，完整经历了哪些环节？每个环节背后是哪条设计主题在起作用？如果让你给一个朋友用三分钟讲清「Langfuse 到底是怎么工作的、为什么这么设计」，你会怎么讲？（这道题没有标准答案——能讲清楚，就说明这 55 课真的内化成了你的东西。）",
                "en": "This is the guide's final reflection. Look back on this trace's life — born, ingested, stored, read, evaluated, acted on, retired — answering the big question 'turn an AI app's unobservability back into observability'. Close this guide and, without looking at the answer, retell it in your own words: from leaving your app to finally being deleted, what complete sequence of stages does a trace go through? Which design theme is at work behind each stage? If you had three minutes to explain to a friend 'how Langfuse actually works and why it's designed this way', how would you tell it? (There's no standard answer here — being able to explain it clearly means these 55 lessons have truly become your own.)",
            },
        ],
    },

    "56-v4-architecture-delta.html": {
        "mcq": [{"q": {"zh": "Langfuse v4 最核心的架构变化是什么？", "en": "What is the central Langfuse v4 architecture shift?"},
                 "opts": [
                    {"zh": "把所有数据都搬到 PostgreSQL", "en": "Move all data into PostgreSQL"},
                    {"zh": "observation-first + unified events + OTel-native", "en": "observation-first + unified events + OTel-native"},
                    {"zh": "取消 worker，只保留 web", "en": "Remove the worker and keep only web"}],
                 "answer": 1,
                 "why": {"zh": "v4 的主线是 observation-first、统一 events 读模型和 OTel 原生 SDK/摄取；基础设施角色并没有被整体推翻。", "en": "V4 converges on observation-first semantics, unified events, and OTel-native SDK/ingestion; it does not replace the whole infrastructure."}}],
        "open": [{"zh": "为什么说 v4 是数据模型迁移，而不只是 API 改名？", "en": "Why is v4 a data-model migration rather than just an API rename?"}],
    },
    "57-v4-unified-events.html": {
        "mcq": [{"q": {"zh": "为什么 <code>events_full</code> 会重复保存 user/session/tags 等 trace 维度？", "en": "Why does <code>events_full</code> repeat trace dimensions such as user/session/tags?"},
                 "opts": [
                    {"zh": "为了减少热点分析查询中的 JOIN", "en": "To reduce joins on hot analytical reads"},
                    {"zh": "因为 ClickHouse 不支持 JOIN", "en": "Because ClickHouse cannot perform joins"},
                    {"zh": "为了让 PostgreSQL 更小", "en": "To make PostgreSQL smaller"}],
                 "answer": 0,
                 "why": {"zh": "这是面向分析的反范式化：多存一些字节，换取列裁剪、过滤、聚合和全文检索更直接。", "en": "This is analytics-oriented denormalization: spend storage bytes to simplify filtering, aggregation, pruning and search."}}],
        "open": [{"zh": "如果一条 observation 的 input/output 很大，为什么列表查询不应该总扫 <code>events_full</code> 的全部列？", "en": "Why should list queries avoid scanning every <code>events_full</code> column when I/O is large?"}],
    },
    "58-python-sdk-v4-otel.html": {
        "mcq": [{"q": {"zh": "Python SDK v4 中父子 observation 关系主要由什么决定？", "en": "What primarily determines parent-child observation relationships in Python SDK v4?"},
                 "opts": [
                    {"zh": "当前 OTel span/context", "en": "The current OTel span/context"},
                    {"zh": "一个手工维护的全局 trace_id 列表", "en": "A manually maintained global trace-id list"},
                    {"zh": "PostgreSQL 外键", "en": "PostgreSQL foreign keys"}],
                 "answer": 0,
                 "why": {"zh": "v4 SDK 基于 OpenTelemetry context 建树；<code>@observe</code> 和 <code>start_as_current_observation</code> 都利用当前上下文。", "en": "The v4 SDK builds the tree from OpenTelemetry context; both <code>@observe</code> and <code>start_as_current_observation</code> use current context."}}],
        "open": [{"zh": "为什么短生命周期脚本通常要显式 <code>flush()</code>？", "en": "Why should short-lived scripts commonly call <code>flush()</code> explicitly?"}],
    },
    "59-agent-langchain-v4.html": {
        "mcq": [{"q": {"zh": "复杂 LangGraph Agent 只挂一个 Langfuse CallbackHandler 后，哪件事仍可能需要手工埋点？", "en": "After adding one Langfuse CallbackHandler to a complex LangGraph agent, what can still require manual instrumentation?"},
                 "opts": [
                    {"zh": "LangChain 已经发出的标准 model callback", "en": "Standard model callbacks already emitted by LangChain"},
                    {"zh": "业务层 supervisor 路由与自研 HTTP/DB 工具边界", "en": "Business supervisor routing and custom HTTP/DB tool boundaries"},
                    {"zh": "Python 函数返回语句本身", "en": "The Python return statement itself"}],
                 "answer": 1,
                 "why": {"zh": "Callback 覆盖框架事件，但不会自动理解所有业务边界和自研 I/O；这些地方需要选择性手工 observation。", "en": "Callbacks cover framework events but cannot understand every business boundary or custom I/O, so selected manual observations are still needed."}}],
        "open": [{"zh": "你的 Agent State 里哪些字段值得进 trace，哪些不应该每步完整复制？为什么？", "en": "Which Agent State fields belong in traces, and which should not be copied on every step? Why?"}],
    },
    "60-v4-evals-real-time.html": {
        "mcq": [{"q": {"zh": "线上 evaluator 与离线 experiment 最合理的关系是什么？", "en": "What is the most useful relationship between online evaluators and offline experiments?"},
                 "opts": [
                    {"zh": "二者完全独立", "en": "They should be completely independent"},
                    {"zh": "线上找 bad case，固化进 dataset，再用 experiment 回归验证修复", "en": "Mine bad cases online, promote them to a dataset, then regression-test fixes in experiments"},
                    {"zh": "只保留平均 score dashboard 即可", "en": "Keep only an average-score dashboard"}],
                 "answer": 1,
                 "why": {"zh": "生产 observation → score → bad case → dataset → experiment 才形成持续改进闭环。", "en": "Production observation → score → bad case → dataset → experiment forms a continuous improvement loop."}}],
        "open": [{"zh": "整次 Agent 任务的 score 和某个 generation/tool 的局部 score 应分别挂在哪里？", "en": "Where should whole-task scores and local generation/tool scores be attached?"}],
    },
    "61-v4-self-hosted-migration.html": {
        "mcq": [{"q": {"zh": "为什么自托管 v3→v4 不应该直接一步切到 <code>events_only</code>？", "en": "Why should a self-hosted v3→v4 migration not jump directly to <code>events_only</code>?"},
                 "opts": [
                    {"zh": "因为需要先验证 dual write、历史回填、producer/reader 与恢复路径", "en": "Because dual writes, backfill, producers/readers and recovery must be validated first"},
                    {"zh": "因为 v4 不支持 ClickHouse", "en": "Because v4 does not support ClickHouse"},
                    {"zh": "因为 worker 必须永久停机", "en": "Because the worker must remain stopped"}],
                 "answer": 0,
                 "why": {"zh": "v4 涉及 ClickHouse 数据模型迁移；分阶段切换可以验证覆盖率、实时读取、成本和回滚准备。", "en": "V4 changes the ClickHouse data model; staged cutover lets you validate coverage, reads, cost and recovery readiness."}}],
        "open": [{"zh": "如果你负责一次生产升级，上线前会用哪一条真实请求验证 trace→query→score→cost 全链路？", "en": "Which real request would you use to validate trace→query→score→cost before production cutover?"}],
    },

}


def render(fname, lang):
    """Return the self-test HTML block for ``fname`` in ``lang`` ('' if none)."""
    data = QUIZZES.get(fname)
    if not data or not (data.get("mcq") or data.get("open")):
        return ""
    out = ['<div class="selftest">', f'<h2>{_HEAD[lang]}</h2>']
    for i, item in enumerate(data.get("mcq", []), 1):
        shuffled, ans = _shuffle(item["opts"], item["answer"], f"{fname}:{i}")
        opts = "\n".join(f"    <li>{o[lang]}</li>" for o in shuffled)
        letter = chr(65 + ans)
        out.append(
            f'<div class="quiz">\n'
            f'  <div class="qn">{i}. {item["q"][lang]}</div>\n'
            f'  <ol class="opts">\n{opts}\n  </ol>\n'
            f'  <details class="accordion">\n'
            f'    <summary>{_SEE[lang]} <span class="hint">{_CLICK[lang]}</span></summary>\n'
            f'    <div class="acc-body"><div class="qa"><div class="a">'
            f'<strong>{_ANS[lang]}{letter}</strong>{_SEP[lang]}{item["why"][lang]}'
            f"</div></div></div>\n"
            f"  </details>\n"
            f"</div>"
        )
    opens = data.get("open", [])
    if opens:
        lis = "\n".join(f"    <li>{o[lang]}</li>" for o in opens)
        out.append(
            '<div class="card spark">\n'
            f'  <div class="tag">{_OPEN[lang]}</div>\n'
            f"  <ul>\n{lis}\n  </ul>\n"
            "</div>"
        )
    out.append("</div>")
    return "\n".join(out)


def _validate():
    """Fail fast on authoring mistakes in QUIZZES (clear message names the lesson)."""
    for fname, data in QUIZZES.items():
        for qi, item in enumerate(data.get("mcq", []), 1):
            opts = item["opts"]
            if not (0 <= item["answer"] < len(opts)):
                raise ValueError(
                    f"quizzes[{fname!r}] Q{qi}: answer {item['answer']} out of range 0..{len(opts) - 1}"
                )
            for o in opts:
                if not ({"zh", "en"} <= o.keys()):
                    raise ValueError(f"quizzes[{fname!r}] Q{qi}: an option is missing zh/en")
            if not ({"zh", "en"} <= item["q"].keys() and {"zh", "en"} <= item["why"].keys()):
                raise ValueError(f"quizzes[{fname!r}] Q{qi}: q/why missing zh/en")
        for oi, o in enumerate(data.get("open", []), 1):
            if not ({"zh", "en"} <= o.keys()):
                raise ValueError(f"quizzes[{fname!r}] open{oi}: missing zh/en")


_validate()
