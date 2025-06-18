from enum import Enum


class Resultatområde(Enum):
    MØRE_OG_ROMSDAL = "møre_og_romsdal"
    AGDER = "agder"
    OSLO = "oslo"
    INNLANDET = "innlandet"
    NORDLAND = "nordland"
    TROMS_OG_FINNMARK = "troms_og_finnmark"
    TRØNDELAG = "trøndelag"
    VESTFOLD_OG_TELEMARK = "vestfold_og_telemark"
    VESTLAND = "vestland"
    ROGALAND = "rogaland"
    VEST_VIKEN = "vest-viken"
    ØST_VIKEN = "øst-viken"


class Sektor(Enum):
    STATLIG = "1"
    KOMMUNAL = "2"
    PRIVAT = "3"


# Nødvendig som konstant i tilfelle et sett av samarbeidsplaner ikke har inkludert alle undertemaer minst én gang
undertema_navn: list[str] = [
    "Endring og omstilling",
    "HelseIArbeid",
    "Livsfaseorientert personalpolitikk",
    "Oppfølging av arbeidsmiljøundersøkelser",
    "Oppfølgingssamtaler",
    "Psykisk helse",
    "Sykefravær - enkeltsaker",
    "Sykefraværsrutiner",
    "Tilretteleggings- og medvirkningsplikt",
    "Utvikle arbeidsmiljøet",
    "Utvikle partssamarbeidet",
]
undertema_labels: dict[str, str] = {
    "Endring og omstilling": "Endring og omstilling",
    "HelseIArbeid": "HelseIArbeid",
    "Livsfaseorientert personalpolitikk": "Livsfaseorientert <br>personalpolitikk",
    "Oppfølging av arbeidsmiljøundersøkelser": "Oppfølging av <br>arbeidsmiljøundersøkelser",
    "Oppfølgingssamtaler": "Oppfølgingssamtaler",
    "Psykisk helse": "Psykisk helse",
    "Sykefravær - enkeltsaker": "Sykefravær - enkeltsaker",
    "Sykefraværsrutiner": "Sykefraværsrutiner",
    "Tilretteleggings- og medvirkningsplikt": "Tilretteleggings- <br>og medvirkningsplikt",
    "Utvikle arbeidsmiljøet": "Utvikle arbeidsmiljøet",
    "Utvikle partssamarbeidet": "Utvikle partssamarbeidet",
}


statusordre: list[str] = [
    "NY",
    "VURDERES",
    "KONTAKTES",
    "KARTLEGGES",
    "VI_BISTÅR",
    "FULLFØRT",
    "IKKE_AKTUELL",
    "SLETTET",
]

# 'fylker' er fylker før og etter kommune- og fylkesendringer 1.1.2024
fylker: dict[str, str] = {
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
    "33": "Buskerud",
    "32": "Akershus",
    "31": "Østfold",
    "40": "Telemark",
    "39": "Vestfold",
    "56": "Finnmark",
    "55": "Troms",
}

# Resultatområder forblir uendret etter kommune- og fylkesendringer 1.1.2024
resultatområder: dict[str, str] = {
    "03": "Oslo",
    "11": "Rogaland",
    "15": "Møre og Romsdal",
    "18": "Nordland",
    "V30": "Vest-Viken",
    "Ø30": "Øst-Viken",
    "34": "Innlandet",
    "38": "Vestfold og Telemark",
    "40": "Vestfold og Telemark",
    "39": "Vestfold og Telemark",
    "42": "Agder",
    "46": "Vestland",
    "50": "Trøndelag",
    "54": "Troms og Finnmark",
    "56": "Troms og Finnmark",
    "55": "Troms og Finnmark",
    "33": "Vest-Viken",
    "31": "Øst-Viken",
}

viken_akershus: dict[str, str] = {
    "3201": "Vest-Viken",  # Bærum kommune
    "3203": "Vest-Viken",  # Asker kommune
    "3236": "Vest-Viken",  # Jevnaker kommune
    "3205": "Øst-Viken",  # Lillestrøm kommune
    "3207": "Øst-Viken",  # Nordre Follo kommune
    "3209": "Øst-Viken",  # Ullensaker kommune
    "3212": "Øst-Viken",  # Nesodden kommune
    "3214": "Øst-Viken",  # Frogn kommune
    "3216": "Øst-Viken",  # Vestby kommune
    "3218": "Øst-Viken",  # Ås kommune
    "3220": "Øst-Viken",  # Enebakk kommune
    "3222": "Øst-Viken",  # Lørenskog kommune
    "3224": "Øst-Viken",  # Rælingen kommune
    "3226": "Øst-Viken",  # Aurskog-Høland kommune
    "3228": "Øst-Viken",  # Nes kommune
    "3230": "Øst-Viken",  # Gjerdrum kommune
    "3232": "Øst-Viken",  # Nittedal kommune
    "3234": "Øst-Viken",  # Lunner kommune
    "3238": "Øst-Viken",  # Nannestad kommune
    "3240": "Øst-Viken",  # Eidsvoll kommune
    "3242": "Øst-Viken",  # Hurdal kommune
}

rogaland_lund: dict[str, str] = {
    "1112": "Agder",  # Lund kommune
    "1101": "Rogaland",  # Eigersund kommune
    "1103": "Rogaland",  # Stavanger kommune
    "1106": "Rogaland",  # Haugesund kommune
    "1108": "Rogaland",  # Sandnes kommune
    "1111": "Rogaland",  # Sokndal kommune
    "1114": "Rogaland",  # Bjerkreim kommune
    "1119": "Rogaland",  # Hå kommune
    "1120": "Rogaland",  # Klepp kommune
    "1121": "Rogaland",  # Time kommune
    "1122": "Rogaland",  # Gjesdal kommune
    "1124": "Rogaland",  # Sola kommune
    "1127": "Rogaland",  # Randaberg kommune
    "1130": "Rogaland",  # Strand kommune
    "1133": "Rogaland",  # Hjelmeland kommune
    "1134": "Rogaland",  # Suldal kommune
    "1135": "Rogaland",  # Sauda kommune
    "1144": "Rogaland",  # Kvitsøy kommune
    "1145": "Rogaland",  # Bokn kommune
    "1146": "Rogaland",  # Tysvær kommune
    "1149": "Rogaland",  # Karmøy kommune
    "1151": "Rogaland",  # Utsira kommune
    "1160": "Rogaland",  # Vindafjord kommune
}


intervall_sortering: list[str] = [
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

plotly_colors: list[str] = [
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

ikkeaktuell_hovedgrunn: dict[str, str] = {
    # NAV
    "IKKE_DIALOG_MELLOM_PARTENE": "NAV",
    "FOR_FÅ_TAPTE_DAGSVERK": "NAV",
    # Virksomhet
    "VIRKSOMHETEN_ØNSKER_IKKE_SAMARBEID": "Virksomhet",
    "VIRKSOMHETEN_HAR_IKKE_RESPONDERT": "Virksomhet",
}
