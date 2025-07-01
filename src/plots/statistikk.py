from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import hex_to_rgb
from plotly.subplots import make_subplots

from src.utils.datahandler import filtrer_bort_saker_på_avsluttet_tidspunkt
from src.utils.helper import (
    alle_måneder_mellom_datoer,
    annotate_ikke_offisiell_statistikk,
)
from src.utils.konstanter import (
    intervall_sortering,
    plotly_colors,
    resultatområder,
    statusordre,
)


def saker_per_status_per_måned(data_status: pd.DataFrame) -> go.Figure:
    data_status = filtrer_bort_saker_på_avsluttet_tidspunkt(
        data_status, antall_dager=365
    )

    alle_måneder = alle_måneder_mellom_datoer(data_status["endretTidspunkt"].min())
    statuser = [status for status in statusordre if status != "NY"]

    status_per_måned = dict(zip(statuser, [[0]] * len(statuser)))
    for måned in alle_måneder:
        data_måned = data_status[
            data_status["endretTidspunkt"].dt.strftime("%Y-%m") == måned
        ]
        for status in statuser:
            sist_count = status_per_måned[status][-1]
            count = (
                sist_count
                - len(data_måned[data_måned["forrige_status"] == status])
                + len(data_måned[data_måned["status"] == status])
            )
            status_per_måned[status] = status_per_måned[status] + [count]

    fig = go.Figure()
    antall_mnd = min(len(alle_måneder), 12)
    for status in statuser:
        fig.add_trace(
            go.Scatter(
                x=alle_måneder[-antall_mnd:],
                y=status_per_måned[status][-antall_mnd - 1 : -1],
                name=status.capitalize().replace("_", " "),
            )
        )

    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Dato",
        yaxis_title="Antall saker",
        hovermode="x unified",
    )
    return annotate_ikke_offisiell_statistikk(fig)


def saker_per_status_over_tid(
    data_status: pd.DataFrame, valgte_resultatområder=None
) -> go.Figure:
    første_dato = data_status["endretTidspunkt"].min()
    siste_dato = datetime.now()
    alle_datoer = pd.date_range(første_dato, siste_dato, freq="d", normalize=True)
    statuser = [status for status in statusordre if status != "NY"]

    def beregn_status_per_dato(data, datoer):
        status_per_dato = dict(zip(statuser, [[0]] * len(statuser)))
        for dato in datoer:
            data_dato = data[data["endretTidspunkt"].dt.date == dato.date()]
            for status in statuser:
                sist_count = status_per_dato[status][-1]
                count = (
                    sist_count
                    - len(data_dato[data_dato["forrige_status"] == status])
                    + len(data_dato[data_dato["status"] == status])
                )
                status_per_dato[status] = status_per_dato[status] + [count]
        return status_per_dato

    fig = go.Figure()

    # En strek for hver status med alle fylker inkludert
    status_per_dato = beregn_status_per_dato(data_status, alle_datoer)
    for status in statuser:
        fig.add_trace(
            go.Scatter(
                visible=True,
                x=alle_datoer,
                y=status_per_dato[status],
                name=status.capitalize().replace("_", " "),
            )
        )

    if not valgte_resultatområder:
        valgte_resultatområder = list(set(resultatområder.values()))

    # En strek for hver kombinasjon av fylke og status
    for resultatområde in [s.replace(" ", "_").lower() for s in valgte_resultatområder]:
        status_per_dato = beregn_status_per_dato(
            data_status[data_status.resultatomrade == resultatområde], alle_datoer
        )
        for status in statuser:
            fig.add_trace(
                go.Scatter(
                    visible=False,
                    x=alle_datoer,
                    y=status_per_dato[status],
                    name=status.capitalize().replace("_", " "),
                )
            )

    # Hvis 12 fylker og 7 statuser, da finnes det 1+12=13 knapper
    # og 13*7 = 84 strekker.
    # Argument "visible" er en liste med enten 0 (False) eller 1 (True),
    # som velger hvilke strekker som vises med hver knapp.
    # Hvis vi hadde 3 fylker og 2 statuser, det ville være:
    # [1, 1, 0, 0, 0, 0], [0, 0, 1, 1, 0, 0], [0, 0, 0, 0, 1, 1]
    knapper_navn = ["Alle resultatområder"] + valgte_resultatområder
    knapper = [
        dict(
            args=[
                {
                    "visible": [
                        trace_index // len(statuser) == knapp_index
                        for trace_index in range(len(knapper_navn) * len(statuser))
                    ]
                }
            ],
            label=knappe_navn,
            method="update",
        )
        for knapp_index, knappe_navn in enumerate(knapper_navn)
    ]
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Dato",
        yaxis_title="Antall saker",
        hovermode="x unified",
        updatemenus=[
            dict(
                active=0,
                direction="down",
                buttons=knapper,
                showactive=True,
                xanchor="left",
                yanchor="top",
                x=0,
                y=1.3,
            ),
        ],
    )

    return annotate_ikke_offisiell_statistikk(fig)


