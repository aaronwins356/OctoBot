from __future__ import annotations

import pytest

from chat_unreal.api.utils.validators import _domain_allowed, validate_domain, ValidationError


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/path",
        "https://sub.github.com/resource",
    ],
)
def test_domain_validation_accepts_allowed_hosts(url: str) -> None:
    assert _domain_allowed(url, ["github.com"]) is True
    validate_domain(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://evilgithub.com",
        "https://github.com.evil",
    ],
)
def test_domain_validation_rejects_impersonators(url: str) -> None:
    assert _domain_allowed(url, ["github.com"]) is False
    with pytest.raises(ValidationError):
        validate_domain(url)
