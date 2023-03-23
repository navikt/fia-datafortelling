FROM python:3.11

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl \
    jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /quarto

RUN QUARTO_VERSION=$(curl https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest | jq '.tag_name' | sed -e 's/[\"v]//g') && \
    wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    tar -xvzf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    ln -s /quarto/quarto-${QUARTO_VERSION}/bin/quarto /usr/local/bin/quarto && \
    rm -rf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz

COPY run.sh .

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY main.qmd .

ENV DENO_DIR=/quarto/deno
ENV XDG_CACHE_HOME=/quarto/cache
ENV XDG_DATA_HOME=/quarto/share

RUN chown 1069:1069 /quarto -R

USER 1069:1069

ENTRYPOINT ["./run.sh"]