def aktive_saker_per_kolonne(data_status: pd.DataFrame, kolonne: str) -> go.Figure:
    kolonne_ordre: list = (
        data_status[data_status.aktiv_sak]
        .groupby(kolonne)
        .saksnummer.nunique()
        .sort_values(ascending=False)
        .index.tolist()
    )

    aktive_saker_per_kolonne_og_status: pd.DataFrame = (
        data_status[data_status.aktiv_sak]
        .groupby([kolonne, "siste_status"])
        .saksnummer.nunique()
        .reset_index()
        .sort_values(
            by="siste_status", key=lambda col: col.map(lambda e: statusordre.index(e))
        )
        .sort_values(
            by=kolonne, key=lambda col: -col.map(lambda e: kolonne_ordre.index(e))
        )
    )

    fig = go.Figure()

    for status in aktive_saker_per_kolonne_og_status.siste_status.unique():
        aktive_saker_per_kolonne_filtered = aktive_saker_per_kolonne_og_status[
            aktive_saker_per_kolonne_og_status.siste_status == status
        ]
        fig.add_trace(
            go.Bar(
                y=aktive_saker_per_kolonne_filtered[kolonne],
                x=aktive_saker_per_kolonne_filtered["saksnummer"],
                name=status.capitalize().replace("_", " "),
                orientation="h",
            )
        )

    fig.update_layout(
        xaxis_title="Antall aktive saker",
        barmode="stack",
        hovermode="y unified",
        legend_traceorder="normal",
    )
    return annotate_ikke_offisiell_statistikk(fig)


def antall_saker_per_status(data_status: pd.DataFrame) -> go.Figure:
    saker_per_status = (
        data_status.groupby("siste_status")["saksnummer"]
        .nunique()
        .reset_index()
        .sort_values(
            by="siste_status", key=lambda col: -col.map(lambda e: statusordre.index(e))
        )
        .reset_index()
    )

    fig = go.Figure(
        data=[
            go.Bar(
                y=saker_per_status["siste_status"]
                .str.capitalize()
                .str.replace("_", " "),
                x=saker_per_status["saksnummer"],
                text=saker_per_status["saksnummer"],
                orientation="h",
            )
        ]
    )
    fig.update_xaxes(visible=False)
    fig.update_layout(width=850, height=400, plot_bgcolor="rgb(255,255,255)")

    return annotate_ikke_offisiell_statistikk(fig)


