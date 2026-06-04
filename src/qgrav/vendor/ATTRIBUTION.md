# Vendored third-party code

qgrav vendors two third-party packages under `src/qgrav/vendor/` so that runs are
reproducible against a pinned copy. Both licenses are compatible with qgrav's
own `GPL-3.0-or-later`. Full credit to the upstream authors.

| Package | Upstream | Author(s) | License | Role in qgrav |
|---------|----------|-----------|---------|----------------|
| `aisim` | https://github.com/bleykauf/aisim | Bastian Leykauf et al. | GPL-3.0-or-later | Semiclassical atom-interferometer / atom-optics simulator — the simulation core. |
| `allantools` | https://github.com/aewallin/allantools | Anders Wallin | LGPL-3.0-or-later | Allan / overlapping-Allan deviation and related frequency-stability statistics. |

## Modifications

The vendored sources are kept **unmodified** so they can be diffed against
upstream. qgrav's physics changes to AISim (the integrated-laser-phase propagator,
chirped wavevectors, gravity free-propagator, AC-Stark correction) live in
`src/qgrav/sim_ai/_aisim_overrides.py` as **subclasses**, not in-place edits — see
`docs/PATCHES_AND_ARCHITECTURE_NOTES.md`. A regression test
(`tests/test_vendor_aisim_unmodified.py`) guards that the vendored tree is not
patched.

If you redistribute qgrav, these upstream notices and licenses must be preserved.
