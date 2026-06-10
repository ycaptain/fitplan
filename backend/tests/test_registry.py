from __future__ import annotations

from app.ai.core import registry


def test_all_planning_algorithms_are_registered() -> None:
    import app.ai.adaptability  # noqa: F401
    import app.ai.baselines  # noqa: F401
    import app.ai.csp  # noqa: F401
    import app.ai.local  # noqa: F401
    import app.ai.search  # noqa: F401

    expected = {
        registry.AlgorithmKey.CSP_BT_FC,
        registry.AlgorithmKey.BEAM_SEARCH,
        registry.AlgorithmKey.GREEDY_BASELINE,
        registry.AlgorithmKey.HILL_CLIMBING,
        registry.AlgorithmKey.SIMULATED_ANNEALING,
        registry.AlgorithmKey.ORCHESTRATE_REPLAN,
    }
    assert expected <= set(registry.names())


def test_generators_share_the_initial_generator_signature() -> None:
    import inspect

    import app.ai.baselines  # noqa: F401
    import app.ai.csp  # noqa: F401
    import app.ai.search  # noqa: F401

    for key in (
        registry.AlgorithmKey.CSP_BT_FC,
        registry.AlgorithmKey.BEAM_SEARCH,
        registry.AlgorithmKey.GREEDY_BASELINE,
    ):
        fn = registry.get(key)
        params = list(inspect.signature(fn).parameters)
        assert params[:2] == ["req", "constraints"], key
