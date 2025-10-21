"""
File: octobot/interface/dashboard.py
Fix Type: Security / Interface
Summary:
- ✅ Fixed: dashboard approval endpoint lacked authentication and validation checks
- ✅ Added: robust JSON parsing with warnings for malformed artefacts
- ✅ Tested by: tests/test_dashboard_auth.py

The dashboard now requires a valid ``OCTOBOT_KEY`` token, gracefully handles
missing proposal artefacts, and refuses to apply proposals unless the most
recent validation report is compliant with coverage ≥ 90%.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from octobot.core.orchestrator import Orchestrator
from octobot.core.proposal_manager import ProposalManager
from octobot.laws.validator import validate_proposal
from octobot.memory.reporter import Reporter
from octobot.security.auth_shared import AuthenticationError, verify_token, startup_guard

_TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
startup_guard()


def get_token(request: Request) -> str:
    token = request.headers.get("X-Octobot-Key") or request.cookies.get("octobot-key")
    if not token:
        raise HTTPException(status_code=401, detail="Missing OCTOBOT_KEY token")
    return token


def create_app() -> FastAPI:
    manager = ProposalManager()
    orchestrator = Orchestrator(proposals=manager)
    reporter = Reporter(manager.store)
    app = FastAPI(title="OctoBot Dashboard", docs_url=None, redoc_url=None)

    def _safe_json(path: Path) -> tuple[Optional[Dict[str, object]], Optional[str]]:
        if not path.exists():
            return None, "Artefact missing"
        try:
            return json.loads(path.read_text(encoding="utf-8")), None
        except json.JSONDecodeError as error:
            return None, f"Malformed JSON: {error}"

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
        impact_data, impact_warning = _safe_json(proposal.path / "impact.json")
        validation = validate_proposal(proposal)
        warnings = [msg for msg in [impact_warning] if msg]
        return _TEMPLATES.TemplateResponse(
            "proposal_detail.html",
            {
                "request": request,
                "proposal": proposal,
                "impact": impact_data or {},
                "diff": diff_text,
                "validation": validation,
                "warnings": warnings,
            },
        )

    @app.post("/approve/{proposal_id}", response_class=HTMLResponse)
    async def approve(
        proposal_id: str,
        token: str = Depends(get_token),
    ) -> HTMLResponse:
        try:
            if not verify_token(token):
                raise AuthenticationError("Invalid OCTOBOT_KEY")
        except AuthenticationError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error
        proposal = manager.load(proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        report = validate_proposal(proposal)
        if not report.compliant or report.coverage < 0.9:
            raise HTTPException(
                status_code=403,
                detail="Proposal failed validation checks",
            )
        commit = await orchestrator.async_approve_proposal(proposal_id, "dashboard")
        if not commit:
            raise HTTPException(status_code=409, detail="Proposal could not be applied")
        return HTMLResponse(f"<p>Proposal {proposal_id} applied with commit {commit}.</p>")

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
                    scaled = round(max(0.0, min(value, 1.0)) * 100.0, 2)
                    item["value"] = f"{scaled:.2f}"
            data[key] = series
        summary = reporter.generate_weekly_summary()
        return _TEMPLATES.TemplateResponse(
            "metrics.html",
            {"request": request, "metrics": data, "summary": summary},
        )

    return app


__all__ = ["create_app"]

