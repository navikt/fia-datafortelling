from google.cloud.bigquery import Client
import json


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


def split_data_statistikk(data_statistikk):
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

    # Fylkesnavn
    data_status["fylkesnavn"] = data_status.fylkesnummer.map(fylker)

    # Hoved næring
    data_status["hoved_nering"] = data_status.neringer.apply(
        lambda x: json.loads(x)[0]["navn"]
    )
    data_status["hoved_nering_truncated"] = data_status.hoved_nering
    data_status.loc[
        data_status.hoved_nering.str.len() > 50, "hoved_nering_truncated"
    ] = (data_status.hoved_nering.str[:47] + "...")

    # Gruppering av virksomheter per antall ansatte
    data_status.loc[data_status.antallPersoner == 0, "antallPersoner_gruppe"] = "0"
    data_status.loc[data_status.antallPersoner.between(1, 4), "antallPersoner_gruppe"] = "1-4"
    data_status.loc[data_status.antallPersoner.between(5, 19), "antallPersoner_gruppe"] = "5-19"
    data_status.loc[data_status.antallPersoner.between(20, 49), "antallPersoner_gruppe"] = "20-49"
    data_status.loc[data_status.antallPersoner.between(50, 99), "antallPersoner_gruppe"] = "50-99"
    data_status.loc[data_status.antallPersoner >= 100, "antallPersoner_gruppe"] = "100+"
    data_status.loc[data_status.antallPersoner.isna(), "antallPersoner_gruppe"] = "Ukjent"

    return data_status


def preprocess_data_leveranse(data_leveranse):
    data_leveranse = data_leveranse.sort_values(
        ["saksnummer", "sistEndret"], ascending=True
    ).drop_duplicates(["saksnummer", "iaTjenesteId", "iaModulId"], keep="last")

    data_leveranse = data_leveranse[data_leveranse.status != "SLETTET"]

    return data_leveranse
