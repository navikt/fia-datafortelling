#!/bin/bash

quarto render test.qmd

curl -X PUT -F file=@test.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"
