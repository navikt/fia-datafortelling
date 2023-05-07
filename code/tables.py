import numpy as np
import pandas as pd
from IPython.display import Markdown
from tabulate import tabulate


def moduler_per_maaned(data_leveranse):
    data_leveranse.loc[
        data_leveranse.status == "LEVERT", "fullfort_yearmonth"
    ] = data_leveranse[data_leveranse.status == "LEVERT"].fullfort.apply(
        lambda x: f"{x.year}/{x.month:02d}"
    )

    table = pd.pivot_table(
        data=(
            data_leveranse.groupby(["iaModulNavn", "fullfort_yearmonth"])
            .saksnummer.size()
            .reset_index()
        ),
        values="saksnummer",
        index="iaModulNavn",
        columns="fullfort_yearmonth",
        aggfunc=np.sum,
    )

    table = (
        table.fillna(0)
        .assign(Total=table.sum(axis=1))
        .astype(int)
        .sort_values("Total", ascending=False)
        .reset_index()
        .rename(columns={"iaModulNavn": "IA-modul"})
    )

    return Markdown(tabulate(table.to_numpy(), headers=table.columns))
