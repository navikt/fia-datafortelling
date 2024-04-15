import pandas as pd
from datetime import datetime, timedelta

from datetime import datetime
from dateutil.relativedelta import relativedelta, FR
from enum import Enum


class SakStatus(Enum):
    NY = "NY"
    VURDERES = "VURDERES"
    IKKE_AKTUELL = "IKKE_AKTUELL"
    KONTAKTES = "KONTAKTES"
    KARTLEGGES = "KARTLEGGES"
    VI_BISTÅR = "VI_BISTÅR"
    FULLFØRT = "FULLFØRT"
    SLETTET = "SLETTET"


class TjenesteStatus(Enum):
    LEVERT = "LEVERT"
    UNDER_ARBEID = "UNDER_ARBEID"


def filtrer_på_kolonne_tid(
    df: pd.DataFrame,
    start_dato: datetime,
    slutt_dato: datetime,
    kolonne_tid: str = "opprettetTidspunkt",
) -> pd.DataFrame:
    return df[((df[kolonne_tid] > start_dato) & (df[kolonne_tid] < slutt_dato))]


def filtrer_på_kolonne_status(
    df: pd.DataFrame,
    status: TjenesteStatus | SakStatus,
) -> pd.DataFrame:
    return df[df.status == status.value]


def antall_tjenester_denne_perioden(
    data_leveranse: pd.DataFrame,
    startdato: datetime,
    sluttdato: datetime,
):
    tjenester = data_leveranse.iaTjenesteNavn.unique()
    data = {}

    levert_denne_perioden = filtrer_på_kolonne_tid(
        df=data_leveranse,
        start_dato=startdato,
        slutt_dato=sluttdato,
        kolonne_tid="fullfort",
    )

    levert_denne_perioden = filtrer_på_kolonne_status(
        df=levert_denne_perioden, status=TjenesteStatus.LEVERT
    )

    opprettet_denne_perioden = filtrer_på_kolonne_tid(
        df=data_leveranse,
        start_dato=startdato,
        slutt_dato=sluttdato,
        kolonne_tid="opprettetTidspunkt",
    )

    etterregistrerte_tjenester = antall_tjenester_opprettet_og_fullført_innen_et_døgn(
        opprettet_denne_perioden=opprettet_denne_perioden,
    )

    for tjeneste in tjenester:
        data[tjeneste] = {}

        data[tjeneste]["LEVERT"] = len(
            levert_denne_perioden[levert_denne_perioden.iaTjenesteNavn == tjeneste]
        )
        data[tjeneste]["OPPRETTET"] = len(
            opprettet_denne_perioden[
                opprettet_denne_perioden.iaTjenesteNavn == tjeneste
            ]
        )
        data[tjeneste]["ETTERREGISTRERT"] = len(
            etterregistrerte_tjenester[
                etterregistrerte_tjenester.iaTjenesteNavn == tjeneste
            ]
        )

    return data


def antall_saker(
    data_status: pd.DataFrame,
    start_dato: datetime,
    slutt_dato: datetime,
    kolonne_tid: str,
    status_sak: SakStatus | None = None,
):
    filtrerte_saker = filtrer_på_kolonne_tid(
        df=data_status,
        start_dato=start_dato,
        slutt_dato=slutt_dato,
        kolonne_tid=kolonne_tid,  # endret ila. perioden
    )

    if status_sak is not None:
        filtrerte_saker = filtrer_på_kolonne_status(
            df=filtrerte_saker, status=status_sak
        )

    return len(filtrerte_saker)


def antall_saker_i_vi_bistår(data_status: pd.DataFrame, status="VI_BISTÅR") -> int:
    return len(data_status[(data_status.status == status) & data_status.aktiv_sak])


def start_og_slutt_for_periode(
    dato: datetime,
    hour: int = 9,
    minute: int = 0,
    second: int = 0,
) -> tuple[datetime, datetime]:
    if dato.weekday() != 4:
        dato = dato + relativedelta(weekday=FR(-1))

    startdato = dato.replace(
        hour=(hour) % 24,
        minute=(minute) % 60,
        second=(second) % 60,
        microsecond=0,
    ) - timedelta(7)

    sluttdato = dato.replace(
        hour=(hour - 1) % 24,
        minute=(minute - 1) % 60,
        second=(second - 1) % 60,
        microsecond=0,
    )

    return startdato, sluttdato


def antall_tjenester_opprettet_og_fullført_innen_et_døgn(
    opprettet_denne_perioden: pd.DataFrame,
    antall_timer: int = 24,
):
    # Kun de levert
    df = filtrer_på_kolonne_status(
        df=opprettet_denne_perioden, status=TjenesteStatus.LEVERT
    )
    df["diff"] = df["fullfort"] - df["opprettetTidspunkt"]
    df[df["diff"] < timedelta(hours=antall_timer)]
    return df


def data_denne_perioden(
    data_status: pd.DataFrame,
    data_leveranse: pd.DataFrame,
    dato: datetime = datetime.now(),
    hour: int = 9,
    minute: int = 0,
    second: int = 0,
):
    startdato, sluttdato = start_og_slutt_for_periode(
        dato=dato, hour=hour, minute=minute, second=second
    )

    saker_vi_bistår = antall_saker(
        data_status=data_status,
        kolonne_tid="endretTidspunkt",
        status_sak=SakStatus.VI_BISTÅR,
        start_dato=startdato,
        slutt_dato=sluttdato,
    )

    fullførte_saker = antall_saker(
        data_status=data_status,
        kolonne_tid="endretTidspunkt",
        status_sak=SakStatus.FULLFØRT,
        start_dato=startdato,
        slutt_dato=sluttdato,
    )

    antall_tjenester = antall_tjenester_denne_perioden(
        data_leveranse=data_leveranse,
        startdato=startdato,
        sluttdato=sluttdato,
    )

    return (startdato, sluttdato, saker_vi_bistår, fullførte_saker, antall_tjenester)


import plotly.graph_objects as go

from helper import annotate_ikke_offisiell_statistikk


def plot_historiske_data(
    data_status,
    antall_uker: int = 52,
    startdato=datetime.now(),
):
    tid = []
    inn = []
    ut = []

    for _ in range(antall_uker):
        startdato, sluttdato = start_og_slutt_for_periode(dato=startdato)
        tid.append(str(sluttdato))
        inn.append(
            antall_saker(
                data_status=data_status,
                kolonne_tid="endretTidspunkt",
                status_sak=SakStatus.VI_BISTÅR,
                start_dato=startdato,
                slutt_dato=sluttdato,
            )
        )

        ut.append(
            antall_saker(
                data_status=data_status,
                kolonne_tid="endretTidspunkt",
                status_sak=SakStatus.FULLFØRT,
                start_dato=startdato,
                slutt_dato=sluttdato,
            )
        )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=inn,
            x=tid,
            orientation="v",
            name="Vi bistår",
        )
    )

    fig.add_trace(
        go.Bar(
            y=ut,
            x=tid,
            orientation="v",
            name="Fullført",
        )
    )

    fig.update_layout(
        height=500,
        width=800,
        plot_bgcolor="rgb(255,255,255)",
        yaxis_title="Antall saker",
        xaxis_title_standoff=80,
        xaxis_title="Per uke",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=0.3),
    )

    return annotate_ikke_offisiell_statistikk(fig, y=1.2)
