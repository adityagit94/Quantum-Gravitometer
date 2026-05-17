"""Published reference values for quantum gravimeter validation.

Provides a registry of published experimental results and a helper to compare
measured values against them.

Several entries that existed in qgrav <= 0.7 carried incorrect or mislabelled
numerical values. They have been corrected in v0.8 and given more specific
keys. The old keys remain importable via :data:`_LEGACY_KEYS` and emit a
``DeprecationWarning`` on first access; they will be removed in a future
release.

References
----------
- Freier, C. et al., *Mobile quantum gravity sensor with unprecedented
  stability*, J. Phys. Conf. Ser. 723, 012050 (2016),
  DOI: 10.1088/1742-6596/723/1/012050
- Menoret, V. et al., *Gravity measurements below 10^-9 g with a transportable
  absolute quantum gravimeter*, Sci. Rep. 8, 12300 (2018),
  DOI: 10.1038/s41598-018-30608-1
- Hu, Z.-K. et al., *Demonstration of an ultrahigh-sensitivity
  atom-interferometry absolute gravimeter*, Phys. Rev. A 88, 043610 (2013)
- Peters, A., Chung, K.Y., Chu, S., *High-precision gravity measurements using
  atom interferometry*, Metrologia 38, 25 (2001),
  DOI: 10.1088/0026-1394/38/1/4
- Kasevich, M., Chu, S., *Atomic interferometry using stimulated Raman
  transitions*, Phys. Rev. Lett. 67, 181 (1991)
- Bidel, Y. et al., *Absolute marine gravimetry with matter-wave
  interferometry*, Nat. Commun. 9, 627 (2018)
- Peterson, J., *Observations and modeling of seismic background noise*,
  USGS Open-File Report 93-322 (1993)
- Hinderer, J., Crossley, D., Warburton, R., *Gravimetric methods,
  superconducting gravity meters*, in *Treatise on Geophysics* vol. 3 (2007)
"""
from __future__ import annotations

import warnings
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
    doi: str = ""  # DOI link, if available

    def contains(self, measured: float, abs_tol: float = 1e-15) -> bool:
        """Return True if *measured* falls within the tolerance band."""
        half = abs(self.value) * self.tolerance_pct / 100.0
        if half == 0.0:
            half = abs_tol
        return (self.value - half) <= measured <= (self.value + half)


REFERENCES: dict[str, PublishedReference] = {
    # ------------------------------------------------------------------
    # Freier et al. 2016 (GAIN, Berlin transportable Rb gravimeter)
    # ------------------------------------------------------------------
    "freier_2016_short_term_noise": PublishedReference(
        key="freier_2016_short_term_noise",
        description="GAIN short-term gravimetric noise (Freier 2016)",
        value=9.6e-8,
        unit="m/s^2/sqrt(Hz)",
        source="Freier et al., J. Phys.: Conf. Ser. 723 012050 (2016), §3",
        year=2016,
        tolerance_pct=50.0,
        doi="10.1088/1742-6596/723/1/012050",
    ),
    "freier_2016_accuracy": PublishedReference(
        key="freier_2016_accuracy",
        description="GAIN absolute accuracy (Freier 2016)",
        value=3.9e-8,
        unit="m/s^2",
        source="Freier et al., J. Phys.: Conf. Ser. 723 012050 (2016), §3",
        year=2016,
        tolerance_pct=50.0,
        doi="10.1088/1742-6596/723/1/012050",
    ),
    "freier_2016_long_term_stability": PublishedReference(
        key="freier_2016_long_term_stability",
        description="GAIN long-term stability (Freier 2016)",
        value=5e-10,
        unit="m/s^2",
        source="Freier et al., J. Phys.: Conf. Ser. 723 012050 (2016), §3",
        year=2016,
        tolerance_pct=80.0,
        doi="10.1088/1742-6596/723/1/012050",
    ),
    # ------------------------------------------------------------------
    # Menoret et al. 2018 (Muquans AQG, transportable absolute gravimeter)
    # ------------------------------------------------------------------
    "menoret_2018_short_term_noise": PublishedReference(
        key="menoret_2018_short_term_noise",
        description="AQG short-term noise (Menoret 2018)",
        value=5e-7,
        unit="m/s^2/sqrt(Hz)",
        source="Menoret et al., Sci. Rep. 8, 12300 (2018)",
        year=2018,
        tolerance_pct=50.0,
        doi="10.1038/s41598-018-30608-1",
    ),
    "menoret_2018_long_term_stability": PublishedReference(
        key="menoret_2018_long_term_stability",
        description="AQG long-term stability (Menoret 2018)",
        value=1e-8,
        unit="m/s^2",
        source="Menoret et al., Sci. Rep. 8, 12300 (2018)",
        year=2018,
        tolerance_pct=50.0,
        doi="10.1038/s41598-018-30608-1",
    ),
    # ------------------------------------------------------------------
    # Hu et al. 2013 (Wuhan 10 m atom-interferometry absolute gravimeter)
    # ------------------------------------------------------------------
    "hu_2013_short_term_noise": PublishedReference(
        key="hu_2013_short_term_noise",
        description="Wuhan 10 m AI gravimeter short-term noise (Hu 2013)",
        value=4.2e-9,
        unit="m/s^2/sqrt(Hz)",
        source="Hu et al., Phys. Rev. A 88, 043610 (2013)",
        year=2013,
        tolerance_pct=50.0,
        doi="10.1103/PhysRevA.88.043610",
    ),
    # ------------------------------------------------------------------
    # Peters, Chung, Chu 2001 (Stanford caesium fountain)
    # ------------------------------------------------------------------
    "peters_2001_accuracy": PublishedReference(
        key="peters_2001_accuracy",
        description="Stanford Cs fountain absolute accuracy (Peters 2001)",
        value=3e-8,
        unit="m/s^2",
        source="Peters, Chung, Chu, Metrologia 38, 25 (2001)",
        year=2001,
        tolerance_pct=50.0,
        doi="10.1088/0026-1394/38/1/4",
    ),
    # ------------------------------------------------------------------
    # Kasevich & Chu 1991 (first AI gravimeter demonstration)
    # ------------------------------------------------------------------
    "kasevich_chu_1991_first_demo": PublishedReference(
        key="kasevich_chu_1991_first_demo",
        description="First atom-interferometric gravimeter demonstration noise",
        value=3e-6,
        unit="m/s^2/sqrt(Hz)",
        source="Kasevich & Chu, Phys. Rev. Lett. 67, 181 (1991)",
        year=1991,
        tolerance_pct=100.0,
        doi="10.1103/PhysRevLett.67.181",
    ),
    # ------------------------------------------------------------------
    # Bidel et al. 2018 (marine quantum gravimeter)
    # ------------------------------------------------------------------
    "bidel_2018_marine": PublishedReference(
        key="bidel_2018_marine",
        description="Marine quantum gravimeter short-term noise (Bidel 2018)",
        value=1.7e-6,
        unit="m/s^2/sqrt(Hz)",
        source="Bidel et al., Nat. Commun. 9, 627 (2018)",
        year=2018,
        tolerance_pct=50.0,
        doi="10.1038/s41467-018-03040-2",
    ),
    # ------------------------------------------------------------------
    # USGS New Low Noise Model (Peterson 1993)
    # ------------------------------------------------------------------
    "nlnm_low_freq": PublishedReference(
        key="nlnm_low_freq",
        description="USGS New Low Noise Model acceleration spectral density "
        "at 0.01 Hz (quiet site)",
        value=7e-10,
        unit="m/s^2/sqrt(Hz)",
        source="Peterson, USGS Open-File Report 93-322 (1993)",
        year=1993,
        tolerance_pct=100.0,
        doi="10.3133/ofr93322",
    ),
    # ------------------------------------------------------------------
    # Retained from v0.7
    # ------------------------------------------------------------------
    "sg_noise_floor": PublishedReference(
        key="sg_noise_floor",
        description="Typical superconducting gravimeter noise floor "
        "(post-correction)",
        value=1e-11,
        unit="m/s^2/sqrt(Hz)",
        source="Hinderer, Crossley & Warburton, Treatise on Geophysics (2007)",
        year=2007,
        tolerance_pct=100.0,
        doi="10.1016/B978-044452748-6.00058-4",
    ),
    "mz_visibility": PublishedReference(
        key="mz_visibility",
        description="Typical Mach-Zehnder fringe visibility (contrast)",
        value=0.5,
        unit="dimensionless",
        source="Peters, Chung & Chu, Metrologia 38, 25 (2001)",
        year=2001,
        tolerance_pct=80.0,
        doi="10.1088/0026-1394/38/1/4",
    ),
}


