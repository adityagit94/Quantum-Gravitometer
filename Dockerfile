# qgrav — minimal headless container for batch runs and CI.
# Build:   docker build -t qgrav .
# Run:     docker run --rm -v "$PWD/configs:/work/configs" -v "$PWD/runs:/work/runs" qgrav run --config /work/configs/example.yaml
FROM python:3.11-slim AS base

# System deps for matplotlib + scipy + git (for editable installs from a clone).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip \
    && pip install . \
    && rm -rf /root/.cache/pip

# Default workdir for mounted configs/runs.
WORKDIR /work
ENTRYPOINT ["qgrav"]
CMD ["--help"]
