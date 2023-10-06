from google.cloud.bigquery import Client
import json
import pandas as pd
from datetime import datetime, timedelta

from code.konstanter import fylker, intervall_sortering


def load_data(project, dataset, table):
    sql_query = f"SELECT  * FROM `{project}.{dataset}.{table}`"
    bq_client = Client(project=project)
    data = bq_client.query(query=sql_query).to_dataframe()
    return data


def load_data_deduplicate(project, dataset, table):
    sql_query = f"""
        SELECT
           * except (radnummerBasertPaaTidsstempel)
        FROM (
            SELECT
                *,
                row_number() over (partition by endretAvHendelseId order by tidsstempel desc) radnummerBasertPaaTidsstempel
            FROM `{project}.{dataset}.{table}`
        ) WHERE radnummerBasertPaaTidsstempel = 1;
    """
    bq_client = Client(project=project)
    data = bq_client.query(query=sql_query).to_dataframe()
    return data


def fjern_tidssone(data):
    date_columns = data.select_dtypes(include=["datetimetz"]).columns.tolist()
    for col in date_columns:
        data[col] = data[col].dt.tz_localize(None)
    return data


def preprocess_data_statistikk(data_statistikk):
    # Sorter basert på endrettidspunkt
    data_statistikk = data_statistikk.sort_values(
        "endretTidspunkt", ascending=True
    ).reset_index(drop=True)

    # Måned til endrettidspunkt
    data_statistikk[
        "endretTidspunkt_måned"
    ] = data_statistikk.endretTidspunkt.dt.strftime("%Y-%m")

    # Fylkesnavn
    data_statistikk["fylkesnavn"] = data_statistikk.fylkesnummer.map(fylker)

    # Hoved næring
    data_statistikk["hoved_nering"] = data_statistikk.neringer.apply(
        lambda x: json.loads(x)[0]["navn"]
    )
    data_statistikk["hoved_nering_truncated"] = data_statistikk.hoved_nering
    data_statistikk.loc[
        data_statistikk.hoved_nering.str.len() > 50, "hoved_nering_truncated"
    ] = (data_statistikk.hoved_nering.str[:47] + "...")

    # Gruppering av virksomheter per antall ansatte
    col_name = "antallPersoner_gruppe"
    data_statistikk.loc[data_statistikk.antallPersoner == 0, col_name] = "0"
    data_statistikk.loc[data_statistikk.antallPersoner.between(1, 4), col_name] = "1-4"
    data_statistikk.loc[
        data_statistikk.antallPersoner.between(5, 19), col_name
    ] = "5-19"
    data_statistikk.loc[
        data_statistikk.antallPersoner.between(20, 49), col_name
    ] = "20-49"
    data_statistikk.loc[
        data_statistikk.antallPersoner.between(50, 99), col_name
    ] = "50-99"
    data_statistikk.loc[data_statistikk.antallPersoner >= 100, col_name] = "100+"
    data_statistikk.loc[data_statistikk.antallPersoner.isna(), col_name] = "Ukjent"

    return data_statistikk


def split_data_statistikk(data_statistikk):
    # Fjern tidssone fra datoene, alt i utc
    data_statistikk = fjern_tidssone(data_statistikk)

    # Split data_statistikk inn i data_status og data_eierskap
    eierskap = data_statistikk.hendelse == "TA_EIERSKAP_I_SAK"
    data_status = data_statistikk[~eierskap].reset_index(drop=True)
    data_eierskap = data_statistikk[eierskap].reset_index(drop=True)

    return data_status, data_eierskap


def preprocess_data_status(data_status):
    # Sorter basert på sak og endret tidspunkt
    data_status = data_status.sort_values(
        ["saksnummer", "endretTidspunkt"], ascending=True
    ).reset_index(drop=True)

    # Fjern rader basert på tilbake-knapp
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


def preprocess_data_leveranse(data_leveranse):
    slettet_leveranse_id = data_leveranse[data_leveranse.status == "SLETTET"].id
    data_leveranse = data_leveranse[~data_leveranse.id.isin(slettet_leveranse_id)]

    # Frist fra dbdate til datetime
    data_leveranse.frist = pd.to_datetime(data_leveranse.frist)

    # Fjern tidssone fra datoene, alt i utc
    data_leveranse = fjern_tidssone(data_leveranse)

    return data_leveranse


def kollaps_leveranse_historikk(data_leveranse):
    return data_leveranse.sort_values(
        ["saksnummer", "sistEndret"], ascending=True
    ).drop_duplicates(["saksnummer", "iaTjenesteId", "iaModulId"], keep="last")


def beregn_siste_oppdatering(
    data_status,
    data_eierskap,
    data_leveranse,
    beregningsdato=datetime.now(),
):
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

    # Beregne siste oppdatering
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

    siste_oppdatering = siste_oppdatering_status.merge(
        siste_oppdatering_eierskap, on="saksnummer", how="left"
    )
    siste_oppdatering = siste_oppdatering.merge(
        siste_oppdatering_leveranse, on="saksnummer", how="left"
    )

    siste_oppdatering["siste_oppdatering"] = siste_oppdatering[
        [
            "siste_oppdatering_status",
            "siste_oppdatering_eierskap",
            "siste_oppdatering_leveranse",
        ]
    ].max(axis=1, numeric_only=False)

    siste_oppdatering["dager_siden_siste_oppdatering"] = (
        beregningsdato - siste_oppdatering.siste_oppdatering
    ).dt.days

    siste_oppdatering = siste_oppdatering.merge(
        data_status[["saksnummer", "status_beregningsdato"]].drop_duplicates(
            "saksnummer"
        ),
        on="saksnummer",
        how="left",
    )

    return siste_oppdatering


def beregn_intervall_tid_siden_siste_endring(data_status):
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
    data_status.loc[
        seconds.between(60 * 60, 60 * 60 * 8), col_name
    ] = intervall_sortering[3]
    data_status.loc[
        seconds.between(60 * 60 * 8, 60 * 60 * 24), col_name
    ] = intervall_sortering[4]
    data_status.loc[days.between(1, 10), col_name] = intervall_sortering[5]
    data_status.loc[days.between(10, 30), col_name] = intervall_sortering[6]
    data_status.loc[days.between(30, 100), col_name] = intervall_sortering[7]
    data_status.loc[days.between(100, 365), col_name] = intervall_sortering[8]
    data_status.loc[days >= 365, col_name] = intervall_sortering[9]

    return data_status


def explode_ikke_aktuell_begrunnelse(data_status):
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


def get_data_siste_x_dager(data, variabel, antall_dager=365):
    dato_some_time_ago = datetime.now() - timedelta(days=antall_dager)
    saker_some_time_ago = data[data[variabel] < dato_some_time_ago].saksnummer.unique()
    return data[~data.saksnummer.isin(saker_some_time_ago)]
