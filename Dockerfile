FROM python:3.9

COPY main.qmd .
COPY requirements.txt .

RUN apt-get update && apt-get install -yq --no-install-recommends \
    curl \
    jq

RUN cd /opt && \
    QUARTO_VERSION=$(curl https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest | jq '.tag_name' | sed -e 's/[\"v]//g') && \
#    QUARTO_VERSION="1.2.335" && \
    wget https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    tar -zxvf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    rm -rf quarto-${QUARTO_VERSION}-linux-amd64.tar.gz && \
    echo "export PATH=${PATH}:/opt/quarto-${QUARTO_VERSION}/bin" >> /etc/profile


RUN pip3 install -r requirements.txt

CMD ["python3", "main.py"]