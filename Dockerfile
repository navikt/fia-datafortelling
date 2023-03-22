FROM python:3.9

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl \
    jq

RUN cd /opt && \
    QUARTO_VERSION=$(curl https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest | jq '.tag_name' | sed -e 's/[\"v]//g') && \
    wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    tar -zxvf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    rm -rf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    echo "export PATH=${PATH}:/opt/quarto-${QUARTO_VERSION}/bin" >> /etc/profile

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY main.qmd .

ENTRYPOINT ["quarto"]

RUN curl -X PUT -F file=@main.html \
        https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
        -H 'Authorization:Bearer ${QUARTO_TOKEN}'