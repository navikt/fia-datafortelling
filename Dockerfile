ARG PYTHON_VERSION=3.14
ARG QUARTO_VERSION=1.10.18

FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:${PYTHON_VERSION}-dev AS compile-image

ARG QUARTO_VERSION
USER root
WORKDIR /home/python

ENV CPU=amd64
# for å bygge for Apple Silicon Mac til local kjøring:
# ENV CPU=arm64

RUN apk add --no-cache coreutils wget

RUN case "$CPU" in \
        amd64) SHA256=afad071b5bd22c02f2d300695743189d3650e0537a53073e654b630cff2b0c73 ;; \
        arm64) SHA256=f6a07df68e25330b5df34f65d3df66bca605acce3b830c593a58e91884d4cf6c ;; \
        *) echo "Unsupported CPU: $CPU" >&2; exit 1 ;; \
    esac && \
    wget "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz" && \
    echo "${SHA256}  quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz" | sha256sum -c - && \
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

FROM europe-north1-docker.pkg.dev/cgr-nav/pull-through/nav.no/python:${PYTHON_VERSION}-dev AS runner-image
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

COPY --chown=1069:1069 docker-diagnostic.py .
RUN ["/home/python/.venv/bin/python", "docker-diagnostic.py"]

RUN ["/home/python/.venv/bin/python", "-c", "import shutil, subprocess, tempfile; tempfile.TemporaryFile(dir='.').close(); tempfile.TemporaryFile(dir='pages').close(); q = shutil.which('quarto'); assert q, 'quarto not found in PATH'; print(f'QUARTO_PATH={q}', flush=True); subprocess.run([q, '--version'], check=True)"]
RUN ["/home/python/.venv/bin/python", "-c", "import pathlib, shutil, subprocess; subprocess.run(['quarto', 'render', 'index.qmd'], check=True); assert pathlib.Path('pages/index.html').is_file(); shutil.rmtree('pages'); pathlib.Path('pages').mkdir()"]

ENTRYPOINT ["/home/python/.venv/bin/python", "main.py"]
