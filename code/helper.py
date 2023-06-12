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


def pretty_time_delta(seconds):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s %d dager %d timer %d min %d sek' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return '%s %d timer %d min %d sek' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return '%s %d min %d sek' % (sign_string, minutes, seconds)
    else:
        return '%s %d sek' % (sign_string, seconds)


def modul_sortering(data_siste_leveranse):
    tjeneste_sortering = (
        data_siste_leveranse.groupby("iaTjenesteNavn")
        .saksnummer.nunique()
        .sort_values(ascending=False)
        .index.to_list()
    )
    tjeneste_sortering_map = dict(
        zip(tjeneste_sortering, range(len(tjeneste_sortering)))
    )
    modul_sortering = (
        data_siste_leveranse.groupby(["iaTjenesteNavn", "iaModulNavn"])
        .saksnummer.nunique()
        .sort_values(ascending=False)
        .reset_index()
        .sort_values("iaTjenesteNavn", key=lambda col: col.map(tjeneste_sortering_map))
        .iaModulNavn.to_list()
    )
    return modul_sortering
