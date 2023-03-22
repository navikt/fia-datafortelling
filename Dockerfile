FROM python:3.9

USER root

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl

ENV QUARTO_VERSION=1.2.335

RUN cd /opt && \
    wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    tar -zxvf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    rm -rf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY main.qmd .
COPY run.sh .

ENV DENO_DIR=/tmp/deno

ENTRYPOINT ["./run.sh"]