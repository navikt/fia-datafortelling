from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from google.cloud.bigquery import Client

from utils.konstanter import (
    fylker,
    intervall_sortering,
    resultatområder,
    rogaland_lund,
    viken_akershus,
)


def load_data_deduplicate(
    project: str, dataset: str, table: str, distinct_colunms: str
) -> pd.DataFrame:
    """
    Henter data fra BigQuery og fjerner duplikater med å beholde siste tidsstempel av repeterende distinct_colunms.
    """
    sql_query = f"""
        SELECT
           * except (radnummerBasertPaaTidsstempel)
        FROM (
            SELECT
                *,
                row_number() over (partition by {distinct_colunms} order by tidsstempel desc) radnummerBasertPaaTidsstempel
            FROM `{project}.{dataset}.{table}`
        ) WHERE radnummerBasertPaaTidsstempel = 1;
    """
    bq_client = Client(project=project)
    data = bq_client.query(query=sql_query).to_dataframe()
    return data


def fjern_tidssone(data: pd.DataFrame) -> pd.DataFrame:
    """
    Fjerner tidssone fra alle kolonner som har datatype datetimetz
    """
    date_columns = data.select_dtypes(include=["datetimetz"]).columns.tolist()
    for col in date_columns:
        data[col] = data[col].dt.tz_localize(None)
    return data


def parse_næring(rad):
    if type(rad) != np.ndarray:
        return "Feil ved innhenting av hovednæring, feil format"
    elif rad.size < 1:
        # ca 6 tilfeller hvor rad == []
        return "Feil ved innhenting av hovednæring, mangler næring"
    else:
        return rad[0]["navn"]


def preprocess_data_statistikk(
    data_statistikk: pd.DataFrame, adm_enheter: pd.DataFrame
) -> pd.DataFrame:
    # Sorter basert på endrettidspunkt
    data_statistikk = data_statistikk.sort_values(
        "endretTidspunkt", ascending=True
    ).reset_index(drop=True)

    # Måned til endrettidspunkt
    data_statistikk["endretTidspunkt_måned"] = (
        data_statistikk.endretTidspunkt.dt.strftime("%Y-%m")
    )

    # Fylkesnavn
    data_statistikk["fylkesnavn"] = data_statistikk.fylkesnummer.map(fylker)

    # Resultatområde
    data_statistikk["resultatomrade"] = data_statistikk.fylkesnummer.map(
        resultatområder
    )

    # Del akershus på øst og vest-viken
    data_statistikk.loc[data_statistikk["fylkesnummer"] == "32", "resultatomrade"] = (
        data_statistikk.kommunenummer.map(viken_akershus)
    )
    # Flytt Lund kommune i Rogaland til Agder da de er der de blir fulgt opp
    data_statistikk.loc[data_statistikk["fylkesnummer"] == "11", "resultatomrade"] = (
        data_statistikk.kommunenummer.map(rogaland_lund)
    )

    # Leser alle kommunenummer og mapper til 2024 kommunenummer
    alle_kommunenummer = adm_enheter[["kommunenummer", "kommunenummer 2023"]]

    data_statistikk["kommunenummer 2024"] = (
        data_statistikk["kommunenummer"]
        .map(alle_kommunenummer.set_index("kommunenummer 2023")["kommunenummer"])
        .fillna(data_statistikk["kommunenummer"])
    )

    # Hovednæring
    data_statistikk["hoved_nering"] = data_statistikk.neringer.apply(parse_næring)

    data_statistikk["hoved_nering_truncated"] = data_statistikk.hoved_nering
    data_statistikk.loc[
        data_statistikk.hoved_nering.str.len() > 50, "hoved_nering_truncated"
    ] = data_statistikk.hoved_nering.str[:47] + "..."

    # Gruppering av virksomheter per antall ansatte
    col_name = "antallPersoner_gruppe"
    data_statistikk.loc[data_statistikk.antallPersoner == 0, col_name] = "0"
    data_statistikk.loc[data_statistikk.antallPersoner.between(1, 4), col_name] = "1-4"
    data_statistikk.loc[data_statistikk.antallPersoner.between(5, 19), col_name] = (
        "5-19"
    )
    data_statistikk.loc[data_statistikk.antallPersoner.between(20, 49), col_name] = (
        "20-49"
    )
    data_statistikk.loc[data_statistikk.antallPersoner.between(50, 99), col_name] = (
        "50-99"
    )
    data_statistikk.loc[data_statistikk.antallPersoner >= 100, col_name] = "100+"
    data_statistikk.loc[data_statistikk.antallPersoner.isna(), col_name] = "Ukjent"

    return data_statistikk


