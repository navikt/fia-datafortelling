import pandas as pd
import plotly.graph_objects as go
from datetime import datetime


from code.helper import annotate_ikke_offisiell_statistikk
from code.config import statusordre


def saker_per_status_over_tid(data_status):
    første_dato = data_status.endretTidspunkt.dt.date.min()
    siste_dato = datetime.now().strftime("%Y-%m-%d")
    alle_datoer = pd.date_range(første_dato, siste_dato, freq="d")

    statuser = [status for status in statusordre if status != "NY"]
    status_per_dato = dict(zip(statuser, [[0]] * len(statuser)))
    for dato in alle_datoer:
        data_status_dato = data_status[
            data_status.endretTidspunkt.dt.date == dato.date()
        ]
        for status in statuser:
            sist_count = status_per_dato[status][-1]
            count = (
                sist_count
                - sum(data_status_dato.forrige_status == status)
                + sum(data_status_dato.status == status)
            )
            status_per_dato[status] = status_per_dato[status] + [count]

    fig = go.Figure()
    for status in statuser:
        fig.add_trace(
            go.Scatter(
                x=alle_datoer,
                y=status_per_dato[status],
                name=status,
            )
        )

    fig.update_layout(
        height=500,
        width=850,
        xaxis_title="Dato",
        yaxis_title="Antall saker",
    )

    return annotate_ikke_offisiell_statistikk(fig)
