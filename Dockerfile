ARG PYTHON_VERSION=3.13.1

FROM python:${PYTHON_VERSION} AS compile-image

# Endre til feks arm64 for å bygge for Apple Silicon Mac
# ENV CPU=arm64
ENV CPU=amd64

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl \
    jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN QUARTO_VERSION=$(curl https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest | jq '.tag_name' | sed -e 's/[\"v]//g') && \
    wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz && \
    tar -xvzf quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz && \
    ln -s quarto-${QUARTO_VERSION} quarto-dist && \
    rm -rf quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN touch README.md

COPY uv.lock pyproject.toml ./
COPY src/ src/

RUN uv sync --frozen --no-dev  --compile-bytecode
# Compiling Python source files to bytecode is typically desirable for production images as it tends to improve startup time (at the cost of increased installation time).

FROM python:${PYTHON_VERSION}-slim AS runner-image

RUN apt-get update && apt-get install -yq --no-install-recommends \
      curl \
    && apt-get upgrade -y curl \
    && apt-get purge -y imagemagick git-man golang libexpat1-dev \
    && apt-get -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1069 python && \
    useradd -r -u 1069 -g python python

WORKDIR /home/python

COPY --chown=python:python --from=compile-image /.venv /home/python/.venv
COPY --chown=python:python --from=compile-image quarto-dist/ quarto-dist/
RUN ln -s /home/python/quarto-dist/bin/quarto /usr/local/bin/quarto

ENV PATH="/home/python/.venv/bin:$PATH"

COPY main.py index.qmd datakvalitet.qmd _quarto.yml ./
COPY data/ data/
COPY src/ src/
COPY assets/ assets/
COPY datafortellinger/ datafortellinger/

RUN chown python:python /home/python -R

ENV DENO_DIR=/home/python/deno
ENV XDG_CACHE_HOME=/home/python/cache
ENV XDG_DATA_HOME=/home/python/share

USER 1069
ENTRYPOINT ["python",  "main.py"]
