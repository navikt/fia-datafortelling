ARG PYTHON_VERSION=3.13.2

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

# Config for quarto website
COPY _quarto.yml .

# Main script for rendering av quarto og opplasting
COPY main.py .

# Generelle datafortellinger
COPY index.qmd .
COPY datakvalitet.qmd .

# Fia Tall
COPY datafortelling_fia.qmd .
COPY fia_agder.qmd .
COPY fia_innlandet.qmd .
COPY fia_more_og_romsdal.qmd .
COPY fia_nordland.qmd .
COPY fia_norge.qmd .
COPY fia_oslo.qmd .
COPY fia_ost-viken.qmd .
COPY fia_rogaland.qmd .
COPY fia_troms_og_finnmark.qmd .
COPY fia_trondelag.qmd .
COPY fia_vest-viken.qmd .
COPY fia_vestfold_og_telemark.qmd .
COPY fia_vestland.qmd .


# Samarbeid datafortelling
COPY datafortelling_samarbeid.qmd .
COPY fia_agder_samarbeid.qmd .
COPY fia_innlandet_samarbeid.qmd .
COPY fia_more_og_romsdal_samarbeid.qmd .
COPY fia_nordland_samarbeid.qmd .
COPY fia_norge_samarbeid.qmd .
COPY fia_oslo_samarbeid.qmd .
COPY fia_ost-viken_samarbeid.qmd .
COPY fia_rogaland_samarbeid.qmd .
COPY fia_troms_og_finnmark_samarbeid.qmd .
COPY fia_trondelag_samarbeid.qmd .
COPY fia_vest-viken_samarbeid.qmd .
COPY fia_vestfold_og_telemark_samarbeid.qmd .
COPY fia_vestland_samarbeid.qmd .

# Samarbeid datafortelling
COPY datafortelling_samarbeidsplan.qmd .
COPY fia_agder_samarbeidsplan.qmd .
COPY fia_innlandet_samarbeidsplan.qmd .
COPY fia_more_og_romsdal_samarbeidsplan.qmd .
COPY fia_nordland_samarbeidsplan.qmd .
COPY fia_norge_samarbeidsplan.qmd .
COPY fia_oslo_samarbeidsplan.qmd .
COPY fia_ost-viken_samarbeidsplan.qmd .
COPY fia_rogaland_samarbeidsplan.qmd .
COPY fia_troms_og_finnmark_samarbeidsplan.qmd .
COPY fia_trondelag_samarbeidsplan.qmd .
COPY fia_vest-viken_samarbeidsplan.qmd .
COPY fia_vestfold_og_telemark_samarbeidsplan.qmd .
COPY fia_vestland_samarbeidsplan.qmd .

# Data, assets, kode og qmd-filer inkludert i datafortellinger
COPY data/ data/
COPY src/ src/
COPY assets/ assets/
COPY includes/ includes/

RUN chown python:python /home/python -R

ENV DENO_DIR=/home/python/deno
ENV XDG_CACHE_HOME=/home/python/cache
ENV XDG_DATA_HOME=/home/python/share

USER 1069

ENTRYPOINT ["python",  "main.py"]
