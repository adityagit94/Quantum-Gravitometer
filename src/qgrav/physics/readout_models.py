from __future__ import annotations

from typing import Any

import numpy as np


def clip_probabilities(x: np.ndarray | float) -> np.ndarray:
    return np.clip(np.asarray(x, dtype=np.float64), 0.0, 1.0)


def port_differential_summary(port2: np.ndarray, port3: np.ndarray) -> dict[str, Any]:
    p2 = clip_probabilities(port2)
    p3 = clip_probabilities(port3)
    total = np.maximum(p2 + p3, 1e-15)
    diff = p3 - p2
    norm_diff = diff / total
    return {
        'output_port_2': p2,
        'output_port_3': p3,
        'differential_signal': diff,
        'normalized_differential_signal': norm_diff,
        'closed_total': total,
    }