def virksomhetsprofil(data_input: pd.DataFrame) -> go.Figure:
    data = data_input.sort_values(
        ["saksnummer", "endretTidspunkt"], ascending=True
    ).drop_duplicates(["saksnummer"], keep="last")

    specs = [
        [{}, {}],
        [{"type": "domain", "r": 0.1}, {}],
        [{}, {}],
    ]
    subplot_titles = (
        "Antall arbeidsforhold",
        "Sykefraværsprosent",
        "Sektor",
        "Bransjeprogram",
        "",
        "Topp 10 hovednæringer",
    )

    fig = make_subplots(
        rows=3,
        cols=2,
        specs=specs,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.1,
        vertical_spacing=0.1,
    )
    fig.update_layout(
        height=900,
        width=850,
        showlegend=False,
    )

    # Antall arbeidsforhold
    saker_per_storrelsesgruppe = (
        data.groupby("antallPersoner_gruppe").saksnummer.nunique().reset_index()
    )
    fig.add_trace(
        go.Bar(
            x=saker_per_storrelsesgruppe.antallPersoner_gruppe,
            y=saker_per_storrelsesgruppe.saksnummer,
            text=saker_per_storrelsesgruppe.saksnummer,
        ),
        row=1,
        col=1,
    )
    fig.update_yaxes(visible=False, row=1, col=1)
    storrelse_sortering = (
        data.groupby("antallPersoner_gruppe").antallPersoner.min().sort_values().index
    )
    fig.update_xaxes(categoryorder="array", categoryarray=storrelse_sortering)

    # Sykefraværsprosent
    fig.add_trace(go.Histogram(x=data.sykefraversprosent), row=1, col=2)
    gjennomsnitt = data.sykefraversprosent.mean()
    fig.add_vline(
        x=gjennomsnitt,
        line_width=1,
        line_dash="solid",
        line_color="red",
        annotation_text=f"gjennomsnitt={gjennomsnitt:.3}",
        annotation_position="top right",
        annotation_bgcolor="red",
        row=1,
        col=2,
    )

    # Sektor
    virksomheter_per_sektor = (
        data.groupby("sektor").saksnummer.nunique().reset_index().sort_values("sektor")
    )
    fig.add_trace(
        go.Pie(
            labels=virksomheter_per_sektor.sektor,
            values=virksomheter_per_sektor.saksnummer,
            text=virksomheter_per_sektor.sektor.str.capitalize(),
            sort=False,
        ),
        row=2,
        col=1,
    )
    fig.update_xaxes(visible=False, row=2, col=1)

    # Bransje
    virksomheter_per_bransje = (
        data.groupby("bransjeprogram", dropna=False)
        .saksnummer.nunique()
        .sort_values(ascending=True)
        .reset_index()
        .fillna("Ikke bransjeprogram")
    )
    fig.add_trace(
        go.Bar(
            y=virksomheter_per_bransje.bransjeprogram.str.capitalize(),
            x=virksomheter_per_bransje.saksnummer,
            text=virksomheter_per_bransje.saksnummer,
            orientation="h",
        ),
        row=2,
        col=2,
    )
    fig.update_xaxes(visible=False, row=2, col=2)

    # Hoved næring
    virksomheter_per_nering = (
        data.groupby("hoved_nering")["saksnummer"]
        .nunique()
        .sort_values(ascending=True)
        .reset_index()
    )
    antall_næringer_å_vise = 10
    truncation_map = dict(zip(data["hoved_nering"], data["hoved_nering_truncated"]))
    fig.add_trace(
        go.Bar(
            y=virksomheter_per_nering[-antall_næringer_å_vise:]["hoved_nering"],
            x=virksomheter_per_nering[-antall_næringer_å_vise:]["saksnummer"],
            text=virksomheter_per_nering[-antall_næringer_å_vise:]["saksnummer"],
            orientation="h",
        ),
        row=3,
        col=2,
    )
    fig.update_layout(
        yaxis5_tickvals=list(truncation_map.keys()),
        yaxis5_ticktext=list(truncation_map.values()),
    )
    fig.update_xaxes(
        visible=False,
        row=3,
        col=2,
    )

    return annotate_ikke_offisiell_statistikk(fig)


