"""Utilities for managing venture proposals on disk."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import yaml

from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)


@dataclass
class VentureProposal:
    """Serializable representation of a single venture proposal."""

    proposal_id: str
    proposal_name: str
    author_agent: str
    description: str
    expected_cost: str
    expected_revenue: str
    strategy: str
    ethical_statement: str
    files_created: List[str] = field(default_factory=list)
    status: str = "pending"
    require_human_approval: bool = True
    created_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    storage_path: Optional[Path] = None

    @property
    def is_approved(self) -> bool:
        """Return whether the venture has obtained human approval."""

        return self.status.lower() == "approved"

    @property
    def slug(self) -> str:
        """Create a filesystem friendly identifier for the proposal."""

        slug_base = self.proposal_name.lower().replace(" ", "-")
        return f"{self.proposal_id}_{slug_base}" if self.proposal_id else slug_base

    def to_dict(self) -> dict:
        """Serialise the proposal to a dictionary suitable for YAML output."""

        data = {
            "proposal_name": self.proposal_name,
            "author_agent": self.author_agent,
            "description": self.description,
            "expected_cost": self.expected_cost,
            "expected_revenue": self.expected_revenue,
            "strategy": self.strategy,
            "ethical_statement": self.ethical_statement,
            "files_created": self.files_created,
            "status": self.status,
            "require_human_approval": self.require_human_approval,
        }
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.approved_at:
            data["approved_at"] = self.approved_at.isoformat()
        if self.proposal_id:
            data["proposal_id"] = self.proposal_id
        return data


def proposal_root() -> Path:
    """Return the configured root directory for venture proposals."""

    root = Path(SETTINGS.runtime.proposal_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        LOGGER.warning("Ignoring malformed datetime %s", value)
        return None


def load_proposal(path: Path) -> VentureProposal:
    """Load a proposal manifest from the supplied ``proposal.yaml`` path."""

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    proposal = VentureProposal(
        proposal_id=data.get("proposal_id", path.parent.name),
        proposal_name=data["proposal_name"],
        author_agent=data.get("author_agent", "unknown"),
        description=data.get("description", ""),
        expected_cost=data.get("expected_cost", "unknown"),
        expected_revenue=data.get("expected_revenue", "unknown"),
        strategy=data.get("strategy", ""),
        ethical_statement=data.get("ethical_statement", ""),
        files_created=list(data.get("files_created", [])),
        status=data.get("status", "pending"),
        require_human_approval=bool(data.get("require_human_approval", True)),
        created_at=_parse_datetime(data.get("created_at")),
        approved_at=_parse_datetime(data.get("approved_at")),
        storage_path=path.parent,
    )
    LOGGER.debug("Loaded proposal %s from %s", proposal.proposal_name, path)
    return proposal


def load_proposals(root: Optional[Path] = None) -> List[VentureProposal]:
    """Load all proposals stored beneath the configured root."""

    base_path = root or proposal_root()
    proposals: List[VentureProposal] = []
    for proposal_dir in sorted(base_path.iterdir()):
        if not proposal_dir.is_dir():
            continue
        manifest = proposal_dir / "proposal.yaml"
        if not manifest.exists():
            LOGGER.debug("Skipping %s (missing proposal.yaml)", proposal_dir)
            continue
        proposals.append(load_proposal(manifest))
    return proposals


def save_proposal(proposal: VentureProposal, base_path: Optional[Path] = None) -> Path:
    """Persist a venture proposal to disk without overwriting existing ones."""

    root = base_path or proposal_root()
    target_dir = root / proposal.slug
    counter = 1
    while target_dir.exists():
        counter += 1
        target_dir = root / f"{proposal.slug}-{counter}"
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest = target_dir / "proposal.yaml"
    manifest.write_text(yaml.safe_dump(proposal.to_dict(), sort_keys=False), encoding="utf-8")
    proposal.storage_path = target_dir
    LOGGER.info("Saved proposal %s to %s", proposal.proposal_name, target_dir)
    return manifest


def mark_proposal_status(proposal: VentureProposal, status: str) -> None:
    """Update the status field of a proposal and persist it."""

    if proposal.storage_path is None:
        raise ValueError("Proposal has no storage_path; cannot update status")
    proposal.status = status
    if proposal.is_approved:
        proposal.approved_at = datetime.utcnow()
    manifest = proposal.storage_path / "proposal.yaml"
    manifest.write_text(yaml.safe_dump(proposal.to_dict(), sort_keys=False), encoding="utf-8")
    LOGGER.info("Marked proposal %s as %s", proposal.proposal_name, status)


def filter_approved(proposals: Iterable[VentureProposal]) -> List[VentureProposal]:
    """Return only the proposals that are approved."""

    return [proposal for proposal in proposals if proposal.is_approved]


__all__ = [
    "VentureProposal",
    "proposal_root",
    "load_proposals",
    "load_proposal",
    "save_proposal",
    "mark_proposal_status",
    "filter_approved",
]
