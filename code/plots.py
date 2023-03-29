import plotly.graph_objects as go
from datetime import datetime, timezone

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

def aktive_saker_per_fylke(data_statistikk):
    aktive_saker_per_fylke = (
        data_statistikk[data_statistikk.aktiv_sak]
        .groupby("fylkesnummer")
        .saksnummer.nunique()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig = go.Figure(
        data=[
            go.Bar(
                x=aktive_saker_per_fylke["fylkesnummer"].map(fylker),
                y=aktive_saker_per_fylke["saksnummer"],
            )
        ]
    )
    fig.update_layout(
        xaxis_title="Fylkesnummer",
        yaxis_title="Antall aktive saker",
    )
    return fig


def dager_siden_siste_oppdatering(data_statistikk, data_leveranse):
    siste_oppdatering_statistikk = (
        data_statistikk[data_statistikk.aktiv_sak]
        .groupby("saksnummer")
        .endretTidspunkt.max()
        .reset_index()
    )
    siste_oppdatering_leveranse = (
        data_leveranse.groupby("saksnummer").sistEndret.max().reset_index()
    )

    siste_oppdatering = siste_oppdatering_statistikk.merge(
        siste_oppdatering_leveranse, on="saksnummer", how="left"
    )
    siste_oppdatering = siste_oppdatering.rename(
        columns={
            "endretTidspunkt": "siste_oppdatering_statistikk",
            "sistEndret": "siste_oppdatering_leveranse",
        }
    )

    siste_oppdatering["siste_oppdatering"] = siste_oppdatering[
        ["siste_oppdatering_statistikk", "siste_oppdatering_leveranse"]
    ].max(axis=1, numeric_only=False)

    now = datetime.now(timezone.utc)
    siste_oppdatering["dager_siden_siste_oppdatering"] = (
        now - siste_oppdatering.siste_oppdatering
    ).dt.days

    fig = go.Figure(
        data=[
            go.Histogram(
                x=siste_oppdatering["dager_siden_siste_oppdatering"], nbinsx=20
            )
        ]
    )
    fig.update_layout(
        xaxis_title="Dager siden siste oppdatering i Fia",
        yaxis_title="Antall saker",
    )

    return fig
