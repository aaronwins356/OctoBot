"""Append-only cryptographic ledger for proposals."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from octobot.core.proposal_manager import Proposal
from octobot.memory.utils import ensure_directory, repo_root, timestamp

__all__ = ["Ledger", "LedgerEntry"]


@dataclass(frozen=True)
class LedgerEntry:
    """Immutable record of a proposal lifecycle event."""

    proposal_id: str
    proposer: str
    status: str
    digest: str
    recorded_at: str


class Ledger:
    """Maintain an append-only ledger of proposal hashes."""

    def __init__(self, path: Path | None = None) -> None:
        root = repo_root()
        self.path = path or (root / "memory" / "ledger.json")
        ensure_directory(self.path.parent)
        if not self.path.exists():
            self.path.touch()

    def append(self, proposal: Proposal, status: str, proposer: str) -> LedgerEntry:
        entry = LedgerEntry(
            proposal_id=proposal.proposal_id,
            proposer=proposer,
            status=status,
            digest=self._hash_proposal(proposal.path),
            recorded_at=timestamp(),
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.__dict__) + "\n")
        return entry

    def iter_entries(self) -> Iterator[LedgerEntry]:
        if not self.path.exists():
            return iter(())

        def _generator() -> Iterator[LedgerEntry]:
            with self.path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    yield LedgerEntry(**data)

        return _generator()

    def _hash_proposal(self, path: Path) -> str:
        sha = hashlib.sha256()
        for file in sorted(path.rglob("*")):
            if file.is_file():
                sha.update(file.relative_to(path).as_posix().encode("utf-8"))
                sha.update(file.read_bytes())
        return sha.hexdigest()
