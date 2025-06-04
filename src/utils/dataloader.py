import pandas as pd

from src.utils.datahandler import (
    legg_til_sektor_og_resultatområde,
    load_data_deduplicate,
    preprocess_data_samarbeid,
    preprocess_data_statistikk,
)
from src.utils.konstanter import Resultatområde


def last_inn_spørreundersøkelser(
    project: str,
    dataset: str,
    data_statistikk: pd.DataFrame,
    resultatområde: Resultatområde | None = None,
):
    data_spørreundersøkelse = load_data_deduplicate(
        project=project,
        dataset=dataset,
        table="sporreundersokelse-v1",
        distinct_colunms="id",
    )

    data_spørreundersøkelse = data_spørreundersøkelse[
        (data_spørreundersøkelse["harMinstEttSvar"])
        & (data_spørreundersøkelse["status"] != "SLETTET")
    ]

    # Legg til sektor?
    data_spørreundersøkelse = legg_til_sektor_og_resultatområde(
        data=data_spørreundersøkelse,
        data_statistikk=data_statistikk,
    )

    if resultatområde is not None:
        data_spørreundersøkelse = data_spørreundersøkelse[
            data_spørreundersøkelse["resultatomrade"] == resultatområde.value
        ]

    return data_spørreundersøkelse


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

    data_samarbeid = preprocess_data_samarbeid(
        raw_data_samarbeid=raw_data_samarbeid,
        data_statistikk=data_statistikk,
    )

    if resultatområde is not None:
        data_samarbeid = data_samarbeid[
            data_samarbeid["resultatomrade"] == resultatområde.value
        ]

    return data_samarbeid


def last_inn_data_samarbeidsplan(
    project: str,
    dataset: str,
    data_samarbeid: pd.DataFrame,
    data_statistikk: pd.DataFrame,
    resultatområde: Resultatområde | None = None,
):
    data_samarbeidsplan = load_data_deduplicate(
        project,
        dataset,
        "samarbeidsplan-bigquery-v1",
        distinct_colunms="id",
    )

    data_samarbeidsplan = data_samarbeidsplan.merge(
        data_samarbeid[["id", "saksnummer"]].rename({"id": "samarbeidId"}, axis=1),
        how="left",
        on="samarbeidId",
    )

    data_samarbeidsplan = legg_til_sektor_og_resultatområde(
        data_samarbeidsplan, data_statistikk
    )

    if resultatområde is not None:
        data_samarbeidsplan = data_samarbeidsplan[
            data_samarbeidsplan["resultatomrade"] == resultatområde.value
        ]

    return data_samarbeidsplan


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
            data_statistikk["resultatomrade"] == resultatområde.value
        ]

    data_statistikk = data_statistikk.dropna(subset=["resultatomrade"])

    return data_statistikk
