#!/bin/bash

quarto render index.qmd

FILER="-F index.html=@index.html"
for FYLKESNAVN in "Oslo" "Rogaland" "Møre og Romsdal" "Nordland" "Vest-Viken" "Øst-Viken" "Innlandet" "Vestfold og Telemark" "Agder" "Vestland" "Trøndelag" "Troms og Finnmark"
do
    export FYLKESNAVN
    export FILNAVN=`echo "datafortelling_per_fylke_$FYLKESNAVN.html" | sed 's/ /_/g'`
    quarto render datafortelling_per_fylke.qmd --output $FILNAVN
    FILER="$FILER -F $FILNAVN=@$FILNAVN"
done

curl -X PUT $FILER \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

quarto render datakvalitet.qmd

curl -X PUT -F index.html=@datakvalitet.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_DATAKVALITET} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"
