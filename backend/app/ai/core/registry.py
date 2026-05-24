from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final


class AlgorithmKey:
    CSP_BT_FC: Final[str] = "csp_bt_fc"
    GA_GENERATE: Final[str] = "ga_generate"
    HILL_CLIMBING: Final[str] = "hill_climbing"
    SIMULATED_ANNEALING: Final[str] = "simulated_annealing"
    ORCHESTRATE_REPLAN: Final[str] = "orchestrate_replan"
    GREEDY_BASELINE: Final[str] = "greedy_baseline"
    RANDOM_RESTART: Final[str] = "random_restart"
    RULE_BASED: Final[str] = "rule_based"


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
