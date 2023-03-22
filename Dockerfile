FROM python:3.9

USER root

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl

ENV QUARTO_VERSION=1.2.335

RUN cd /opt && \
    wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    tar -zxvf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    rm -rf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz

WORKDIR /tmp/quarto

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY main.qmd .
COPY run.sh .

RUN chown 1069:1069 /tmp/quarto -R
ENV DENO_DIR=/tmp/quarto/deno
ENV XDG_CACHE_HOME=/tmp/cache
USER 1069

ENTRYPOINT ["./run.sh"]