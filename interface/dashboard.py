"""Lightweight review dashboard for human supervisors."""
from __future__ import annotations

from flask import Flask, redirect, render_template_string, request, url_for

from government.proposal_manager import load_proposals, mark_proposal_status

TEMPLATE = """
<!doctype html>
<title>Grounded Lifestyle Review</title>
<h1>Proposal Review Console</h1>
<table border="1" cellpadding="8" cellspacing="0">
  <tr><th>Name</th><th>Status</th><th>Description</th><th>Action</th></tr>
  {% for proposal in proposals %}
  <tr>
    <td>{{ proposal.proposal_name }}</td>
    <td>{{ proposal.status }}</td>
    <td>{{ proposal.description }}</td>
    <td>
      {% if proposal.status != 'approved' %}
      <form method="post" action="{{ url_for('approve_proposal') }}">
        <input type="hidden" name="identifier" value="{{ proposal.storage_path.name }}" />
        <button type="submit">Approve</button>
      </form>
      {% else %}
      Approved
      {% endif %}
    </td>
  </tr>
  {% endfor %}
</table>
"""


def create_dashboard_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index() -> str:
        return render_template_string(TEMPLATE, proposals=load_proposals())

    @app.post("/approve")
    def approve_proposal():
        identifier = request.form["identifier"]
        for proposal in load_proposals():
            if proposal.storage_path and proposal.storage_path.name == identifier:
                mark_proposal_status(proposal, "approved")
                break
        return redirect(url_for("index"))

    return app


app = create_dashboard_app()
