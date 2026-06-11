"""Enable ``python -m qgrav.gui`` as an alternative to the ``qgrav-gui`` /
``qgrav gui`` console entry points."""

from qgrav.gui.app import main

if __name__ == "__main__":
    main()
