"""Offline evaluation harness.

Runs all registered algorithms against every scenario from ``scenarios.py``
and writes a markdown report.
"""

from __future__ import annotations


def main() -> int:
    print("Load scenarios, dispatch algorithms via the registry, write report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
