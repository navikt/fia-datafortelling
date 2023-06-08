import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta


from code.datahandler import beregn_siste_oppdatering
from code.helper import annotate_ikke_offisiell_statistikk
from code.konstanter import statusordre, fylker


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


def dager_mellom_statusendringer(
    data_status: pd.DataFrame,
    intervall_sortering: list,
    forrige_status_filter: str = None,
    status_filter : str = None,
):
    filtre = True
    if forrige_status_filter:
        filtre = filtre & (data_status.forrige_status == forrige_status_filter)
    if status_filter:
        filtre = filtre & (data_status.status == status_filter)

    saker_per_intervall = (
        data_status[filtre]
        .groupby("intervall_tid_siden_siste_endring")
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
        xaxis_title="Tidsgruppering",
        yaxis_title="Antall saker",
    )
    fig.update_xaxes(categoryorder="array", categoryarray=intervall_sortering)

    return annotate_ikke_offisiell_statistikk(fig)


def urørt_saker_over_tid(data_status, data_eierskap, data_leveranse, antall_dager):
    første_dato = data_status.endretTidspunkt.dt.date.min()
    siste_dato = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    alle_datoer = pd.date_range(første_dato, siste_dato, freq="d", tz=timezone.utc)
    aktive_statuser = ["VURDERES", "KONTAKTES", "KARTLEGGES", "VI_BISTÅR"]

    urørt_per_status_og_dato = dict(zip(aktive_statuser, [[]] * len(aktive_statuser)))
    for beregningsdato in alle_datoer:
        siste_oppdatering = beregn_siste_oppdatering(
            data_status,
            data_eierskap,
            data_leveranse,
            beregningsdato + timedelta(days=1),
        )
        for status in aktive_statuser:
            antall_urørt = (
                siste_oppdatering[
                    (siste_oppdatering.status_beregningsdato == status)
                ].dager_siden_siste_oppdatering
                > antall_dager
            ).sum()
            urørt_per_status_og_dato[status] = urørt_per_status_og_dato[status] + [
                antall_urørt
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
        xaxis=dict(
            autorange=True,
            rangeslider=dict(
                autorange=True,
                visible=True
            )
        )
    )
            
    return annotate_ikke_offisiell_statistikk(fig)