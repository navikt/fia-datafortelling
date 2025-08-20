from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go

from datafortelling_utils.datahandler import beregn_siste_oppdatering
from datafortelling_utils.helper import annotate_ikke_offisiell_statistikk


def dager_siden_siste_oppdatering(
    data_status: pd.DataFrame, data_eierskap: pd.DataFrame, data_leveranse: pd.DataFrame
) -> go.Figure:
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


def urørt_saker_over_tid(
    data_status: pd.DataFrame,
    data_eierskap: pd.DataFrame,
    data_leveranse: pd.DataFrame,
    antall_dager: int,
) -> go.Figure:
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
