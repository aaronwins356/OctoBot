"""Helper script to package proposal directories into a zip archive."""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from utils.logger import get_logger
from utils.settings import SETTINGS

LOGGER = get_logger(__name__)


def create_archive(output: Path) -> Path:
    proposals_dir = Path(SETTINGS.runtime.proposal_dir)
    if not proposals_dir.exists():
        raise FileNotFoundError("No proposals directory found")

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in proposals_dir.rglob("*"):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(proposals_dir))
    LOGGER.info("Packaged proposals into %s", output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Package proposals for review")
    parser.add_argument("--output", default="proposals_bundle.zip")
    args = parser.parse_args()
    create_archive(Path(args.output))


if __name__ == "__main__":  # pragma: no cover - manual usage
    main()
