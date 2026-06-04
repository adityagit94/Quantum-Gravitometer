import importlib


def test_gui_imports():
    mod = importlib.import_module("qgrav.gui")
    assert hasattr(mod, "QGravApp")


def test_gui_module_entrypoint_importable():
    """`python -m qgrav.gui` must resolve (a __main__.py exposing main)."""
    mod = importlib.import_module("qgrav.gui.__main__")
    assert hasattr(mod, "main")

