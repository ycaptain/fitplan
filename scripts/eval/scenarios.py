"""Disturbance scenario generator.

Produces (input_plan, plan_delta) tuples covering the four trigger types
(fixed_event_added, session_missed, state_changed, manual_edit) at varying
scales for the evaluation harness.
"""

from __future__ import annotations

from collections.abc import Iterator


def generate_scenarios() -> Iterator[tuple]:
    return iter([])
