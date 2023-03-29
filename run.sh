#!/bin/bash

quarto render index.qmd

curl -X PUT -F file=@index.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"
