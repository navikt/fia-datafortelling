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


def preprocess_data(data_statistikk):
    data_statistikk = data_statistikk.sort_values(
        ["saksnummer", "tidsstempel"], ascending=True
    )

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

    # Første næring
    data_statistikk["første_nering"] = data_statistikk.neringer.apply(
        lambda x: json.loads(x)[0]["navn"]
    )

    return data_statistikk
