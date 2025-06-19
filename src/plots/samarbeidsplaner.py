import pandas as pd
import plotly.graph_objects as go

from src.utils.konstanter import undertema_labels, undertema_navn


def plot_samarbeidsplaner_etter_status(
    data: pd.DataFrame,
    undertema_navn: list[str] = undertema_navn,
    undertema_labels: dict[str, str] = undertema_labels,
    width: int = 850,
    farge_pågår: str = "#368da8",
    farge_planlagt: str = "#c77300",
    farge_fullført: str = "#06893a",
    farge_avbrutt: str = "#c30000",
) -> go.Figure:
    if data.empty:
        return go.Figure()

    # Data PÅGÅR
    inkluderte_undertemaer: pd.DataFrame = data[data["inkludert"]]
    pågående_undertemaer: pd.DataFrame = inkluderte_undertemaer[
        inkluderte_undertemaer["status"] == "PÅGÅR"
    ]
    alle_pågående_undertemaer: pd.Series[int] = (
        pågående_undertemaer["navn"]
        .value_counts()
        .reindex(undertema_navn, fill_value=0)
        .sort_values(ascending=True)
    )

    # Data PLANLAGT
    inkluderte_undertemaer: pd.DataFrame = data[data["inkludert"]]
    planlagte_undertemaer: pd.DataFrame = inkluderte_undertemaer[
        inkluderte_undertemaer["status"] == "PLANLAGT"
    ]
    alle_planlagte_undertemaer: pd.Series[int] = (
        planlagte_undertemaer["navn"]
        .value_counts()
        .reindex(undertema_navn, fill_value=0)
        .sort_values(ascending=True)
    )

    # Data FULLFØRT
    inkluderte_undertemaer: pd.DataFrame = data[data["inkludert"]]
    fullførte_undertemaer: pd.DataFrame = inkluderte_undertemaer[
        inkluderte_undertemaer["status"] == "FULLFØRT"
    ]
    alle_fullførte_undertemaer: pd.Series[int] = (
        fullførte_undertemaer["navn"]
        .value_counts()
        .reindex(undertema_navn, fill_value=0)
        .sort_values(ascending=True)
    )

    # Data AVBRUTT
    inkluderte_undertemaer: pd.DataFrame = data[data["inkludert"]]
    avbrutte_undertemaer: pd.DataFrame = inkluderte_undertemaer[
        inkluderte_undertemaer["status"] == "AVBRUTT"
    ]
    alle_avbrutte_undertemaer: pd.Series[int] = (
        avbrutte_undertemaer["navn"]
        .value_counts()
        .reindex(undertema_navn, fill_value=0)
        .sort_values(ascending=True)
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=[undertema_labels[x] for x in alle_pågående_undertemaer.index],
            x=alle_pågående_undertemaer.values,
            name="PÅGÅR",
            orientation="h",
            marker=dict(
                color=farge_pågår, line=dict(color="rgb(248, 248, 249)", width=1)
            ),
        )
    )
    fig.add_trace(
        go.Bar(
            y=[undertema_labels[x] for x in alle_planlagte_undertemaer.index],
            x=alle_planlagte_undertemaer.values,
            name="PLANLAGT",
            orientation="h",
            marker=dict(
                color=farge_planlagt, line=dict(color="rgb(248, 248, 249)", width=1)
            ),
        )
    )

    fig.add_trace(
        go.Bar(
            y=[undertema_labels[x] for x in alle_fullførte_undertemaer.index],
            x=alle_fullførte_undertemaer.values,
            name="FULLFØRT",
            orientation="h",
            marker=dict(
                color=farge_fullført, line=dict(color="rgb(248, 248, 249)", width=1)
            ),
        )
    )
    fig.add_trace(
        go.Bar(
            y=[undertema_labels[x] for x in alle_avbrutte_undertemaer.index],
            x=alle_avbrutte_undertemaer.values,
            name="AVBRUTT",
            orientation="h",
            marker=dict(
                color=farge_avbrutt, line=dict(color="rgb(248, 248, 249)", width=1)
            ),
        )
    )

    fig.update_layout(
        xaxis_title="Antall planer med undertema inkludert",
        barmode="stack",
        width=width,
        bargap=0.04,
        legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99),
    )

    return fig
