import json
import uuid
from pathlib import Path

class Proposal:
    def __init__(self, title, metadata=None, state="pending"):
        self.id = str(uuid.uuid4())
        self.title = title
        self.metadata = metadata or {}
        self.state = state

class ProposalManager:
    """In-memory + JSON-file store for proposals."""
    def __init__(self, store_path="proposals.json"):
        self.path = Path(store_path)
        self.proposals = {}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                for pid, pdata in data.items():
                    self.proposals[pid] = Proposal(
                        title=pdata["title"],
                        metadata=pdata.get("metadata", {}),
                        state=pdata.get("state", "pending"),
                    )
            except Exception:
                pass

    def save(self):
        dump = {pid: vars(p) for pid, p in self.proposals.items()}
        self.path.write_text(json.dumps(dump, indent=2))

    def list_all(self):
        return list(self.proposals.values())

    def get(self, pid):
        return self.proposals.get(pid)

    def create(self, title, metadata=None):
        p = Proposal(title, metadata)
        self.proposals[p.id] = p
        self.save()
        return p

    def mark_approved(self, pid, approver, token):
        p = self.get(pid)
        if not p:
            raise ValueError("Proposal not found")
        p.state = "approved"
        p.metadata["approved_by"] = approver
        self.save()

    def mark_rejected(self, pid, reason=""):
        p = self.get(pid)
        if not p:
            raise ValueError("Proposal not found")
        p.state = "rejected"
        p.metadata["reason"] = reason
        self.save()

    def exists(self, pid):
        return pid in self.proposals
