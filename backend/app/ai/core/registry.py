"""String-keyed algorithm registry.

Algorithms (generators, replanners, baselines) register themselves under a
stable name so orchestrators and the evaluation harness can dispatch by
string without importing concrete implementations.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_REGISTRY: dict[str, Callable[..., Any]] = {}


def register(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if name in _REGISTRY:
            raise ValueError(f"algorithm '{name}' already registered")
        _REGISTRY[name] = fn
        return fn

    return decorator


def get(name: str) -> Callable[..., Any]:
    if name not in _REGISTRY:
        raise KeyError(f"algorithm '{name}' not registered. Available: {list(_REGISTRY)}")
    return _REGISTRY[name]


def names() -> list[str]:
    return sorted(_REGISTRY.keys())
