import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.helper import (
    alle_måneder_mellom_datoer,
    annotate_ikke_offisiell_statistikk,
)
from utils.konstanter import ikkeaktuell_hovedgrunn, plotly_colors


def leveranse_per_maaned(data_leveranse: pd.DataFrame) -> go.Figure:
    data_leveranse["fullfort_yearmonth"] = data_leveranse.fullfort.dt.strftime("%Y-%m")
    alle_måneder = alle_måneder_mellom_datoer(data_leveranse.sistEndret.min())
    antall_mnd = min(len(alle_måneder), 12)

    saker_per_måned = (
        data_leveranse[data_leveranse.status == "LEVERT"]
        .groupby("fullfort_yearmonth")
        .saksnummer.size()
        .reindex(alle_måneder, fill_value=0)
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=saker_per_måned.index[-antall_mnd:],
            y=saker_per_måned.values[-antall_mnd:],
        )
    )

    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Fullført måned",
        yaxis_title="Antall fullførte leveranser",
    )
    return annotate_ikke_offisiell_statistikk(fig)


def leveranse_tjeneste_per_maaned(data_leveranse: pd.DataFrame) -> go.Figure:
    data_leveranse["fullfort_yearmonth"] = data_leveranse.fullfort.dt.strftime("%Y-%m")
    saker_per_tjeneste_og_måned = (
        data_leveranse[data_leveranse.status == "LEVERT"]
        .groupby(["iaTjenesteNavn", "fullfort_yearmonth"])
        .saksnummer.size()
        .reset_index()
    )

    fig = go.Figure()

    alle_måneder = alle_måneder_mellom_datoer(data_leveranse.sistEndret.min())
    antall_mnd = min(len(alle_måneder), 12)

    for tjeneste in saker_per_tjeneste_og_måned.iaTjenesteNavn.unique():
        filtrert = (
            saker_per_tjeneste_og_måned[
                saker_per_tjeneste_og_måned.iaTjenesteNavn == tjeneste
            ]
            .set_index("fullfort_yearmonth")
            .reindex(alle_måneder, fill_value=0)
        )
        fig.add_trace(
            go.Scatter(
                x=filtrert.index[-antall_mnd:],
                y=filtrert.saksnummer[-antall_mnd:],
                name=tjeneste,
            )
        )

    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Levert måned",
        yaxis_title="Antall leverte IA-tjenester",
        legend_orientation="h",
        legend_y=1.1,
    )
    return annotate_ikke_offisiell_statistikk(fig, y=1.2)


def forskjell_frist_fullfort(data_leveranse: pd.DataFrame) -> go.Figure():
    fullfort_leveranser = data_leveranse[data_leveranse.status == "LEVERT"]
    forskjell_frist_fullfort = (
        fullfort_leveranser.fullfort.dt.normalize()
        - pd.to_datetime(fullfort_leveranser.frist)
    ).dt.days

    min_ = forskjell_frist_fullfort.min()
    max_ = forskjell_frist_fullfort.max()

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=forskjell_frist_fullfort,
            xbins={
                "start": min_,
                "end": max_,
                "size": 1,
            },
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        yaxis_title="Antall fullførte IA-tjenester",
        xaxis=dict(
            title="Antall dager",
            rangeslider=dict(visible=True),
            range=[max(min_, -100), min(max_, 100)],
        ),
    )

    return annotate_ikke_offisiell_statistikk(fig)


def andel_leveranseregistreringer_gjort_av_superbrukere(
    data_leveranse: pd.DataFrame,
) -> go.Figure():
    data_leveranse["sistEndret_måned"] = data_leveranse.sistEndret.dt.strftime("%Y-%m")

    antall_registreringer_superbrukere_per_måned = (
        data_leveranse[
            (data_leveranse.status == "LEVERT")
            & (data_leveranse.sistEndretAvRolle == "SUPERBRUKER")
        ]
        .groupby("sistEndret_måned")
        .sistEndretAv.size()
    )

    antall_registreringer_per_måned = (
        data_leveranse[data_leveranse.status == "LEVERT"]
        .groupby("sistEndret_måned")
        .sistEndretAv.size()
    )

    andel_registreringer_superbrukere_per_måned = (
        antall_registreringer_superbrukere_per_måned / antall_registreringer_per_måned
    ).dropna()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=andel_registreringer_superbrukere_per_måned.index,
            y=andel_registreringer_superbrukere_per_måned.values * 100,
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Måned",
        yaxis_title="Andel registreringer (%)",
        xaxis={"type": "category"},
    )

    return annotate_ikke_offisiell_statistikk(fig)


