import importlib


def test_gui_imports():
    mod = importlib.import_module("qgrav.gui")
    assert hasattr(mod, "QGravApp")
