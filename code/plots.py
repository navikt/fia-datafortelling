import plotly.express as px
from datetime import datetime, timezone


def dager_siden_siste_oppdatering(data_statistikk, data_leveranse):

    data_statistikk["aktiv_sak"] = ~data_statistikk.status.isin(['IKKE_AKTUELL', 'FULLFØRT', 'NY'])

    siste_oppdatering_statistikk = data_statistikk[data_statistikk.aktiv_sak].groupby("saksnummer").endretTidspunkt.max().reset_index()
    siste_oppdatering_leveranse = data_leveranse.groupby("saksnummer").sistEndret.max().reset_index()

    siste_oppdatering = siste_oppdatering_statistikk.merge(siste_oppdatering_leveranse, on='saksnummer', how='left')
    siste_oppdatering = siste_oppdatering.rename(
        columns={'endretTidspunkt': 'siste_oppdatering_statistikk', 'sistEndret': 'siste_oppdatering_leveranse'}
    )

    siste_oppdatering["siste_oppdatering"] = siste_oppdatering[
        ['siste_oppdatering_statistikk', 'siste_oppdatering_leveranse']
    ].max(axis=1, numeric_only=False)

    now = datetime.now(timezone.utc)
    siste_oppdatering["dager_siden_siste_oppdatering"] = (now - siste_oppdatering.siste_oppdatering).dt.days

    return px.histogram(siste_oppdatering.dager_siden_siste_oppdatering)
