import plotly.graph_objs as go
import plotly.subplots as sp


def antall_saker_indicator(data_statistikk):
    fig = sp.make_subplots(
        rows=1,
        cols=2,
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}],
        ],
    )
    fig.add_trace(
        go.Indicator(
            mode="number",
            title_text="Totalt antall saker",
            value=data_statistikk.saksnummer.nunique(),
            number={"valueformat": ","},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Indicator(
            mode="number",
            title_text="Antall aktive saker",
            value=data_statistikk[data_statistikk.aktiv_sak].saksnummer.nunique(),
            number={"valueformat": ","},
        ),
        row=1,
        col=2,
    )
    fig.update_layout(
        height=230,
        width=700,
    )
    return fig
