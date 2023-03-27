FROM python:3.11-slim-buster AS setup-image

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -yq --no-install-recommends \
    wget \
    curl \
    jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN QUARTO_VERSION=$(curl https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest | jq '.tag_name' | sed -e 's/[\"v]//g') && \
    wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    tar -xvzf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    ln -s quarto-${QUARTO_VERSION} quarto-dist && \
    rm -rf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz


FROM python:3.11-slim-buster AS runner-image

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /quarto
COPY --from=setup-image /opt/venv /opt/venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=setup-image quarto-dist/ quarto-dist/
RUN ln -s /quarto/quarto-dist/bin/quarto /usr/local/bin/quarto
COPY run.sh .
COPY code/ code/
COPY main.qmd .

ENV DENO_DIR=/quarto/deno
ENV XDG_CACHE_HOME=/quarto/cache
ENV XDG_DATA_HOME=/quarto/share

RUN chown 1069:1069 /quarto -R
USER 1069:1069

ENTRYPOINT ["./run.sh"]
