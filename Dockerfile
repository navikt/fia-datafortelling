ARG PYTHON_VERSION=3.13.7

FROM python:${PYTHON_VERSION} AS compile-image

ENV CPU=amd64
# for å bygge for Apple Silicon Mac til local kjøring:
# ENV CPU=arm64

RUN apt-get update \
    && apt-get install -yq --no-install-recommends curl jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN QUARTO_VERSION=$(curl https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest | jq '.tag_name' | sed -e 's/[\"v]//g') && \
    wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz && \
    tar -xvzf quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz && \
    ln -s quarto-${QUARTO_VERSION} quarto-dist && \
    rm -rf quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN touch README.md

COPY uv.lock pyproject.toml ./
COPY src/ src/

RUN uv sync --frozen --no-dev --compile-bytecode

FROM python:${PYTHON_VERSION}-slim AS runner-image
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /home/python

RUN apt-get update \
    && apt-get install -yq --no-install-recommends curl \
    && apt-get upgrade -y curl \
    && apt-get purge -y imagemagick git-man golang libexpat1-dev \
    && apt-get -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1069 python && \
    useradd -r -u 1069 -g python python

COPY --from=compile-image ./.venv ./.venv
COPY --from=compile-image /quarto-dist ./quarto-dist
RUN ln -s /home/python/quarto-dist/bin/quarto /usr/local/bin/quarto

ENV PATH="/home/python/.venv/bin:$PATH" \
    QUARTO_PYTHON="/home/python/.venv/bin/python" \
    PYTHONUNBUFFERED=1 \
    DENO_DIR=/home/python/deno \
    XDG_CACHE_HOME=/home/python/cache \
    XDG_DATA_HOME=/home/python/share


# Config for quarto website
COPY _quarto.yml .
COPY index.qmd .
COPY main.py .



# Python scripts
COPY src/ /src

# Datafortellinger
COPY datafortelling/ datafortelling/
# Assets (logo)
COPY assets/ assets/


RUN chown python:python /home/python -R

USER 1069

ENTRYPOINT ["python",  "main.py"]
