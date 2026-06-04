from __future__ import annotations

import numpy as np


def add_white_noise(x: np.ndarray, std: float, *, rng: np.random.Generator) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if std <= 0:
        return arr.copy()
    return arr + rng.normal(0.0, float(std), size=arr.shape)


def add_bias(x: np.ndarray, bias: float) -> np.ndarray:
    return np.asarray(x, dtype=np.float64) + float(bias)


def add_random_walk_drift(x: np.ndarray, step_std: float, *, rng: np.random.Generator) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if step_std <= 0:
        return arr.copy()
    return arr + np.cumsum(rng.normal(0.0, float(step_std), size=arr.shape))


def add_outlier_spikes(
    x: np.ndarray,
    *,
    rate: float,
    spike_std: float,
    rng: np.random.Generator,
) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64).copy()
    if rate <= 0 or spike_std <= 0:
        return arr
    mask = rng.uniform(0.0, 1.0, size=arr.shape) < float(rate)
    if np.any(mask):
        arr[mask] += rng.normal(0.0, float(spike_std), size=int(np.sum(mask)))
    return arr


def generate_vibration_timeseries(
    *,
    duration_s: float,
    sample_rate_hz: float,
    seismic_model: str = "nlnm",
    isolation_cutoff_hz: float = 0.0,
    seed: int | None = None,
) -> dict[str, np.ndarray]:
    """Generate a synthetic vibration time-series matching a Peterson PSD.

    Builds an acceleration time-series whose power spectral density (PSD)
    follows the New Low/High Noise Model (NLNM / NHNM) from Peterson 1993.
    An optional second-order high-pass isolation filter

        H^2(f) = f^4 / (f^2 + f_c^2)^2

    is applied to model a vibration isolation system with cutoff f_c.  The
    method:

    1. Build an rFFT frequency grid for the requested duration & sample rate.
    2. Interpolate the Peterson PSD at those frequencies.
    3. Multiply by the isolation filter ``H^2(f)``.
    4. Draw a complex random spectrum with magnitude ``sqrt(PSD*N*fs/4)``
       on real and imaginary parts (independent Gaussians).
    5. Inverse-rFFT to obtain a real-valued acceleration time-series.
    6. Compute velocity and displacement spectra by dividing by ``jω`` and
       ``-ω^2`` respectively (with DC handled as zero), then inverse-FFT.

    Parameters
    ----------
    duration_s : float
        Total duration of the time-series in seconds.
    sample_rate_hz : float
        Sampling rate in Hz.
    seismic_model : str
        ``"nlnm"`` (default) or ``"nhnm"``.
    isolation_cutoff_hz : float
        Cutoff frequency f_c of the isolation high-pass filter.  ``0.0``
        disables filtering.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    dict with keys ``t_s``, ``accel_m_s2``, ``velocity_m_s``,
    ``displacement_m``, ``psd_freq_hz``, ``psd_input_m_s2_2_per_hz``,
    ``psd_filtered_m_s2_2_per_hz``.
    """
    from qgrav.physics._seismic_models import interpolate_psd

    duration = float(duration_s)
    fs = float(sample_rate_hz)
    if duration <= 0:
        raise ValueError("duration_s must be > 0")
    if fs <= 0:
        raise ValueError("sample_rate_hz must be > 0")

    n = int(round(duration * fs))
    if n < 2:
        raise ValueError("duration_s * sample_rate_hz must give at least 2 samples")

    dt = 1.0 / fs
    t = np.arange(n) * dt

    # rFFT frequency grid (positive frequencies only)
    freqs = np.fft.rfftfreq(n, d=dt)
    n_freq = len(freqs)

    # Interpolate Peterson PSD at positive frequencies (PSD(0) = 0 by definition)
    psd_input = np.zeros_like(freqs)
    if np.any(freqs > 0):
        psd_input[freqs > 0] = interpolate_psd(freqs[freqs > 0], model=seismic_model)

    # Apply isolation filter H^2(f) = f^4 / (f^2 + f_c^2)^2
    if isolation_cutoff_hz > 0:
        f_c = float(isolation_cutoff_hz)
        H2 = (freqs**4) / ((freqs**2 + f_c**2) ** 2)
        psd_filtered = psd_input * H2
    else:
        psd_filtered = psd_input.copy()

    # Random complex spectrum: real & imag parts are independent Gaussians.
    # Scaling: for one-sided PSD P(f) such that variance = ∫P(f)df, the
    # rFFT amplitudes satisfy |X[k]|^2 = P(f_k) * fs * N / 2.  Splitting
    # equally between real and imaginary gives sigma = sqrt(P(f) * fs * N / 4).
    rng = np.random.default_rng(seed)
    sigma_per_bin = np.sqrt(psd_filtered * fs * n / 4.0)
    real_part = rng.normal(0.0, 1.0, size=n_freq) * sigma_per_bin
    imag_part = rng.normal(0.0, 1.0, size=n_freq) * sigma_per_bin
    # DC bin must be real
    imag_part[0] = 0.0
    # Nyquist bin must be real (only present for even N)
    if n % 2 == 0:
        imag_part[-1] = 0.0
    accel_spectrum = real_part + 1j * imag_part

    # Inverse rFFT -> real acceleration time series
    accel = np.fft.irfft(accel_spectrum, n=n)

    # Velocity = ∫a dt; in freq: divide by jω
    # Displacement = ∫∫a dt; in freq: divide by (jω)^2 = -ω^2
    omega = 2.0 * np.pi * freqs
    vel_spectrum = np.zeros_like(accel_spectrum)
    disp_spectrum = np.zeros_like(accel_spectrum)
    nonzero = freqs > 0
    vel_spectrum[nonzero] = accel_spectrum[nonzero] / (1j * omega[nonzero])
    disp_spectrum[nonzero] = -accel_spectrum[nonzero] / (omega[nonzero] ** 2)
    # Ensure Nyquist remains real for even n
    if n % 2 == 0:
        vel_spectrum[-1] = float(np.real(vel_spectrum[-1]))
        disp_spectrum[-1] = float(np.real(disp_spectrum[-1]))

    velocity = np.fft.irfft(vel_spectrum, n=n)
    displacement = np.fft.irfft(disp_spectrum, n=n)

    return {
        "t_s": t,
        "accel_m_s2": accel,
        "velocity_m_s": velocity,
        "displacement_m": displacement,
        "psd_freq_hz": freqs,
        "psd_input_m_s2_2_per_hz": psd_input,
        "psd_filtered_m_s2_2_per_hz": psd_filtered,
    }


