# OctoBot Architectural Overview

OctoBot is a governed self-analysis platform that inspects the repository, proposes improvements, and stages them for human review. The system is composed of several cooperating packages, each with clear responsibilities and defensive boundaries.

## Package Layout

- `government/` — Owns lifecycle orchestration and application of proposals.
- `engineers/` — Provides analysis capabilities and authoring support.
- `connectors/` — Houses controlled bridges to internal services such as Chat Unreal.
- `laws/` — Defines constitutional rules and exposes the enforcement API.
- `memory/` — Supplies persistent storage, logging, and reporting utilities.
- `interface/` & `website/` — Deliver the CLI and dashboard for human operators.
- `entrepreneurs/` — Reserved for future venture generation tooling.

All directories contain `__init__.py` files to ensure deterministic module discovery and to encourage explicit relative imports within package internals.

## Lifecycle Flow

1. **Analyze** — `engineers.analyzer_agent.AnalyzerAgent` scans the repository, collecting complexity metrics, TODO markers, and documentation gaps. Results are stored under `proposals/_workspace/` to comply with safety rules.
2. **Propose** — `government.proposal_manager.ProposalManager` packages a proposal bundle (`proposal.yaml`, `rationale.md`, `diff.patch`, `impact.json`, and `tests/`). Metadata is synchronised with the SQLite store.
3. **Evaluate** — `government.orchestrator.Orchestrator` checks metrics such as coverage to determine whether a proposal can be marked “ready for review”.
4. **Present** — Proposals transition to the `awaiting_approval` state and surface in the CLI and dashboard.
5. **Await Approval** — Humans review artefacts, optionally approving proposals through the CLI or dashboard.
6. **Apply** — Once approved, `government.updater.Updater` enforces the merge rule, applies the staged patch, commits, and tags the repository.

Each transition is logged with a Git SHA, timestamp, and status in `memory/system.log`.

## Safety Enforcement

`laws/validator.py` exposes a single `enforce(rule_name, context)` function that every agent calls before writing files, touching external services, or applying code. Violations raise `RuleViolationError` and are logged to `memory/audit.log`. The default constitution contains:

- `external_request` — Only allow connectors to talk to external systems.
- `filesystem_write` — Restrict writes to `/proposals` or `/ventures`.
- `code_merge` — Require an explicit approval flag before applying changes.

## Storage & Logging

`memory/history_logger.MemoryStore` manages the SQLite database (`memory/memory.db`) with tables for history events, proposals, errors, and metrics. `memory/logger.log_event` emits JSON entries with the schema `{"time", "agent", "action", "status", "details"}` and rotates automatically. The weekly summary exposed on the dashboard originates from `memory/reporter.Reporter`.

## Interfaces

- **CLI** (`interface/cli.py`) — Provides commands (`octobot propose`, `evaluate`, `list-proposals`, `show`, `approve`, `apply`, `dashboard`). All commands rely on the orchestrator and proposal manager while respecting safety rules.
- **Dashboard** (`website/app.py`) — Flask + Tailwind UI with tabs for System Health, Proposals, Ventures, Logs, and Laws. Approvals propagate through `ProposalManager` and can trigger `Updater.apply()` if conditions are satisfied.

## Connectors

`connectors/unreal_bridge.py` supplies a resilient queue with exponential back-off. It performs health checks against the embedded Chat Unreal assets and serialises errors with detailed context. All network-esque actions go through this bridge, satisfying the `external_request` rule.

## Future Extensions

- Populate `entrepreneurs/` with venture generators.
- Integrate summarisation agents for proposal rationales.
- Add notification plugins (e.g., Slack) on top of the existing governance pipeline.
