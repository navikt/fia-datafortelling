import numbers

import pandas as pd
import plotly.graph_objects as go

from src.utils.helper import annotate_ikke_offisiell_statistikk


def plot_antall_samarbeid_over_tid(data_samarbeid: pd.DataFrame) -> go.Figure:
    """
    Plotter antall spørreundersøkelser av type spr_type over tid, gruppert per uke.

    Args:
        data_spørreundersøkelse: DataFrame med spørreundersøkelser
        spr_type: Type spørreundersøkelse ("Behovsvurdering" eller "Evaluering")

    Returns:
        Plotly figur som viser antall gjennomførte spørreundersøkelser per uke
    """
    # Create a base figure
    fig = go.Figure()

    if data_samarbeid.empty:
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

    # Create completion date column using fullfort if available, otherwise endret

    # Drop rows with no completion date

    # Convert to datetime
    data_samarbeid["opprettet"] = pd.to_datetime(data_samarbeid["opprettet"])

    # Filter data to only include dates on or after 24.09.2024
    target_date = pd.to_datetime("2024-09-24", utc=True)
    data_samarbeid = data_samarbeid[data_samarbeid["opprettet"] >= target_date]

    # Sort by completion date

    # Group by week and count occurrences
    weekly_counts = data_samarbeid.resample("W-MON", on="opprettet").size()

    # Reset index to get a dataframe with date and count columns
    weekly_counts_df = weekly_counts.reset_index()

    # Add week number and year columns
    weekly_counts_df["week_num"] = weekly_counts_df["opprettet"].dt.isocalendar().week
    weekly_counts_df["year"] = weekly_counts_df["opprettet"].dt.isocalendar().year

    # Create week labels in format "Week XX YYYY"
    weekly_counts_df["week_label"] = (
        "Uke "
        + weekly_counts_df["week_num"].astype(str).str.zfill(2)
        + " "
        + weekly_counts_df["year"].astype(str)
    )

    fig.add_trace(
        go.Bar(
            x=weekly_counts_df["opprettet"],
            y=weekly_counts_df[0],
            name="Opprettede samarbeid",
            marker_color="#3366CC",
            hovertemplate="Uke %{customdata[0]} %{customdata[1]}<br>Antall: %{y}<extra></extra>",
            customdata=weekly_counts_df[["week_num", "year"]],
        )
    )

    # Select every nth tick
    tick_indices = range(0, len(weekly_counts_df), 2)
    tickvals = weekly_counts_df.iloc[tick_indices]["opprettet"]
    ticktext = weekly_counts_df.iloc[tick_indices]["week_label"]

    # Update layout
    fig.update_layout(
        xaxis_title="Uke",
        yaxis_title="Antall",
        xaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=-45,
        ),
    )

    # Add annotation for unofficial statistics
    return annotate_ikke_offisiell_statistikk(fig, y=1.15, color="red", weight="bold")


def plot_gjennomførte_spørreundersøkelser_over_tid(
    data_spørreundersøkelse: pd.DataFrame, spr_type: str
):
    """
    Plotter antall spørreundersøkelser av type spr_type over tid, gruppert per uke.

    Args:
        data_spørreundersøkelse: DataFrame med spørreundersøkelser
        spr_type: Type spørreundersøkelse ("Behovsvurdering" eller "Evaluering")

    Returns:
        Plotly figur som viser antall gjennomførte spørreundersøkelser per uke
    """
    # Create a base figure
    fig = go.Figure()

    # Filter by survey type
    filtered_df = data_spørreundersøkelse[
        data_spørreundersøkelse["type"] == spr_type
    ].copy()

    # Filter for completed surveys (status = "AVSLUTTET")
    completed_df = filtered_df[filtered_df["status"] == "AVSLUTTET"].copy()

    if completed_df.empty:
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

    # Create completion date column using fullfort if available, otherwise endret
    completed_df["completion_date"] = completed_df["fullfort"].fillna(
        completed_df["endret"]
    )

    # Drop rows with no completion date
    completed_df = completed_df.dropna(subset=["completion_date"])

    # Convert to datetime
    completed_df["completion_date"] = pd.to_datetime(completed_df["completion_date"])

    # Sort by completion date
    completed_df = completed_df.sort_values("completion_date")

    # Group by week and count occurrences
    weekly_counts = completed_df.resample("W-MON", on="completion_date").size()

    # Reset index to get a dataframe with date and count columns
    weekly_counts_df = weekly_counts.reset_index()

    # Add week number and year columns
    weekly_counts_df["week_num"] = weekly_counts_df["completion_date"].dt.isocalendar()[
        "week"
    ]
    weekly_counts_df["year"] = weekly_counts_df["completion_date"].dt.isocalendar()[
        "year"
    ]

    # Create week labels in format "Week XX YYYY"
    weekly_counts_df["week_label"] = (
        "Uke "
        + weekly_counts_df["week_num"].astype(str).str.zfill(2)
        + " "
        + weekly_counts_df["year"].astype(str)
    )

    fig.add_trace(
        go.Bar(
            x=weekly_counts_df["completion_date"],
            y=weekly_counts_df[0],  # The count column
            name=f"Gjennomførte {spr_type}er",
            marker_color="#3366CC",
            hovertemplate="Uke %{customdata[0]} %{customdata[1]}<br>Antall: %{y}<extra></extra>",
            customdata=weekly_counts_df[["week_num", "year"]],
        )
    )

    # Select every nth tick
    tick_indices = range(0, len(weekly_counts_df), 2)
    tickvals = weekly_counts_df.iloc[tick_indices]["completion_date"]
    ticktext = weekly_counts_df.iloc[tick_indices]["week_label"]

    # Update layout
    fig.update_layout(
        xaxis_title="Uke",
        yaxis_title="Antall",
        xaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=-45,
        ),
        yaxis=dict(
            range=[
                0,
                max(weekly_counts_df[0].max() * 1.1, 3),
            ],  # Ensures minimum height
        ),
        bargap=0.5,  # Controls space between bars (0-1)
        width=850,  # Fixed width for the entire plot
    )

    # Add annotation for unofficial statistics
    return annotate_ikke_offisiell_statistikk(fig, y=1.15, color="red", weight="bold")