def add_detection_noise(
    populations: np.ndarray,
    *,
    n_detected: int,
    seed: int | None = None,
) -> np.ndarray:
    """Add detection (shot) noise to population fractions.

    Each population value gets Gaussian noise with σ = 1/sqrt(N_detected),
    representing the projection-noise limit of a state-selective measurement
    on N atoms.  Results are clipped to [0, 1].

    Parameters
    ----------
    populations : array_like
        Population fractions (each in [0, 1]).
    n_detected : int
        Number of atoms detected per measurement.
    seed : int, optional
        Random seed.

    Returns
    -------
    Noisy populations array, clipped to [0, 1].
    """
    arr = np.asarray(populations, dtype=np.float64)
    n = int(n_detected)
    if n <= 0:
        raise ValueError("n_detected must be > 0")
    sigma = 1.0 / np.sqrt(float(n))
    rng = np.random.default_rng(seed)
    noisy = arr + rng.normal(0.0, sigma, size=arr.shape)
    return np.clip(noisy, 0.0, 1.0)


def spontaneous_emission_loss_probability(
    *,
    rabi_freq_rad_s: float,
    single_photon_detuning_hz: float,
    pulse_duration_s: float,
    excited_state_lifetime_s: float = 26.24e-9,
) -> float:
    """Probability of spontaneous emission loss during a Raman pulse.

    For a Raman transition with Rabi frequency Ω_eff and single-photon
    detuning Δ from the intermediate excited state, the population in the
    intermediate state scales as (Ω_eff / Δ)^2.  Integrated over the pulse
    duration τ, the spontaneous-emission loss probability is

        p_se = (Ω_eff / (2π Δ))^2 * τ / τ_sp

    where τ_sp is the excited-state lifetime (default 26.24 ns for Rb-87 D2).

    Parameters
    ----------
    rabi_freq_rad_s : float
        Effective Raman Rabi frequency Ω_eff in rad/s.
    single_photon_detuning_hz : float
        Single-photon detuning Δ from the intermediate state in Hz.
    pulse_duration_s : float
        Pulse duration τ in seconds.
    excited_state_lifetime_s : float
        Excited-state lifetime τ_sp in seconds.  Default 26.24 ns (Rb-87 D2).

    Returns
    -------
    Probability of spontaneous emission loss per atom per pulse.
    """
    omega_eff = float(rabi_freq_rad_s)
    delta_rad_s = 2.0 * np.pi * float(single_photon_detuning_hz)
    tau = float(pulse_duration_s)
    tau_sp = float(excited_state_lifetime_s)
    if delta_rad_s == 0:
        raise ValueError("single_photon_detuning_hz must be non-zero")
    if tau_sp <= 0:
        raise ValueError("excited_state_lifetime_s must be > 0")
    return float((omega_eff / delta_rad_s) ** 2 * tau / tau_sp)
