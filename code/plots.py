import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from code.datahandler import beregn_siste_oppdatering, explode_ikke_aktuell_begrunnelse
from code.helper import annotate_ikke_offisiell_statistikk
from code.konstanter import statusordre, plotly_colors


def aktive_saker_per_fylke(data_status):
    fylkeordre = (
        data_status[data_status.aktiv_sak]
        .groupby("fylkesnavn")
        .saksnummer.nunique()
        .sort_values(ascending=False)
        .index.tolist()
    )

    aktive_saker_per_fylke_og_status = (
        data_status[data_status.aktiv_sak]
        .groupby(["fylkesnavn", "siste_status"])
        .saksnummer.nunique()
        .reset_index()
        .sort_values(
            by="siste_status", key=lambda col: col.map(lambda e: statusordre.index(e))
        )
        .sort_values(
            by="fylkesnavn", key=lambda col: -col.map(lambda e: fylkeordre.index(e))
        )
    )

    fig = go.Figure()

    for status in aktive_saker_per_fylke_og_status.siste_status.unique():
        aktive_saker_per_fylke_filtered = aktive_saker_per_fylke_og_status[
            aktive_saker_per_fylke_og_status.siste_status == status
        ]
        fig.add_trace(
            go.Bar(
                y=aktive_saker_per_fylke_filtered["fylkesnavn"],
                x=aktive_saker_per_fylke_filtered["saksnummer"],
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


def dager_siden_siste_oppdatering(data_status, data_eierskap, data_leveranse):
    siste_oppdatering = beregn_siste_oppdatering(
        data_status, data_eierskap, data_leveranse
    )

    fig = go.Figure(
        data=[
            go.Histogram(
                x=siste_oppdatering["dager_siden_siste_oppdatering"], nbinsx=20
            )
        ]
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Dager siden siste oppdatering i Fia",
        yaxis_title="Antall saker",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def antall_saker_per_status(data_status):
    saker_per_status = (
        data_status.groupby("siste_status")
        .saksnummer.nunique()
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
    fig.update_layout(plot_bgcolor="rgb(255,255,255)")

    return annotate_ikke_offisiell_statistikk(fig)


def antall_leveranser_per_sak(data_status, data_leveranse):
    # saker som har leveranser registrert
    leveranser_per_sak = data_leveranse.groupby("saksnummer").iaModulId.nunique()

    # saker som ikke har leveranser registrert men kunne har hatt
    første_registrert_leveranse_dato = data_leveranse.sistEndret.min()
    saker_med_leveranser = data_leveranse.saksnummer.unique().tolist()
    # saker fullført etter det ble mulig å registrere leveranser
    saker_uten_leveranser = (
        data_status[
            (data_status.status == "FULLFØRT")
            & (data_status.endretTidspunkt >= første_registrert_leveranse_dato)
            & ~data_status.saksnummer.isin(saker_med_leveranser)
        ]
        .saksnummer.unique()
        .tolist()
    )
    # saker i bistand nå
    saker_uten_leveranser.extend(
        data_status[
            (data_status.siste_status == "VI_BISTÅR")
            & (data_status.status == "VI_BISTÅR")
            & ~data_status.saksnummer.isin(saker_med_leveranser)
            & ~data_status.saksnummer.isin(saker_uten_leveranser)
        ].saksnummer.unique()
    )

    # samlet series med saker med og uten leveranser
    leveranser_per_sak = pd.concat(
        [
            leveranser_per_sak,
            pd.Series(data=0, index=saker_uten_leveranser),
        ],
        axis=0,
    )

    fig = go.Figure(data=[go.Histogram(x=leveranser_per_sak)])
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Antall moduler (leverte og under arbeid)",
        yaxis_title="Antall saker",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def antall_leveranser_per_tjeneste(data_leveranse):
    leveranser_per_tjeneste = (
        data_leveranse.drop_duplicates(["saksnummer", "iaTjenesteId"], keep="last")
        .groupby(["iaTjenesteNavn", "status"])
        .saksnummer.nunique()
        .sort_values(ascending=True)
        .reset_index()
    )

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
        width=850,
        plot_bgcolor="rgb(255,255,255)",
        xaxis_showticklabels=False,
        xaxis_title="Antall saker",
        xaxis_title_standoff=80,
        legend=dict(orientation="h", yanchor="bottom", y=0, xanchor="right", x=1),
    )

    return annotate_ikke_offisiell_statistikk(fig, y=1.2)


def antall_leveranser_per_modul(data_leveranse, modul_sortering):
    leveranser_per_modul = (
        data_leveranse.groupby(["iaTjenesteNavn", "iaModulNavn"])
        .saksnummer.nunique()
        .reset_index()
        .sort_values(
            "iaModulNavn", key=lambda col: col.map(lambda e: modul_sortering.index(e))
        )
    )

    fig = go.Figure()

    for tjeneste in leveranser_per_modul.iaTjenesteNavn.unique():
        leveranser_per_modul_filtered = leveranser_per_modul[
            leveranser_per_modul.iaTjenesteNavn == tjeneste
        ]
        fig.add_trace(
            go.Bar(
                y=leveranser_per_modul_filtered.iaModulNavn,
                x=leveranser_per_modul_filtered.saksnummer,
                text=leveranser_per_modul_filtered.saksnummer,
                orientation="h",
                name=tjeneste,
            )
        )

    fig.update_layout(
        height=500,
        width=800,
        plot_bgcolor="rgb(255,255,255)",
        xaxis_showticklabels=False,
        xaxis_title="Antall saker per modul",
        xaxis_title_standoff=80,
        yaxis_autorange="reversed",
        legend=dict(orientation="h", yanchor="bottom", y=0, xanchor="right", x=1.1),
    )
    fig.update_yaxes(categoryorder="array", categoryarray=modul_sortering)

    return annotate_ikke_offisiell_statistikk(fig, y=1.2)


def virksomhetsprofil(data_input):
    data = data_input.sort_values(
        ["saksnummer", "endretTidspunkt"], ascending=True
    ).drop_duplicates(["saksnummer"], keep="last")

    specs = [
        [{}, {}],
        [{"type": "domain", "r": 0.1}, {}],
        [{}, {}],
    ]
    subplot_titles = (
        "Antall ansatte",
        "Sykefraværsprosent",
        "Sektor",
        "Bransjeprogram",
        "",
        "Hovednæring",
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

    # Antall ansatte
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
        data.groupby("hoved_nering")
        .saksnummer.nunique()
        .sort_values(ascending=True)
        .reset_index()
    )
    show_n_neringer = 10
    truncation_map = dict(zip(data.hoved_nering, data.hoved_nering_truncated))
    fig.add_trace(
        go.Bar(
            y=virksomheter_per_nering[-show_n_neringer:].hoved_nering,
            x=virksomheter_per_nering[-show_n_neringer:].saksnummer,
            text=virksomheter_per_nering[-show_n_neringer:].saksnummer,
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


def statusflyt(data_status):
    status_indexes = dict(zip(statusordre, range(len(statusordre))))
    status_endringer = data_status.value_counts(["forrige_status", "status"])
    source_status = status_endringer.index.get_level_values(0).map(status_indexes)
    target_status = status_endringer.index.get_level_values(1).map(status_indexes)
    count_endringer = status_endringer.values

    status_label = [x.capitalize().replace("_", " ") for x in statusordre]
    status_label = [x if x != "Ny" else "Alle saker" for x in status_label]
    fig = go.Figure()
    fig.add_trace(
        go.Sankey(
            node=dict(
                pad=200,
                label=status_label,
                # node position in the open interval (0, 1)
                x=[0.001, 0.2, 0.4, 0.6, 0.8, 0.999, 0.999, 0.999],
                y=[0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.001, 0.999],
            ),
            link=dict(
                source=source_status,
                target=target_status,
                value=count_endringer,
            ),
        )
    )
    return annotate_ikke_offisiell_statistikk(fig)


def begrunnelse_ikke_aktuell(data_status, begrunnelse_sortering):
    antall_saker_ikke_aktuell = (
        data_status[data_status.status == "IKKE_AKTUELL"]
        .drop_duplicates("saksnummer", keep="last")
        .shape[0]
    )
    ikke_aktuell = explode_ikke_aktuell_begrunnelse(data_status)
    ikke_aktuell.ikkeAktuelBegrunnelse = (
        ikke_aktuell.ikkeAktuelBegrunnelse.str.replace("_", " ")
        .str.capitalize()
        .str.replace("bht", "BHT")
    )

    ikke_aktuell_per_begrunnelse = (
        ikke_aktuell.groupby("ikkeAktuelBegrunnelse")
        .saksnummer.nunique()
        .reset_index()
        .sort_values(
            "ikkeAktuelBegrunnelse",
            key=lambda col: col.map(lambda e: begrunnelse_sortering.index(e)),
        )
        .reset_index()
    )
    andel = [
        x * 100 / antall_saker_ikke_aktuell
        for x in ikke_aktuell_per_begrunnelse.saksnummer
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=ikke_aktuell_per_begrunnelse.ikkeAktuelBegrunnelse,
            x=andel,
            text=[
                f"{andel[i]:.2f}%, {ikke_aktuell_per_begrunnelse.saksnummer[i]}"
                for i in range(len(andel))
            ],
            marker_color=plotly_colors,
            orientation="h",
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        plot_bgcolor="rgb(255,255,255)",
        xaxis_showticklabels=False,
        xaxis_title="Andel og antall saker med status ikke aktuell",
        xaxis_title_standoff=80,
        yaxis_autorange="reversed",
        xaxis_range=[0, 60],
    )

    return annotate_ikke_offisiell_statistikk(fig, y=1.2)