def split_data_statistikk(
    data_statistikk: pd.DataFrame,
) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame):
    """
    Splitter data_statistikk inn i data_status og data_eierskap
    """
    # Fjern tidssone fra datoene, alt i utc
    data_statistikk = fjern_tidssone(data_statistikk)

    # Split data_statistikk inn i data_status og data_eierskap
    eierskap = data_statistikk.hendelse == "TA_EIERSKAP_I_SAK"
    prosess = data_statistikk.hendelse.isin(
        ["NY_PROSESS", "ENDRE_PROSESS", "SLETT_PROSESS"]
    )
    data_status = data_statistikk[~eierskap & ~prosess].reset_index(drop=True)
    data_eierskap = data_statistikk[eierskap].reset_index(drop=True)
    data_prosess = data_statistikk[prosess].reset_index(drop=True)

    return data_status, data_eierskap, data_prosess


def preprocess_data_status(data_status: pd.DataFrame) -> pd.DataFrame:
    # Sorter basert på sak og endret tidspunkt
    data_status = data_status.sort_values(
        ["saksnummer", "endretTidspunkt"], ascending=True
    ).reset_index(drop=True)

    # Fjern rader når tilbake-knappen ikke funket
    data_status.loc[
        data_status.saksnummer == data_status.saksnummer.shift(1),
        "forrige_status_med_tilbake",
    ] = data_status.status.shift(1)
    feil_tilbake = (data_status.hendelse == "TILBAKE") & (
        data_status.status == data_status.forrige_status_med_tilbake
    )
    # Det er forventet kun 2 rader, mer enn dette er en ny bug
    if feil_tilbake.sum() > 2:
        raise ValueError(
            f"Fant {feil_tilbake.sum()} rader som ikke endret status etter bruk av tilbake-knappen"
        )
    data_status = data_status[~feil_tilbake]
    data_status.drop(["forrige_status_med_tilbake"], axis=1, inplace=True)

    # Fjern rader som var angret med bruk av tilbake-knappen
    data_status.reset_index(drop=True, inplace=True)
    tilbake_rader = data_status[data_status.hendelse == "TILBAKE"].index.tolist()
    fjern_rader = set(tilbake_rader)
    for index in tilbake_rader:
        rad = index - 1
        while rad in fjern_rader:
            rad -= 1
        fjern_rader.add(rad)
    data_status = data_status.drop(index=fjern_rader).reset_index(drop=True)

    # Forrige status
    data_status.loc[
        data_status.saksnummer == data_status.saksnummer.shift(1),
        "forrige_status",
    ] = data_status.status.shift(1)

    # Forrige endret tidspunkt
    data_status.loc[
        data_status.saksnummer == data_status.saksnummer.shift(1),
        "forrige_endretTidspunkt",
    ] = data_status.endretTidspunkt.shift(1)

    # Siste status
    siste_status = (
        data_status[["saksnummer", "status"]]
        .drop_duplicates("saksnummer", keep="last")
        .rename(columns={"status": "siste_status"})
    )
    data_status = data_status.merge(siste_status, on="saksnummer", how="left")

    # Aktive saker
    aktive_statuser = ["VURDERES", "KONTAKTES", "KARTLEGGES", "VI_BISTÅR"]
    data_status["aktiv_sak"] = data_status.siste_status.isin(aktive_statuser)

    return data_status


def preprocess_data_leveranse(data_leveranse: pd.DataFrame) -> pd.DataFrame:
    # Filtrere bort endret av Fia systemet
    data_leveranse = data_leveranse[data_leveranse.sistEndretAv != "Fia system"]

    # Fjern slettede leveranser
    slettet_leveranse_id = data_leveranse[data_leveranse.status == "SLETTET"].id
    data_leveranse = data_leveranse[~data_leveranse.id.isin(slettet_leveranse_id)]

    # Frist fra dbdate til datetime
    # data_leveranse.frist = pd.to_datetime(data_leveranse.frist)
    data_leveranse.loc[:, "frist"] = pd.to_datetime(
        data_leveranse["frist"], errors="coerce"
    )

    # Fjern tidssone fra datoene, alt i utc
    data_leveranse = fjern_tidssone(data_leveranse)

    return data_leveranse


