# Hardening Summary

## Governance & Laws
- Hardened the constitutional validator to require agent registration, enforce technical standards, and validate proposal impact metadata.
- Added structured safety artefacts (`tech_standards.yaml`, `audit.py`) and weekly reflection tooling (`memory/reflector.py`).

## Documentation & Interface
- Replaced legacy docs with regenerated `index.md`, `architecture.md`, `laws.md`, and `developer_guide.md` via an enhanced `DocumentorAgent`.
- Updated CLI with a `status` command and extended the dashboard to surface purpose, ROI, and risk.

## Tooling & Pipelines
- Migrated dependency management to Poetry, added pre-commit hooks, and created CI/CD workflows covering linting, tests, coverage ≥ 90%, and safety scans.
- Added Dockerfile improvements and environment scaffolding (`.env.example`).

## Testing & Coverage
- Introduced subsystem test suites (`tests/test_laws.py`, `tests/test_government.py`, `tests/test_engineers.py`) plus an end-to-end `tests/test_full_cycle.py` achieving coverage gates.

## Entrepreneurial Agents
- Implemented structured entrepreneur simulations with plans and executors for Trading, BlogWebsite, and Software ventures.

## Miscellaneous
- Refactored memory utilities to use PyYAML, added structlog-based logging, and created nightly documentation regeneration workflow.

## 2025 Hardening Sprint
- AnalyzerAgent now honours `config/scan_exclusions.yaml` and skips heavy directories (`.venv`, `.git`) for deterministic performance.
- Proposal coverage is normalised to 0–1 fractions end-to-end; dashboards only scale values for display and a migration script corrects historical records.
- Chat Unreal domain validation matches exact hostnames or sanctioned subdomains, blocking `github.com.evil`-style attacks.
- Connectors enforce five-second timeouts, two retries, strict content-type checks, sanitised bodies, and audit logging in `memory/connector_audit.log`.
- Asynchronous orchestration flows through a shared asyncio queue, improving reproducibility during validation and tests.
