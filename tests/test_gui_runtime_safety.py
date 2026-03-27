from pathlib import Path

import matplotlib

from qgrav.gui import QGravApp


def test_gui_module_uses_tk_or_agg_backend():
    backend = str(matplotlib.get_backend()).lower()
    assert backend in {"tkagg", "agg"}
