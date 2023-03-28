def antall_saker_per_status(data_statistikk):
    return (
        data_statistikk.groupby("siste_status")
        .saksnummer.nunique()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"siste_status":"Status", "saksnummer": "Antall saker"})
    )
