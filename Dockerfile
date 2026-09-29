ARG PYTHON_VERSION=3.14

FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:${PYTHON_VERSION}-dev AS compile-image

USER root
WORKDIR /home/python

ENV CPU=amd64
# for å bygge for Apple Silicon Mac til local kjøring:
# ENV CPU=arm64

RUN apk add --no-cache jq wget

RUN QUARTO_VERSION=$(wget -qO- https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest | jq -r '.tag_name' | sed -e 's/^v//') && \
    wget "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz" && \
    python -c "import tarfile; tarfile.open('quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz', 'r:gz').extractall('.')" && \
    mv "quarto-${QUARTO_VERSION}" quarto-dist && \
    rm "quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN touch README.md

COPY uv.lock pyproject.toml ./
COPY src/ src/

RUN uv sync --frozen --no-dev --compile-bytecode && \
    mkdir -p /runtime/pages /runtime/deno /runtime/cache /runtime/share && \
    mv .venv quarto-dist /runtime/

FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:${PYTHON_VERSION} AS runner-image
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY --from=compile-image --chown=1069:1069 /runtime/ /home/python/
WORKDIR /home/python

ENV HOME="/home/python" \
    PATH="/home/python/.venv/bin:/home/python/quarto-dist/bin:$PATH" \
    QUARTO_PYTHON="/home/python/.venv/bin/python" \
    PYTHONUNBUFFERED=1 \
    DENO_DIR=/home/python/deno \
    XDG_CACHE_HOME=/home/python/cache \
    XDG_DATA_HOME=/home/python/share

# Config for quarto
COPY --chown=1069:1069 _quarto.yml .
COPY --chown=1069:1069 index.qmd .
COPY --chown=1069:1069 main.py .
# Python scripts
COPY --chown=1069:1069 src/ /src
# Datafortellinger
COPY --chown=1069:1069 datafortelling/ datafortelling/
# Assets (logo)
COPY --chown=1069:1069 assets/ assets/

USER 1069:1069

RUN ["/home/python/.venv/bin/python", "-c", "import subprocess, tempfile; tempfile.TemporaryFile(dir='.').close(); tempfile.TemporaryFile(dir='pages').close(); subprocess.run(['quarto', '--version'], check=True)"]

ENTRYPOINT ["/home/python/.venv/bin/python", "main.py"]
