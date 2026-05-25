from __future__ import annotations

from app.ai.core import registry


def test_hill_climbing_registered() -> None:
    import app.ai.local  # noqa: F401

    fn = registry.get(registry.AlgorithmKey.HILL_CLIMBING)
    assert callable(fn)