def plot_tid_mellom_hendelser(
    df: pd.DataFrame,
    kolonne_start: str,
    kolonne_slutt: str,
    hendelse_navn: str,
    width: int = 850,
    farge_gjennomsnitt: str = "#00a693",
    farge_median: str = "#74afda",
    farge_stolper: str = "#494e84",
    yaxis_range_max: float | None = None,
) -> tuple[go.Figure, float]:
    # TODO: Dropdown: Næring + Bransje
    """
    Lager et stolpediagram som viser hvor lang tid det mellom hendelser i et samarbeid

    Skal være generisk nok til å brukes for både tid mellom opprettelse og første spørreundersøkelse, og opprettet til fullført samarbeid, eller evaluering

    Args:
        df: DataFrame av samarbeid som inneholder kolonnene 'opprettet' og 'fullfort'.

    Returns:
        Plotly figur med histogram og gjennomsnittlig tid mellom hendelser.
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
            width=width,
            showarrow=False,
            font=dict(size=20),
        )
        return fig, 0

    kolonne_tid = "tid_brukt_timer"
    df[kolonne_tid] = (df[kolonne_slutt] - df[kolonne_start]).dt.total_seconds() / (
        60 * 60
    )

    custom_bins, x_labels = bins_and_labels(bin_type=hendelse_navn)

    counts = pd.cut(df[kolonne_tid], bins=custom_bins).value_counts().sort_index()

    # lager stolpediagam
    fig = go.Figure(
        data=[
            go.Bar(
                x=x_labels,
                y=counts.values,
                marker_color=farge_stolper,
                hovertemplate="Tid: %{x}<br>Antall samarbeid: %{y}<extra></extra>",
            )
        ]
    )

    # Annotations og linjer for gjennomsnitt og median
    gjennomsnitt = df[kolonne_tid].mean()
    avg_bin_index = pd.cut([gjennomsnitt], bins=custom_bins).codes[0]
    median = df[kolonne_tid].median()
    median_bin_index = pd.cut([median], bins=custom_bins).codes[0]

    fig.add_vline(
        x=median_bin_index,
        line_width=2,
        line_dash="dash",
        line_color=farge_median,
        annotation_text=f"Median: {(median / 24):.1f} dager",
        annotation_position="top left" if median <= gjennomsnitt else "top right",
        annotation_borderwidth=6,
        annotation_font_color="white",
        annotation_bgcolor=farge_median,
    )

    fig.add_vline(
        x=avg_bin_index,
        line_width=2,
        line_dash="dash",
        line_color=farge_gjennomsnitt,
        annotation_text=f"Gjennomsnitt: {(gjennomsnitt / 24):.1f} dager",
        annotation_position="top right" if median <= gjennomsnitt else "top left",
        annotation_borderwidth=6,
        annotation_font_color="white",
        annotation_bgcolor=farge_gjennomsnitt,
    )

    yaxis_max = int(
        yaxis_range_max
        if yaxis_range_max is not None
        else int(counts.values.max() * 1.4)
    )

    # Oppdater layout med aksetitler og range for plass til annotasjoner
    fig.update_layout(
        xaxis_title=f"Tid fra samarbeid ble opprettet til første {hendelse_navn.lower()} ble gjennomført (dager)",
        yaxis_title="Antall samarbeid",
        bargap=0.04,
        width=width,
        yaxis_range=[
            0,
            yaxis_max,
        ],
    )

    # Display the plot
    return fig, yaxis_max


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
    ].samarbeidId.nunique()

    antall_aktive_samarbeid_med_fullfort_evaluering = data_spørreundersøkelse[
        data_spørreundersøkelse.samarbeidId.isin(aktive_samarbeid)
        & (data_spørreundersøkelse.status == "AVSLUTTET")
        & (data_spørreundersøkelse.type == "Evaluering")
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


def bin_label(timer: float) -> str:
    if timer < 1:
        return f"{int(timer * 60)} min"
    elif timer < 24:
        return f"{int(timer)} {'time' if timer == 1 else 'timer'}"
    elif timer < 24 * 7:
        return daglig_bin_label(timer)
    elif timer <= 24 * 7 * 4:
        return ukentlig_bin_label(timer)
    elif timer < 24 * 365:
        return månedlig_bin_label(timer)
    else:
        return årlig_bin_label(timer)


def daglig_bin_label(timer: float) -> str:
    dager = round(timer / 24, 1)
    val = f"{int(dager)}" if dager.is_integer() else f"{dager:.1f}"
    return f"{val} {'dag' if dager == 1 else 'dager'}"


def ukentlig_bin_label(timer: float) -> str:
    uker = round(timer / 24 / 7, 1)
    val = f"{int(uker)}" if uker.is_integer() else f"{uker:.1f}"
    return f"{val} {'uke' if uker == 1 else 'uker'}"


def månedlig_bin_label(timer: float) -> str:
    måneder = round(timer / 24 / (365 / 12), 1)
    val = f"{int(måneder)}" if måneder.is_integer() else f"{måneder:.1f}"
    return f"{val} mnd"


def årlig_bin_label(timer: float) -> str:
    år = timer / 24 / 365
    val = f"{int(år)}" if år.is_integer() else f"{år:.1f}"
    return f"{val} år"


def bins_and_labels(bin_type: str) -> tuple[list[float], list[str]]:
    custom_bins = make_custom_bins(bin_type=bin_type)

    x_labels: list[str] = []
    for i in range(len(custom_bins) - 1):
        x_labels.append(f"{bin_label(custom_bins[i])}-{bin_label(custom_bins[i + 1])}")

    return custom_bins, x_labels


def make_custom_bins(bin_type: str) -> list[float]:
    custom_bins: list[float] = []

    if bin_type == "Behovsvurdering":
        custom_bins = [
            # minutter
            0,
            1 / 6,  # 10 minutter
            0.5,
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
            24 * (365 / 12) * 6,
            # år
            24 * 365,
            24 * 365 * 1.5,
        ]
    elif bin_type == "Evaluering":
        custom_bins = [
            # minutter
            0,
            # 0.25,
            # 0.5,
            # 0.75,
            # timer
            # 1,
            # 2,
            # 4,
            # 12,
            # dager
            24,
            # 24 * 2,
            # 24 * 3,
            # 24 * 4,
            # 24 * 5,
            # 24 * 6,
            # uker
            24 * 7,
            24 * 7 * 2,
            24 * 7 * 3,
            # måneder
            24 * (365 / 12),
            24 * (365 / 12) * 2,
            24 * (365 / 12) * 2.5,
            24 * (365 / 12) * 3,
            24 * (365 / 12) * 4,
            24 * (365 / 12) * 4.5,
            24 * (365 / 12) * 5,
            24 * (365 / 12) * 5.5,
            24 * (365 / 12) * 6,
            24 * (365 / 12) * 6.5,
            24 * (365 / 12) * 7,
            24 * (365 / 12) * 7.5,
            24 * (365 / 12) * 8,
            24 * (365 / 12) * 9,
            24 * (365 / 12) * 10,
            24 * (365 / 12) * 11,
            # år
            24 * 365,
            24 * 365 * 2,
        ]
    elif bin_type == "Samarbeid":
        custom_bins = [
            # minutter
            0,
            # 0.25,
            # 0.5,
            # 0.75,
            # timer
            # 1,
            # 2,
            # 4,
            # 12,
            # dager
            24,
            # 24 * 2,
            # 24 * 3,
            # 24 * 4,
            # 24 * 5,
            # 24 * 6,
            # uker
            24 * 7,
            24 * 7 * 2,
            24 * 7 * 3,
            # måneder
            24 * (365 / 12),
            24 * (365 / 12) * 2,
            24 * (365 / 12) * 2.5,
            24 * (365 / 12) * 3,
            24 * (365 / 12) * 4,
            24 * (365 / 12) * 4.5,
            24 * (365 / 12) * 5,
            24 * (365 / 12) * 5.5,
            24 * (365 / 12) * 6,
            24 * (365 / 12) * 6.5,
            24 * (365 / 12) * 7,
            24 * (365 / 12) * 7.5,
            24 * (365 / 12) * 8,
            24 * (365 / 12) * 9,
            24 * (365 / 12) * 10,
            24 * (365 / 12) * 11,
            # år
            24 * 365,
            24 * 365 * 2,
        ]

    return custom_bins
