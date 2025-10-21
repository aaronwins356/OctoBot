# OctoBot Architectural Overview

OctoBot is a governed self-analysis platform that inspects the repository, proposes improvements, and stages them for human review. The system is composed of several cooperating packages, each with clear responsibilities and defensive boundaries.

## Package Layout

- `octobot/core/` — Government layer responsible for orchestration, proposal management, evaluation, and updates.
- `octobot/agents/engineers/` — Creative layer comprising analyzer, writer, documentor, and tester agents.
- `octobot/agents/entrepreneurs/` — Economic layer (presently a placeholder) for future venture modules.
- `octobot/connectors/` — Communication layer that connects to Chat Unreal and other external interfaces under law enforcement.
- `octobot/laws/` — Immutable law set with constitutional YAML and runtime validators.
- `octobot/memory/` — Reflection layer with persistent stores, metrics reporting, logging, and the cryptographic ledger.
- `octobot/interface/` — Human interaction layer exposing the CLI and FastAPI + HTMX dashboard.
- `octobot/utils/` — Shared helpers, such as YAML utilities.
- `octobot/tests/` — Automated coverage of critical behaviours.

All directories contain `__init__.py` files to ensure deterministic module discovery and to encourage explicit relative imports within package internals.

## Lifecycle Flow

1. **Analyze** — `octobot.agents.engineers.analyzer_agent.AnalyzerAgent` scans the repository, collecting complexity metrics, TODO markers, and documentation gaps. Results are stored under `proposals/_workspace/` to comply with safety rules.
2. **Propose** — `octobot.core.proposal_manager.ProposalManager` packages a proposal bundle (`proposal.yaml`, `rationale.md`, `diff.patch`, `impact.json`, and `tests/`). Metadata is synchronised with the SQLite store.
3. **Evaluate** — `octobot.core.orchestrator.Orchestrator` publishes lifecycle events. Validation runs in response to `proposal.created`, and scoring happens after `proposal.validated`.
4. **Present** — Compliant proposals transition to the `awaiting_approval` state and surface in the CLI and dashboard.
5. **Await Approval** — Humans review artefacts, optionally approving proposals through the CLI or dashboard. Approval emits a `proposal.approved` event.
6. **Apply** — Upon approval, `octobot.core.updater.Updater` enforces the merge rule, applies the staged patch, commits, and tags the repository after verifying tests.

Each transition is logged with a Git SHA, timestamp, and status in `memory/system.log`, and proposal hashes are appended to `memory/ledger.json`.

## Safety Enforcement

`octobot/laws/validator.py` exposes the `enforce(rule_name, context)` guard alongside `validate_proposal()`. Agents call `enforce` before writing files, touching external services, or applying code. Violations raise `RuleViolationError` and are logged to `memory/audit.log`. The default constitution contains:

- `external_request` — Only allow connectors to talk to external systems.
- `filesystem_write` — Restrict writes to `/proposals` or `/ventures`.
- `code_merge` — Require an explicit approval flag before applying changes.

## Storage & Logging

`octobot/memory/history_logger.MemoryStore` manages the SQLite database (`memory/memory.db`) with tables for history events, proposals, errors, and metrics. `octobot/memory/logger.log_event` emits JSON entries with the schema `{"time", "agent", "action", "status", "details"}` and rotates automatically. The weekly summary exposed on the dashboard originates from `octobot/memory/reporter.Reporter`, while `octobot/memory/ledger.Ledger` maintains append-only hashes of proposals.

## Interfaces

- **CLI** (`octobot/interface/cli.py`) — Provides commands (`octobot propose`, `evaluate`, `list-proposals`, `show`, `approve`, `dashboard`). All commands rely on the orchestrator and proposal manager while respecting safety rules.
- **Dashboard** (`octobot/interface/dashboard.py`) — FastAPI + Jinja2 + HTMX interface covering proposal lists, detailed reports, approvals, and metrics visualisation.

## Connectors

`octobot/connectors/unreal_bridge.py` exposes a minimal REST client for Chat Unreal. It enforces the `external_request` rule before sending prompts and gracefully falls back to an offline response when the service is unavailable.

## Future Extensions

- Populate `entrepreneurs/` with venture generators.
- Integrate summarisation agents for proposal rationales.
- Add notification plugins (e.g., Slack) on top of the existing governance pipeline.
