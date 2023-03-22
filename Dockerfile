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

RUN mkdir /.cache
RUN chmod 777 /.cache
RUN mkdir main_files
RUN chmod 777 main_files
RUN chmod 777 .


COPY main.qmd .
COPY run.sh .

ENTRYPOINT ["./run.sh"]