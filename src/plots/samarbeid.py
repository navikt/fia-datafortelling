import numbers

import pandas as pd
import plotly.graph_objects as go

from src.utils.helper import annotate_ikke_offisiell_statistikk


def plot_tid_brukt_i_samarbeid(df: pd.DataFrame) -> go.Figure:
    """
    Lager et histogram som viser hvor lang tid det tar fra et samarbeid blir opprettet til det blir fullført.

    Args:
        df: DataFrame av samarbeid som inneholder kolonnene 'opprettet' og 'fullfort'.

    Returns:
        Plotly figur med histogram og gjennomsnittlig tid til fullføring.
    """

    # Create a base figure
    fig = go.Figure()

    # Handle empty DataFrame
    if df.empty:
        fig.add_annotation(
            text="Ingen data tilgjengelig",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20),
        )
        return fig

    # Calculate time to completion in days, handling potential NaN values
    df = df.copy()  # Create copy to avoid modifying original
    df["time_to_completion"] = (df["fullfort"] - df["opprettet"]).dt.total_seconds() / (
        60 * 60 * 24
    )

    # Calculate average
    gjennomsnitt = df["time_to_completion"].mean()

    # Create histogram
    fig = go.Figure(
        data=[
            go.Histogram(
                x=df["time_to_completion"],
                nbinsx=40,  # Adjust based on your data spread
                marker_color="#3366CC",
                hovertemplate="Tid brukt i samarbeid: %{x:.1f} dager<br>Antall samarbeid: %{y}<extra></extra>",
            )
        ]
    )

    # Add vertical line for average
    fig.add_vline(
        x=gjennomsnitt,
        line_width=2,
        line_dash="dash",
        line_color="#ef553b",
        annotation_text=f"Gjennomsnitt: {gjennomsnitt:.1f} dager",
        annotation_position="top right",
        annotation_borderwidth=6,
        annotation_font_color="white",
        annotation_bgcolor="#ef553b",
    )

    # Update layout
    fig.update_layout(
        xaxis_title="Tid fra samarbeid ble opprettet til det ble fullført",
        yaxis_title="Antall samarbeid",
        bargap=0.04,
    )

    # Display the plot
    return fig


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

        maxIndex = antall_saker_per_antall_samarbeid.index.max()
        if not isinstance(maxIndex, numbers.Number):
            maxIndex = 0

        # Fyller inn manglende verdier
        antall_saker_per_antall_samarbeid = antall_saker_per_antall_samarbeid.reindex(
            range(1, maxIndex + 1), fill_value=0
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


def trakt_antall_samarbeid(
    data_samarbeid: pd.DataFrame,
    data_spørreundersøkelse: pd.DataFrame,
    data_samarbeidsplan: pd.DataFrame,
) -> go.Figure:
    # Aktive samarbeid
    aktive_samarbeid = data_samarbeid[data_samarbeid.status == "AKTIV"].id.unique()

    # Antall aktive samarbeid
    antall_aktive_samarbeid = len(aktive_samarbeid)

    # Antall aktive samarbeid med fullført behovsvurdering
    antall_aktive_samarbeid_med_fullfort_behovsvurdering = data_spørreundersøkelse[
        data_spørreundersøkelse.samarbeidId.isin(aktive_samarbeid)
        & (data_spørreundersøkelse.status == "AVSLUTTET")
        & (data_spørreundersøkelse.type == "Behovsvurdering")
        & (data_spørreundersøkelse.harMinstEttSvar)
    ].samarbeidId.nunique()

    antall_aktive_samarbeid_med_fullfort_evaluering = data_spørreundersøkelse[
        data_spørreundersøkelse.samarbeidId.isin(aktive_samarbeid)
        & (data_spørreundersøkelse.status == "AVSLUTTET")
        & (data_spørreundersøkelse.type == "Evaluering")
        & (data_spørreundersøkelse.harMinstEttSvar)
    ].samarbeidId.nunique()

    # Antall aktive samarbeid med opprettet samarbeidsplan
    antall_aktive_samarbeid_med_samarbeidsplan = data_samarbeidsplan[
        data_samarbeidsplan.samarbeidId.isin(aktive_samarbeid)
    ].samarbeidId.nunique()

    # TODO: hvordan fjerne null?

    fig = go.Figure(
        go.Funnel(
            y=[
                "Antall aktive samarbeid/underavdelinger",
                "Antall aktive samarbeid/underavdelinger<br>med fullført behovsvudering med minst ett svar",
                "Antall aktive samarbeid/underavdelinger<br>med opprettet samarbeidsplan",
                "Antall aktive samarbeid/underavdelinger<br>med fullført evaluering med minst ett svar",
            ],
            x=[
                antall_aktive_samarbeid,
                antall_aktive_samarbeid_med_fullfort_behovsvurdering,
                antall_aktive_samarbeid_med_samarbeidsplan,
                antall_aktive_samarbeid_med_fullfort_evaluering,
            ],
            textposition="inside",
            textinfo="value+percent initial",
            hoverinfo="x+y+text+percent initial+percent previous",
        )
    )
    fig.update_layout(
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return annotate_ikke_offisiell_statistikk(fig)
