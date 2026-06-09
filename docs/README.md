# qgrav documentation

Start with the **[Complete guide](COMPLETE_GUIDE.md)**. The documents below are
grouped by purpose. A rendered version (MkDocs) is published from this folder;
see `mkdocs.yml` for the site navigation.

## Start here
| Document | What it covers |
|----------|----------------|
| [COMPLETE_GUIDE.md](COMPLETE_GUIDE.md) | The full user guide: install, run, configure, interpret results. |
| [GUI.md](GUI.md) | The six-tab desktop workbench, screen by screen. |
| [REPRODUCTION.md](REPRODUCTION.md) | Reproducing a pipeline run from a config. |

## Real-data analysis
| Document | What it covers |
|----------|----------------|
| [REAL_GRAVITY_DATA.md](REAL_GRAVITY_DATA.md) | Ingesting IGETS / GGP / CSV gravimetry data. |

## Physics and validation
| Document | What it covers |
|----------|----------------|
| [V1_PHYSICS_UPGRADE.md](V1_PHYSICS_UPGRADE.md) | The emergent-gravity simulation design and equations. |
| [AISIM_GRAVIMETER_STUDIES.md](AISIM_GRAVIMETER_STUDIES.md) | What each study model computes and means. |
| [AISIM_INTEGRATION.md](AISIM_INTEGRATION.md) | How the vendored AISim core is integrated and extended. |
| [SCIENTIFIC_HARDENING.md](SCIENTIFIC_HARDENING.md) | What is fully simulated vs hybrid vs analytical. |
| [SCIENTIFIC_PACKAGE_EVALUATION.md](SCIENTIFIC_PACKAGE_EVALUATION.md) | Which scientific packages were evaluated and why. |
| [PHYSICS_REVIEW_PACKET.md](PHYSICS_REVIEW_PACKET.md) | Self-contained packet for an external physics reviewer. |
| [PERFORMANCE.md](PERFORMANCE.md) | Benchmark numbers and scaling notes. |
| [SCIENTIFIC_NOTES.md](SCIENTIFIC_NOTES.md) | Assorted physics notes. |

## Architecture and internals
| Document | What it covers |
|----------|----------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Module map and data flow. |
| [PATCHES_AND_ARCHITECTURE_NOTES.md](PATCHES_AND_ARCHITECTURE_NOTES.md) | The vendor-subclass override strategy. |

## Project and process
| Document | What it covers |
|----------|----------------|
| [ROADMAP_V1_TO_V2.md](ROADMAP_V1_TO_V2.md) | Development roadmap toward v2.0. |
| [AI_USAGE_DISCLOSURE.md](AI_USAGE_DISCLOSURE.md) | How AI assistance was used and verified. |
| [REVIEW_REQUEST_TEMPLATE.md](REVIEW_REQUEST_TEMPLATE.md) | Outreach template for requesting expert review. |

## Supporting material
- [`research/`](research/) - raw background-research notes compiled while building
  qgrav. These are working notes (sources and parameter derivations), not polished
  documentation; the conclusions are folded into the documents above.
- [`THIRD_PARTY_LICENSES/`](THIRD_PARTY_LICENSES/) - licenses of vendored code.
- `reviewer_notebook.ipynb` - executable companion to the physics-review packet.
