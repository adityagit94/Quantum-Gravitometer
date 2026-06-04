# AISim integration (v1.0.0)

The repository includes a **patched** vendored `aisim` package and a wrapper module:

- `src/qgrav/vendor/aisim/` - vendored upstream AISim with local v1.0 physics patches
- `src/qgrav/sim_ai/aisim_adapter.py` - high-level qgrav-side wrapper

## Available models

| Model | Backend kwargs | Scope |
|-------|----------------|-------|
| `rabi_scan` | `pre_pulse_delay_s`, `tau_step_s`, `n_steps` | FULLY_SIMULATED |
| `mach_zehnder_phase_scan` | `tau_pi_half_s`, `interferometer_time_s`, `phase_min_rad`, `phase_max_rad`, `n_phase_points` | FULLY_SIMULATED |
| `gravity_sweep` | `gravity_center_m_s2`, `gravity_span_m_s2`, `n_gravity_points`, **`gravity_propagation`** (v1.0), **`gravity_gradient_per_m`** (v1.0) | HYBRID or FULLY_SIMULATED (v1.0) |
| `vibration_sensitivity_sweep` | `vibration_frequency_hz`, `amplitude_min_m`, `amplitude_max_m`, **`gravity_propagation`** (v1.0) | HYBRID or FULLY_SIMULATED (v1.0) |
| `multi_drop_cycle` (v1.0) | `n_drops`, `cycle_time_s`, `gravity_true_m_s2`, `gravity_propagation`, `detection_noise_enabled`, `n_detected_per_drop`, `servo_enabled`, `servo_gain` | FULLY_SIMULATED |

## What the v1.0 patches change

Three local patches in the vendored AISim:

1. **`GravityFreePropagator`** (`vendor/aisim/prop.py`) - new class. Performs exact ballistic kinematics under uniform gravity with optional linear gradient. Sibling of upstream `FreePropagator`. Exported through `vendor/aisim/__init__.py`.

2. **Chirped `Wavevectors`** (`vendor/aisim/beam.py`) - adds `chirp_rate_rad_per_s2` parameter. The `doppler_shift` method returns `-v_z*k_eff + chirp_rate*atoms.time`. For `chirp_rate=0` (the default) the function is byte-identical to upstream.

3. **Integrated laser phase + AC Stark** in `TwoLevelTransitionPropagator._prop_matrix` (`vendor/aisim/prop.py`) - replaces `exp(-i*delta*t0)` with `exp(-i*(-k_eff*z(t0) + 0.5*chirp*t0**2))` as the laser-phase imprint at each pulse. Adds optional `single_photon_detuning_hz` for AC Stark `Ω_eff²/(4Δ)`. `SpatialSuperpositionTransitionPropagator` forwards both kwargs to the base class.

For atoms at z=0 with constant velocity and zero chirp, the new imprint reduces exactly to the old `delta*t0`. The change matters only for time-varying detuning (falling atoms with a chirped laser), where the upstream formula double-counts gravity and chirp phases.

The patches are clearly marked with `[LOCAL PATCH]` comments and documented in `docs/V1_PHYSICS_UPGRADE.md`.

## License

The vendored AISim code is derived from the upstream `aisim` package (GPL-3.0). See `docs/THIRD_PARTY_LICENSES/AISim-LICENSE.txt` for details and license status. The local v1.0 patches are also under GPL-3.0.

## See also

- `docs/V1_PHYSICS_UPGRADE.md` - full design rationale and equations for the v1.0 patches.
- `docs/AISIM_GRAVIMETER_STUDIES.md` - scientific meaning of each AISim study.
- `docs/SCIENTIFIC_HARDENING.md` - what is fully simulated vs hybrid.
- `docs/ARCHITECTURE.md` - module map and dependency rules.
