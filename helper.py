from datetime import datetime

import pandas as pd
import plotly.graph_objects as go


def annotate_ikke_offisiell_statistikk(fig: go.Figure, x=0.5, y=1.05) -> go.Figure:
    """
    Legger til en annotasjon om at dette ikke er offisiell statistikk
    """
    fig.add_annotation(
        text="NB! Dette er ikke offisiell statistikk og må ikke deles utenfor NAV.",
        xref="paper",
        yref="paper",
        x=x,
        y=y,
        showarrow=False,
        opacity=0.7,
        font_size=11,
    )
    return fig


def pretty_time_delta(seconds: int) -> str:
    """
    Returnerer en lesbar streng av antall sekunder
    """
    sign_string = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%s %d dager %d timer %d min %d sek" % (
            sign_string,
            days,
            hours,
            minutes,
            seconds,
        )
    elif hours > 0:
        return "%s %d timer %d min %d sek" % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return "%s %d min %d sek" % (sign_string, minutes, seconds)
    else:
        return "%s %d sek" % (sign_string, seconds)


def ikke_aktuell_begrunnelse_sortering(ikke_aktuell: pd.DataFrame) -> list:
    """
    Returnerer en sortert liste av ikke aktuell begrunnelse
    """
    begrunnelse_sortering = (
        ikke_aktuell.groupby("ikkeAktuelBegrunnelse_lesbar")
        .saksnummer.nunique()
        .sort_values(ascending=False)
        .index.tolist()
    )

    return begrunnelse_sortering


def alle_måneder_mellom_datoer(
    første_dato: str, siste_dato=datetime.now()
) -> pd.Series:
    """
    Returnerer alle måneder mellom to datoer
    """
    alle_datoer: pd.DatetimeIndex = pd.date_range(
        første_dato, siste_dato, freq="d", normalize=True
    )
    alle_måneder: pd.Series = alle_datoer.strftime("%Y-%m").drop_duplicates()
    return alle_måneder


def iatjeneste_og_status_sortering(data_leveranse: pd.DataFrame) -> pd.MultiIndex:
    """
    Returnerer en sortert multiindex av IA-tjeneste og status
    """
    return (
        data_leveranse.drop_duplicates(["saksnummer", "iaTjenesteId"], keep="last")
        .groupby(["iaTjenesteNavn", "status"])
        .saksnummer.count()
        .sort_values(ascending=True)
        .index
    )
