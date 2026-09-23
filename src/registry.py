"""Single source of truth: ordered map of output filename -> bilingual content.

Each value is a dict ``{"zh": html, "en": html}``. build.py and build_print.py
both import this so the lesson set stays in sync with shell.PAGES.

Grows one Part module per milestone (part1 .. part11). M0 ships only L01.
"""
import part1
import part2
import part3
import part4
import part5
import part6
import part7
import part8
import part9
import part10
import part11
import part12
# Filename -> {"zh": ..., "en": ...}. Keep keys in sync with shell.PAGES.
CONTENT = {
    "01-what-is-langfuse.html": part1.LESSON_01,
    "02-observability-2-and-wide-events.html": part1.LESSON_02,
    "03-three-pillars-deep.html": part1.LESSON_03,
    "04-project-map-monorepo.html": part1.LESSON_04,
    "05-life-of-a-trace.html": part1.LESSON_05,
    "06-instrumenting-an-llm-app.html": part2.LESSON_06,
    "07-dual-store-architecture.html": part2.LESSON_07,
    "08-clickhouse-wide-events.html": part2.LESSON_08,
    "09-postgres-metadata-schema.html": part2.LESSON_09,
    "10-multi-tenancy.html": part2.LESSON_10,
    "11-deployment-topology.html": part2.LESSON_11,
    "12-ingestion-api.html": part3.LESSON_12,
    "13-event-types-merge.html": part3.LESSON_13,
    "14-ingestion-queue.html": part3.LESSON_14,
    "15-ingestion-service.html": part3.LESSON_15,
    "16-token-counting-cost.html": part3.LESSON_16,
    "17-clickhouse-writer.html": part3.LESSON_17,
    "18-opentelemetry-ingestion.html": part3.LESSON_18,
    "19-media-blob-storage.html": part3.LESSON_19,
    "20-web-app-architecture.html": part4.LESSON_20,
    "21-trpc-backbone.html": part4.LESSON_21,
    "22-repository-layer.html": part4.LESSON_22,
    "23-filtering-search-bar.html": part4.LESSON_23,
    "24-lists-and-tables.html": part4.LESSON_24,
    "25-trace-detail-tree.html": part4.LESSON_25,
    "26-sessions.html": part4.LESSON_26,
    "27-public-rest-api.html": part4.LESSON_27,
    "28-scoring-model.html": part5.LESSON_28,
    "29-llm-as-a-judge.html": part5.LESSON_29,
    "30-eval-execution-pipeline.html": part5.LESSON_30,
    "31-code-based-evaluation.html": part5.LESSON_31,
    "32-human-annotation.html": part5.LESSON_32,
    "33-monitors-and-alerting.html": part5.LESSON_33,
    "34-datasets-and-items.html": part6.LESSON_34,
    "35-dataset-runs.html": part6.LESSON_35,
    "36-experiments-and-comparison.html": part6.LESSON_36,
    "37-prompt-management.html": part7.LESSON_37,
    "38-prompt-serving-caching.html": part7.LESSON_38,
    "39-playground-llm-connections.html": part7.LESSON_39,
    "40-dashboards-and-widgets.html": part8.LESSON_40,
    "41-query-engine.html": part8.LESSON_41,
    "42-models-and-pricing.html": part8.LESSON_42,
    "43-cloud-usage-metering.html": part8.LESSON_43,
    "44-automations-webhooks.html": part9.LESSON_44,
    "45-slack-and-notifications.html": part9.LESSON_45,
    "46-analytics-integrations.html": part9.LESSON_46,
    "47-batch-exports-and-actions.html": part9.LESSON_47,
    "48-auth-and-sessions.html": part10.LESSON_48,
    "49-rbac-apikeys-scim.html": part10.LESSON_49,
    "50-open-core-and-entitlements.html": part10.LESSON_50,
    "51-self-observability-and-config.html": part10.LESSON_51,
    "52-data-lifecycle-and-deletion.html": part10.LESSON_52,
    "53-build-test-dev-workflow.html": part10.LESSON_53,
    "54-design-themes-synthesis.html": part11.LESSON_54,
    "55-capstone-trace-life.html": part11.LESSON_55,
    "56-v4-architecture-delta.html": part12.LESSON_56,
    "57-v4-unified-events.html": part12.LESSON_57,
    "58-python-sdk-v4-otel.html": part12.LESSON_58,
    "59-agent-langchain-v4.html": part12.LESSON_59,
    "60-v4-evals-real-time.html": part12.LESSON_60,
    "61-v4-self-hosted-migration.html": part12.LESSON_61,
}
