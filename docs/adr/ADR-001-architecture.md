# ADR-001: CloseAgent architecture decisions - DRAFT for Zain's edits

Status: accepted 2026-11-15 (Zain reviewed the Step 1 drafts; only the
travel storyline was changed). Amendable - architecture decisions can be
revisited with a new ADR that supersedes this one.

## Decision 1: The agent reads from a semantic model, never raw tables
Numbers the agent reports (AR balance, tax provision, account totals) come
from defined, tested metrics - one definition of each number, used by
everyone. Rejected alternative: let the agent write SQL against raw tables
(faster to build, but two questions can produce two different "truths").

## Decision 2: Evaluations gate every change
A fixed set of test questions with known-correct answers (the gold dataset)
runs automatically on every change. If scores drop, the change does not
ship. Rejected alternative: spot-check answers by hand before demos
(does not scale, and misses regressions).

## Decision 3: All model calls go through a gateway
The agent never calls a model directly. The gateway can route between a
hosted model API and the self-hosted Triton endpoint, and logs cost and
latency for every call. Rejected alternative: hard-code one model
(no cost visibility, no fallback, vendor lock-in by accident).

## Decision 4: Generated official content needs human approval
Anything drafted for the close package (e.g. flux commentary) is a draft
until a person approves it. The agent proposes; the human disposes.

## Decision 5: Retrieval respects permissions
Policy and SOP documents carry access labels, and search filters by them
before the model sees anything - the lesson carried over from the Sagent
Copilot rollout, where loose document permissions were the core risk.
