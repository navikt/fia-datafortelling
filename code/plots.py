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


def for_lavt_sykefravær(
    data_status: pd.DataFrame, ikke_aktuell: pd.DataFrame
) -> go.Figure():
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


def mindre_virksomhet(
    data_status: pd.DataFrame, ikke_aktuell: pd.DataFrame
) -> go.Figure():
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
        xaxis_title="Antall arbeidsforhold (%)",
        yaxis_title="Andel saker (%)",
        barmode="overlay",
    )
    fig.update_traces(opacity=0.75)

    return annotate_ikke_offisiell_statistikk(fig)


def andel_fullforte_saker_med_leveranse_per_måned(
    data_status: pd.DataFrame, data_leveranse: pd.DataFrame
) -> go.Figure():
    første_dato = data_leveranse.sistEndret.min()
    alle_måneder = alle_måneder_mellom_datoer(første_dato)
    antall_mnd = min(len(alle_måneder), 12)

    fullført_per_måned = (
        data_status[
            (data_status.status == "FULLFØRT")
            & (data_status.endretTidspunkt >= første_dato.strftime("%Y-%m-%d"))
        ]
        .endretTidspunkt_måned.value_counts()
        .sort_index()
        .reindex(alle_måneder, fill_value=0)
    )

    saker_med_leveranser = data_leveranse.saksnummer.unique()
    data_status["med_leveranse"] = False
    data_status.loc[
        data_status.saksnummer.isin(saker_med_leveranser), "med_leveranse"
    ] = True
    fullført_per_måned_med_leveranse = (
        data_status[(data_status.status == "FULLFØRT") & data_status.med_leveranse]
        .endretTidspunkt_måned.value_counts()
        .sort_index()
    )

    andel_fullført_med_leveranse = fullført_per_måned_med_leveranse / fullført_per_måned
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=andel_fullført_med_leveranse.index[-antall_mnd:],
            y=100 * andel_fullført_med_leveranse.values[-antall_mnd:],
        )
    )
    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Fullført måned",
        yaxis_title="Andel fullførte saker med leveranse (%)",
    )

    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color=plotly_colors[1],
    )
    fig.update_yaxes(range=[0, 110])

    return annotate_ikke_offisiell_statistikk(fig)


def andel_fullforte_saker_med_leveranse_over_tid(
    data_status: pd.DataFrame, data_leveranse: pd.DataFrame
) -> go.Figure():
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