def preprocess_data_samarbeid(
    data_samarbeid: pd.DataFrame, data_statistikk: pd.DataFrame
) -> pd.DataFrame:
    # Legge til antall personer i samarbeid-tabellen
    antall_personer = data_statistikk.sort_values("endretTidspunkt")[
        ["saksnummer", "antallPersoner"]
    ].drop_duplicates("saksnummer", keep="last")
    data_samarbeid = data_samarbeid.merge(antall_personer, on="saksnummer", how="left")

    # Legge til kommunenummer 2024 i samarbeid-tabellen
    kommunenummer = (
        data_statistikk.sort_values("endretTidspunkt")[
            ["saksnummer", "kommunenummer 2024"]
        ]
        .drop_duplicates("saksnummer", keep="last")
        .rename(columns={"kommunenummer 2024": "kommunenummer"})
    )
    data_samarbeid = data_samarbeid.merge(kommunenummer, on="saksnummer", how="left")

    return data_samarbeid


def legg_til_resultatområde(
    data: pd.DataFrame, data_statistikk: pd.DataFrame
) -> pd.DataFrame:
    """
    Legger til resultatområde basert på data_statistikk.
    Vi filtrerer på resultatområde for å lage en datafortelling per resultatområde.
    """
    resultatomrade = data_statistikk.sort_values("endretTidspunkt")[
        ["saksnummer", "resultatomrade"]
    ].drop_duplicates("saksnummer", keep="last")
    data = data.merge(resultatomrade, on="saksnummer", how="left")
    return data


def hent_leveranse_sistestatus(data_leveranse: pd.DataFrame) -> pd.DataFrame:
    """
    Henter siste status for hver leveranse
    """
    return data_leveranse.sort_values(
        ["saksnummer", "sistEndret"], ascending=True
    ).drop_duplicates(["saksnummer", "iaTjenesteId", "iaModulId"], keep="last")


def beregn_siste_oppdatering(
    data_status: pd.DataFrame,
    data_eierskap: pd.DataFrame,
    data_leveranse: pd.DataFrame,
    beregningsdato=datetime.now(),
) -> pd.DataFrame:
    """
    Beregner siste oppdatering for hver sak
    """
    # Filtrere på beregningsdato
    data_status = data_status[data_status.endretTidspunkt < beregningsdato]
    data_eierskap = data_eierskap[data_eierskap.endretTidspunkt < beregningsdato]
    data_leveranse = data_leveranse[data_leveranse.sistEndret < beregningsdato]

    # Status på beregningsdato
    status_beregningsdato = (
        data_status[["saksnummer", "status"]]
        .drop_duplicates("saksnummer", keep="last")
        .rename(columns={"status": "status_beregningsdato"})
    )
    data_status = data_status.merge(status_beregningsdato, on="saksnummer", how="left")

    # Filtrere bort saker med avsluttet status på beregningsdato
    aktive_statuser = ["VURDERES", "KONTAKTES", "KARTLEGGES", "VI_BISTÅR"]
    aktiv_sak_beregningsdato = data_status.status_beregningsdato.isin(aktive_statuser)
    data_status = data_status[aktiv_sak_beregningsdato]

    # Hente rader med siste oppdatering for hver sak i hvert enkelt datasett
    siste_oppdatering_status = (
        data_status.groupby("saksnummer")
        .endretTidspunkt.max()
        .reset_index()
        .rename(columns={"endretTidspunkt": "siste_oppdatering_status"})
    )
    siste_oppdatering_eierskap = (
        data_eierskap.groupby("saksnummer")
        .endretTidspunkt.max()
        .reset_index()
        .rename(columns={"endretTidspunkt": "siste_oppdatering_eierskap"})
    )
    siste_oppdatering_leveranse = (
        data_leveranse.groupby("saksnummer")
        .sistEndret.max()
        .reset_index()
        .rename(columns={"sistEndret": "siste_oppdatering_leveranse"})
    )

    # Merge datasettene
    siste_oppdatering = siste_oppdatering_status.merge(
        siste_oppdatering_eierskap, on="saksnummer", how="left"
    )
    siste_oppdatering = siste_oppdatering.merge(
        siste_oppdatering_leveranse, on="saksnummer", how="left"
    )

    # Beregne siste oppdatering av alle datasettene
    siste_oppdatering["siste_oppdatering"] = siste_oppdatering[
        [
            "siste_oppdatering_status",
            "siste_oppdatering_eierskap",
            "siste_oppdatering_leveranse",
        ]
    ].max(axis=1, numeric_only=False)

    # Beregne antall dager siden siste oppdatering til berengningsdato
    siste_oppdatering["dager_siden_siste_oppdatering"] = (
        beregningsdato - siste_oppdatering.siste_oppdatering
    ).dt.days

    # Hente informasjon/kolonner fra data_status
    siste_oppdatering = siste_oppdatering.merge(
        data_status[["saksnummer", "status_beregningsdato"]].drop_duplicates(
            "saksnummer"
        ),
        on="saksnummer",
        how="left",
    )

    return siste_oppdatering


