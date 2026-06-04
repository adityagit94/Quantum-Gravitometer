# Security Policy

## Supported versions

qgrav is a research codebase under active development. Fixes are applied to the
latest released version on the `main` branch.

| Version | Supported |
|---------|-----------|
| 1.3.x   | ✅ |
| < 1.3   | ❌ |

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

- **Preferred:** GitHub → *Security* → *Report a vulnerability* (private
  vulnerability reporting) on
  <https://github.com/adityagit94/Quantum-Gravitometer>.
- **Alternatively:** email the maintainer at `aditya_2312res46@iitp.ac.in`.

Please include a description, reproduction steps, and the affected version. You
can expect an acknowledgement within a few working days.

## Scope

qgrav is a simulation and data-analysis tool with **no network services and no
hardware control**, so the attack surface is small. The most relevant concerns
are the handling of untrusted input files:

- Loading a **YAML config** or a **dataset** (`.ggp` / CSV / `.zip`) runs this
  package's parsers on that input. Only run configs and datasets you trust.
- Dependency vulnerabilities (numpy, scipy, matplotlib, pyyaml, jinja2). qgrav
  uses `yaml.safe_load` (never `yaml.load`) and does not `eval` config content.
