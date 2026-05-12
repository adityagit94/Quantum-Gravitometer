"""Published reference values for quantum gravimeter validation.

Provides a registry of published experimental results and a helper to compare
measured values against them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PublishedReference:
    """A single published measurement or benchmark value."""

    key: str
    description: str
    value: float
    unit: str
    source: str
    year: int
    tolerance_pct: float = 10.0  # default ±10 % acceptance band

    def contains(self, measured: float) -> bool:
        """Return True if *measured* falls within the tolerance band."""
        half = abs(self.value) * self.tolerance_pct / 100.0
        return (self.value - half) <= measured <= (self.value + half)


REFERENCES: dict[str, PublishedReference] = {
    "freier_2016_sensitivity": PublishedReference(
        key="freier_2016_sensitivity",
        description="Gravimetric sensitivity reported by Freier et al. (2016)",
        value=5e-8,
        unit="m/s^2/sqrt(Hz)",
        source="Freier et al., J. Phys.: Conf. Ser. 723 012050 (2016)",
        year=2016,
        tolerance_pct=50.0,
    ),
    "menoret_2018_accuracy": PublishedReference(
        key="menoret_2018_accuracy",
        description="Absolute accuracy reported by Menoret et al. (2018)",
        value=2.5e-8,
        unit="m/s^2",
        source="Menoret et al., Sci. Rep. 8, 12300 (2018)",
        year=2018,
        tolerance_pct=50.0,
    ),
    "sg_noise_floor": PublishedReference(
        key="sg_noise_floor",
        description="Typical superconducting gravimeter noise floor",
        value=1e-11,
        unit="m/s^2/sqrt(Hz)",
        source="Hinderer, Crossley & Warburton, Treatise on Geophysics (2007)",
        year=2007,
        tolerance_pct=100.0,
    ),
    "mz_visibility": PublishedReference(
        key="mz_visibility",
        description="Typical Mach-Zehnder fringe visibility (contrast)",
        value=0.5,
        unit="dimensionless",
        source="Peters, Chung & Chu, Metrologia 38, 25 (2001)",
        year=2001,
        tolerance_pct=80.0,
    ),
}


def compare_to_reference(
    key: str,
    measured: float,
) -> dict[str, Any]:
    """Compare a measured value to a published reference.

    Parameters
    ----------
    key:
        Key into :data:`REFERENCES`.
    measured:
        The measured value to compare.

    Returns
    -------
    dict with keys: ``key``, ``measured``, ``reference_value``, ``unit``,
    ``source``, ``within_tolerance``, ``deviation_pct``.

    Raises
    ------
    KeyError
        If *key* is not found in :data:`REFERENCES`.
    """
    ref = REFERENCES[key]
    if ref.value != 0:
        deviation_pct = (measured - ref.value) / abs(ref.value) * 100.0
    else:
        deviation_pct = float("inf") if measured != 0 else 0.0

    return {
        "key": key,
        "measured": measured,
        "reference_value": ref.value,
        "unit": ref.unit,
        "source": ref.source,
        "within_tolerance": ref.contains(measured),
        "deviation_pct": deviation_pct,
        "tolerance_pct": ref.tolerance_pct,
    }
