"""Normalize proposal coverage units from percentages to fractions."""

from __future__ import annotations

from octobot.memory.utils import dump_yaml, load_yaml, proposals_root


def _normalize(value: float) -> float:
    coverage = float(value)
    if coverage > 1:
        coverage /= 100.0
    if coverage < 0:
        coverage = 0.0
    if coverage > 1:
        coverage = 1.0
    return round(coverage, 4)


def migrate() -> None:
    proposals_dir = proposals_root()
    for proposal in proposals_dir.iterdir():
        metadata_path = proposal / "proposal.yaml"
        if not metadata_path.exists():
            continue
        data = load_yaml(metadata_path)
        if not data:
            continue
        raw = data.get("coverage", 0.0)
        try:
            numeric = float(raw)
        except (TypeError, ValueError):
            numeric = 0.0
        normalized = _normalize(numeric)
        data["coverage"] = normalized
        dump_yaml(data, metadata_path)
    print("Coverage values normalized.")


if __name__ == "__main__":  # pragma: no cover - script entry point
    migrate()
