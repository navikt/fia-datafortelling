from google.cloud.bigquery import Client


def load_data(project, dataset, table):
    sql_query = f"SELECT  * FROM `{project}.{dataset}.{table}`"
    bq_client = Client(project=project)
    data = bq_client.query(query=sql_query).to_dataframe()
    return data


def get_aktive_saker(data_statistikk):
    df = data_statistikk.sort_values(
        ["saksnummer", "endretTidspunkt"], ascending=True
    ).drop_duplicates("saksnummer", keep="last")
    df["aktiv_sak"] = ~df.status.isin(["IKKE_AKTUELL", "FULLFØRT", "NY"])
    return df[["saksnummer", "aktiv_sak"]]
