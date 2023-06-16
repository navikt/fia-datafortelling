import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone, timedelta


from code.datahandler import explode_ikke_aktuell_begrunnelse
from code.helper import annotate_ikke_offisiell_statistikk
from code.konstanter import statusordre, fylker, intervall_sortering, plotly_colors


def saker_per_status_over_tid(data_status):
    første_dato = data_status.endretTidspunkt.dt.date.min()
    siste_dato = datetime.now().strftime("%Y-%m-%d")
    alle_datoer = pd.date_range(første_dato, siste_dato, freq="d")
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

    # En strek for hver kombinasjon av fylke og status
    for fylkesnr in fylker.keys():
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
    knapper_navn = ["Alle fylker"] + list(fylker.values())
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
    første_dato = data_status.endretTidspunkt.dt.date.min()
    now = datetime.now(timezone.utc)
    alle_datoer = pd.date_range(
        første_dato, now.strftime("%Y-%m-%d"), freq="d", tz=timezone.utc
    )
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
        data_status[data_status.siste_status.isin(["VI_BISTÅR", "FULLFØRT"])]
        .drop_duplicates("saksnummer", keep="last")
        .groupby("eierAvSak")
        .saksnummer.nunique()
    )

    fig = go.Figure(data=[go.Histogram(x=saker_per_eier)])
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Antall saker",
        yaxis_title="Antall eiere",
    )

    return annotate_ikke_offisiell_statistikk(fig)


def for_lavt_sykefravær(data_status):
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
    ikke_aktuell = explode_ikke_aktuell_begrunnelse(data_status)
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


def mindre_virksomhet(data_status):
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
    ikke_aktuell = explode_ikke_aktuell_begrunnelse(data_status)
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
    data_status["endretTidspunkt_måned"] = data_status.endretTidspunkt.dt.strftime(
        "%Y-%m"
    )
    fullført_per_måned = (
        data_status.loc[data_status.status == "FULLFØRT"]
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
    )
    return annotate_ikke_offisiell_statistikk(fig)
