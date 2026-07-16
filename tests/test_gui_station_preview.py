"""The Data Browser station preview computation must be Tk-free (it runs on
a worker thread) and produce plottable arrays for the preview figure."""

from __future__ import annotations

import numpy as np

from qgrav.gui._tab_data_browser import _compute_station_preview


def test_compute_station_preview_on_sample_data(sample_data_path):
    preview = _compute_station_preview(str(sample_data_path), "ap046")

    data = preview["data"]
    assert data["station_code"] == "ap046"
    assert len(np.asarray(data["gravity_residual"])) > 0

    adev = preview["adev"]
    assert len(np.asarray(adev["taus_s"])) > 0
    assert np.all(np.isfinite(np.asarray(adev["adev"])))

    psd = preview["psd"]
    assert len(np.asarray(psd["f_hz"])) > 0
    assert np.all(np.asarray(psd["psd"]) >= 0.0)
