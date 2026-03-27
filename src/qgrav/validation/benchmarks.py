from __future__ import annotations

from typing import Any

import numpy as np


def linear_fit_r2(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    A = np.column_stack([np.ones_like(x), x])
    coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    fitted = A @ coeffs
    ss_res = float(np.sum((y - fitted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')


def build_check(name: str, passed: bool, *, observed: Any = None, expected: Any = None, tolerance: Any = None, note: str | None = None) -> dict[str, Any]:
    out = {'name': name, 'passed': bool(passed)}
    if observed is not None:
        out['observed'] = observed
    if expected is not None:
        out['expected'] = expected
    if tolerance is not None:
        out['tolerance'] = tolerance
    if note is not None:
        out['note'] = note
    return out


def finalize_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        'all_passed': bool(all(bool(c.get('passed', False)) for c in checks)),
        'passed_count': int(sum(bool(c.get('passed', False)) for c in checks)),
        'total_count': int(len(checks)),
        'checks': checks,
    }
