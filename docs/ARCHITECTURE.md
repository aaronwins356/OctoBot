# OctoBot Architectural Overview

OctoBot orchestrates self-inspection cycles consisting of analysis, proposal generation, evaluation, human review, and
curated merging. This document outlines the participating subsystems and the flow of data between them.

## 1. Government Layer

The government package coordinates the lifecycle of improvement initiatives.

- **orchestrator.py** — Schedules and executes improvement cycles. It invokes the analyzer, proposal manager, evaluator, and
  reporter to assemble contextual data for human review.
- **proposal_manager.py** — Persists proposals on disk in YAML + Markdown bundles. Each proposal is timestamped and backed by
  rationale metadata.
- **evaluator.py** — Scores proposals according to cyclomatic complexity impact, test coverage delta, documentation coverage,
  and qualitative risk factors.
- **compiler.py** — Consolidates evaluated proposals into dashboard-friendly payloads and exported reports.
- **updater.py** — Applies approved proposals by invoking GitPython. The updater refuses to run unless an approval record is
  present in the database.

## 2. Engineering Agents

The engineers package contains specialized workers focused on different aspects of the repository.

- **analyzer_agent.py** — Walks the repository, constructs ASTs for Python files, and surfaces hotspots such as repeated logic,
  high-complexity functions, missing docstrings, and unused imports. Results are saved as JSON.
- **code_writer_agent.py** — Builds rewrite candidates from analyzer findings. For offline operation it emits deterministic
  suggestions seeded by heuristics and stores them under `proposals/<date_topic>/code/`.
- **tester_agent.py** — Runs the project's test suites and captures success/failure metrics for use by the evaluator.
- **documentor_agent.py** — Generates and maintains Markdown summaries of proposals and code modules.

## 3. Governance and Ethics

The `laws/` directory contains YAML manifest files describing OctoBot's constitutional rules and ethical principles.
`validator.py` ensures that every agent invocation respects these laws, preventing network access, unapproved merges, and
missing rationales.

## 4. Connectors

External communication is isolated to the `connectors/` package.

- **unreal_bridge.py** — A controlled outbound interface that simulates network calls while enforcing restrictions.
- **web_crawler.py** — Example connector that would consume the bridge to gather documentation in an auditable manner.

## 5. Interfaces

OctoBot exposes two primary human-facing surfaces:

- **interface/cli.py** — A Click-based command line entry point providing commands to analyze, propose, evaluate, launch the
  dashboard, approve proposals, and inspect logs.
- **interface/dashboard.py** — A Flask application with pages for the system overview, proposals, history, and laws.

## 6. Memory Layer

The `memory/` package manages persistence using SQLite.

- **memory.db** — Created automatically on first use.
- **reporter.py** — Aggregates metrics from analyzer runs and evaluator scores for dashboard display.
- **history_logger.py** — Provides a typed interface for inserting and querying historical events and approvals.

## 7. Data Flow Summary

1. `orchestrator.run_cycle()` triggers the analyzer to produce a repository report.
2. `proposal_manager.generate()` converts the report into structured proposals saved on disk.
3. `evaluator.score()` grades each proposal, storing metrics via the reporter.
4. Humans inspect results through the dashboard or CLI.
5. Upon approval, `updater.merge()` validates the laws and commits changes using GitPython.

## 8. Testing Strategy

Automated tests cover:

- Analyzer correctness for detecting missing docstrings and unused imports.
- Proposal formatting to guarantee YAML schema compliance.
- Dashboard health checks ensuring Flask routes render successfully.
- Validator enforcement confirming that laws are parsed and applied to agent actions.

## 9. Extending OctoBot

Developers can add new agents or connectors by registering them with the validator and updating the CLI. Additional metrics can
be logged by extending `memory/reporter.py` with new aggregation routines.

