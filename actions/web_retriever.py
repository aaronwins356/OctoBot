"""Controlled web retrieval with domain allow-list."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse


@dataclass
class WebRetriever:
    """Retrieve content from approved domains only."""

    allowed_domains: Iterable[str]

    def fetch(self, url: str) -> str:
        """Fetch content if the domain is approved."""

        domain = urlparse(url).hostname or ""
        if domain not in self.allowed_domains:
            raise PermissionError(f"Domain '{domain}' is not whitelisted.")
        raise RuntimeError("Network access is disabled in this environment.")
