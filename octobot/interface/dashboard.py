"""FastAPI dashboard exposing proposal lifecycle data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from octobot.core.orchestrator import Orchestrator
from octobot.core.proposal_manager import ProposalManager
from octobot.laws.validator import validate_proposal
from octobot.memory.reporter import Reporter

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def create_app() -> FastAPI:
    manager = ProposalManager()
    orchestrator = Orchestrator(proposals=manager)
    reporter = Reporter(manager.store)
    app = FastAPI(title="OctoBot Dashboard", docs_url=None, redoc_url=None)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return await proposals(request)

    @app.get("/proposals", response_class=HTMLResponse)
    async def proposals(request: Request) -> HTMLResponse:
        records = manager.list_proposals()
        return _TEMPLATES.TemplateResponse(
            "proposals.html",
            {"request": request, "proposals": records},
        )

    @app.get("/proposal/{proposal_id}", response_class=HTMLResponse)
    async def proposal_detail(
        request: Request, proposal_id: str
    ) -> HTMLResponse | RedirectResponse:
        proposal = manager.load(proposal_id)
        if not proposal:
            return RedirectResponse(url="/proposals", status_code=302)
        diff_path = proposal.path / "diff.patch"
        diff_text = (
            diff_path.read_text(encoding="utf-8") if diff_path.exists() else "Diff not available."
        )
        impact_path = proposal.path / "impact.json"
        impact = json.loads(impact_path.read_text(encoding="utf-8")) if impact_path.exists() else {}
        validation = validate_proposal(proposal)
        return _TEMPLATES.TemplateResponse(
            "proposal_detail.html",
            {
                "request": request,
                "proposal": proposal,
                "impact": impact,
                "diff": diff_text,
                "validation": validation,
            },
        )

    @app.post("/approve/{proposal_id}", response_class=HTMLResponse)
    async def approve(proposal_id: str) -> HTMLResponse:
        commit = await orchestrator.async_approve_proposal(proposal_id, "dashboard")
        if not commit:
            message = f"Proposal {proposal_id} not applied. Check validation and test logs."
        else:
            message = f"Proposal {proposal_id} applied with commit {commit}."
        return HTMLResponse(f"<p>{message}</p>")

    @app.get("/metrics", response_class=HTMLResponse)
    async def metrics(request: Request) -> HTMLResponse:
        keys: List[str] = ["coverage", "files_scanned", "todos", "missing_docstrings"]
        data: Dict[str, List[Dict[str, str]]] = {}
        for key in keys:
            series = reporter.store.fetch_metrics(key, limit=1)
            if key == "coverage":
                for item in series:
                    try:
                        value = float(item.get("value", 0.0))
                    except (TypeError, ValueError):
                        value = 0.0
                    scaled = round(value * 100.0, 2)
                    item["value"] = f"{scaled:.2f}"
            data[key] = series
        summary = reporter.generate_weekly_summary()
        return _TEMPLATES.TemplateResponse(
            "metrics.html",
            {"request": request, "metrics": data, "summary": summary},
        )

    return app


__all__ = ["create_app"]
