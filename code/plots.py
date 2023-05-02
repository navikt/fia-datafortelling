import plotly.graph_objects as go
from datetime import datetime, timezone


def aktive_saker_per_fylke(data_statistikk):
    aktive_saker_per_fylke = (
        data_statistikk[data_statistikk.aktiv_sak]
        .groupby("fylkesnavn")
        .saksnummer.nunique()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig = go.Figure(
        data=[
            go.Bar(
                x=aktive_saker_per_fylke["fylkesnavn"],
                y=aktive_saker_per_fylke["saksnummer"],
            )
        ]
    )
    fig.update_layout(
        xaxis_title="Fylke",
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


def antall_saker_per_status(data_statistikk):
    sortering = [
        "VURDERES",
        "KONTAKTES",
        "KARTLEGGES",
        "VI_BISTÅR",
        "FULLFØRT",
        "IKKE_AKTUELL",
        "SLETTET",
    ]

    saker_per_status = (
        data_statistikk.groupby("siste_status")
        .saksnummer.nunique()
        .reset_index()
        .sort_values(
            by="siste_status", key=lambda col: -col.map(lambda e: sortering.index(e))
        )
        .reset_index()
    )

    fig = go.Figure(
        data=[
            go.Bar(
                y=saker_per_status["siste_status"],
                x=saker_per_status["saksnummer"],
                text=saker_per_status["saksnummer"],
                orientation="h",
            )
        ]
    )
    fig.update_xaxes(visible=False)
    fig.update_layout(plot_bgcolor="rgb(255,255,255)")

    return fig
