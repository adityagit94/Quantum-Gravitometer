import matplotlib
import pytest

try:
    import tkinter  # noqa: F401
except ImportError:  # pragma: no cover - depends on the Python build
    pytest.skip("Tk not available in this Python build", allow_module_level=True)

# Importing the GUI is the point: it must not switch the matplotlib backend.
from qgrav.gui import QGravApp  # noqa: E402,F401


def test_gui_module_uses_tk_or_agg_backend():
    backend = str(matplotlib.get_backend()).lower()
    assert backend in {"tkagg", "agg"}