def hexfarge_til_rgba(hex_farge: str, alpha: float) -> str:
    r, g, b = hex_to_rgb(hex_farge)
    return f"rgba({r}, {g}, {b}, {alpha})"


def statusflyt(
    data_status: pd.DataFrame,
    farger_nodes: dict[str, str] = {
        "Alle saker": "#828bfb",
        "Vurderes": "#f68282",
        "Kontaktes": "#47dbf5",
        "Kartlegges": "#ffd799",
        "Vi bistår": "#bb82fb",
        "Fullført": "#33d6ab",
        "Ikke aktuell": "#f27762",
    },
    farger_links: dict[str, str] = {
        "Alle saker": "#cccccc",
        "Vurderes": "#cccccc",
        "Kontaktes": "#cccccc",
        "Kartlegges": "#cccccc",
        "Vi bistår": "#cccccc",
        "Fullført": "#33d6ab",
        "Ikke aktuell": "#f27762",
    },
) -> go.Figure:
    data_status_uslettet: pd.DataFrame = data_status[
        data_status["siste_status"] != "SLETTET"
    ]
    statusordre_uslettet: list[str] = [x for x in statusordre if x != "SLETTET"]

    status_indexes = dict(zip(statusordre_uslettet, range(len(statusordre_uslettet))))
    status_endringer = data_status_uslettet.value_counts(["forrige_status", "status"])
    source_status = status_endringer.index.get_level_values(0).map(status_indexes)
    target_status = status_endringer.index.get_level_values(1).map(status_indexes)
    count_endringer = status_endringer.values

    node_plus = {i: 0 for i in range(7)}
    node_plus[0] = count_endringer[0]

    for src, tgt, count in zip(source_status, target_status, count_endringer):
        node_plus[tgt] += count

    status_label = [x.capitalize().replace("_", " ") for x in statusordre_uslettet]
    status_label = [x if x != "Ny" else "Alle saker" for x in status_label]

    label_with_value = []
    for node, total in node_plus.items():
        label_with_value.append(f"{status_label[node]} ({total})")

    target_status_label = [status_label[i] for i in target_status]

    fig = go.Figure()
    fig.add_trace(
        go.Sankey(
            node=dict(
                # pad=200,
                thickness=10,
                label=label_with_value,
                color=[
                    hexfarge_til_rgba(farger_nodes[status], 1)
                    for status in status_label
                ],
                # node position in the open interval (0, 1)
                x=[0.02, 0.2, 0.4, 0.6, 0.8, 0.98, 0.98],
                y=[0.5, 0.5, 0.55, 0.6, 0.6, 0.7, 0.20],
            ),
            link=dict(
                source=source_status,
                target=target_status,
                value=count_endringer,
                color=[
                    hexfarge_til_rgba(farger_links[target_status], 0.4)
                    for target_status in target_status_label
                ],
            ),
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    return annotate_ikke_offisiell_statistikk(fig)


def gjennomstrømmingstall(data_status: pd.DataFrame, status="VI_BISTÅR") -> go.Figure:
    alle_måneder = alle_måneder_mellom_datoer(data_status.endretTidspunkt.min())
    antall_mnd = min(len(alle_måneder), 12)
    inn = (
        data_status[data_status.status == status]
        .endretTidspunkt.dt.strftime("%Y-%m")
        .value_counts()
        .sort_index()
        .reindex(alle_måneder, fill_value=0)[-antall_mnd:]
    )
    ut = (
        data_status[data_status.forrige_status == status]
        .endretTidspunkt.dt.strftime("%Y-%m")
        .value_counts()
        .sort_index()
        .reindex(alle_måneder, fill_value=0)[-antall_mnd:]
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=inn.index, y=inn.values, name="inn"))
    fig.add_trace(go.Scatter(x=ut.index, y=ut.values, name="ut"))
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Måned",
        yaxis_title="Antall saker",
    )
    return annotate_ikke_offisiell_statistikk(fig)


