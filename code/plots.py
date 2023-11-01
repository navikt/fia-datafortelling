import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from code.datahandler import beregn_siste_oppdatering
from code.helper import annotate_ikke_offisiell_statistikk, alle_måneder_mellom_datoer
from code.konstanter import plotly_colors


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


def antall_leveranser_per_sak(
    data_status: pd.DataFrame, data_leveranse: pd.DataFrame
) -> go.Figure:
    # saker som har leveranser registrert
    leveranser_per_sak = data_leveranse.groupby("saksnummer").iaModulId.nunique()

    # saker som ikke har leveranser registrert men kunne ha hatt
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

    summert_leveranser_per_sak = leveranser_per_sak.value_counts().sort_index()
    fig = go.Figure(
        go.Sunburst(
            labels=["Alle", ">0"] + summert_leveranser_per_sak.index.tolist(),
            parents=["", "Alle", "Alle"] + [">0"] * len(summert_leveranser_per_sak),
            values=[
                summert_leveranser_per_sak.sum(),
                summert_leveranser_per_sak[summert_leveranser_per_sak.index > 0].sum(),
            ]
            + summert_leveranser_per_sak.values.tolist(),
            branchvalues="total",
        )
    )
    fig.update_layout(
        height=500, width=850, margin=go.layout.Margin(t=0, l=0, r=0, b=0)
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
