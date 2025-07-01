from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from google.cloud import bigquery

from src.utils.konstanter import (
    intervall_sortering,
)


def samarbeid_med_spørreundersøkelse(
    data_samarbeid: pd.DataFrame,
    data_spørreundersøkelse: pd.DataFrame,
    type_spørreundersøkelse: str = "Behovsvurdering",
) -> pd.DataFrame:
    if data_samarbeid.empty or data_spørreundersøkelse.empty:
        return pd.DataFrame()

    samarbeid_ikke_slettet = data_samarbeid[data_samarbeid["status"] != "SLETTET"]

    if samarbeid_ikke_slettet.empty:
        return pd.DataFrame()

    behovsvurderinger = data_spørreundersøkelse[
        data_spørreundersøkelse["type"] == type_spørreundersøkelse
    ]

    avsluttede_behovsvurderinger = behovsvurderinger[
        behovsvurderinger["status"] == "AVSLUTTET"
    ]

    behovsvurderinger_med_svar = avsluttede_behovsvurderinger[
        avsluttede_behovsvurderinger["harMinstEttSvar"]
    ]

    # BUG: Dataene inneholder ikke alltid fullfort timestamp for gjennomførte behovsvurderinger (253 av 584 manglet ved sjekk 16.04.2025)
    #  Midlertidig fiks er å bruke endret i tilfelle fullfort mangler, men kan få feil om det skjer endringer etter gjennomføring
    behovsvurderinger_med_svar["fullfort_or_endret"] = behovsvurderinger_med_svar[
        "fullfort"
    ].fillna(behovsvurderinger_med_svar["endret"])

    ny_kolonne = f"tidligste_{type_spørreundersøkelse.lower()}_fullfort"
    tidligste_fullført = (
        behovsvurderinger_med_svar.groupby("samarbeid_id")["fullfort_or_endret"]
        .min()
        .reset_index()
        .rename(
            columns={
                "fullfort_or_endret": ny_kolonne,
                "samarbeid_id": "id",
            }
        )
    )

    # Filter samarbeid to include only those with completed behovsvurdering
    samarbeid_med_fullført_behovsvurdering = samarbeid_ikke_slettet[
        samarbeid_ikke_slettet["id"].isin(
            behovsvurderinger_med_svar["samarbeid_id"].unique()
        )
    ]

    if samarbeid_med_fullført_behovsvurdering.empty:
        return pd.DataFrame()

    # Merge dataframes
    samarbeid_med_tid_for_gjennomføring = samarbeid_med_fullført_behovsvurdering.merge(
        tidligste_fullført, on="id", how="left"
    )

    # Filtrer ut behovsvurderinger opprettet før samarbeidet ble opprettet
    result = samarbeid_med_tid_for_gjennomføring[
        samarbeid_med_tid_for_gjennomføring[ny_kolonne]
        > samarbeid_med_tid_for_gjennomføring["opprettet"]
    ].reset_index(drop=True)

    return result


def load_data_deduplicate(
    project: str,
    dataset: str,
    table: str,
    distinct_colunms: str,
    dtypes: dict[str, Any] | None = None,
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
    bq_client = bigquery.Client(project=project)
    query_job = bq_client.query(query=sql_query)
    return query_job.to_dataframe(dtypes=dtypes)  # type: ignore


def fjern_tidssone(data: pd.DataFrame) -> pd.DataFrame:
    """
    Fjerner tidssone fra alle kolonner som har datatype datetimetz
    """
    date_columns = data.select_dtypes(include=["datetimetz"]).columns.tolist()
    for col in date_columns:
        data[col] = data[col].dt.tz_localize(None)
    return data


def split_data_statistikk(
    data_statistikk: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splitter data_statistikk inn i data_status og data_eierskap
    """
    # Fjern tidssone fra datoene, alt i utc
    data_statistikk = fjern_tidssone(data_statistikk)

    # Split data_statistikk inn i data_status og data_eierskap
    eierskap_mask = data_statistikk["hendelse"] == "TA_EIERSKAP_I_SAK"
    # BUG: VI må filtrere bort hendelser som relaterer til samarbeid, da de skaler løkker i sankey-diagram da de ikke fører til statusendring i sak
    samarbeid_mask = data_statistikk["hendelse"].isin(
        [
            "NY_PROSESS",
            "ENDRE_PROSESS",
            "SLETT_PROSESS",
            "FULLFØR_PROSESS",
            "FULLFØR_PROSESS_MASKINELT_PÅ_EN_FULLFØRT_SAK",
            "AVBRYT_PROSESS",
        ]
    )

    data_eierskap = data_statistikk[eierskap_mask].reset_index(drop=True)
    data_prosess = data_statistikk[samarbeid_mask].reset_index(drop=True)
    data_status = data_statistikk[~eierskap_mask & ~samarbeid_mask].reset_index(
        drop=True
    )

    return preprocess_data_status(data_status), data_eierskap, data_prosess


def preprocess_data_status(data_status: pd.DataFrame) -> pd.DataFrame:
    # Sorter basert på sak og endret tidspunkt
    data_status = data_status.sort_values(
        ["saksnummer", "endretTidspunkt"], ascending=True
    ).reset_index(drop=True)

    # Fjern rader når tilbake-knappen ikke funket
    data_status.loc[
        data_status["saksnummer"] == data_status["saksnummer"].shift(1),
        "forrige_status_med_tilbake",
    ] = data_status["status"].shift(1)
    feil_tilbake = (data_status["hendelse"] == "TILBAKE") & (
        data_status["status"] == data_status["forrige_status_med_tilbake"]
    )
    # Det er forventet kun 2 rader, mer enn dette er en ny bug
    if feil_tilbake.sum() > 10:
        raise ValueError(
            f"Fant {feil_tilbake.sum()} rader som ikke endret status etter bruk av tilbake-knappen"
        )
    data_status = data_status[~feil_tilbake]
    data_status.drop(["forrige_status_med_tilbake"], axis=1, inplace=True)

    # Fjern rader som var angret med bruk av tilbake-knappen
    data_status.reset_index(drop=True, inplace=True)
    tilbake_rader = data_status[data_status["hendelse"] == "TILBAKE"].index.tolist()
    fjern_rader = set(tilbake_rader)
    for index in tilbake_rader:
        rad = index - 1
        while rad in fjern_rader:
            rad -= 1
        fjern_rader.add(rad)
    data_status = data_status.drop(index=fjern_rader).reset_index(drop=True)

    # Forrige status
    data_status.loc[
        data_status["saksnummer"] == data_status["saksnummer"].shift(1),
        "forrige_status",
    ] = data_status["status"].shift(1)

    # Forrige endret tidspunkt
    data_status.loc[
        data_status["saksnummer"] == data_status["saksnummer"].shift(1),
        "forrige_endretTidspunkt",
    ] = data_status["endretTidspunkt"].shift(1)

    # Siste status
    siste_status = (
        data_status[["saksnummer", "status"]]
        .drop_duplicates("saksnummer", keep="last")
        .rename(columns={"status": "siste_status"})
    )
    data_status = data_status.merge(siste_status, on="saksnummer", how="left")

    # Aktive saker
    aktive_statuser = ["VURDERES", "KONTAKTES", "KARTLEGGES", "VI_BISTÅR"]
    data_status["aktiv_sak"] = data_status["siste_status"].isin(aktive_statuser)

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


def beregn_ikke_aktuell(data_statistikk):
    data_status, _, _ = split_data_statistikk(data_statistikk)
    return explode_ikke_aktuell_begrunnelse(data_status)


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
