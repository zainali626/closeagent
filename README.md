# CloseAgent (working name)

A governed AI agent for month-end close, built as an enterprise AI
transformation pilot: the build receipt for Staff/Senior TPM and Senior
Architect, Enterprise AI / AI Transformation roles.

A finance user asks questions and gets work done at close - variance
explanations, policy lookups, account analysis. Every answer is computed
from governed data, cited, evaluated, and costed.

## Layers

1. **Data foundation** - finance data modeled in dbt; one mart, ported to
   Databricks and Microsoft Fabric; a semantic model the agent reads from.
2. **Knowledge layer** - RAG over close SOPs and policies, a finance
   ontology, permission-aware retrieval.
3. **Model gateway** - routes between a hosted model API and a self-hosted
   NVIDIA Triton endpoint; cost and latency logged per call.
4. **Agent** - LangGraph: SQL, document search, and calculator tools, with
   a human-approval step before anything is drafted into the close package.
5. **Evaluation & governance** - gold dataset built from real Copilot
   rollout failure modes; automated evals gate every change; guardrails.
6. **Transformation pack** - Azure deployment, CI / automated code review,
   UAT pack, adoption and rollout plan, ROI model.

## Working method

Step by step. At each step we decide together who does what: work with no
learning value is automated and reviewed; concept-bearing work is done by
Zain personally, with coaching. Automation with human review.

## Status

Step 1 (scope the pilot) complete 2026-11-15: 10-question pilot set,
dataset design, and ADR-001 architecture decisions approved.
Step 2 (data foundation) in progress: the pilot question set was rebuilt
2026-11-15 from month-end close research (12 questions, every one mapped
to a documented close pain - bank rec, close blockers, accrual reversals,
intercompany, subledger tie-outs, flux). Synthetic dataset regenerated to
match and verified (`scripts/generate_data.py`, `scripts/verify_data.py` -
all 13 storyline checks pass, 8 data files), dbt project scaffolded with
seeds loading and the example staging model building. Next: Zain writes
`stg_gl_lines` and the first mart models.
The ERP sync from the earlier LedgerGraph design is demoted to a data
connector; no F&O trial.
