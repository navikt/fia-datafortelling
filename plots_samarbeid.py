import numpy as np
import pandas as pd
import plotly.graph_objects as go

from helper import annotate_ikke_offisiell_statistikk


def plot_antall_saker_per_antall_samarbeid(
    data_samarbeid: pd.DataFrame, normalisert=False
) -> go.Figure:
    fig = go.Figure()

    def legg_til_trace(fig, data_samarbeid, filter, trace_name, normalisert):
        # Beregner antall saker per antall aktive samarbeid
        antall_saker_per_antall_samarbeid = (
            data_samarbeid[(data_samarbeid.status == "AKTIV") & filter]
            .groupby("saksnummer")
            .count()
            .id.value_counts()
            .sort_index()
        )

        # Fyller inn manglende verdier
        antall_saker_per_antall_samarbeid = antall_saker_per_antall_samarbeid.reindex(
            range(1, antall_saker_per_antall_samarbeid.index.max() + 1), fill_value=0
        )

        # Beregne andel
        if normalisert:
            totalt = antall_saker_per_antall_samarbeid.sum()
            antall_saker_per_antall_samarbeid = (
                antall_saker_per_antall_samarbeid / totalt
            )

        # Legger til trace
        fig = fig.add_trace(
            go.Bar(
                x=antall_saker_per_antall_samarbeid.index,
                y=antall_saker_per_antall_samarbeid.values,
                name=trace_name,
            )
        )
        return fig

    små_bedrifter = data_samarbeid.antallPersoner <= 20
    mellomstore_bedrifter = (data_samarbeid.antallPersoner > 20) & (
        data_samarbeid.antallPersoner <= 100
    )
    store_bedrifter = data_samarbeid.antallPersoner > 100

    fig = legg_til_trace(
        fig,
        data_samarbeid,
        små_bedrifter,
        "Små virksomheter (<= 20 ansatte)",
        normalisert,
    )
    fig = legg_til_trace(
        fig,
        data_samarbeid,
        mellomstore_bedrifter,
        "Mellomstore virksomheter (21-100 ansatte)",
        normalisert,
    )
    fig = legg_til_trace(
        fig,
        data_samarbeid,
        store_bedrifter,
        "Store virksomheter (> 100 ansatte)",
        normalisert,
    )

    fig = fig.update_layout(
        width=850,
        height=400,
        xaxis_title="Antall samarbeid",
        yaxis_title="Andel virksomheter" if normalisert else "Antall virksomheter",
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
        ),
    )

    fig = fig.update_xaxes(type="category")
    if normalisert:
        fig = fig.update_yaxes(tickformat=",.1%")

    return annotate_ikke_offisiell_statistikk(fig)


def indicator_antall_samarbeid(
    data_samarbeid: pd.DataFrame, data_behovsvurdering: pd.DataFrame
) -> go.Figure:
    antall_aktive_samarbeid = data_samarbeid[
        data_samarbeid.status == "AKTIV"
    ].id.nunique()

    data = data_behovsvurdering.merge(
        data_samarbeid[["id", "status"]],
        left_on="samarbeidId",
        right_on="id",
        how="left",
        suffixes=("_behovsvurdering", "_samarbeid"),
    )
    antall_aktive_samarbeid_med_fullfort_behovsvurdering = data[
        (data.status_samarbeid == "AKTIV")
        & (data.status_behovsvurdering == "AVSLUTTET")
    ].id_samarbeid.nunique()

    fig = go.Figure()

    fig = fig.add_trace(
        go.Indicator(
            title_text="Antall aktive samarbeid",
            value=antall_aktive_samarbeid,
            domain={"row": 0, "column": 0},
        )
    )
    fig = fig.add_trace(
        go.Indicator(
            title_text="Antall aktive samarbeid<br>med fullført behovsvurdering",
            value=antall_aktive_samarbeid_med_fullfort_behovsvurdering,
            domain={"row": 0, "column": 1},
        )
    )
    fig = fig.add_trace(
        go.Indicator(
            title_text="Antall aktive samarbeid<br>med opprettet samarbeidsplan<br><span style='font-size:0.8em;color:gray'>(kommer snart)</span>",
            value=np.nan,
            domain={"row": 1, "column": 0},
        )
    )
    fig = fig.add_trace(
        go.Indicator(
            title_text="Antall aktive samarbeid<br>med fullført evaluering<br><span style='font-size:0.8em;color:gray'>(kommer senere)</span>",
            value=np.nan,
            domain={"row": 1, "column": 1},
        )
    )

    fig = fig.update_layout(height=600, grid={"rows": 2, "columns": 2})

    return fig
