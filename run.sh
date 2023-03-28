#!/bin/bash

quarto render main.qmd

curl -X PUT -F file=@main.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

find ./main_files -type f -exec curl -X PUT -F file=@{} https://${NADA_ENV}/quarto/update/${QUARTO_ID} -H "Authorization:Bearer ${QUARTO_TOKEN}" \;