def begrunnelse_ikke_aktuell(
    ikke_aktuell: pd.DataFrame, begrunnelse_sortering: list
) -> go.Figure:
    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "domain", "r": 0.1}, {}]],
        subplot_titles=("Hovedgrunn", "Detaljert begrunnelse"),
        column_widths=[0.4, 0.6],
    )
    fig.update_layout(
        height=450,
        width=850,
        showlegend=False,
    )

    # Hovedgrunn

    ikke_aktuell["hovedgrunn"] = ikke_aktuell.ikkeAktuelBegrunnelse.map(
        ikkeaktuell_hovedgrunn
    )
    antall_hovedgrunn = ikke_aktuell.hovedgrunn.value_counts().sort_values(
        ascending=True
    )
    fig.add_trace(
        go.Pie(
            labels=antall_hovedgrunn.index,
            values=antall_hovedgrunn.values,
            textinfo="label+percent",
            hole=0.4,
            marker_colors=plotly_colors,
        ),
        row=1,
        col=1,
    )

    # Detaljert begrunnelse

    antall_saker_ikke_aktuell = ikke_aktuell.drop_duplicates(
        "saksnummer", keep="last"
    ).shape[0]

    ikke_aktuell_per_begrunnelse = (
        ikke_aktuell.groupby("ikkeAktuelBegrunnelse_lesbar")
        .saksnummer.nunique()
        .reset_index()
        .sort_values(
            "ikkeAktuelBegrunnelse_lesbar",
            key=lambda col: col.map(lambda e: begrunnelse_sortering.index(e)),
        )
        .reset_index()
    )
    andel = [
        x * 100 / antall_saker_ikke_aktuell
        for x in ikke_aktuell_per_begrunnelse.saksnummer
    ]
    fig.add_trace(
        go.Bar(
            y=ikke_aktuell_per_begrunnelse.ikkeAktuelBegrunnelse_lesbar,
            x=andel,
            text=[
                f"{andel[i]:.2f}%, {ikke_aktuell_per_begrunnelse.saksnummer[i]}"
                for i in range(len(andel))
            ],
            marker_color=plotly_colors,
            orientation="h",
        ),
        row=1,
        col=2,
    )
    for idx, begrunnelse in enumerate(
        ikke_aktuell_per_begrunnelse.ikkeAktuelBegrunnelse_lesbar
    ):
        fig.add_annotation(
            x=0,
            y=idx - 0.4,
            text=begrunnelse,
            xanchor="left",
            showarrow=False,
            row=1,
            col=2,
        )
    fig.update_layout(plot_bgcolor="rgb(255,255,255)", bargap=0.4)
    fig.update_xaxes(showticklabels=False, row=1, col=2)
    fig.update_yaxes(autorange="reversed", visible=False, row=1, col=2)

    return annotate_ikke_offisiell_statistikk(fig, y=1.2)


def antall_leveranser_per_tjeneste(
    data_leveranse: pd.DataFrame, alle_iatjenester_og_status=None
) -> go.Figure:
    leveranser_per_tjeneste = (
        data_leveranse.drop_duplicates(["saksnummer", "iaTjenesteId"], keep="last")
        .groupby(["iaTjenesteNavn", "status"])
        .saksnummer.nunique()
        .sort_values(ascending=True)
    )
    if alle_iatjenester_og_status is not None:
        leveranser_per_tjeneste = leveranser_per_tjeneste.reindex(
            alle_iatjenester_og_status, fill_value=0
        )

    leveranser_per_tjeneste = leveranser_per_tjeneste.reset_index()

    fig = go.Figure()

    for status in leveranser_per_tjeneste.status.unique():
        leveranser_per_tjeneste_filtered = leveranser_per_tjeneste[
            leveranser_per_tjeneste.status == status
        ]
        fig.add_trace(
            go.Bar(
                y=leveranser_per_tjeneste_filtered["iaTjenesteNavn"],
                x=leveranser_per_tjeneste_filtered["saksnummer"],
                text=leveranser_per_tjeneste_filtered["saksnummer"],
                orientation="h",
                name=status.capitalize().replace("_", " "),
            )
        )

    fig.update_layout(
        height=500,
        width=800,
        plot_bgcolor="rgb(255,255,255)",
        xaxis_showticklabels=False,
        xaxis_title="Antall saker",
        xaxis_title_standoff=80,
        legend=dict(orientation="h", yanchor="bottom", y=0, xanchor="right", x=1),
    )

    return annotate_ikke_offisiell_statistikk(fig, y=1.2)
