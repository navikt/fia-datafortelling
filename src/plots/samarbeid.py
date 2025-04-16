import numbers

import pandas as pd
import plotly.graph_objects as go

from src.utils.helper import annotate_ikke_offisiell_statistikk


def plot_tid_til_første_spørreundersøkelse(
    df: pd.DataFrame,
    kolonne: str,
    type_spørreundersøkelse: str = "Behovsvurdering",
) -> go.Figure:
    """
    Lager et stolpediagram som viser hvor lang tid det tar fra et samarbeid blir opprettet til spørreundersøkelse er gjennomført.

    Args:
        df: DataFrame av samarbeid som inneholder kolonnene 'opprettet' og 'fullfort'.

    Returns:
        Plotly figur med histogram og gjennomsnittlig tid til fullføring.
    """

    # Starter med en tom figur for å unngå feil ved tom DataFrame
    fig = go.Figure()

    # Ved tom DataFrame, vis en melding
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

    df["time_to_completion"] = (df[kolonne] - df["opprettet"]).dt.total_seconds() / (
        60 * 60
    )

    custom_bins = make_custom_bins(type_bin=type_spørreundersøkelse)
    counts = (
        pd.cut(df["time_to_completion"], bins=custom_bins).value_counts().sort_index()
    )

    x_labels = []
    for i in range(len(custom_bins) - 1):
        x_labels.append(f"{bin_label(custom_bins[i])}-{bin_label(custom_bins[i + 1])}")

    # lager stolpediagam
    fig = go.Figure(
        data=[
            go.Bar(
                x=x_labels,
                y=counts.values,
                marker_color="#3366CC",
                hovertemplate="Tid: %{x}<br>Antall samarbeid: %{y}<extra></extra>",
            )
        ]
    )

    # Annotations og linjer for gjennomsnitt og median
    gjennomsnitt = df["time_to_completion"].mean()
    avg_bin_index = pd.cut([gjennomsnitt], bins=custom_bins).codes[0]
    median = df["time_to_completion"].median()
    median_bin_index = pd.cut([median], bins=custom_bins).codes[0]

    fig.add_vline(
        x=median_bin_index,
        line_width=2,
        line_dash="dash",
        line_color="#ef553b",
        annotation_text=f"Median: {(median / 24):.1f} dager",
        annotation_position="top left" if median <= gjennomsnitt else "top right",
        annotation_borderwidth=6,
        annotation_font_color="white",
        annotation_bgcolor="#ef553b",
    )

    fig.add_vline(
        x=avg_bin_index,
        line_width=2,
        line_dash="dash",
        line_color="#ef553b",
        annotation_text=f"Gjennomsnitt: {(gjennomsnitt / 24):.1f} dager",
        annotation_position="top right" if median <= gjennomsnitt else "top left",
        annotation_borderwidth=6,
        annotation_font_color="white",
        annotation_bgcolor="#ef553b",
    )

    # Oppdater layout med aksetitler og range for plass til annotasjoner
    fig.update_layout(
        xaxis_title=f"Tid fra samarbeid ble opprettet til første {type_spørreundersøkelse.lower()} ble gjennomført (dager)",
        yaxis_title="Antall samarbeid",
        bargap=0.04,
        yaxis_range=[0, (counts.values.max() * 1.4)],
    )

    # Display the plot
    return fig


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

    df["time_to_completion"] = (df["fullfort"] - df["opprettet"]).dt.total_seconds() / (
        60 * 60
    )

    custom_bins = make_custom_bins(type_bin="Samarbeid")
    counts = (
        pd.cut(df["time_to_completion"], bins=custom_bins).value_counts().sort_index()
    )

    x_labels = []
    for i in range(len(custom_bins) - 1):
        x_labels.append(f"{bin_label(custom_bins[i])}-{bin_label(custom_bins[i + 1])}")

    # lager stolpediagam
    fig = go.Figure(
        data=[
            go.Bar(
                x=x_labels,
                y=counts.values,
                marker_color="#3366CC",
                hovertemplate="Tid: %{x}<br>Antall samarbeid: %{y}<extra></extra>",
            )
        ]
    )

    # Annotations og linjer for gjennomsnitt og median
    gjennomsnitt = df["time_to_completion"].mean()
    avg_bin_index = pd.cut([gjennomsnitt], bins=custom_bins).codes[0]
    median = df["time_to_completion"].median()
    median_bin_index = pd.cut([median], bins=custom_bins).codes[0]

    fig.add_vline(
        x=median_bin_index,
        line_width=2,
        line_dash="dash",
        line_color="#ef553b",
        annotation_text=f"Median: {(median / 24):.1f} dager",
        annotation_position="top left" if median <= gjennomsnitt else "top right",
        annotation_borderwidth=6,
        annotation_font_color="white",
        annotation_bgcolor="#ef553b",
    )

    fig.add_vline(
        x=avg_bin_index,
        line_width=2,
        line_dash="dash",
        line_color="#ef553b",
        annotation_text=f"Gjennomsnitt: {(gjennomsnitt / 24):.1f} dager",
        annotation_position="top right" if median <= gjennomsnitt else "top left",
        annotation_borderwidth=6,
        annotation_font_color="white",
        annotation_bgcolor="#ef553b",
    )

    # Oppdater layout med aksetitler og range for plass til annotasjoner
    fig.update_layout(
        xaxis_title="Tid fra samarbeid ble opprettet til det ble fullført",
        yaxis_title="Antall samarbeid",
        bargap=0.04,
        yaxis_range=[0, (counts.values.max() * 1.4)],
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


def bin_label(timer) -> str:
    if timer < 1:
        return f"{int(timer * 60)} min"
    elif timer < 24:
        return f"{int(timer)} {'time' if timer == 1 else 'timer'}"
    elif timer < 24 * 7:
        dager = timer / 24
        val = f"{int(dager)}" if dager.is_integer() else f"{dager:.1f}"
        return f"{val} {'dag' if dager == 1 else 'dager'}"
    elif timer <= 24 * 7 * 4:
        uker = timer / 24 / 7
        val = f"{int(uker)}" if uker.is_integer() else f"{uker:.1f}"
        return f"{val} {'uke' if uker == 1 else 'uker'}"
    elif timer < 24 * 365:
        måneder = timer / 24 / (365 / 12)
        val = f"{int(måneder)}" if måneder.is_integer() else f"{måneder:.1f}"
        return f"{val} mnd"
    else:
        år = timer / 24 / 365
        val = f"{int(år)}" if år.is_integer() else f"{år:.1f}"
        return f"{val} år"


def make_custom_bins(type_bin: str) -> list:
    custom_bins = []
    if type_bin == "Behovsvurdering":
        custom_bins = [
            # minutter
            0,
            0.25,
            0.5,
            0.75,
            # timer
            1,
            2,
            4,
            12,
            # dager
            24,
            24 * 2,
            24 * 3,
            24 * 4,
            24 * 5,
            24 * 6,
            # uker
            24 * 7,
            24 * 7 * 2,
            24 * 7 * 3,
            # måneder
            24 * (365 / 12),
            24 * (365 / 12) * 2,
            24 * (365 / 12) * 3,
            24 * (365 / 12) * 4,
            24 * (365 / 12) * 5,
            24 * (365 / 12) * 6,
            # år
            24 * 365,
        ]
    elif type_bin == "Samarbeid":
        custom_bins = [
            # minutter
            0,
            0.25,
            0.5,
            0.75,
            # timer
            1,
            2,
            4,
            12,
            # dager
            24,
            24 * 2,
            24 * 3,
            24 * 4,
            24 * 5,
            24 * 6,
            # uker
            24 * 7,
            24 * 7 * 2,
            24 * 7 * 3,
            # måneder
            24 * (365 / 12),
            24 * (365 / 12) * 2,
            24 * (365 / 12) * 3,
            24 * (365 / 12) * 4,
            24 * (365 / 12) * 5,
            24 * (365 / 12) * 6,
            # år
            24 * 365,
            24 * 365 * 1.5,
            24 * 365 * 2,
        ]
    elif type_bin == "Evaluering":
        custom_bins = [
            0,
            24,
            # uker
            24 * 7,
            24 * 7 * 2,
            24 * 7 * 3,
            # måneder
            24 * (365 / 12),
            24 * (365 / 12) * 2,
            24 * (365 / 12) * 3,
            24 * (365 / 12) * 4,
            24 * (365 / 12) * 5,
            24 * (365 / 12) * 6,
            # år
            24 * 365,
            24 * 365 * 1.5,
            24 * 365 * 2,
        ]

    return custom_bins