def dager_mellom_statusendringer(data_status: pd.DataFrame) -> go.Figure:
    saker_per_intervall = (
        data_status.groupby("intervall_tid_siden_siste_endring")
        .saksnummer.nunique()
        .reset_index()
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=saker_per_intervall.intervall_tid_siden_siste_endring,
            y=saker_per_intervall.saksnummer,
            text=saker_per_intervall.saksnummer,
        )
    )
    fig.update_layout(
        height=500,
        width=800,
        xaxis_title="Tidsgruppering (fra og med, til)",
        yaxis_title="Antall saker",
    )
    fig.update_xaxes(categoryorder="array", categoryarray=intervall_sortering)

    return annotate_ikke_offisiell_statistikk(fig)


def median_og_gjennomsnitt_av_tid_mellom_statusendringer(
    data_status: pd.DataFrame,
) -> go.Figure:
    data_status["endretTidspunkt_måned"] = data_status.endretTidspunkt.dt.strftime(
        "%Y-%m"
    )
    data_status["dager_siden_siste_endring"] = (
        data_status.tid_siden_siste_endring.dt.total_seconds() / 60 / 60 / 24
    )

    gjennomsnitt = data_status.groupby(
        "endretTidspunkt_måned"
    ).dager_siden_siste_endring.mean()
    median = data_status.groupby(
        "endretTidspunkt_måned"
    ).dager_siden_siste_endring.median()
    antall_saker = data_status.groupby(
        "endretTidspunkt_måned"
    ).dager_siden_siste_endring.count()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=gjennomsnitt.index,
            y=gjennomsnitt.values,
            name="Gjennomsnitt",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=median.index,
            y=median.values,
            name="Median",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=antall_saker.index,
            y=antall_saker.values,
            name="Antall saker",
            marker_color="black",
            line_dash="dash",
            opacity=0.2,
        ),
        secondary_y=True,
    )

    fig.update_layout(
        height=500,
        width=800,
        xaxis_title="Endringstidspunkt",
        yaxis_title="Antall dager",
    )

    fig.update_yaxes(title_text="Antall saker", secondary_y=True)

    return annotate_ikke_offisiell_statistikk(fig)


def antall_saker_per_eier(data_status: pd.DataFrame) -> go.Figure():
    saker_per_eier = (
        data_status[data_status.siste_status.isin(["VI_BISTÅR"])]
        .drop_duplicates("saksnummer", keep="last")
        .groupby("eierAvSak")
        .saksnummer.nunique()
    )

    fig = go.Figure(
        data=[
            go.Histogram(
                x=saker_per_eier, xbins=dict(start=1, end=saker_per_eier.max())
            )
        ]
    )

    gjennomsnitt = saker_per_eier.mean()
    fig.add_vline(
        x=gjennomsnitt,
        line_width=1,
        line_dash="solid",
        line_color=plotly_colors[1],
        annotation_text=f"gjennomsnitt={gjennomsnitt:.3}",
        annotation_position="top right",
        annotation_bgcolor=plotly_colors[1],
    )

    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Antall saker",
        yaxis_title="Antall eiere",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def fullført_per_måned(data_status: pd.DataFrame) -> go.Figure():
    fullført_per_måned = (
        data_status[data_status.status == "FULLFØRT"]
        .endretTidspunkt_måned.value_counts()
        .sort_index()
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=fullført_per_måned.index,
            y=fullført_per_måned.values,
        )
    )

    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Fullført måned",
        yaxis_title="Antall fullførte saker",
        xaxis={"type": "category"},
    )
    return annotate_ikke_offisiell_statistikk(fig)


