"""Regression tests for ``qgrav.physics.constants``.

These tests pin the numerical values to their cited sources so that any
inadvertent edit produces a test failure with a clear message.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from qgrav.physics import constants as C


def test_codata_speed_of_light_is_exact():
    assert C.C_LIGHT.value == 299_792_458.0
    assert C.C_LIGHT.unit == "m/s"


def test_codata_hbar_value():
    # CODATA 2018: hbar = h / (2*pi) with h = 6.62607015e-34 J*s exactly.
    expected = 6.626_070_15e-34 / (2.0 * math.pi)
    assert math.isclose(C.H_BAR.value, expected, rel_tol=1e-9)


def test_rb87_wavelength_matches_steck():
    """Steck Rb-87 D Line Data v2.2.1 (2019): lambda_D2 = 780.241 209 686 nm."""
    assert math.isclose(C.WAVELENGTH_RB87_D2.value, 780.241_209_686e-9, rel_tol=1e-12)


def test_keff_rb87_d2_derives_from_wavelength():
    """k_eff = 2 * (2 pi / lambda) for counter-propagating Raman."""
    expected = 2.0 * (2.0 * math.pi / C.WAVELENGTH_RB87_D2.value)
    assert math.isclose(C.K_EFF_RB87_D2.value, expected, rel_tol=1e-12)
    # Numerical value approximately 1.6105747e7 rad/m
    assert math.isclose(C.K_EFF_RB87_D2.value, 1.6105747e7, rel_tol=1e-4)


def test_rb87_recoil_velocity_consistent():
    """v_rec = hbar * k_laser / m  (single-photon recoil)."""
    expected = C.H_BAR.value * C.K_LASER_RB87_D2.value / C.MASS_RB87.value
    assert math.isclose(C.RECOIL_VELOCITY_RB87_D2.value, expected, rel_tol=1e-12)
    # ~ 5.8845 mm/s in literature
    assert math.isclose(C.RECOIL_VELOCITY_RB87_D2.value, 5.8845e-3, rel_tol=5e-3)


def test_rb87_recoil_energy_approx_3771_hz():
    """Steck quotes single-photon recoil frequency ~ 3.7710 kHz."""
    assert math.isclose(C.RECOIL_ENERGY_RB87_D2_HZ.value, 3771.0, rel_tol=5e-3)


def test_earth_rotation_rate_iers_2010():
    """IERS Conventions 2010: 7.2921150e-5 rad/s."""
    assert math.isclose(C.OMEGA_EARTH.value, 7.292_115_0e-5, rel_tol=1e-9)


def test_free_air_gradient_heiskanen_moritz():
    """Heiskanen & Moritz (1967): 3.086e-6 /s^2 per m."""
    assert math.isclose(C.FREE_AIR_GRADIENT.value, 3.086e-6, rel_tol=1e-6)


def test_standard_gravity_exact():
    """3rd CGPM (1901): g_n = 9.80665 m/s^2 exactly."""
    assert C.STANDARD_GRAVITY.value == 9.806_65


def test_cs133_hyperfine_si_second_definition():
    """SI second: 9 192 631 770 Hz exactly."""
    assert C.HYPERFINE_CS133.value == 9_192_631_770.0


def test_all_constants_have_source_field():
    for name, const in C.all_constants().items():
        assert const.source, f"{name} missing source"


def test_no_stray_wavelength_literal_in_systematics():
    """Regression: systematics.py must not hard-code 780e-9 or 7.2921e-5.

    Constants are now imported from qgrav.physics.constants. This test
    enforces that fact so accidental future edits are caught.
    """
    sys_file = Path(__file__).parent.parent / "src" / "qgrav" / "physics" / "systematics.py"
    raw = sys_file.read_text(encoding="utf-8")
    # Strip triple-quoted docstrings and single-line comments so we only check
    # actual code statements.
    no_docstrings = re.sub(r'(?s)""".*?"""', "", raw)
    code_only = re.sub(r"#[^\n]*", "", no_docstrings)
    forbidden_literals = [
        r"\b7\.2921e-5\b",
        r"\b3\.086e-6\b",
        r"=\s*9\.81\b",
    ]
    for pattern in forbidden_literals:
        assert not re.search(pattern, code_only), (
            f"systematics.py code contains forbidden literal matching {pattern!r}; "
            f"use the constants module instead."
        )


def test_aisim_adapter_uses_constants_for_defaults():
    """Function defaults in aisim_adapter.py reference the constants module.

    The bare literals ``780e-9`` and the bare default ``= 9.81`` were replaced
    in v0.8 with references to WAVELENGTH_RB87_D2 and NOMINAL_GRAVITY.
    """
    path = Path(__file__).parent.parent / "src" / "qgrav" / "sim_ai" / "aisim_adapter.py"
    text = path.read_text(encoding="utf-8")
    # Function-signature defaults must reference the constants module.
    assert (
        "wavelength_m: float = 780e-9" not in text
    ), "Replace bare default with WAVELENGTH_RB87_D2.value"
    assert "gravity_center_m_s2: float = 9.81" not in text
    assert "gravity_ref_m_s2: float = 9.81" not in text
    # Also catch the sim_cfg.get(..., 9.81) literal fallbacks: those should
    # also use NOMINAL_GRAVITY.value.
    no_docstrings = re.sub(r'(?s)""".*?"""', "", text)
    code_only = re.sub(r"#[^\n]*", "", no_docstrings)
    # 9.81 appearing immediately after a comma is the dispatcher default
    # fallback pattern. NOMINAL_GRAVITY.value carries the same value.
    assert ", 9.81)" not in code_only, "Use NOMINAL_GRAVITY.value as the fallback in sim_cfg.get()"
    # 780e-9 literal as a numeric fallback should be gone too.
    assert (
        ", 780e-9)" not in code_only
    ), "Use WAVELENGTH_RB87_D2.value as the fallback in sim_cfg.get()"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
