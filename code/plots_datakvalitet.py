import pandas as pd
import plotly.graph_objects as go
from datetime import datetime


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


def dager_mellom_statusendringer(data_status, forrige_status, status):
    data_status["tid_siden_siste_endring"] = (
        data_status.endretTidspunkt - data_status.forrige_endretTidspunkt
    )
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=data_status[
                (data_status.forrige_status == forrige_status)
                & (data_status.status == status)
            ].tid_siden_siste_endring.dt.days,
            nbinsx=20,
        )
    )
    fig.update_layout(title=f"{forrige_status} - {status}".title().replace("_", " "))
    return annotate_ikke_offisiell_statistikk(fig)
