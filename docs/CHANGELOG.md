# Changelog

## Unreleased
- Establish deterministic proposal lifecycle with Analyzer → Propose → Evaluate → Present → Await Approval → Apply states.
- Centralise rule enforcement via `laws.validator.enforce` and audit logging.
- Implement resilient Chat Unreal bridge with health checks, queuing, and retries.
- Introduce Tailwind-powered dashboard with approval workflow integration.
- Add environment validation, Docker configuration, and pyproject metadata.
- Expand SQLite schema to track proposals, metrics, and errors.
- Provide comprehensive unit tests covering validator rules, bridge behaviour, CLI commands, and proposal generation.
