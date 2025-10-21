# Refactor Output Manifest

| File | Issue Fixed | Verification Plan |
| --- | --- | --- |
| chat_unreal/api/auth.py | Introduces shared authentication guard for Flask routes. | `tests/test_auth_security.py` ensuring 401 responses for missing tokens. |
| octobot/security/auth_shared.py | Centralises OCTOBOT_KEY loading and decorator logic. | `tests/test_auth_security.py` covering startup guard and decorator. |
| octobot/interface/dashboard.py | Protects approval flow with token + validation checks and resilient JSON parsing. | `tests/test_dashboard_auth.py` validating token enforcement and malformed impact handling. |
| octobot/core/orchestrator.py | Enforces validator compliance and per-instance event queues. | `tests/test_orchestrator_validation.py` covering validation gating and queue isolation. |
| octobot/agents/engineers/analyzer_agent.py | Skips excluded directories, logs parse errors, and uses safe_write. | `tests/test_analyzer_resilience.py` with corrupt/binary files. |
| octobot/laws/validator.py | Normalises coverage fractions and handles malformed JSON via validate_json helper. | `tests/test_validator_resilience.py` verifying malformed artefacts. |
| chat_unreal/connectors/api_handler.py | Validates domains prior to outbound requests and writes via safe_write. | `tests/test_connector_domains.py` asserting whitelist enforcement. |
| chat_unreal/validators/domain_validator.py | Provides strict hostname allowlist for connectors. | `tests/test_connector_domains.py` asserting rejection of spoofed domains. |
| octobot/utils/persistence.py | Adds safe_write wrapper enforcing filesystem laws. | `tests/test_persistence_enforcement.py` simulating allowed/blocked writes. |
| .github/workflows/ci.yml | Switches CI to Poetry install with coverage threshold. | GitHub Actions run; `pytest --cov --cov-fail-under=90`. |
| README.md | Documents hardened architecture and verification commands. | Documentation review + `tests/test_docs.py`. |
| changelog/auto_refactor.md | Summarises refactor scope for reviewers. | Manual audit. |

