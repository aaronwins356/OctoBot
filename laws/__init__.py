"""Laws package exposing enforcement helpers and version metadata.

This package should be treated as immutable during runtime. All APIs provided
here are read-only and designed to help the government enforce the
constitution. Agents must never import these modules directly for modification.
"""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("ai-republic-laws")
except PackageNotFoundError:  # pragma: no cover - package metadata optional
    __version__ = "1.0.0"
