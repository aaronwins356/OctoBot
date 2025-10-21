"""Flask dashboard for OctoBot."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

try:  # pragma: no cover - import guard for optional dependency
    from flask import Flask, redirect, render_template_string, request, url_for
except ModuleNotFoundError:  # pragma: no cover
    Flask = None  # type: ignore
    redirect = render_template_string = request = url_for = None  # type: ignore

from government.evaluator import Evaluation
from government.proposal_manager import Proposal, ProposalManager
from laws.validator import DEFAULT_VALIDATOR
from memory.history_logger import HistoryLogger
from memory.reporter import Reporter

HOME_TEMPLATE = """
<!doctype html>
<title>OctoBot Dashboard</title>
<h1>OctoBot System Overview</h1>
<section>
  <h2>Active Proposals</h2>
  <ul>
    {% for proposal in proposals %}
    <li><a href="{{ url_for('proposal_detail', proposal_id=proposal.proposal_id) }}">{{ proposal.proposal_id }}</a> — {{ proposal.summary }}</li>
    {% else %}
    <li>No proposals yet.</li>
    {% endfor %}
  </ul>
</section>
<section>
  <h2>Metrics</h2>
  <ul>
    {% for key, records in metrics.items() %}
    <li>{{ key }}: {% if records %}{{ records[0].value }} (latest at {{ records[0].captured_at }}){% else %}no data{% endif %}</li>
    {% endfor %}
  </ul>
</section>
"""

PROPOSAL_TEMPLATE = """
<!doctype html>
<title>Proposal {{ proposal.proposal_id }}</title>
<h1>{{ proposal.summary }}</h1>
<p><strong>Impact:</strong> {{ proposal.impact }}</p>
<p><strong>Risk:</strong> {{ proposal.risk }}</p>
<p><strong>Rationale:</strong> {{ proposal.rationale }}</p>
<form method="post" action="{{ url_for('approve_proposal', proposal_id=proposal.proposal_id) }}">
  <label>Approve as:</label>
  <input name="approver" placeholder="Your name" required>
  <button type="submit">Approve</button>
</form>
<section>
  <h2>Evaluation</h2>
  {% for evaluation in evaluations %}
  <p>Complexity: {{ evaluation.complexity }}, Tests: {{ evaluation.tests }}, Docs: {{ evaluation.docs }}, Risk: {{ evaluation.risk }}</p>
  <p>{{ evaluation.rationale }}</p>
  {% endfor %}
</section>
"""

HISTORY_TEMPLATE = """
<!doctype html>
<title>History</title>
<h1>Event History</h1>
<ul>
{% for event, created_at in events %}
  <li>{{ created_at }} — {{ event }}</li>
{% else %}
  <li>No events recorded.</li>
{% endfor %}
</ul>
"""

LAWS_TEMPLATE = """
<!doctype html>
<title>Laws</title>
<h1>Governance Documents</h1>
<p>{{ laws }}</p>
"""


@dataclass
class DashboardContext:
    proposals: List[Proposal]
    evaluations: Dict[str, Evaluation]
    metrics: Dict[str, List]

    @classmethod
    def from_data(cls, proposals: Iterable[Proposal], evaluations: Iterable[Evaluation]) -> "DashboardContext":
        evaluation_map = {evaluation.proposal_id: evaluation for evaluation in evaluations}
        reporter = Reporter()
        metrics = reporter.latest_metrics()
        return cls(list(proposals), evaluation_map, metrics)


def create_app(
    proposal_manager: ProposalManager | None = None,
    logger: HistoryLogger | None = None,
    reporter: Reporter | None = None,
) -> Flask:
    if Flask is None:  # pragma: no cover
        raise RuntimeError("Flask is required to create the dashboard application.")
    proposal_manager = proposal_manager or ProposalManager()
    logger = logger or HistoryLogger()
    reporter = reporter or Reporter()

    app = Flask(__name__)

    @app.route("/")
    def home() -> str:
        context = DashboardContext.from_data(
            proposal_manager.list_proposals(),
            [],
        )
        return render_template_string(HOME_TEMPLATE, proposals=context.proposals, metrics=context.metrics)

    @app.route("/proposals")
    def proposals_page() -> str:
        proposals = proposal_manager.list_proposals()
        evaluations = []
        return render_template_string(
            HOME_TEMPLATE,
            proposals=proposals,
            metrics=DashboardContext.from_data(proposals, evaluations).metrics,
        )

    @app.route("/proposals/<proposal_id>")
    def proposal_detail(proposal_id: str) -> str:
        proposal = proposal_manager.load_proposal(proposal_id)
        if proposal is None:
            return "Proposal not found", 404
        evaluation = DashboardContext.from_data([proposal], []).evaluations.get(proposal_id)
        evaluations = [evaluation] if evaluation else []
        return render_template_string(PROPOSAL_TEMPLATE, proposal=proposal, evaluations=evaluations)

    @app.post("/approve/<proposal_id>")
    def approve_proposal(proposal_id: str):
        DEFAULT_VALIDATOR.ensure(["human approval", "rationale logged"])
        approver = request.form.get("approver", "unknown")
        logger.approve(proposal_id, approver)
        return redirect(url_for("proposal_detail", proposal_id=proposal_id))

    @app.route("/history")
    def history_page() -> str:
        events = logger.list_events()
        return render_template_string(HISTORY_TEMPLATE, events=events)

    @app.route("/laws")
    def laws_page() -> str:
        return render_template_string(LAWS_TEMPLATE, laws=DEFAULT_VALIDATOR.describe())

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
