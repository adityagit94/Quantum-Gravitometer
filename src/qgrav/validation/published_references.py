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
    # Menoret et al. 2018 (Muquans AQG-A01, transportable absolute gravimeter)
    # ------------------------------------------------------------------
    "menoret_2018_short_term_noise": PublishedReference(
        key="menoret_2018_short_term_noise",
        description="AQG-A01 Larzac short-term noise (Menoret 2018): 750 nm/s^2/sqrt(Hz)",
        # CORRECTED in v1.0.1: was 5e-7 in v1.0.0.  The paper reports a
        # 750 nm/s^2/sqrt(Hz) sensitivity in the Larzac trace (Fig. 4).
        # 750 nm/s^2/sqrt(Hz) = 7.5e-7 m/s^2/sqrt(Hz) = 75 microGal/sqrt(Hz).
        value=7.5e-7,
        unit="m/s^2/sqrt(Hz)",
        source="Menoret et al., Sci. Rep. 8, 12300 (2018), Fig. 4 (Larzac trace)",
        year=2018,
        tolerance_pct=50.0,
        doi="10.1038/s41598-018-30608-1",
    ),
    "menoret_2018_long_term_stability": PublishedReference(
        key="menoret_2018_long_term_stability",
        description="AQG-A01 long-term stability (Menoret 2018): < 10 nm/s^2 = 1 microGal",
        value=1e-8,
        unit="m/s^2",
        source="Menoret et al., Sci. Rep. 8, 12300 (2018), abstract",
        year=2018,
        tolerance_pct=50.0,
        doi="10.1038/s41598-018-30608-1",
    ),
    # ------------------------------------------------------------------
    # Hu et al. 2013 (Wuhan 10 m atom-interferometry absolute gravimeter)
    # ------------------------------------------------------------------
    "hu_2013_short_term_noise": PublishedReference(
        key="hu_2013_short_term_noise",
        description="Wuhan 10 m AI gravimeter short-term noise (Hu 2013): 4.2 microGal/sqrt(Hz)",
        # CORRECTED in v1.0.1: was 4.2e-9 in v1.0.0 (factor 10 too small).
        # The published value is 4.2 microGal/sqrt(Hz), and since
        # 1 microGal = 1e-8 m/s^2, this equals 4.2e-8 m/s^2/sqrt(Hz).
        # See Phys. Rev. A 88, 043610 (2013), §III "Sensitivity".
        value=4.2e-8,
        unit="m/s^2/sqrt(Hz)",
        source="Hu et al., Phys. Rev. A 88, 043610 (2013), §III",
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
        # CORRECTED in v1.0.2: was value=3e-6, unit="m/s^2/sqrt(Hz)".
        # The paper's "3e-6" is a DIMENSIONLESS fractional resolution
        # (delta_g/g) reached after 1000 s of integration, NOT an amplitude
        # spectral density.  Re-typed to dimensionless.  Also note the 1991
        # PRL used SODIUM atoms (the 3e-8 g Rb result is the 1992 follow-up).
        description="First AI gravimeter demonstration: delta_g/g resolution "
        "after 1000 s integration (sodium atoms)",
        value=3e-6,
        unit="dimensionless (delta_g/g at 1000 s)",
        source="Kasevich & Chu, Phys. Rev. Lett. 67, 181 (1991), abstract",
        year=1991,
        tolerance_pct=100.0,
        doi="10.1103/PhysRevLett.67.181",
    ),
    # ------------------------------------------------------------------
    # Bidel et al. 2018 (marine quantum gravimeter)
    # ------------------------------------------------------------------
    "bidel_2018_marine": PublishedReference(
        key="bidel_2018_marine",
        # CORRECTED in v1.0.2: was value=1.7e-6.  That number is the 0.17 mGal
        # STATIC measurement uncertainty (a bias, no /sqrt(Hz)), not the
        # short-term sensitivity.  The paper's actual static sensitivity is
        # 0.8 mGal/sqrt(Hz) = 8e-6 m/s^2/sqrt(Hz) (limited by the force-balance
        # accelerometer).  See bidel_2018_marine_static_uncertainty below for
        # the 0.17 mGal figure stored separately.
        description="Marine quantum gravimeter static short-term sensitivity "
        "(Bidel 2018): 0.8 mGal/sqrt(Hz)",
        value=8e-6,
        unit="m/s^2/sqrt(Hz)",
        source="Bidel et al., Nat. Commun. 9, 627 (2018), 'static' section",
        year=2018,
        tolerance_pct=50.0,
        doi="10.1038/s41467-018-03040-2",
    ),
    "bidel_2018_marine_static_uncertainty": PublishedReference(
        key="bidel_2018_marine_static_uncertainty",
        # Separated out in v1.0.2: the 0.17 mGal static MEASUREMENT
        # UNCERTAINTY (T=20 ms, 14 mm drop).  Distinct quantity from the
        # /sqrt(Hz) sensitivity above; stored without a /sqrt(Hz) dimension.
        description="Marine quantum gravimeter static measurement uncertainty "
        "(Bidel 2018): 0.17 mGal at T=20 ms",
        value=1.7e-6,
        unit="m/s^2",
        source="Bidel et al., Nat. Commun. 9, 627 (2018), 'static' section",
        year=2018,
        tolerance_pct=50.0,
        doi="10.1038/s41467-018-03040-2",
    ),
    # ------------------------------------------------------------------
    # USGS New Low Noise Model (Peterson 1993)
    # ------------------------------------------------------------------
    "nlnm_low_freq": PublishedReference(
        key="nlnm_low_freq",
        # CORRECTED in v1.0.2: was value=7e-10 (~ -183 dB), about 4 dB high.
        # The true NLNM acceleration-ASD minimum is ~4e-10 m/s^2/sqrt(Hz)
        # (-187.5 dB rel. (1 m/s^2)^2/Hz) at ~30-100 s period.  The NLNM is
        # strongly frequency-dependent, so this scalar is only the band
        # minimum; tolerance is wide.
        description="USGS New Low Noise Model acceleration ASD minimum "
        "(~30-100 s period band); strongly frequency-dependent",
        value=4e-10,
        unit="m/s^2/sqrt(Hz)",
        source="Peterson, USGS Open-File Report 93-322 (1993); "
        "conversion per Bormann, J. Seismology 2, 37 (1998)",
        year=1993,
        tolerance_pct=100.0,
        doi="10.3133/ofr93322",
    ),
    # ------------------------------------------------------------------
    # Retained from v0.7
    # ------------------------------------------------------------------
    "sg_noise_floor": PublishedReference(
        key="sg_noise_floor",
        # CORRECTED in v1.0.2: was value=1e-11 (= 1 nGal/sqrt(Hz)).  The
        # "1 nGal" figure from Hinderer/Crossley/Warburton is a frequency-
        # domain DETECTABILITY, not an amplitude spectral density.  The true
        # SG ASD noise floor is ~1-3e-9 m/s^2/sqrt(Hz); the best-site LSBB
        # value is 1.8e-9 m/s^2/sqrt(Hz) at 1 mHz (Van Camp et al. 2017).
        # ~100-300x higher than the old stored value.
        description="Best-site superconducting-gravimeter ASD noise floor "
        "(LSBB at 1 mHz); SG noise is strongly frequency-dependent",
        value=1.8e-9,
        unit="m/s^2/sqrt(Hz)",
        source="Van Camp et al., Rev. Geophys. 55 (2017), Fig. A11 / LSBB",
        year=2017,
        tolerance_pct=100.0,
        doi="10.1002/2017RG000566",
    ),
    "sg_detectability_nGal": PublishedReference(
        key="sg_detectability_nGal",
        # Separated out in v1.0.2: the 1 nGal frequency-domain detectability,
        # explicitly labelled as such (NOT an ASD).  1 nGal = 1e-11 m/s^2.
        description="Superconducting-gravimeter frequency-domain detectability "
        "(1 nGal); NOT an amplitude spectral density",
        value=1e-11,
        unit="m/s^2",
        source="Hinderer, Crossley & Warburton, Treatise on Geophysics (2007)",
        year=2007,
        tolerance_pct=100.0,
        doi="10.1016/B978-044452748-6.00058-4",
    ),
    "mz_visibility": PublishedReference(
        key="mz_visibility",
        # CLARIFIED in v1.0.2: the 0.5 value could NOT be confirmed in the
        # cited Peters 2001 primary text (the contrast figure is paywalled).
        # 0.5 is the idealised two-output Mach-Zehnder maximum, retained as a
        # generic reference rather than attributed to Peters 2001.  A
        # verified real-instrument contrast is 0.3 (Bidel et al. 2018).
        description="Idealised two-output Mach-Zehnder maximum fringe "
        "visibility (generic; real instruments report ~0.16-0.6)",
        value=0.5,
        unit="dimensionless",
        source="Idealised MZ value (unverified in Peters 2001; cf. "
        "Bidel et al. 2018 reports C=0.3)",
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


# Reference values that were numerically wrong in qgrav v1.0.0.  These are
# *the same keys* as in REFERENCES (no key rename) but with previously-wrong
# values that the user may have hard-coded into downstream noise budgets.
# Anyone seeing this dict during a debug session should reconsider whether
# their downstream analysis used the wrong value.
_V1_0_0_VALUE_BUGS: dict[str, tuple[float, float, str]] = {
    # key: (v1.0.0 value, v1.0.1 corrected value, reason)
    "hu_2013_short_term_noise": (
        4.2e-9,
        4.2e-8,
        "v1.0.0 had 4.2e-9 m/s^2/sqrt(Hz); the correct value is 4.2e-8 "
        "(4.2 microGal/sqrt(Hz) = 4.2e-8 m/s^2/sqrt(Hz)). Off by factor of 10.",
    ),
    "menoret_2018_short_term_noise": (
        5e-7,
        7.5e-7,
        "v1.0.0 had 5e-7 m/s^2/sqrt(Hz); the paper's Larzac Allan-deviation "
        "trace (Fig. 4) reports 750 nm/s^2/sqrt(Hz) = 7.5e-7.",
    ),
}


# Reference values fixed in v1.0.2 following the Topic-13 audit
# (docs/research/RESEARCH_REFERENCE_AUDIT.md).  Three were unit-category
# errors (a number transcribed correctly but tagged with the wrong physical
# quantity); two were ambiguous and were re-labelled.  Format:
#   key: (v1.0.1 value, v1.0.2 value, unit change, reason)
_V1_0_1_VALUE_BUGS: dict[str, tuple[float, float, str, str]] = {
    "kasevich_chu_1991_first_demo": (
        3e-6, 3e-6,
        "m/s^2/sqrt(Hz) -> dimensionless (delta_g/g at 1000 s)",
        "Value unchanged but RE-TYPED: 3e-6 is a dimensionless fractional "
        "resolution after 1000 s integration (sodium atoms), not an ASD. "
        "As an ASD it would be ~9e-4 m/s^2/sqrt(Hz).",
    ),
    "bidel_2018_marine": (
        1.7e-6, 8e-6,
        "m/s^2/sqrt(Hz) (unchanged dimension, corrected value)",
        "v1.0.1 stored the 0.17 mGal STATIC UNCERTAINTY as a sensitivity. "
        "The true static sensitivity is 0.8 mGal/sqrt(Hz) = 8e-6. The "
        "0.17 mGal figure is now a separate key bidel_2018_marine_static_uncertainty.",
    ),
    "sg_noise_floor": (
        1e-11, 1.8e-9,
        "m/s^2/sqrt(Hz) (corrected value)",
        "v1.0.1 stored the 1 nGal frequency-domain DETECTABILITY as an ASD. "
        "True SG ASD floor is ~1-3e-9 m/s^2/sqrt(Hz) (LSBB best site 1.8e-9 "
        "at 1 mHz). The 1 nGal figure is now key sg_detectability_nGal.",
    ),
    "nlnm_low_freq": (
        7e-10, 4e-10,
        "m/s^2/sqrt(Hz) (corrected value)",
        "v1.0.1 value was ~4 dB high (-183 dB). True NLNM acceleration-ASD "
        "minimum is ~4e-10 m/s^2/sqrt(Hz) (-187.5 dB) at ~30-100 s period.",
    ),
    "mz_visibility": (
        0.5, 0.5,
        "dimensionless (unchanged value, re-sourced)",
        "Value unchanged but the 0.5 could NOT be verified in Peters 2001 "
        "(paywalled figure). Re-labelled as the idealised MZ maximum, not "
        "attributed to Peters 2001. A verified real value is C=0.3 (Bidel 2018).",
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
