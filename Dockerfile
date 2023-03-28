FROM python:3.11 AS compile-image

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl \
    jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN QUARTO_VERSION=$(curl https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest | jq '.tag_name' | sed -e 's/[\"v]//g') && \
    wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    tar -xvzf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    ln -s quarto-${QUARTO_VERSION} quarto-dist && \
    rm -rf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz


FROM python:3.11-slim AS runner-image

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -g 999 python && \
    useradd -r -u 999 -g python python

WORKDIR /quarto
COPY --chown=python:python --from=compile-image /opt/venv /opt/venv
COPY --chown=python:python --from=compile-image quarto-dist/ quarto-dist/
RUN ln -s /quarto/quarto-dist/bin/quarto /usr/local/bin/quarto

ENV PATH="/opt/venv/bin:$PATH"
RUN python3 -m venv /opt/venv

COPY run.sh .
COPY code/ /tmp/quarto/project/code/
COPY main.qmd /tmp/quarto/project/

RUN chown python:python /quarto -R
RUN chown python:python /tmp/quarto -R

ENV DENO_DIR=/tmp/quarto/deno
ENV XDG_CACHE_HOME=/tmp/quarto/cache
ENV XDG_DATA_HOME=/tmp/quarto/share

USER 999
ENTRYPOINT ["./run.sh"]
