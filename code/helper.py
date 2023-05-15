def annotate_ikke_offisiell_statistikk(fig, x=0.5, y=1.1):
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
