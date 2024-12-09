ARG PYTHON_VERSION=3.12.7

# TODO: Se på -bookworm eller -buster
FROM python:${PYTHON_VERSION} as builder

# RUN apt-get update && apt-get install -yq --no-install-recommends \
#     curl \
#     jq && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

ENV QUARTO_VERSION=1.6.39 \
    CPU=arm64
    # sett til: 'CPU=arm64' for å installere Quarto for ARM (f.eks. Apple silicon).

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl \
    jq

# Hent quarto
RUN wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz && \
    tar -xvzf quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz && \
    rm -rf quarto-${QUARTO_VERSION}-linux-${CPU}.tar.gz && \
    mv quarto-${QUARTO_VERSION} /quarto

# Installerer Poetry og avhengigheter

ENV POETRY_VERSION=1.8.4 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install --root-user-action=ignore --upgrade pip poetry==${POETRY_VERSION}

WORKDIR /app

# Kopier prosjekt config
COPY pyproject.toml poetry.lock ./

# 4. Installer virtuelt miljø uten dev og test dependencies && fjern cached 
RUN poetry install --without dev,test --no-root && rm -rf $POETRY_CACHE_DIR

############################# RUNTIME ##############################################

FROM python:${PYTHON_VERSION}-slim AS runtime



# Installerer nødvendige pakker og fjerner sårbarheter
RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl \
    && apt-get upgrade -y curl \
    && apt-get purge -y golang \
    && apt-get -y autoremove \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Oppretter en bruker
RUN groupadd -g 1069 python && \
    useradd -r -u 1069 -g python python


# Kopierer Quarto fra builder-stadiet
COPY --from=builder /quarto /quarto
RUN ln -s /quarto/bin/quarto /usr/local/bin/quarto


# Kopier virtuelt miljø
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
COPY --chown=python:python --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}


ENV DENO_DIR=/app/deno
ENV XDG_CACHE_HOME=/app/cache
ENV XDG_DATA_HOME=/app/share

# Kopierer nødvendige filer
COPY run.sh .
# run.sh
COPY _quarto.yml .
# quarto project config
COPY /src ./src

RUN chown python:python /app -R
USER python
ENTRYPOINT ["./run.sh"]