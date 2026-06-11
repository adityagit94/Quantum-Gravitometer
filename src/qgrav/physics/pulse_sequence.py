from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class RabiPulseScan:
    tau_step_s: float
    n_steps: int

    def tau_axis(self) -> np.ndarray:
        if self.tau_step_s <= 0:
            raise ValueError("tau_step_s must be positive.")
        if self.n_steps <= 0:
            raise ValueError("n_steps must be positive.")
        return np.arange(int(self.n_steps) + 1, dtype=np.float64) * float(self.tau_step_s)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MachZehnderPulseSequence:
    tau_pi_half_s: float
    interferometer_time_s: float

    def pulse_durations_s(self) -> tuple[float, float, float]:
        if self.tau_pi_half_s <= 0:
            raise ValueError("tau_pi_half_s must be positive.")
        return (
            float(self.tau_pi_half_s),
            2.0 * float(self.tau_pi_half_s),
            float(self.tau_pi_half_s),
        )

    def pulse_times_s(self) -> tuple[float, float, float]:
        if self.interferometer_time_s <= 0:
            raise ValueError("interferometer_time_s must be positive.")
        T = float(self.interferometer_time_s)
        return (0.0, T, 2.0 * T)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pulse_durations_s"] = list(self.pulse_durations_s())
        d["pulse_times_s"] = list(self.pulse_times_s())
        return d


def phase_scan_axis(phase_min_rad: float, phase_max_rad: float, n_points: int) -> np.ndarray:
    if n_points < 5:
        raise ValueError("Phase scan requires at least 5 points.")
    return np.linspace(float(phase_min_rad), float(phase_max_rad), int(n_points), dtype=np.float64)


def gravity_sweep_axis(center_m_s2: float, span_m_s2: float, n_points: int) -> np.ndarray:
    if n_points < 5:
        raise ValueError("Gravity sweep requires at least 5 points.")
    return np.linspace(
        float(center_m_s2) - float(span_m_s2) / 2.0,
        float(center_m_s2) + float(span_m_s2) / 2.0,
        int(n_points),
        dtype=np.float64,
    )


def vibration_amplitude_axis(
    amplitude_min_m: float, amplitude_max_m: float, n_points: int
) -> np.ndarray:
    if n_points < 5:
        raise ValueError("Vibration amplitude sweep requires at least 5 points.")
    return np.linspace(
        float(amplitude_min_m), float(amplitude_max_m), int(n_points), dtype=np.float64
    )
