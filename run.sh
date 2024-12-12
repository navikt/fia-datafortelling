#!/bin/bash
set -e
# Vil helst at jobben stopper om et steg feiler

# ----------------- Fia helsesjekk
quarto render helsesjekk.qmd

# ----------------- Fia datakvalitet
quarto render datakvalitet.qmd

# ----------------- En datafortelling om de nye løsningene i Fia
quarto render teampia.qmd

# ----------------- Fia datafortelling - Hovedside
quarto render index.qmd
FILER="-F index.html=@index.html"


# ----------------- Fia datafortelling - Leveranser
quarto render ia_tjenester.qmd
FILER="$FILER -F ia_tjenester.html=@ia_tjenester.html"

# ----------------- Fia datafortelling - Per resultatområde
for RESULTATOMRADE in "Oslo" "Rogaland" "Møre og Romsdal" "Nordland" "Vest-Viken" "Øst-Viken" "Innlandet" "Vestfold og Telemark" "Agder" "Vestland" "Trøndelag" "Troms og Finnmark"
do
    export RESULTATOMRADE

    export FILNAVN=`echo "datafortelling_per_resultatområde_$RESULTATOMRADE.html" | sed 's/ /_/g'`
    quarto render datafortelling_per_resultatområde.qmd --output $FILNAVN
    FILER="$FILER -F $FILNAVN=@$FILNAVN"

    export FILNAVN=`echo "ia_tjenester_per_resultatområde_$RESULTATOMRADE.html" | sed 's/ /_/g'`
    quarto render ia_tjenester_per_resultatområde.qmd --output $FILNAVN
    FILER="$FILER -F $FILNAVN=@$FILNAVN"
done

if [[ -z "$DRYRUN" ]]; then
  # ----------------- Oppdater datafortellinger i NADA

  # ----------------- Fia helsesjekk
  curl -X PUT -F index.html=@helsesjekk.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_HELSESJEKK} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

  # ----------------- Fia datakvalitet
  curl -X PUT -F index.html=@datakvalitet.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_DATAKVALITET} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

  # ----------------- En datafortelling om de nye løsningene i Fia
  curl -X PUT -F index.html=@teampia.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_TEAMPIA} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

  # ----------------- Fia datafortelling - "hovedside", "leveranser" og "per resultatområde"
  curl -X PUT $FILER \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"
fi