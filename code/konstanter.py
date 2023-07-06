statusordre = [
    "NY",
    "VURDERES",
    "KONTAKTES",
    "KARTLEGGES",
    "VI_BISTÅR",
    "FULLFØRT",
    "IKKE_AKTUELL",
    "SLETTET",
]

fylker = {
    "03": "Oslo",
    "11": "Rogaland",
    "15": "Møre og Romsdal",
    "18": "Nordland",
    "V30": "Vest-Viken",
    "Ø30": "Øst-Viken",
    "34": "Innlandet",
    "38": "Vestfold og Telemark",
    "42": "Agder",
    "46": "Vestland",
    "50": "Trøndelag",
    "54": "Troms og Finnmark",
}

intervall_sortering = [
    "0-1 min",
    "1-10 min",
    "10-60 min",
    "1-8 timer",
    "8-24 timer",
    "1-10 dager",
    "10-30 dager",
    "30-100 dager",
    "100-365 dager",
    "fra 365 dager",
]

plotly_colors = [
    "#636EFA",
    "#EF553B",
    "#00CC96",
    "#AB63FA",
    "#FFA15A",
    "#19D3F3",
    "#FF6692",
    "#B6E880",
    "#FF97FF",
    "#FECB52",
]

ikkeaktuell_hovedgrunn = {
    # NAV
    "IKKE_DIALOG_MELLOM_PARTENE": "NAV",
    "FOR_FÅ_TAPTE_DAGSVERK": "NAV",
    # Virksomhet
    "VIRKSOMHETEN_ØNSKER_IKKE_SAMARBEID": "Virksomhet",
    "VIRKSOMHETEN_HAR_IKKE_RESPONDERT": "Virksomhet",
}

# Gamle begrunnelser, fra før 30-06-2023
gamle_ikkeaktuell_hovedgrunn = {
    # NAV
    "FOR_LAVT_SYKEFRAVÆR": "NAV",
    "IKKE_TID": "NAV",
    "MINDRE_VIRKSOMHET": "NAV",
    "MANGLER_PARTSGRUPPE": "NAV",
    "IKKE_TILFREDSSTILLENDE_SAMARBEID": "NAV",
    # Virksomhet
    "GJENNOMFØRER_TILTAK_MED_BHT": "Virksomhet",
    "GJENNOMFØRER_TILTAK_PÅ_EGENHÅND": "Virksomhet",
    "HAR_IKKE_KAPASITET": "Virksomhet",
}
