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

WORKDIR /tmp/quarto
COPY --from=compile-image /opt/venv /opt/venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=compile-image quarto-dist/ quarto-dist/
RUN ln -s /tmp/quarto/quarto-dist/bin/quarto /usr/local/bin/quarto
COPY run.sh .
COPY code/ code/
COPY main.qmd .

ENV DENO_DIR=/tmp/quarto/deno
ENV XDG_CACHE_HOME=/tmp/quarto/cache
ENV XDG_DATA_HOME=/tmp/quarto/share

RUN chown 1069:1069 /tmp/quarto -R
USER 1069:1069

ENTRYPOINT ["./run.sh"]