def antall_brukere_per_resultatområde(data_statistikk: pd.DataFrame) -> go.Figure():
    bruker_per_resultatområde = (
        data_statistikk.groupby("resultatomrade").endretAv.nunique().sort_values()
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=bruker_per_resultatområde.values,
            y=bruker_per_resultatområde.index,
            orientation="h",
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Antall brukere",
        yaxis_title="Virksomhetsfylke",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def antall_brukere_per_resultatområde_og_nav_enhet(
    data_statistikk: pd.DataFrame,
) -> go.Figure():
    data_statistikk["resultatomrade"] = data_statistikk.fylkesnummer.map(
        resultatområder
    )
    resultatområdeordre = (
        data_statistikk.groupby("resultatomrade")
        .endretAv.nunique()
        .sort_values()
        .index.tolist()
    )
    enhetsordre = (
        data_statistikk.groupby("enhetsnavn")
        .endretAv.nunique()
        .sort_values(ascending=False)
        .index.tolist()
    )

    første_register_navenhet = data_statistikk[
        (data_statistikk.enhetsnavn != "Ukjent") & (~data_statistikk.enhetsnavn.isna())
    ].endretTidspunkt.min()
    bruker_per_navenhet = (
        data_statistikk[data_statistikk.endretTidspunkt >= første_register_navenhet]
        .groupby(["resultatomrade", "enhetsnavn"])
        .endretAv.nunique()
        .reset_index()
    )

    fig = go.Figure()

    for kol in resultatområdeordre:
        for enhet in enhetsordre:
            filtert = bruker_per_navenhet[
                (bruker_per_navenhet["resultatomrade"] == kol)
                & (bruker_per_navenhet.enhetsnavn == enhet)
            ]
            fig.add_trace(
                go.Bar(
                    y=filtert["resultatomrade"],
                    x=filtert.endretAv,
                    text=enhet,
                    textposition="none",
                    orientation="h",
                    hoverinfo="text+x",
                )
            )

    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Antall brukere",
        yaxis_title="Virksomhetsfylke",
        barmode="stack",
        showlegend=False,
        hovermode="y unified",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def antall_brukere_per_måned(data_statistikk: pd.DataFrame) -> go.Figure():
    antall_brukere_per_måned = data_statistikk.groupby(
        "endretTidspunkt_måned"
    ).endretAv.nunique()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=antall_brukere_per_måned.index,
            y=antall_brukere_per_måned.values,
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Måned",
        yaxis_title="Antall brukere",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def andel_statusendringer_gjort_av_superbrukere(
    data_statistikk: pd.DataFrame,
) -> go.Figure():
    antall_endringer_superbrukere_per_måned = (
        data_statistikk[data_statistikk.endretAvRolle == "SUPERBRUKER"]
        .groupby("endretTidspunkt_måned")
        .endretAv.size()
    )

    antall_endringer_per_måned = data_statistikk.groupby(
        "endretTidspunkt_måned"
    ).endretAv.size()

    andel_endringer_superbrukere_per_måned = (
        antall_endringer_superbrukere_per_måned / antall_endringer_per_måned
    ).dropna()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=andel_endringer_superbrukere_per_måned.index,
            y=andel_endringer_superbrukere_per_måned.values * 100,
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Måned",
        yaxis_title="Andel statusendring (%)",
        xaxis={"type": "category"},
    )

    return annotate_ikke_offisiell_statistikk(fig)


def andel_superbrukere(data_statistikk: pd.DataFrame) -> go.Figure():
    antall_superbrukere_per_måned = (
        data_statistikk[data_statistikk.endretAvRolle == "SUPERBRUKER"]
        .groupby("endretTidspunkt_måned")
        .endretAv.nunique()
    )

    antall_brukere_per_måned = data_statistikk.groupby(
        "endretTidspunkt_måned"
    ).endretAv.nunique()

    andel_superbrukere_per_måned = (
        antall_superbrukere_per_måned / antall_brukere_per_måned
    ).dropna()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=andel_superbrukere_per_måned.index,
            y=andel_superbrukere_per_måned.values * 100,
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Måned",
        yaxis_title="Andel superbrukere (%)",
        xaxis={"type": "category"},
    )

    return annotate_ikke_offisiell_statistikk(fig)
