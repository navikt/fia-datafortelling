import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone, timedelta


from code.helper import annotate_ikke_offisiell_statistikk
from code.konstanter import statusordre, fylker, intervall_sortering, plotly_colors


def saker_per_status_per_måned(data_status):
    første_dato = data_status.endretTidspunkt.min()
    siste_dato = datetime.now()
    alle_datoer = pd.date_range(første_dato, siste_dato, freq="d", normalize=True)
    alle_måneder = alle_datoer.strftime("%Y-%m").drop_duplicates()
    statuser = [status for status in statusordre if status != "NY"]

    status_per_måned = dict(zip(statuser, [[0]] * len(statuser)))
    for måned in alle_måneder:
        data_måned = data_status[data_status.endretTidspunkt.dt.strftime("%Y-%m") == måned]
        for status in statuser:
            sist_count = status_per_måned[status][-1]
            count = (
                sist_count
                - sum(data_måned.forrige_status == status)
                + sum(data_måned.status == status)
            )
            status_per_måned[status] = status_per_måned[status] + [count]

    fig = go.Figure()
    for status in statuser:
        fig.add_trace(
            go.Scatter(
                x=alle_måneder,
                y=status_per_måned[status][:-1],
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


def saker_per_status_over_tid(data_status, valgte_fylker=None):
    første_dato = data_status.endretTidspunkt.min()
    siste_dato = datetime.now()
    alle_datoer = pd.date_range(første_dato, siste_dato, freq="d", normalize=True)
    statuser = [status for status in statusordre if status != "NY"]

    def beregn_status_per_dato(data, datoer):
        status_per_dato = dict(zip(statuser, [[0]] * len(statuser)))
        for dato in datoer:
            data_dato = data[data.endretTidspunkt.dt.date == dato.date()]
            for status in statuser:
                sist_count = status_per_dato[status][-1]
                count = (
                    sist_count
                    - sum(data_dato.forrige_status == status)
                    + sum(data_dato.status == status)
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

    if not valgte_fylker:
        valgte_fylker = fylker.keys()
    
    # En strek for hver kombinasjon av fylke og status
    for fylkesnr in valgte_fylker:
        status_per_dato = beregn_status_per_dato(
            data_status[data_status.fylkesnummer == fylkesnr], alle_datoer
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
    knapper_navn = ["Alle fylker"] + [fylker[valgt_fylke] for valgt_fylke in valgte_fylker]
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


def dager_mellom_statusendringer(data_status):
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


def urørt_saker_over_tid(data_status, data_eierskap, data_leveranse, antall_dager):
    første_dato = data_status.endretTidspunkt.min()
    now = datetime.now()
    alle_datoer = pd.date_range(første_dato, now, freq="d", normalize=True)
    aktive_statuser = ["VURDERES", "KONTAKTES", "KARTLEGGES", "VI_BISTÅR"]

    data = pd.concat(
        [
            data_status[["saksnummer", "status", "endretTidspunkt"]],
            data_eierskap[["saksnummer", "status", "endretTidspunkt"]],
            (
                data_leveranse[["saksnummer", "sistEndret"]]
                .rename(columns={"sistEndret": "endretTidspunkt"})
                .assign(status="VI_BISTÅR")
            ),
        ]
    )
    data = data.sort_values(
        ["saksnummer", "endretTidspunkt"], ascending=True
    ).reset_index()
    data["aktiv_status"] = data.status.isin(aktive_statuser)
    data.loc[
        data.saksnummer == data.saksnummer.shift(-1),
        "neste_endretTidspunkt",
    ] = data.endretTidspunkt.shift(-1)
    data.loc[
        data.neste_endretTidspunkt.astype(str) == "NaT", "neste_endretTidspunkt"
    ] = now
    data["antall_dager"] = (data.neste_endretTidspunkt - data.endretTidspunkt).dt.days
    data["mer_enn_x_dager"] = data.antall_dager > antall_dager

    urørt_per_status_og_dato = dict(
        zip(aktive_statuser, [[0] * len(alle_datoer)] * len(aktive_statuser))
    )

    for _, row in data[data.mer_enn_x_dager & data.aktiv_status].iterrows():
        status = row["status"]
        endretTidspunkt = row["endretTidspunkt"]
        neste_endretTidspunkt = row["neste_endretTidspunkt"]

        urørt_intervall = []
        for dato in alle_datoer:
            if (dato > endretTidspunkt + timedelta(days=antall_dager)) & (
                dato < neste_endretTidspunkt
            ):
                urørt_intervall.append(1)
            else:
                urørt_intervall.append(0)
        urørt_per_status_og_dato[status] = [
            sum(x) for x in zip(urørt_per_status_og_dato[status], urørt_intervall)
        ]

    fig = go.Figure()

    for status in aktive_statuser:
        fig.add_trace(
            go.Scatter(
                x=alle_datoer,
                y=urørt_per_status_og_dato[status],
                name=status.capitalize().replace("_", " "),
            )
        )

    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Dato",
        yaxis_title="Antall saker",
    )

    # Create slider
    fig.update_layout(
        height=600,
        xaxis=dict(autorange=True, rangeslider=dict(autorange=True, visible=True)),
    )

    return annotate_ikke_offisiell_statistikk(fig)


def median_og_gjennomsnitt_av_tid_mellom_statusendringer(data_status):
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


def antall_saker_per_eier(data_status):
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


def for_lavt_sykefravær(data_status, ikke_aktuell):
    fig = go.Figure()

    # Sammenlignesgrunnlag
    data = data_status[
        data_status.siste_status.isin(["VI_BISTÅR", "FULLFØRT"])
    ].drop_duplicates("saksnummer", keep="last")
    fig.add_trace(
        go.Histogram(
            x=data.sykefraversprosent,
            histnorm="percent",
            nbinsx=100,
            name="Biståtte saker",
        )
    )
    gjennomsnitt = data.sykefraversprosent.mean()
    fig.add_vline(
        x=gjennomsnitt,
        line_width=1,
        line_dash="solid",
        line_color=plotly_colors[0],
        annotation_text=f"gjennomsnitt={gjennomsnitt:.3}",
        annotation_position="top right",
        annotation_bgcolor=plotly_colors[0],
        annotation_yshift=-20,
    )

    # For lavt sykefravær
    data = ikke_aktuell[ikke_aktuell.ikkeAktuelBegrunnelse == "FOR_LAVT_SYKEFRAVÆR"]
    fig.add_trace(
        go.Histogram(
            x=data.sykefraversprosent,
            histnorm="percent",
            nbinsx=100,
            name="For lavt sykefravær",
        )
    )
    gjennomsnitt = data.sykefraversprosent.mean()
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
        xaxis_title="Sykefravær (%)",
        yaxis_title="Andel saker (%)",
        barmode="overlay",
    )
    fig.update_traces(opacity=0.75)

    return annotate_ikke_offisiell_statistikk(fig)


def mindre_virksomhet(data_status, ikke_aktuell):
    fig = go.Figure()

    # Sammenlignesgrunnlag
    data = data_status[
        data_status.siste_status.isin(["VI_BISTÅR", "FULLFØRT"])
    ].drop_duplicates("saksnummer", keep="last")
    fig.add_trace(
        go.Histogram(
            x=data[~data.antallPersoner.isna()].antallPersoner.apply(
                lambda x: 150 if x > 150 else x
            ),
            histnorm="percent",
            nbinsx=100,
            name="Biståtte saker",
        )
    )
    gjennomsnitt = data.antallPersoner.mean()
    fig.add_vline(
        x=gjennomsnitt,
        line_width=1,
        line_dash="solid",
        line_color=plotly_colors[0],
        annotation_text=f"gjennomsnitt={gjennomsnitt:.2f}",
        annotation_position="top right",
        annotation_bgcolor=plotly_colors[0],
        annotation_yshift=-20,
    )

    # Mindre virksomhet
    data = ikke_aktuell[ikke_aktuell.ikkeAktuelBegrunnelse == "MINDRE_VIRKSOMHET"]
    fig.add_trace(
        go.Histogram(
            x=data[~data.antallPersoner.isna()].antallPersoner.apply(
                lambda x: 150 if x > 150 else x
            ),
            histnorm="percent",
            nbinsx=100,
            name="Mindre virksomhet",
        )
    )
    gjennomsnitt = data.antallPersoner.mean()
    fig.add_vline(
        x=gjennomsnitt,
        line_width=1,
        line_dash="solid",
        line_color=plotly_colors[1],
        annotation_text=f"gjennomsnitt={gjennomsnitt:.2f}",
        annotation_position="top right",
        annotation_bgcolor=plotly_colors[1],
    )

    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Antall ansatte (%)",
        yaxis_title="Andel saker (%)",
        barmode="overlay",
    )
    fig.update_traces(opacity=0.75)

    return annotate_ikke_offisiell_statistikk(fig)


def fullført_per_måned(data_status):
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


def andel_fullforte_saker_med_leveranse_per_måned(data_status, data_leveranse):
    første_dato = data_leveranse.sistEndret.min()
    fullført_per_måned = (
        data_status[
            (data_status.status == "FULLFØRT")
            & (data_status.endretTidspunkt >= første_dato.strftime("%Y-%m-%d"))
        ]
        .endretTidspunkt_måned.value_counts()
        .sort_index()
    )

    alle_måneder = pd.date_range(
        start=data_leveranse.sistEndret.min(), end=datetime.now(), freq="M"
    ).strftime("%Y-%m")

    saker_med_leveranser = data_leveranse.saksnummer.unique()
    data_status["med_leveranse"] = False
    data_status.loc[
        data_status.saksnummer.isin(saker_med_leveranser), "med_leveranse"
    ] = True
    fullført_per_måned_med_leveranse = (
        data_status[(data_status.status == "FULLFØRT") & data_status.med_leveranse]
        .endretTidspunkt_måned.value_counts()
        .sort_index()
        .reindex(alle_måneder, fill_value=0)
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=fullført_per_måned.index,
            y=(fullført_per_måned_med_leveranse / fullført_per_måned).values,
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Fullført måned",
        yaxis_title="Andel fullførte saker med leveranse",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def andel_fullforte_saker_med_leveranse_over_tid(data_status, data_leveranse):
    saker_med_leveranser = data_leveranse.saksnummer.unique()
    data_status["med_leveranse"] = False
    data_status.loc[
        data_status.saksnummer.isin(saker_med_leveranser), "med_leveranse"
    ] = True

    første_dato = data_leveranse.sistEndret.min()
    now = datetime.now()
    alle_datoer = pd.date_range(første_dato, now, freq="d", normalize=True)

    fullførte_saker_over_tid = []
    saker_med_leveranser_over_tid = []

    data = data_status[data_status.status == "FULLFØRT"]
    for dato in alle_datoer:
        fullførte_saker_over_tid.append(
            data[
                (data.endretTidspunkt >= første_dato.strftime("%Y-%m-%d"))
                & (data.endretTidspunkt < dato)
            ].saksnummer.nunique()
        )
        saker_med_leveranser_over_tid.append(
            data[
                (data.endretTidspunkt < dato) & data.med_leveranse
            ].saksnummer.nunique()
        )

    andel_saker_med_leveranser = [
        saker_med_leveranser_over_tid[i] / fullførte_saker_over_tid[i]
        if fullførte_saker_over_tid[i] > 0
        else 0
        for i in range(len(alle_datoer))
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=alle_datoer,
            y=andel_saker_med_leveranser,
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Dato",
        yaxis_title="Akumulert andel fullførte saker med leveranse",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def forskjell_frist_fullfort(data_leveranse):
    fullfort_leveranser = data_leveranse[data_leveranse.status == "LEVERT"]
    forskjell_frist_fullfort = (
        fullfort_leveranser.fullfort.dt.normalize() - fullfort_leveranser.frist
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
        yaxis_title="Antall fullførte moduler",
        xaxis=dict(
            title="Antall dager",
            rangeslider=dict(visible=True),
            range=[max(min_, -100), min(max_, 100)],
        ),
    )

    return annotate_ikke_offisiell_statistikk(fig)


def antall_brukere_per_fylke(data_statistikk):
    bruker_per_fylke = (
        data_statistikk.groupby("fylkesnavn").endretAv.nunique().sort_values()
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=bruker_per_fylke.values,
            y=bruker_per_fylke.index,
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


def antall_brukere_per_fylke_og_nav_enhet(data_statistikk):
    data_statistikk["fylkesnavn"] = data_statistikk.fylkesnummer.map(fylker)
    fylkeordre = (
        data_statistikk.groupby("fylkesnavn")
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
        .groupby(["fylkesnavn", "enhetsnavn"])
        .endretAv.nunique()
        .reset_index()
    )

    fig = go.Figure()

    for fylke in fylkeordre:
        for enhet in enhetsordre:
            filtert = bruker_per_navenhet[
                (bruker_per_navenhet.fylkesnavn == fylke)
                & (bruker_per_navenhet.enhetsnavn == enhet)
            ]
            fig.add_trace(
                go.Bar(
                    y=filtert.fylkesnavn,
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


def antall_brukere_akkumulert_over_tid(data_statistikk):
    antall_brukere_akkumulert_over_tid = (
        data_statistikk[["endretTidspunkt", "endretAv"]]
        .assign(
            endretTidspunkt_date=data_statistikk.endretTidspunkt.dt.date.astype(str)
        )
        .sort_values("endretTidspunkt", ascending=True)
        .drop_duplicates("endretAv", keep="first")
        .groupby("endretTidspunkt_date")
        .endretAv.nunique()
        .cumsum()
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=antall_brukere_akkumulert_over_tid.index,
            y=antall_brukere_akkumulert_over_tid.values,
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Dato",
        yaxis_title="Antall brukere",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def antall_brukere_per_måned(data_statistikk):
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


def andel_statusendringer_gjort_av_superbrukere(data_statistikk):
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


def andel_leveranseregistreringer_gjort_av_superbrukere(data_leveranse):
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


def andel_superbrukere(data_statistikk):
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
