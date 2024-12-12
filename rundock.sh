#!/bin/bash

set -e

export ADC=/path/to/adc
export GCP_PROJECT=pia-dev-214a
export DATASET=pia_bigquery_sink_v1_dataset_dev

if [ ! -f "$ADC" ]; then
  echo "      ----     "
  echo "      ----     "
  echo "Finner ikke ADC fil spesifisert ($ADC)!"
  echo "Kjør kommandoen 'gcloud auth application-default login' for å generere credentials. Lim så path inn i ADC variabelen."
  echo "NB! Husk å sjekk at du genererer for riktig prosjekt. Nåværende prosjekt er $(gcloud config get-value project)."
  echo "For å oppdatere dette bruk 'gcloud config set project PROSJEKTID'"
  echo "      ----     "
  echo "      ----     "
  exit 1
fi


if gcloud auth application-default print-access-token &> /dev/null; then
    echo "ADC er gyldig"
else
    echo "ADC er ikke lenger gyldig. Starter auth prosess."
    echo "gcloud auth application-default login"
    sleep 1
    gcloud auth application-default login
fi

docker build . -t docker-fia-datafortelling --platform=linux/amd64

docker run \
-e DRYRUN="true" \
-e GCP_PROJECT=$GCP_PROJECT \
-e DATASET=$DATASET \
-e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/adc.json \
-v $ADC:/tmp/keys/adc.json:ro \
docker-fia-datafortelling
