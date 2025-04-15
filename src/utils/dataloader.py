import pandas as pd

from src.utils.datahandler import (
    legg_til_resultatområde,
    load_data_deduplicate,
    preprocess_data_samarbeid,
    preprocess_data_statistikk,
)
from src.utils.konstanter import Resultatområde


def last_inn_spørreundersøkelser(
    project: str,
    dataset: str,
):
    return load_data_deduplicate(
        project=project,
        dataset=dataset,
        table="sporreundersokelse-v1",
        distinct_colunms="id",
    )


def last_inn_samarbeid(
    project: str,
    dataset: str,
    data_statistikk: pd.DataFrame,
    resultatområde: Resultatområde | None = None,
):
    raw_data_samarbeid = load_data_deduplicate(
        project=project,
        dataset=dataset,
        table="samarbeid-v1",
        distinct_colunms="id",
    )
    # TODO: usikker på hva denne gjør, må det være data_statistikk MED resultatområde?
    #  Se på annen måte å merge dataframes på ?
    raw_data_samarbeid_med_resultatområde = legg_til_resultatområde(
        data=raw_data_samarbeid,
        data_statistikk=data_statistikk,
    )

    if resultatområde is not None:
        raw_data_samarbeid_med_resultatområde = raw_data_samarbeid_med_resultatområde[
            raw_data_samarbeid_med_resultatområde.resultatomrade == resultatområde.value
        ]

    data_samarbeid = preprocess_data_samarbeid(
        data_samarbeid=raw_data_samarbeid_med_resultatområde,
        data_statistikk=data_statistikk,
    )

    return data_samarbeid


def last_inn_data_statistikk(
    project: str,
    dataset: str,
    adm_enheter: pd.DataFrame,
    resultatområde: Resultatområde | None = None,
):
    raw_data_statistikk = load_data_deduplicate(
        project=project,
        dataset=dataset,
        table="ia-sak-statistikk-v1",
        distinct_colunms="endretAvHendelseId",
    )

    # Legger på resultatområde, data statistikk har alltid resultatområde kolonne
    data_statistikk = preprocess_data_statistikk(
        data_statistikk=raw_data_statistikk,
        adm_enheter=adm_enheter,
    )

    if resultatområde is not None:
        data_statistikk = data_statistikk[
            data_statistikk.resultatomrade == resultatområde.value
        ]

    return data_statistikk
