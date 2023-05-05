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


def preprocess_data_statistikk(data_statistikk):

    # Fjern dupliserte rader
    data_statistikk = data_statistikk.drop_duplicates("endretAvHendelseId").reset_index(drop=True)

    # Sorter basert på sak og endret tidspunkt
    data_statistikk = data_statistikk.sort_values(
        ["saksnummer", "endretTidspunkt"], ascending=True
    )

    # Fjern rader som ikke er relevant til analysen
    data_statistikk = data_statistikk[data_statistikk.hendelse!="TA_EIERSKAP_I_SAK"].reset_index(drop=True)
    data_statistikk = data_statistikk[data_statistikk.status!="NY"].reset_index(drop=True)

    # Fjern rader basert på tilbake-knapp
    tilbake_rader = data_statistikk[data_statistikk.hendelse=="TILBAKE"].index.tolist()
    fjern_rader = set(tilbake_rader)
    for index in tilbake_rader:
        rad = index-1
        while rad in fjern_rader:
            rad -= 1
        fjern_rader.add(rad)
    data_statistikk = data_statistikk.drop(index=fjern_rader).reset_index(drop=True)

    # Forrige status
    data_statistikk.loc[
        data_statistikk.saksnummer == data_statistikk.saksnummer.shift(1),
        "forrige_status",
    ] = data_statistikk.status.shift(1)

    # Siste status
    siste_status = (
        data_statistikk[["saksnummer", "status"]]
        .drop_duplicates("saksnummer", keep="last")
        .rename(columns={"status": "siste_status"})
    )
    data_statistikk = data_statistikk.merge(siste_status, on="saksnummer", how="left")

    # Aktive saker
    aktive_statuser = ["VURDERES", "KONTAKTES", "KARTLEGGES", "VI_BISTÅR"]
    data_statistikk["aktiv_sak"] = data_statistikk.siste_status.isin(aktive_statuser)

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
    data_statistikk.loc[data_statistikk.antallPersoner==0, "antallPersoner_gruppe"] = "0"
    data_statistikk.loc[data_statistikk.antallPersoner.between(1, 4), "antallPersoner_gruppe"] = "1-4"
    data_statistikk.loc[data_statistikk.antallPersoner.between(5, 19), "antallPersoner_gruppe"] = "5-19"
    data_statistikk.loc[data_statistikk.antallPersoner.between(20, 49), "antallPersoner_gruppe"] = "20-49"
    data_statistikk.loc[data_statistikk.antallPersoner.between(50, 99), "antallPersoner_gruppe"] = "50-99"
    data_statistikk.loc[data_statistikk.antallPersoner>=100, "antallPersoner_gruppe"] = "100+"
    data_statistikk.loc[data_statistikk.antallPersoner.isna(), "antallPersoner_gruppe"] = "Ukjent"

    return data_statistikk


def preprocess_data_leveranse(data_leveranse):

    data_leveranse = (
        data_leveranse.sort_values(["saksnummer", "sistEndret"], ascending=True)
        .drop_duplicates(["saksnummer", "iaTjenesteId", "iaModulId"], keep="last")
    )

    data_leveranse = data_leveranse[data_leveranse.status!="SLETTET"]

    return data_leveranse