# Proposal Cycle

The proposal pipeline is an event-driven loop managed by `octobot.core.orchestrator.Orchestrator`.

1. **Analyze** — Collect repository metrics (`octobot.agents.engineers.analyzer_agent.AnalyzerAgent`).
2. **Propose** — Write proposal bundles to `proposals/YYYY-MM-DD_<topic>/` (`octobot.core.proposal_manager.ProposalManager`).
3. **Evaluate** — Validation runs on the `proposal.created` event, followed by scoring when `proposal.validated` fires. Coverage must reach 90% before a proposal is marked ready.
4. **Present** — Surface proposals to humans via CLI and dashboard while waiting for approval.
5. **Await Approval** — Manual reviewers inspect `rationale.md`, `diff.patch`, and `impact.json`.
6. **Apply** — After approval, `octobot.core.updater.Updater` applies the patch, commits, and tags the repository (`vYYYY.MM.DD_<topic>`).

All transitions are logged with timestamps and Git SHAs. Proposal metadata is synchronised with `memory/memory.db` and mirrored in `proposal.yaml`.
