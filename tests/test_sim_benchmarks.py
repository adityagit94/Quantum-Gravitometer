from qgrav.sim_ai import phase_mach_zehnder


def test_phase_mach_zehnder_simple():
    k_eff = 1.0e7
    a = 9.81
    T = 0.1
    phi = phase_mach_zehnder(k_eff, a, T)
    # float tolerance: use a small absolute tolerance (phase can be large)
    assert abs(phi - (k_eff * a * T * T)) < 1e-6
