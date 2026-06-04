"""Tests for GravityFreePropagator — Phase 1 of v1.0 upgrade."""
from __future__ import annotations

import numpy as np
import pytest

from qgrav.vendor.aisim import AtomicEnsemble
from qgrav.sim_ai import GravityFreePropagator  # v1.1: moved to overrides (Phase 12)


def _single_atom(x=0.0, y=0.0, z=0.0, vx=0.0, vy=0.0, vz=0.0, state=None):
    """Create a 1-atom ensemble at specified phase-space point."""
    psv = np.array([[x, y, z, vx, vy, vz]], dtype=np.float64)
    atoms = AtomicEnsemble(psv, state_kets=[1, 0] if state is None else state)
    return atoms


# --- Phase 1.3 tests ---

class TestGravityPositionUpdate:
    """Test exact ballistic kinematics under uniform gravity."""

    def test_gravity_position_update(self):
        """Atom at rest falls under g=9.81: z(0.1) = -0.04905 m, vz = -0.981 m/s."""
        atoms = _single_atom(z=0.0, vz=0.0)
        prop = GravityFreePropagator(time_delta=0.1, g_m_s2=9.81)
        result = prop.propagate(atoms)
        expected_z = -0.5 * 9.81 * 0.1**2  # -0.04905
        expected_vz = -9.81 * 0.1           # -0.981
        np.testing.assert_allclose(result.position[0, 2], expected_z, atol=1e-12)
        np.testing.assert_allclose(result.velocity[0, 2], expected_vz, atol=1e-12)

    def test_gravity_with_initial_velocity(self):
        """Atom with vz=1.0 under g=9.81: z(0.1) = 1.0*0.1 - 0.5*9.81*0.01."""
        atoms = _single_atom(z=0.0, vz=1.0)
        prop = GravityFreePropagator(time_delta=0.1, g_m_s2=9.81)
        result = prop.propagate(atoms)
        expected_z = 1.0 * 0.1 - 0.5 * 9.81 * 0.01
        expected_vz = 1.0 - 9.81 * 0.1
        np.testing.assert_allclose(result.position[0, 2], expected_z, atol=1e-12)
        np.testing.assert_allclose(result.velocity[0, 2], expected_vz, atol=1e-12)


class TestGravityPreservesXY:
    """Gravity acts only on z; xy motion is pure drift."""

    def test_gravity_preserves_xy(self):
        """vx=1.0, vy=0.5, dt=0.1 → x=0.1, y=0.05, no gravity effect on xy."""
        atoms = _single_atom(x=0.0, y=0.0, vx=1.0, vy=0.5)
        prop = GravityFreePropagator(time_delta=0.1, g_m_s2=9.81)
        result = prop.propagate(atoms)
        np.testing.assert_allclose(result.position[0, 0], 0.1, atol=1e-12)
        np.testing.assert_allclose(result.position[0, 1], 0.05, atol=1e-12)
        # vx, vy unchanged
        np.testing.assert_allclose(result.velocity[0, 0], 1.0, atol=1e-12)
        np.testing.assert_allclose(result.velocity[0, 1], 0.5, atol=1e-12)


class TestGravityWithGradient:
    """Test gravity gradient g(z) = g₀ + γ·(z − z_ref)."""

    def test_gravity_with_gradient(self):
        """At z=0 with z_ref=0, gradient shouldn't change g from g₀."""
        atoms = _single_atom(z=0.0, vz=0.0)
        prop_uniform = GravityFreePropagator(time_delta=0.1, g_m_s2=9.81)
        prop_gradient = GravityFreePropagator(
            time_delta=0.1, g_m_s2=9.81, gravity_gradient_per_m=3.086e-6, z_ref_m=0.0
        )
        r1 = prop_uniform.propagate(atoms)
        r2 = prop_gradient.propagate(atoms)
        # At z=0, gradient term is zero → identical results
        np.testing.assert_allclose(r1.position[0, 2], r2.position[0, 2], atol=1e-12)
        np.testing.assert_allclose(r1.velocity[0, 2], r2.velocity[0, 2], atol=1e-12)

    def test_gradient_changes_g_away_from_ref(self):
        """At z=100m above z_ref=0, gradient adds γ·100 to g."""
        gamma = 3.086e-6  # typical vertical gradient, 1/s²
        g0 = 9.81
        z0 = 100.0
        g_eff = g0 + gamma * z0  # 9.8100003086
        atoms = _single_atom(z=z0, vz=0.0)
        prop = GravityFreePropagator(
            time_delta=0.1, g_m_s2=g0, gravity_gradient_per_m=gamma, z_ref_m=0.0
        )
        result = prop.propagate(atoms)
        expected_z = z0 - 0.5 * g_eff * 0.1**2
        np.testing.assert_allclose(result.position[0, 2], expected_z, atol=1e-12)


class TestGravityTwoStepsEqualsOne:
    """Two half-steps should equal one full step for uniform g (exact)."""

    def test_gravity_two_steps_equals_one(self):
        atoms = _single_atom(z=0.0, vz=2.0)
        dt = 0.1
        # One full step
        prop_full = GravityFreePropagator(time_delta=dt, g_m_s2=9.81)
        r_full = prop_full.propagate(atoms)
        # Two half steps
        prop_half = GravityFreePropagator(time_delta=dt / 2, g_m_s2=9.81)
        r_half = prop_half.propagate(atoms)
        r_half = prop_half.propagate(r_half)
        np.testing.assert_allclose(r_full.position[0, 2], r_half.position[0, 2], atol=1e-12)
        np.testing.assert_allclose(r_full.velocity[0, 2], r_half.velocity[0, 2], atol=1e-12)


class TestGravityStateUnchanged:
    """Quantum state must be identical before and after gravity propagation."""

    def test_gravity_state_unchanged(self):
        atoms = _single_atom(state=[1, 0])
        prop = GravityFreePropagator(time_delta=0.1, g_m_s2=9.81)
        result = prop.propagate(atoms)
        # state_kets should be unchanged (identity matrix applied)
        np.testing.assert_array_equal(atoms.state_kets, result.state_kets)

    def test_gravity_superposition_state_unchanged(self):
        """Even a superposition state must be preserved."""
        state = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        atoms = _single_atom(state=state)
        prop = GravityFreePropagator(time_delta=0.1, g_m_s2=9.81)
        result = prop.propagate(atoms)
        np.testing.assert_allclose(
            np.abs(result.state_kets[0].flatten()),
            np.abs(atoms.state_kets[0].flatten()),
            atol=1e-15,
        )


class TestGravityTimeUpdate:
    """Ensure atoms.time is correctly advanced."""

    def test_time_updated(self):
        atoms = _single_atom()
        assert atoms.time == 0.0
        prop = GravityFreePropagator(time_delta=0.26, g_m_s2=9.81)
        result = prop.propagate(atoms)
        np.testing.assert_allclose(result.time, 0.26, atol=1e-15)

    def test_original_not_mutated(self):
        """propagate() returns a copy — original is unchanged."""
        atoms = _single_atom(z=0.0, vz=0.0)
        prop = GravityFreePropagator(time_delta=0.1, g_m_s2=9.81)
        _ = prop.propagate(atoms)
        assert atoms.position[0, 2] == 0.0
        assert atoms.velocity[0, 2] == 0.0
        assert atoms.time == 0.0
