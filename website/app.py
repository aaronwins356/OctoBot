"""Flask dashboard for OctoBot."""
from __future__ import annotations

from pathlib import Path

from flask import Flask, redirect, render_template_string, url_for

from government.orchestrator import Orchestrator
from government.proposal_manager import ProposalManager
from memory.history_logger import MemoryStore
from memory.reporter import Reporter

TAILWIND_CDN = "https://cdn.jsdelivr.net/npm/tailwindcss@3.4.1/dist/tailwind.min.css"

TEMPLATE = """
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <link rel=\"stylesheet\" href=\"{{ tailwind }}\">
    <title>OctoBot Dashboard</title>
  </head>
  <body class=\"bg-slate-900 text-slate-100\">
    <div class=\"max-w-6xl mx-auto p-6\">
      <h1 class=\"text-3xl font-bold mb-4\">OctoBot Control Center</h1>
      <div class=\"flex space-x-4 mb-6\">
        <a href=\"{{ url_for('index') }}\" class=\"px-4 py-2 bg-slate-700 rounded\">System Health</a>
        <a href=\"{{ url_for('proposals_view') }}\" class=\"px-4 py-2 bg-slate-700 rounded\">Proposals</a>
        <a href=\"{{ url_for('ventures_view') }}\" class=\"px-4 py-2 bg-slate-700 rounded\">Ventures</a>
        <a href=\"{{ url_for('logs_view') }}\" class=\"px-4 py-2 bg-slate-700 rounded\">Logs</a>
        <a href=\"{{ url_for('laws_view') }}\" class=\"px-4 py-2 bg-slate-700 rounded\">Laws</a>
      </div>
      {% block content %}{% endblock %}
    </div>
  </body>
</html>
"""


def create_app() -> Flask:
    app = Flask(__name__)
    reporter = Reporter()
    store = MemoryStore()
    manager = ProposalManager(store)
    orchestrator = Orchestrator(proposals=manager, store=store)

    @app.route("/")
    def index() -> str:
        metrics = reporter.latest_metrics()
        weekly = reporter.generate_weekly_summary()
        return render_template_string(
            TEMPLATE
            + """
            {% block content %}
            <h2 class=\"text-2xl font-semibold mb-4\">System Health</h2>
            <div class=\"grid grid-cols-2 gap-4\">
              {% for key, series in metrics.items() %}
              <div class=\"bg-slate-800 rounded p-4\">
                <h3 class=\"font-semibold\">{{ key }}</h3>
                <p>Data points: {{ series|length }}</p>
              </div>
              {% endfor %}
            </div>
            <div class=\"mt-6\">
              <h3 class=\"text-xl font-semibold\">Weekly Summary</h3>
              <pre class=\"bg-slate-800 rounded p-4\">{{ weekly | tojson(indent=2) }}</pre>
            </div>
            {% endblock %}
            """,
            metrics=metrics,
            weekly=weekly,
            tailwind=TAILWIND_CDN,
        )

    @app.route("/proposals")
    def proposals_view() -> str:
        proposals = manager.list_proposals()
        return render_template_string(
            TEMPLATE
            + """
            {% block content %}
            <h2 class=\"text-2xl font-semibold mb-4\">Proposals</h2>
            <table class=\"min-w-full bg-slate-800 rounded\">
              <thead>
                <tr>
                  <th class=\"text-left p-2\">ID</th>
                  <th class=\"text-left p-2\">Status</th>
                  <th class=\"text-left p-2\">Summary</th>
                  <th class=\"text-left p-2\">Actions</th>
                </tr>
              </thead>
              <tbody>
                {% for proposal in proposals %}
                <tr class=\"border-t border-slate-700\">
                  <td class=\"p-2\">{{ proposal.proposal_id }}</td>
                  <td class=\"p-2\">{{ proposal.status }}</td>
                  <td class=\"p-2\">{{ proposal.summary }}</td>
                  <td class=\"p-2\">
                    <form method=\"post\" action=\"{{ url_for('approve_proposal', proposal_id=proposal.proposal_id) }}\">
                      <button class=\"px-3 py-1 bg-emerald-600 rounded\">Approve</button>
                    </form>
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
            {% endblock %}
            """,
            proposals=proposals,
            tailwind=TAILWIND_CDN,
        )

    @app.route("/proposals/<proposal_id>/approve", methods=["POST"])
    def approve_proposal(proposal_id: str):
        manager.approve(proposal_id, "dashboard")
        orchestrator.apply_if_approved(proposal_id)
        return redirect(url_for("proposals_view"))

    @app.route("/ventures")
    def ventures_view() -> str:
        return render_template_string(
            TEMPLATE
            + """
            {% block content %}
            <h2 class=\"text-2xl font-semibold mb-4\">Ventures</h2>
            <p class=\"text-slate-300\">Venture generation is planned for a future release.</p>
            {% endblock %}
            """,
            tailwind=TAILWIND_CDN,
        )

    @app.route("/logs")
    def logs_view() -> str:
        events = store.list_history(limit=50)
        return render_template_string(
            TEMPLATE
            + """
            {% block content %}
            <h2 class=\"text-2xl font-semibold mb-4\">Recent Logs</h2>
            <ul class=\"space-y-2\">
              {% for event in events %}
              <li class=\"bg-slate-800 rounded p-3\">
                <p class=\"text-sm text-slate-400\">{{ event.time }} — {{ event.agent }} / {{ event.action }}</p>
                <p>{{ event.details }}</p>
              </li>
              {% endfor %}
            </ul>
            {% endblock %}
            """,
            events=events,
            tailwind=TAILWIND_CDN,
        )

    @app.route("/laws")
    def laws_view() -> str:
        constitution = Path("laws/constitution.yaml").read_text(encoding="utf-8")
        return render_template_string(
            TEMPLATE
            + """
            {% block content %}
            <h2 class=\"text-2xl font-semibold mb-4\">Safety Policy</h2>
            <pre class=\"bg-slate-800 rounded p-4\">{{ constitution }}</pre>
            {% endblock %}
            """,
            constitution=constitution,
            tailwind=TAILWIND_CDN,
        )

    return app
