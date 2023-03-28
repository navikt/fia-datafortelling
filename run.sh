#!/bin/bash

quarto render /tmp/quarto/project/main.qmd --to html --execute-dir /tmp/quarto/project

curl -X PUT -F file=@/tmp/quarto/project/main.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"
