#!/bin/bash
set -e

MAPPE_HELSESJEKK="src/quarto/helsesjekk"
quarto render $MAPPE_HELSESJEKK/helsesjekk.qmd

MAPPE_FIA="src/quarto/fia"
quarto render $MAPPE_FIA/index.qmd
FILER="-F index.html=@$MAPPE_FIA/index.html"

MAPPE_IA_TJENESTER="src/quarto/ia_tjenester"
quarto render $MAPPE_IA_TJENESTER/ia_tjenester.qmd
FILER="$FILER -F ia_tjenester.html=@$MAPPE_IA_TJENESTER/ia_tjenester.html"

MAPPE_RESULTATOMRADE="src/quarto/resultatområde"

for RESULTATOMRADE in "Oslo" "Rogaland" "Møre og Romsdal" "Nordland" "Vest-Viken" "Øst-Viken" "Innlandet" "Vestfold og Telemark" "Agder" "Vestland" "Trøndelag" "Troms og Finnmark"
do

    OUTPUT_DIR=`echo "$MAPPE_RESULTATOMRADE/$RESULTATOMRADE" | sed 's/ /_/g'`
    
    export RESULTATOMRADE
    
    quarto render $MAPPE_RESULTATOMRADE/datafortelling_per_resultatområde.qmd --output-dir $OUTPUT_DIR

    FILNAVN=`echo "datafortelling_per_resultatområde_$RESULTATOMRADE.html" | sed 's/ /_/g'`
    FILER="$FILER -F $FILNAVN=@$OUTPUT_DIR/$MAPPE_RESULTATOMRADE/datafortelling_per_resultatområde.html"

    quarto render $MAPPE_RESULTATOMRADE/ia_tjenester_per_resultatområde.qmd --output-dir $OUTPUT_DIR

    FILNAVN=`echo "ia_tjenester_per_resultatområde_$RESULTATOMRADE.html" | sed 's/ /_/g'`
    FILER="$FILER -F $FILNAVN=@$OUTPUT_DIR/$MAPPE_RESULTATOMRADE/ia_tjenester_per_resultatområde.html"
done


MAPPE_DATAKVALITET="src/quarto/fia_datakvalitet"
quarto render $MAPPE_DATAKVALITET/datakvalitet.qmd 

MAPPE_PIA="src/quarto/pia"
quarto render $MAPPE_PIA/teampia.qmd

# curl -X PUT -F index.html=@$MAPPE_HELSESJEKK/helsesjekk.html \
#     https://${NADA_ENV}/quarto/update/${QUARTO_ID_HELSESJEKK} \
#     -H "Authorization:Bearer ${QUARTO_TOKEN}"

# curl -X PUT -F index.html=@$MAPPE_DATAKVALITET/datakvalitet.html \
#     https://${NADA_ENV}/quarto/update/${QUARTO_ID_DATAKVALITET} \
#     -H "Authorization:Bearer ${QUARTO_TOKEN}"

# curl -X PUT -F index.html=@$MAPPE_PIA/teampia.html \
#     https://${NADA_ENV}/quarto/update/${QUARTO_ID_TEAMPIA} \
#     -H "Authorization:Bearer ${QUARTO_TOKEN}"

# curl -X PUT $FILER \
#     https://${NADA_ENV}/quarto/update/${QUARTO_ID} \
#     -H "Authorization:Bearer ${QUARTO_TOKEN}"
