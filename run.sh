#!/bin/bash
set -e
# Vil helst at jobben stopper om et steg feiler

# path til python miljø
export PATH="$(pwd)/.venv/bin:$PATH"

# ----------------- Fia helsesjekk
quarto render src/helsesjekk.qmd --no-clean --output-dir "output"

# ----------------- Fia datakvalitet
quarto render src/datakvalitet.qmd --no-clean --output-dir "output"

# ----------------- En datafortelling om de nye løsningene i Fia
quarto render src/teampia.qmd --no-clean --output-dir "output"

# ----------------- Fia datafortelling - Hovedside
quarto render src/index.qmd --no-clean --output-dir "output"
FILER="-F index.html=@src/output/index.html"

# ----------------- Fia datafortelling - Leveranser
quarto render src/ia_tjenester.qmd --no-clean --output-dir "output"
FILER="$FILER -F ia_tjenester.html=@src/output/ia_tjenester.html"

# ----------------- Fia datafortelling - Per resultatområde
RESULTATOMRADER=("Oslo" "Rogaland" "Møre og Romsdal" "Nordland" "Vest-Viken" "Øst-Viken" "Innlandet" "Vestfold og Telemark" "Agder" "Vestland" "Trøndelag" "Troms og Finnmark")

for n in "${RESULTATOMRADER[@]}"
do
    export RESULTATOMRADE=`echo "$n" | sed 's/ /_/g'`

    quarto render src/datafortelling_per_resultatområde.qmd --no-clean --output-dir "output/$RESULTATOMRADE"
    OUTPUT_FILNAVN="src/output/$RESULTATOMRADE/datafortelling_per_resultatområde.html"
    FILER="$FILER -F datafortelling_per_resultatområde_$RESULTATOMRADE.html=@$OUTPUT_FILNAVN"

    quarto render src/ia_tjenester_per_resultatområde.qmd --no-clean --output-dir "output/$RESULTATOMRADE"
    OUTPUT_FILNAVN="src/output/$RESULTATOMRADE/ia_tjenester_per_resultatområde.html"
    FILER="$FILER -F ia_tjenester_per_resultatområde_$RESULTATOMRADE.html=@$OUTPUT_FILNAVN"

done

if [[ -z "$DRYRUN" ]]; then
  # ----------------- Oppdater datafortellinger i NADA

  # ----------------- Fia helsesjekk
  curl -X PUT -F index.html=@src/output/helsesjekk.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_HELSESJEKK} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

  # ----------------- Fia datakvalitet
  curl -X PUT -F index.html=@src/output/datakvalitet.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_DATAKVALITET} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

  # ----------------- En datafortelling om de nye løsningene i Fia
  curl -X PUT -F index.html=@src/output/teampia.html \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID_TEAMPIA} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"

  # ----------------- Fia datafortelling - "hovedside", "leveranser" og "per resultatområde"
  curl -X PUT $FILER \
    https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
    -H "Authorization:Bearer ${QUARTO_TOKEN}"
fi