def beregn_intervall_tid_siden_siste_endring(data_status: pd.DataFrame) -> pd.DataFrame:
    data_status["tid_siden_siste_endring"] = (
        data_status.endretTidspunkt - data_status.forrige_endretTidspunkt
    )
    seconds = data_status.tid_siden_siste_endring.dt.seconds
    days = data_status.tid_siden_siste_endring.dt.days

    col_name = "intervall_tid_siden_siste_endring"
    data_status.loc[seconds < 60, col_name] = intervall_sortering[0]
    data_status.loc[seconds.between(60, 60 * 10), col_name] = intervall_sortering[1]
    data_status.loc[seconds.between(60 * 10, 60 * 60), col_name] = intervall_sortering[
        2
    ]
    data_status.loc[seconds.between(60 * 60, 60 * 60 * 8), col_name] = (
        intervall_sortering[3]
    )
    data_status.loc[seconds.between(60 * 60 * 8, 60 * 60 * 24), col_name] = (
        intervall_sortering[4]
    )
    data_status.loc[days.between(1, 10), col_name] = intervall_sortering[5]
    data_status.loc[days.between(10, 30), col_name] = intervall_sortering[6]
    data_status.loc[days.between(30, 100), col_name] = intervall_sortering[7]
    data_status.loc[days.between(100, 365), col_name] = intervall_sortering[8]
    data_status.loc[days >= 365, col_name] = intervall_sortering[9]

    return data_status


def explode_ikke_aktuell_begrunnelse(data_status: pd.DataFrame) -> pd.DataFrame:
    """
    Splitter ikkeAktuelBegrunnelse inn i flere rader, en rad per begrunnelse.
    """
    ikke_aktuell = data_status[data_status.status == "IKKE_AKTUELL"].drop_duplicates(
        "saksnummer", keep="last"
    )
    ikke_aktuell.ikkeAktuelBegrunnelse = ikke_aktuell.ikkeAktuelBegrunnelse.str.strip(
        "[]"
    ).str.split(",")
    ikke_aktuell = ikke_aktuell.explode("ikkeAktuelBegrunnelse")
    ikke_aktuell.ikkeAktuelBegrunnelse = ikke_aktuell.ikkeAktuelBegrunnelse.str.strip()
    ikke_aktuell["ikkeAktuelBegrunnelse_lesbar"] = (
        ikke_aktuell.ikkeAktuelBegrunnelse.str.replace("_", " ")
        .str.capitalize()
        .str.replace("bht", "BHT")
    )

    return ikke_aktuell


def filtrer_bort_saker_på_avsluttet_tidspunkt(
    data: pd.DataFrame, antall_dager=365
) -> pd.DataFrame:
    """
    Filtrerer bort saker avsluttet for over "x" antall dager siden
    """
    dato_some_time_ago = datetime.now() - timedelta(days=antall_dager)
    saker_some_time_ago = data[
        data.avsluttetTidspunkt < dato_some_time_ago
    ].saksnummer.unique()
    return data[~data.saksnummer.isin(saker_some_time_ago)]
