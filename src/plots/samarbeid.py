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

    return annotate_ikke_offisiell_statistikk(fig, y=1.15, color="red", weight="bold")


def plot_gjennomførte_spørreundersøkelser_over_tid(
    data_spørreundersøkelse: pd.DataFrame,
    spr_type: str,
    width: int = 850,
) -> go.Figure:
    """
    Plotter antall spørreundersøkelser av type spr_type over tid, gruppert per uke.

    Args:
        data_spørreundersøkelse: DataFrame med spørreundersøkelser
        spr_type: Type spørreundersøkelse ("Behovsvurdering" eller "Evaluering")

    Returns:
        Plotly figur som viser antall gjennomførte spørreundersøkelser per uke
    """
    fig = go.Figure()

    fullførte_spørreundersøkelser = data_spørreundersøkelse[
        (data_spørreundersøkelse["type"] == spr_type)
        & (data_spørreundersøkelse["status"] == "AVSLUTTET")
    ].copy()

    if fullførte_spørreundersøkelser.empty:
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

    # BUG: noen spørreundersøkelser har per 01.07.2025 ikke fullført dato som de burde ha.
    # Se trello oppg: https://trello.com/c/MQxBbpDU/3372-rydding-i-databasen-for-sp%C3%B8rreunders%C3%B8kelser
    # TODO: Gjør oppgave og kjør reeksport, så kan vi fjerne denne koden.
    fullførte_spørreundersøkelser["completion_date"] = fullførte_spørreundersøkelser[
        "fullfort"
    ].fillna(fullførte_spørreundersøkelser["endret"])

    # Convert to datetime
    fullførte_spørreundersøkelser["completion_date"] = pd.to_datetime(
        fullførte_spørreundersøkelser["completion_date"]
    )

    # Sort by completion date
    fullførte_spørreundersøkelser: pd.DataFrame = (
        fullførte_spørreundersøkelser.sort_values("completion_date")
    )

    # Group by week and count occurrences
    weekly_counts: pd.Series[int] = fullførte_spørreundersøkelser.resample(
        "W-MON", on="completion_date"
    ).size()

    # Reset index to get a dataframe with date and count columns
    weekly_counts_df: pd.DataFrame = weekly_counts.reset_index()

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
            ],
        ),
        bargap=0.5,
        width=width,
    )

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
        xaxis_title=f"Tid fra samarbeid ble opprettet til første {hendelse_navn.lower()} ble gjennomført",
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
    height: int = 400,
    width: int = 850,
    farger: dict[str, str] = {
        "AKTIV": "#368da8",
        "FULLFØRT": "#06893a",
        "AVBRUTT": "#c30000",
    },
) -> go.Figure:
    avsluttede_behovsvurderinger: pd.DataFrame = data_spørreundersøkelse[
        (data_spørreundersøkelse["status"] == "AVSLUTTET")
        & (data_spørreundersøkelse["type"] == "Behovsvurdering")
    ]
    avsluttede_evalueringer: pd.DataFrame = data_spørreundersøkelse[
        (data_spørreundersøkelse["status"] == "AVSLUTTET")
        & (data_spørreundersøkelse["type"] == "Evaluering")
    ]

    trakt_dict: dict[str, int] = {}
    for samarbeid_status in ["AKTIV", "FULLFØRT", "AVBRUTT"]:
        trakt_dict[f"samarbeid_{samarbeid_status}"] = data_samarbeid[
            data_samarbeid["status"] == samarbeid_status
        ]["id"].nunique()

        trakt_dict[f"behovsvurderinger_{samarbeid_status}"] = (
            avsluttede_behovsvurderinger[
                avsluttede_behovsvurderinger["samarbeid_status"] == samarbeid_status
            ]["samarbeid_id"].nunique()
        )

        trakt_dict[f"samarbeidsplaner_{samarbeid_status}"] = data_samarbeidsplan[
            data_samarbeidsplan["samarbeid_status"] == samarbeid_status
        ]["samarbeid_id"].nunique()

        trakt_dict[f"evalueringer_{samarbeid_status}"] = avsluttede_evalueringer[
            avsluttede_evalueringer["samarbeid_status"] == samarbeid_status
        ]["samarbeid_id"].nunique()

    fig = go.Figure()

    for samarbeid_status in ["AKTIV", "FULLFØRT", "AVBRUTT"]:
        fig.add_trace(
            go.Funnel(
                name=f"{samarbeid_status.capitalize()}e samarbeid",
                marker={
                    "color": farger[samarbeid_status],
                },
                y=[
                    "Antall samarbeid/" + "<br>" + "underavdelinger",
                    "Antall samarbeid med"
                    + "<br>"
                    + "fullført behovsvurdering"
                    + "<br>"
                    + "(minst ett svar)",
                    "Antall samarbeid med" + "<br>" + "opprettet samarbeidsplan",
                    "Antall samarbeid med"
                    + "<br>"
                    + "fullført evaluering"
                    + "<br>"
                    + "(minst ett svar)",
                ],
                x=[
                    trakt_dict[f"samarbeid_{samarbeid_status}"],
                    trakt_dict[f"behovsvurderinger_{samarbeid_status}"],
                    trakt_dict[f"samarbeidsplaner_{samarbeid_status}"],
                    trakt_dict[f"evalueringer_{samarbeid_status}"],
                ],
                hovertemplate="%{y}: %{x},<br>%{percentInitial} prosent av {name}",
                textposition="inside",
                textinfo="value+percent initial",
            )
        )

    fig.update_layout(
        height=height,
        width=width,
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99),
    )

    return annotate_ikke_offisiell_statistikk(fig=fig)


