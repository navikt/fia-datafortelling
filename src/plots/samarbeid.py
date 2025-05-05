import numbers
from typing import Literal

import pandas as pd
import plotly.graph_objects as go

from src.utils.helper import annotate_ikke_offisiell_statistikk


def plot_antall_samarbeid_over_tid(data_samarbeid):
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


def plot_gjennomførte_spørreundersøkelser_over_tid(data_spørreundersøkelse, spr_type):
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
        data_spørreundersøkelse.type == spr_type
    ].copy()

    # Filter for completed surveys (status = "AVSLUTTET")
    completed_df = filtered_df[filtered_df.status == "AVSLUTTET"].copy()

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
    weekly_counts_df["week_num"] = (
        weekly_counts_df["completion_date"].dt.isocalendar().week
    )
    weekly_counts_df["year"] = weekly_counts_df["completion_date"].dt.isocalendar().year

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


def plot_tid_til_første_spørreundersøkelse(
    df: pd.DataFrame,
    kolonne: str,
    kolonne_start: str = "opprettet",
    type_spørreundersøkelse: str = "Behovsvurdering",
    farge_gjennomsnitt: str = "#daa520",
    farge_median: str = "#ef553b",
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

    kolonne_tid = "tid_brukt_timer"
    df[kolonne_tid] = (df[kolonne] - df[kolonne_start]).dt.total_seconds() / (60 * 60)

    custom_bins = make_custom_bins(bin_type=type_spørreundersøkelse)
    counts = pd.cut(df[kolonne_tid], bins=custom_bins).value_counts().sort_index()

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

    # Oppdater layout med aksetitler og range for plass til annotasjoner
    fig.update_layout(
        xaxis_title=f"Tid fra samarbeid ble opprettet til første {type_spørreundersøkelse.lower()} ble gjennomført (dager)",
        yaxis_title="Antall samarbeid",
        bargap=0.04,
        yaxis_range=[0, (counts.values.max() * 1.4)],
    )

    # Display the plot
    return fig


def plot_tid_brukt_i_samarbeid(
    df: pd.DataFrame,
    nedtrekk_kolonner: list[str] = ["resultatomrade", "status"],
    kolonne_slutt: str = "fullfort",
    kolonne_start: str = "opprettet",
    farge_gjennomsnitt: str = "#00a693",
    farge_median: str = "#74afda",
    farge_stolper: str = "#494e84",
) -> go.Figure:
    # Create a base figure
    fig = go.Figure()

    ## Feilhåndtering for tom dataframe
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

    # Calculate time to completion for all data
    # TODO: Rename til tid for gjennomføring eller bare tid?
    kolonne_tid = "tid_brukt_timer"
    df[kolonne_tid] = (df[kolonne_slutt] - df[kolonne_start]).dt.total_seconds() / (
        60 * 60
    )

    # Create x-axis labels and custom bins for time categorization
    custom_bins, x_labels = bins_and_labels(bin_type="Samarbeid")

    # For å ikke hoppe for mye i y-aksen lagrer vi maksverdi og holder plot like
    max_count = 0

    # Dictionary to store vlines and annotations for each resultatområde

    filter_verdier = {
        kolonne: ["Total"] + sorted(df[kolonne].unique().tolist())
        for kolonne in nedtrekk_kolonner
    }

    mulige_kombinasjoner = recursive_combinations(
        nedtrekk_kolonner,
        filter_verdier,
    )

    # Dictionary to store vlines and annotations for each filter combination
    vline_dict = {}

    # Add a trace for each filter combination
    for kombinasjon in mulige_kombinasjoner:
        # Filter data based on this combination
        filtered_df = df.copy()
        is_all_total = True

        for col, val in kombinasjon.items():
            if val != "Total":
                filtered_df = filtered_df[filtered_df[col] == val]
                is_all_total = False

        # Skip if filtered data is empty
        if filtered_df.empty:
            # TODO: show empty data trace
            continue

        # Sjekker hvilken kombinasjon av filtre som gir høyest verdi og setter det til taket på y-aksen
        counts = (
            pd.cut(filtered_df[kolonne_tid], bins=custom_bins)
            .value_counts()
            .sort_index()
        )

        if counts.values.max() > max_count:
            max_count = counts.values.max()

        nøkkel = "_".join([f"{col}:{val}" for col, val in kombinasjon.items()])

        # Add bar trace
        fig.add_trace(
            go.Bar(
                x=x_labels,
                y=counts.values,
                name=nøkkel,
                marker_color=farge_stolper,
                visible=is_all_total,  # Only the "all Total" combination is visible by default
                hovertemplate="Tid: %{x}<br>Antall samarbeid: %{y}<extra></extra>",
            )
        )

        # Calculate values for this combination
        gjennomsnitt = filtered_df[kolonne_tid].mean()
        gjennomsnitt_bin_index = pd.cut([gjennomsnitt], bins=custom_bins).codes[0]
        median = filtered_df[kolonne_tid].median()
        median_bin_index = pd.cut([median], bins=custom_bins).codes[0]

        # Store vline and annotation info for later use with dropdown
        vline_dict[nøkkel] = {
            "median_idx": median_bin_index,
            "gjennomsnitt_idx": gjennomsnitt_bin_index,
            "median_val": median,
            "gjennomsnitt_val": gjennomsnitt,
        }

    # Create dropdown menus for each filter column
    updatemenus = []

    # Keep state of current selection across dropdowns
    current_selection = {col: "Total" for col in nedtrekk_kolonner}

    for i, col in enumerate(nedtrekk_kolonner):
        buttons = []
        for val in filter_verdier[col]:
            # Create visible list for each button

            new_selection = current_selection.copy()
            new_selection[col] = val

            # Create the target key from this selection
            target_key = "_".join([f"{c}:{v}" for c, v in new_selection.items()])

            # Find which trace matches this filter combination
            visible_list = [False] * len(mulige_kombinasjoner)
            found_match = False

            # First look for exact match
            for combo_idx, combo in enumerate(mulige_kombinasjoner):
                combo_key = "_".join([f"{c}:{v}" for c, v in combo.items()])
                if combo_key == target_key and combo_key in vline_dict:
                    visible_list[combo_idx] = True
                    found_match = True
                    break

            # If no exact match, look for best alternative
            if not found_match:
                best_match_key = find_best_match(
                    mulige_kombinasjoner,
                    vline_dict,
                    new_selection,
                    nedtrekk_kolonner,
                )

                if best_match_key:
                    for combo_idx, combo in enumerate(mulige_kombinasjoner):
                        combo_key = "_".join([f"{c}:{v}" for c, v in combo.items()])
                        if combo_key == best_match_key:
                            visible_list[combo_idx] = True
                            target_key = best_match_key
                            break
                else:
                    # Fall back to "all Total" if no suitable match found
                    target_key = "_".join([f"{c}:Total" for c in nedtrekk_kolonner])
                    for combo_idx, combo in enumerate(mulige_kombinasjoner):
                        combo_key = "_".join([f"{c}:{v}" for c, v in combo.items()])
                        if combo_key == target_key:
                            visible_list[combo_idx] = True
                            break

            shapes, annotations = shapes_and_annotations(
                farge_gjennomsnitt,
                farge_median,
                vline_dict[target_key],
                target_key=target_key,
            )

            buttons.append(
                dict(
                    label=val,
                    method="update",
                    args=[
                        {"visible": visible_list},
                        {"shapes": shapes, "annotations": annotations},
                    ],
                )
            )

        updatemenus.append(
            dict(
                active=0,  # Set "Total" as active by default
                buttons=buttons,
                x=0.0 + (i * 0.35),  # Position each dropdown to the right
                y=1.50,  # Position each dropdown below the previous one
                xanchor="left",
                yanchor="top",
                # TODO: Add replacing name?
                # TODO: Set to paper anchor and put in the margin ant the top?
            )
        )
        # Add helper function to find best match

    # Initial reference combo (all Total)
    reference_key = "_".join([f"{c}:Total" for c in nedtrekk_kolonner])

    # Add initial lines and annotations for the default view (all Total)
    shapes, annotations = shapes_and_annotations(
        farge_gjennomsnitt,
        farge_median,
        vline_dict[reference_key],
        target_key=reference_key,
    )

    fig.update_layout(
        shapes=shapes,
        annotations=annotations,
    )

    # Update layout with dropdown menus and other settings
    fig.update_layout(
        xaxis_title="Tid fra samarbeid ble opprettet til det ble fullført",
        yaxis_title="Antall samarbeid",
        bargap=0.04,
        yaxis_range=[0, max_count * 1.4],
        updatemenus=updatemenus,
        margin=dict(t=120),  # Add more top margin for the filter label
    )

    return fig


def find_best_match(combinations, valid_keys, selection, columns):
    # Try progressively looser matches

    # First try exact match
    target_key = "_".join([f"{c}:{v}" for c, v in selection.items()])
    if target_key in valid_keys:
        return target_key

    # Try keeping current column value but set others to Total
    col_to_keep = [c for c, v in selection.items() if v != "Total"][0]
    loose_selection = {c: "Total" for c in columns}
    loose_selection[col_to_keep] = selection[col_to_keep]

    target_key = "_".join([f"{c}:{v}" for c, v in loose_selection.items()])
    if target_key in valid_keys:
        return target_key

    # If nothing works, return all Total
    return "_".join([f"{c}:Total" for c in columns])


def shapes_and_annotations(
    farge_gjennomsnitt, farge_median, vline_dict, target_key=None
):
    median_is_larger = vline_dict["median_val"] >= vline_dict["gjennomsnitt_val"]
    shapes = [
        # Median line
        make_vline(
            color=farge_median,
            x_koordinat=vline_dict["median_idx"],
        ),
        # Average line
        make_vline(
            color=farge_gjennomsnitt,
            x_koordinat=vline_dict["gjennomsnitt_idx"],
        ),
    ]
    annotations = [
        # Median annotation
        make_annotation(
            color=farge_median,
            vline_dict=vline_dict,
            isBigger=median_is_larger,
            annotation_type="median",
        ),
        # Average annotation
        make_annotation(
            color=farge_gjennomsnitt,
            vline_dict=vline_dict,
            isBigger=not median_is_larger,
            annotation_type="gjennomsnitt",
        ),
    ]

    # Add annotation for current filter combination if provided
    if target_key:
        # Format the target key for display (replace underscores with spaces, etc.)
        display_key = target_key.replace("_", ", ").replace(":", ": ")

        # Add annotation at the top of the plot
        annotations.append(
            {
                "x": 0.5,
                "y": 1.20,
                "xref": "paper",
                "yref": "paper",
                "text": f"<b>Filter:</b> {display_key}",
                "showarrow": False,
                "font": {"size": 12, "color": "black"},
                "align": "center",
                "bgcolor": "rgba(255, 255, 255, 0.8)",
                "bordercolor": "gray",
                "borderwidth": 1,
                "borderpad": 4,
            }
        )

    return shapes, annotations


def make_vline(
    color,
    x_koordinat,
):
    return {
        "type": "line",
        "x0": x_koordinat,  # rett vertikal linje har samme x-koordinat for start og slutt
        "x1": x_koordinat,  # rett vertikal linje har samme x-koordinat for start og slutt
        "y0": 0,
        "y1": 1,
        "yref": "paper",
        "line": {
            "color": color,
            "width": 2,
            "dash": "dash",
        },
    }


def recursive_combinations(nedtrekk_kolonner, filter_values):
    filter_combinations = []

    # TODO: Må ha code review, usikker på om rekursiv gjennomgang av filter-kombinasjoner er rett
    def generate_combinations(current_combo, level=0, maxlevel=len(nedtrekk_kolonner)):
        if level == maxlevel:
            filter_combinations.append(current_combo.copy())
            return

        for value in filter_values[nedtrekk_kolonner[level]]:
            current_combo[nedtrekk_kolonner[level]] = value
            generate_combinations(current_combo, level + 1)

    generate_combinations({})

    return filter_combinations


def make_annotation(
    color,
    vline_dict,
    isBigger: bool,
    annotation_type: Literal["gjennomsnitt", "median"] = "median",
):
    x = vline_dict[f"{annotation_type}_idx"]

    return {
        "x": x + 0.1 if isBigger else x - 0.1,  # For litt mer plass rundt annotation
        "y": 0.99,
        "xref": "x",
        "yref": "paper",
        "text": f"{annotation_type.capitalize()}: {(vline_dict[f'{annotation_type}_val'] / 24):.1f} dager",
        "showarrow": False,
        "xanchor": "left" if isBigger else "right",
        "yanchor": "top",
        "bgcolor": color,
        "bordercolor": color,
        "borderwidth": 6,
        "font": {"color": "white"},
    }


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
        # BUG: Pga avrunding kan man få f.eks 12.0 måneder når tallet egt er 11.9999999 osv, fjerner desimal for mer lesbarhet
        val = f"{int(måneder)}" if måneder.is_integer() else f"{måneder:.0f}"
        return f"{val} mnd"
    else:
        år = timer / 24 / 365
        val = f"{int(år)}" if år.is_integer() else f"{år:.1f}"
        return f"{val} år"


def bins_and_labels(bin_type: str) -> tuple[list, list]:
    custom_bins = make_custom_bins(bin_type="Samarbeid")

    x_labels = []
    for i in range(len(custom_bins) - 1):
        x_labels.append(f"{bin_label(custom_bins[i])}-{bin_label(custom_bins[i + 1])}")

    return custom_bins, x_labels


def make_custom_bins(bin_type: str) -> list:
    custom_bins = []
    if bin_type == "Behovsvurdering":
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
    elif bin_type == "Samarbeid":
        custom_bins = [
            # minutter
            0,
            # 0.25,
            # 0.5,
            # 0.75,
            # timer
            1,
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
            24 * (365 / 12) * 3,
            24 * (365 / 12) * 4,
            24 * (365 / 12) * 5,
            24 * (365 / 12) * 6,
            24 * (365 / 12) * 7,
            24 * (365 / 12) * 8,
            24 * (365 / 12) * 9,
            24 * (365 / 12) * 10,
            24 * (365 / 12) * 11,
            # år
            24 * 365,
            24 * 365 * 1.5,
            24 * 365 * 2,
        ]
    elif bin_type == "Evaluering":
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
