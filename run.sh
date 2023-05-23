#!/bin/bash

quarto render index.qmd

curl -X PUT -F index.html=@index.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

quarto render datakvalitet.qmd

curl -X PUT -F index.html=@datakvalitet.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_DATAKVALITET} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"