def _format_number(value: float) -> str:
    return f"{int(value)}" if value.is_integer() else f"{value:.1f}"


def _timer_label(input: str) -> str:
    return "timer" if input != "1" else "time"


def _dager_label(input: str):
    return "dager" if input != "1" else "dag"


def _uke_label(input: str):
    return "uker" if input != "1" else "uke"


def _måned_label(input: str):
    return "mnder" if input != "1" else "mnd"


def finn_tidsenhet(timer_input: float) -> tuple[str, str]:
    if timer_input < 1:
        minutter = round(timer_input * 60, 1)
        return _format_number(minutter), "minutter"
    elif timer_input < 24:
        timer = round(timer_input, 1)
        return _format_number(timer), "timer"
    elif timer_input < 24 * 7:
        dager = round(timer_input / 24, 1)
        return _format_number(dager), "dager"
    elif timer_input < 24 * 7 * 4:
        uker = round(timer_input / (24 * 7), 1)
        return _format_number(uker), "uker"
    elif timer_input < 24 * 365:
        måneder = round(timer_input / (24 * (365 / 12)), 1)
        return _format_number(måneder), "måneder"
    else:
        år = round(timer_input / (24 * 365), 1)
        return _format_number(år), "år"


def _bin_label(timerStart: float = 0.0, timerSlutt: float = 0.0) -> str:
    start_str, start_unit = finn_tidsenhet(timerStart)

    end_str, end_unit = finn_tidsenhet(timerSlutt)

    minutt_label = "min"
    år_label = "år"

    if start_unit == end_unit:
        if end_unit == "minutter":
            unit_label = minutt_label
        elif end_unit == "timer":
            unit_label = _timer_label(end_str)
        elif end_unit == "dager":
            unit_label = _dager_label(end_str)
        elif end_unit == "uker":
            unit_label = _uke_label(end_str)
        elif end_unit == "måneder":
            unit_label = _måned_label(end_str)
        elif end_unit == "år":
            unit_label = år_label
        else:
            raise ValueError(f"Ukjent tidsenhet: {end_unit}")

        return f"{start_str} - {end_str} {unit_label}"

    else:
        if start_unit == "minutter":
            start_unit_label = minutt_label
        elif start_unit == "timer":
            start_unit_label = _timer_label(start_str)
        elif start_unit == "dager":
            start_unit_label = _dager_label(start_str)
        elif start_unit == "uker":
            start_unit_label = _uke_label(start_str)
        elif start_unit == "måneder":
            start_unit_label = _måned_label(end_str)
        elif start_unit == "år":
            start_unit_label = år_label
        else:
            raise ValueError(f"Ukjent tidsenhet: {start_unit}")

        if end_unit == "minutter":
            end_unit_label = minutt_label
        elif end_unit == "timer":
            end_unit_label = _timer_label(start_str)
        elif end_unit == "dager":
            end_unit_label = _dager_label(start_str)
        elif end_unit == "uker":
            end_unit_label = _uke_label(start_str)
        elif end_unit == "måneder":
            end_unit_label = _måned_label(end_str)
        elif end_unit == "år":
            end_unit_label = år_label
        else:
            raise ValueError(f"Ukjent tidsenhet: {end_unit}")

        return f"{start_str} {start_unit_label} - {end_str} {end_unit_label}"


def bins_and_labels(bin_type: str) -> tuple[list[float], list[str]]:
    custom_bins = make_custom_bins(bin_type=bin_type)

    x_labels: list[str] = []
    for i in range(len(custom_bins) - 1):
        x_labels.append(_bin_label(custom_bins[i], custom_bins[i + 1]))

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