# Legacy keys that pointed to numerically wrong values in v0.7. They now alias
# to the corrected entries and emit a DeprecationWarning on resolution.
_LEGACY_KEYS: dict[str, tuple[str, str]] = {
    # old_key: (new_key, reason)
    "freier_2016_sensitivity": (
        "freier_2016_short_term_noise",
        "value was 5e-8, true short-term noise is 9.6e-8 m/s^2/sqrt(Hz)",
    ),
    "menoret_2018_accuracy": (
        "menoret_2018_long_term_stability",
        "value was 2.5e-8 mislabeled; long-term stability is 1e-8 m/s^2",
    ),
}


def _resolve_key(key: str) -> str:
    """Resolve a legacy key to its modern replacement, warning the user."""
    if key in _LEGACY_KEYS:
        new_key, reason = _LEGACY_KEYS[key]
        warnings.warn(
            f"published_references key '{key}' is deprecated and will be "
            f"removed in a future release. Use '{new_key}' instead. "
            f"Reason: {reason}.",
            DeprecationWarning,
            stacklevel=3,
        )
        return new_key
    return key


def get_reference(key: str) -> PublishedReference:
    """Return the :class:`PublishedReference` for *key*, resolving legacy aliases."""
    resolved = _resolve_key(key)
    return REFERENCES[resolved]


def compare_to_reference(
    key: str,
    measured: float,
) -> dict[str, Any]:
    """Compare a measured value to a published reference.

    Parameters
    ----------
    key:
        Key into :data:`REFERENCES`. Legacy keys are accepted and emit a
        ``DeprecationWarning``.
    measured:
        The measured value to compare.

    Returns
    -------
    dict with keys: ``key``, ``measured``, ``reference_value``, ``unit``,
    ``source``, ``within_tolerance``, ``deviation_pct``, ``tolerance_pct``.

    Raises
    ------
    KeyError
        If *key* is not found in :data:`REFERENCES` and is not a known legacy
        alias.
    """
    resolved = _resolve_key(key)
    ref = REFERENCES[resolved]
    if ref.value != 0:
        deviation_pct = (measured - ref.value) / abs(ref.value) * 100.0
    else:
        deviation_pct = float("inf") if measured != 0 else 0.0

    return {
        "key": resolved,
        "measured": measured,
        "reference_value": ref.value,
        "unit": ref.unit,
        "source": ref.source,
        "within_tolerance": ref.contains(measured),
        "deviation_pct": deviation_pct,
        "tolerance_pct": ref.tolerance_pct,
    }
