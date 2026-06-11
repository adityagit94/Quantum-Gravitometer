"""Physical constants used throughout qgrav.

Every constant is exposed as a :class:`PhysicalConstant` dataclass instance with
its value, SI unit, citable source, and (where known) standard uncertainty.

This module is the single source of truth: do not write bare numerical literals
for these quantities anywhere else in the codebase. See
``tests/test_physics_constants.py`` for the regression check that enforces this
for files in ``physics/``, ``sim_ai/``, and ``validation/``.

References
----------
- CODATA 2018 recommended values, https://physics.nist.gov/cuu/Constants/
- Steck, D.A., *Rubidium 87 D Line Data*, rev. 2.2.1 (2019),
  https://steck.us/alkalidata/
- Steck, D.A., *Cesium D Line Data*, rev. 2.2.1 (2019)
- IERS Conventions 2010, IERS Technical Note 36
- Heiskanen, W. and Moritz, H., *Physical Geodesy*, Freeman (1967)
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class PhysicalConstant:
    """A single physical constant with provenance.

    Attributes
    ----------
    name:
        Short identifier, e.g. ``"speed_of_light"``.
    value:
        Numerical value in SI units (unless otherwise noted in ``unit``).
    unit:
        SI unit string.
    source:
        Citable provenance (CODATA edition, paper, conventions document).
    uncertainty:
        Standard uncertainty in the same unit as ``value``. ``None`` if exact
        (e.g. defined constants) or not quoted in the source.
    note:
        Free-text note explaining derivation or applicable conditions.
    """

    name: str
    value: float
    unit: str
    source: str
    uncertainty: float | None = None
    note: str = ""

    def __float__(self) -> float:  # convenience for arithmetic
        return float(self.value)


# ---------------------------------------------------------------------------
# Fundamental constants (CODATA 2018)
# ---------------------------------------------------------------------------

C_LIGHT = PhysicalConstant(
    name="speed_of_light",
    value=299_792_458.0,
    unit="m/s",
    source="CODATA 2018 (exact)",
    uncertainty=0.0,
)

H_BAR = PhysicalConstant(
    name="reduced_planck_constant",
    value=1.054_571_817e-34,
    unit="J*s",
    source="CODATA 2018 (exact, h = 6.62607015e-34 J*s)",
    uncertainty=0.0,
)

K_BOLTZMANN = PhysicalConstant(
    name="boltzmann_constant",
    value=1.380_649e-23,
    unit="J/K",
    source="CODATA 2018 (exact)",
    uncertainty=0.0,
)

ATOMIC_MASS_UNIT = PhysicalConstant(
    name="atomic_mass_unit",
    value=1.660_539_066_60e-27,
    unit="kg",
    source="CODATA 2018",
    uncertainty=5.0e-37,
)


# ---------------------------------------------------------------------------
# Atom data (Rubidium-87)
# ---------------------------------------------------------------------------

MASS_RB87 = PhysicalConstant(
    name="mass_Rb87",
    value=1.443_160_648e-25,
    unit="kg",
    source="Steck Rb-87 D Line Data v2.2.1 (2019), 86.909 180 520 u",
    uncertainty=7.2e-34,
)

HYPERFINE_RB87 = PhysicalConstant(
    name="hyperfine_frequency_Rb87",
    value=6_834_682_610.904_29,
    unit="Hz",
    source="Steck Rb-87 D Line Data v2.2.1 (2019); SI second realization",
    uncertainty=0.0,
    note="Ground-state |F=1> <-> |F=2> splitting; defined exactly under the "
    "SI second redefinition but quoted to nominal precision here.",
)

WAVELENGTH_RB87_D2 = PhysicalConstant(
    name="wavelength_Rb87_D2",
    value=780.241_209_686e-9,
    unit="m",
    source="Steck Rb-87 D Line Data v2.2.1 (2019)",
    uncertainty=1.3e-17,
    note="D2 line (5S1/2 -> 5P3/2) in vacuum.",
)

K_LASER_RB87_D2 = PhysicalConstant(
    name="laser_wavevector_Rb87_D2",
    value=2.0 * math.pi / 780.241_209_686e-9,
    unit="rad/m",
    source="2*pi / wavelength_Rb87_D2 (derived)",
    note="Single-photon laser wavevector for Rb-87 D2.",
)

K_EFF_RB87_D2 = PhysicalConstant(
    name="effective_wavevector_Rb87_D2_counterpropagating",
    value=2.0 * (2.0 * math.pi / 780.241_209_686e-9),
    unit="rad/m",
    source="2 * 2*pi / 780.241209686e-9 m (Steck Rb-87 D Line Data v2.2.1, 2019)",
    note="Counterpropagating Raman: k_eff = k1 - k2 with |k1| ~ |k2| ~ 2*pi/lambda. "
    "Numerically ~ 1.6105747e7 rad/m.",
)

RECOIL_VELOCITY_RB87_D2 = PhysicalConstant(
    name="recoil_velocity_Rb87_D2",
    value=H_BAR.value * (2.0 * math.pi / 780.241_209_686e-9) / 1.443_160_648e-25,
    unit="m/s",
    source="hbar * k_laser / m_Rb87 (derived)",
    note="Single-photon recoil velocity ~ 5.8845 mm/s. Two-photon recoil for "
    "counterpropagating Raman is twice this value.",
)

RECOIL_ENERGY_RB87_D2_HZ = PhysicalConstant(
    name="recoil_energy_Rb87_D2",
    value=(H_BAR.value * (2.0 * math.pi / 780.241_209_686e-9) ** 2)
    / (2.0 * 1.443_160_648e-25 * 2.0 * math.pi),
    unit="Hz",
    source="hbar * k_laser^2 / (2 * m_Rb87 * 2*pi) (derived)",
    note="Single-photon recoil frequency ~ 3.7710 kHz.",
)

ZEEMAN_QUADRATIC_RB87 = PhysicalConstant(
    name="quadratic_zeeman_Rb87_clock",
    value=575.15,
    unit="Hz/G^2",
    source="Steck Rb-87 D Line Data v2.2.1 (2019)",
    note="|F=1, m=0> <-> |F=2, m=0> clock transition second-order Zeeman.",
)


# ---------------------------------------------------------------------------
# Atom data (Caesium-133)
# ---------------------------------------------------------------------------

MASS_CS133 = PhysicalConstant(
    name="mass_Cs133",
    value=2.207_169_675e-25,
    unit="kg",
    source="Steck Cs D Line Data v2.2.1 (2019), 132.905 451 96 u",
    uncertainty=1.1e-33,
)

HYPERFINE_CS133 = PhysicalConstant(
    name="hyperfine_frequency_Cs133",
    value=9_192_631_770.0,
    unit="Hz",
    source="SI second definition (exact)",
    uncertainty=0.0,
)

WAVELENGTH_CS_D2 = PhysicalConstant(
    name="wavelength_Cs_D2",
    value=852.347_275_82e-9,
    unit="m",
    source="Steck Cs D Line Data v2.2.1 (2019)",
    uncertainty=2.7e-17,
)

ZEEMAN_QUADRATIC_CS133 = PhysicalConstant(
    name="quadratic_zeeman_Cs133_clock",
    value=426.7,
    unit="Hz/G^2",
    source="Steck Cs D Line Data v2.2.1 (2019)",
    note="|F=3, m=0> <-> |F=4, m=0> clock transition second-order Zeeman, "
    "in Hz/G^2 (some literature quotes 0.4267 kHz/G^2 equivalently).",
)


# ---------------------------------------------------------------------------
# Geophysical / geodetic
# ---------------------------------------------------------------------------

OMEGA_EARTH = PhysicalConstant(
    name="earth_rotation_rate",
    value=7.292_115_0e-5,
    unit="rad/s",
    source="IERS Conventions 2010 (IERS TN 36)",
    note="Mean sidereal rotation rate.",
)

FREE_AIR_GRADIENT = PhysicalConstant(
    name="free_air_vertical_gravity_gradient",
    value=3.086e-6,
    unit="1/s^2 per m",
    source="Heiskanen & Moritz, Physical Geodesy (1967), §2.13",
    note="Magnitude; gravity decreases upward at this rate near Earth's "
    "surface. Sign convention varies; we use the positive magnitude.",
)

STANDARD_GRAVITY = PhysicalConstant(
    name="standard_gravity",
    value=9.806_65,
    unit="m/s^2",
    source="3rd CGPM (1901), definition of standard gravity g_n",
    uncertainty=0.0,
)

NOMINAL_GRAVITY = PhysicalConstant(
    name="nominal_gravity",
    value=9.81,
    unit="m/s^2",
    source="Approximate mean gravity at Earth's surface; used as default "
    "operating point for sweeps.",
    note="Use STANDARD_GRAVITY for the exact CGPM-defined value.",
)

EARTH_RADIUS_MEAN = PhysicalConstant(
    name="earth_radius_mean",
    value=6.371_0e6,
    unit="m",
    source="IUGG mean radius",
    note="Volumetric mean radius.",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def all_constants() -> dict[str, PhysicalConstant]:
    """Return every :class:`PhysicalConstant` defined at module scope.

    Useful for HTML report 'Constants used' appendices and for the regression
    test that scans for stray numerical literals.
    """
    out: dict[str, PhysicalConstant] = {}
    for key, val in globals().items():
        if isinstance(val, PhysicalConstant):
            out[key] = val
    return out


__all__ = [
    "PhysicalConstant",
    "C_LIGHT",
    "H_BAR",
    "K_BOLTZMANN",
    "ATOMIC_MASS_UNIT",
    "MASS_RB87",
    "HYPERFINE_RB87",
    "WAVELENGTH_RB87_D2",
    "K_LASER_RB87_D2",
    "K_EFF_RB87_D2",
    "RECOIL_VELOCITY_RB87_D2",
    "RECOIL_ENERGY_RB87_D2_HZ",
    "ZEEMAN_QUADRATIC_RB87",
    "MASS_CS133",
    "HYPERFINE_CS133",
    "WAVELENGTH_CS_D2",
    "ZEEMAN_QUADRATIC_CS133",
    "OMEGA_EARTH",
    "FREE_AIR_GRADIENT",
    "STANDARD_GRAVITY",
    "NOMINAL_GRAVITY",
    "EARTH_RADIUS_MEAN",
    "all_constants",
]
