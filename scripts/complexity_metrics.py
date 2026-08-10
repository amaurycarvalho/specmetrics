#!/usr/bin/env python3
"""Evaluate warning/informational metrics from radon output.

Runs radon hal and radon mi, parses the emitted values and compares them
against the thresholds defined in the quality gate. Halstead metrics are
Warning or Informational severity and never fail the gate. The Maintainability
Index follows Contract 2 (FR-007 + clarification 2026-08-04):

* worst MI >= 70      -> pass, exit 0
* 30 <= worst MI < 70 -> [Warning], exit 0
* worst MI < 30       -> [Blocking], exit 1

An empty/unparseable MI score is treated conservatively as blocking
(fail-loud, FR-014), never as a silent pass.
"""

from __future__ import annotations

import re
import subprocess
import sys

THRESHOLDS = {
    "Halstead Difficulty": (0.0, 20.0, "Warning"),
    "Halstead Effort": (0.0, 150_000.0, "Warning"),
    "Halstead Bugs": (0.0, 0.5, "Informational"),
}

# Maintainability Index severity tiers (Contract 2).
MI_BLOCKING = 30.0
MI_PASS = 70.0


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout


def halstead_max(hal: str, key: str) -> float:
    values = [float(v) for v in re.findall(rf"^\s+{key}: ([\d.]+)$", hal, re.MULTILINE)]
    return max(values) if values else 0.0


def mi_scores(mi: str) -> list[float]:
    scores: list[float] = []
    for match in re.findall(r"\(([\d.]+)\)\s*$", mi, re.MULTILINE):
        try:
            scores.append(float(match))
        except ValueError:
            continue
    return scores


def main() -> int:
    hal = run([".venv/bin/radon", "hal", "-f", ".", "-i", "tests,build,dist,ccache,mutants,.venv"])
    mi = run([".venv/bin/radon", "mi", "-s", ".", "-i", "tests,build,dist,ccache,mutants,.venv"])

    violations: list[str] = []

    diff = halstead_max(hal, "difficulty")
    eff = halstead_max(hal, "effort")
    bugs = halstead_max(hal, "bugs")
    _, diff_hi, diff_sev = THRESHOLDS["Halstead Difficulty"]
    _, eff_hi, eff_sev = THRESHOLDS["Halstead Effort"]
    _, bugs_hi, bugs_sev = THRESHOLDS["Halstead Bugs"]

    if diff > diff_hi:
        violations.append(f"  [{diff_sev}] Halstead Difficulty {diff:.1f} > {diff_hi}")
    else:
        print(f"  Halstead Difficulty {diff:.1f} <= {diff_hi} (Warning)")
    if eff > eff_hi:
        violations.append(f"  [{eff_sev}] Halstead Effort {eff:.0f} > {eff_hi}")
    else:
        print(f"  Halstead Effort {eff:.0f} <= {eff_hi} (Warning)")
    if bugs > bugs_hi:
        violations.append(f"  [{bugs_sev}] Halstead Bugs {bugs:.2f} > {bugs_hi}")
    else:
        print(f"  Halstead Bugs {bugs:.2f} <= {bugs_hi} (Informational)")

    scores = mi_scores(mi)
    gate_failed = False
    if scores:
        worst = min(scores)
        if worst < MI_BLOCKING:
            violations.append(f"  [Blocking] Maintainability Index {worst:.0f} < 30")
            gate_failed = True
        elif worst < MI_PASS:
            violations.append(f"  [Warning] Maintainability Index {worst:.0f} < 70")
        else:
            print(f"  Maintainability Index worst {worst:.0f} >= 70 (Pass)")
    else:
        violations.append("  [Blocking] Maintainability Index: no modules evaluated")
        gate_failed = True

    for v in violations:
        print(v)

    # Contract 2: only sub-30 MI (or no modules) fails the gate.
    return 1 if gate_failed else 0


if __name__ == "__main__":
    sys.exit(main())