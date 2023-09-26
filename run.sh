#!/bin/bash

quarto render index.qmd

curl -X PUT -F index.html=@index.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

for FYLKE in "Oslo" "Rogaland" "Møre og Romsdal" "Nordland" "Vest-Viken" "Øst-Viken" "Innlandet" "Vestfold og Telemark" "Agder" "Vestland" "Trøndelag" "Troms og Finnmark"
do 
    export FYLKESNAVN=$FYLKE
    quarto render datafortelling_per_fylke.qmd --output "datafortelling_per_fylke_$FYLKESNAVN.html"
    curl -X PUT -F datafortelling_per_fylke_$FYLKESNAVN.html=@datafortelling_per_fylke_$FYLKESNAVN.html \
        https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
        -H "Authorization:Bearer ${QUARTO_TOKEN}"
done

quarto render datakvalitet.qmd

curl -X PUT -F index.html=@datakvalitet.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_DATAKVALITET} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"