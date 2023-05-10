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

    forste_sak_dato = data_statistikk.endretTidspunkt.min().strftime("%d.%m.%Y")
    fig.add_trace(
        go.Indicator(
            mode="number",
            title_text=f"Totalt antall saker<br><span style='font-size:0.6em;color:gray'>Siden {forste_sak_dato}</span><br>",
            value=data_statistikk.saksnummer.nunique(),
            number={"valueformat": ","},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Indicator(
            mode="number",
            title_text="Antall aktive saker<br><span style='font-size:0.6em;color:gray'>(Vurderes, Kontaktes, Kartlegges og Vi bistår)</span><br>",
            value=data_statistikk[data_statistikk.aktiv_sak].saksnummer.nunique(),
            number={"valueformat": ","},
        ),
        row=1,
        col=2,
    )
    fig.update_layout(
        height=230,
        width=850,
    )

    return fig
