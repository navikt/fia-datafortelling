#!/bin/bash

quarto render helsesjekk.qmd

curl -X PUT -F index.html=@helsesjekk.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_HELSESJEKK} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

quarto render index.qmd

FILER="-F index.html=@index.html"
for RESULTATOMRADE in "Oslo" "Rogaland" "Møre og Romsdal" "Nordland" "Vest-Viken" "Øst-Viken" "Innlandet" "Vestfold og Telemark" "Agder" "Vestland" "Trøndelag" "Troms og Finnmark"
do
    export RESULTATOMRADE
    export FILNAVN=`echo "datafortelling_per_resultatområde_$RESULTATOMRADE.html" | sed 's/ /_/g'`
    quarto render datafortelling_per_resultatområde.qmd --output $FILNAVN
    FILER="$FILER -F $FILNAVN=@$FILNAVN"
done

curl -X PUT $FILER \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

quarto render datakvalitet.qmd

curl -X PUT -F index.html=@datakvalitet.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_DATAKVALITET} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

quarto render teampia.qmd

curl -X PUT -F index.html=@teampia.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_TEAMPIA} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"
