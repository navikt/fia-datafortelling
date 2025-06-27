from typing import Any

import pandas as pd

from src.utils.datahandler import (
    load_data_deduplicate,
    preprocess_data_samarbeid,
    preprocess_data_statistikk,
)
from src.utils.konstanter import Resultatområde


def last_inn_spørreundersøkelser(
    project: str,
    dataset: str,
    data_samarbeid: pd.DataFrame,
    resultatområde: Resultatområde | None = None,
) -> pd.DataFrame:
    data_spørreundersøkelse: pd.DataFrame = load_data_deduplicate(
        project=project,
        dataset=dataset,
        table="sporreundersokelse-v1",
        distinct_colunms="id",
    ).rename(columns={"samarbeidId": "samarbeid_id"})

    # filtrer ut spørreundersøkelser uten svar og de som har blitt slettet.
    data_spørreundersøkelse = data_spørreundersøkelse[
        (data_spørreundersøkelse["harMinstEttSvar"])
        & (data_spørreundersøkelse["status"] != "SLETTET")
    ]

    # Merge med samarbeid for rikere data
    data_spørreundersøkelse = data_spørreundersøkelse.merge(
        data_samarbeid[
            [
                "id",
                "saksnummer",
                "resultatomrade",
                "sektor",
                "hoved_nering",
                "status",
            ]
        ].rename(columns={"status": "samarbeid_status", "id": "samarbeid_id"}),
        on="samarbeid_id",
        how="left",
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

    # TODO: Trekk denne koden inn i denne metoden og rydd opp ? Filtrer først, så prosesser
    data_samarbeid = preprocess_data_samarbeid(
        raw_data_samarbeid=raw_data_samarbeid,
        data_statistikk=data_statistikk,
    )

    if resultatområde is not None:
        data_samarbeid = data_samarbeid[
            data_samarbeid["resultatomrade"] == resultatområde.value
        ]

    return data_samarbeid


def antall_planer(data_samarbeidsplan: pd.DataFrame) -> int:
    return data_samarbeidsplan["plan_id"].nunique()


def last_inn_data_samarbeidsplan(
    project: str,
    dataset: str,
    data_samarbeid: pd.DataFrame,
    resultatområde: Resultatområde | None = None,
) -> pd.DataFrame:
    """
    Henter data for samarbeidsplaner og legger til mer data fra samarbeid.
    Args:
        project (str): GCP prosjekt
        dataset (str): BigQuery dataset
        data_samarbeid (pd.DataFrame): DataFrame med samarbeid
        resultatområde (Resultatområde | None): Filtrering på resultatområde, hvis None hentes alle
    Returns:
        pd.DataFrame: DataFrame med samarbeidsplaner og data om samarbeid
    """

    data_samarbeidsplan: pd.DataFrame = load_data_deduplicate(
        project=project,
        dataset=dataset,
        table="samarbeidsplan-v1",
        distinct_colunms="id",
    )

    # Filtrer ut ikke-inkludert innhold.
    # Bryr oss kun om undertemaer som er inkludert.
    data_samarbeidsplan: pd.DataFrame = data_samarbeidsplan[
        data_samarbeidsplan["inkludert"]
    ]

    # Merge med samarbeid for rikere data
    data_samarbeidsplan = data_samarbeidsplan.merge(
        data_samarbeid[
            [
                "id",
                "saksnummer",
                "resultatomrade",
                "sektor",
                "hoved_nering",
                "status",
            ]
        ].rename(columns={"status": "samarbeid_status", "id": "samarbeid_id"}),
        on="samarbeid_id",
        how="left",
    )

    # Filtrer ut basert på geografi
    if resultatområde is not None:
        data_samarbeidsplan = data_samarbeidsplan[
            data_samarbeidsplan["resultatomrade"] == resultatområde.value
        ]

    # Gjør kolonner til datetime og beregn varighet
    data_samarbeidsplan[["start_dato", "slutt_dato"]] = data_samarbeidsplan[
        ["start_dato", "slutt_dato"]
    ].apply(pd.to_datetime)

    data_samarbeidsplan["varighet"] = (
        data_samarbeidsplan["slutt_dato"] - data_samarbeidsplan["start_dato"]
    ).dt.days

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
        dtypes=statistikk_dtypes,
    )

    # TODO: Trekk denne koden inn i denne metoden og rydd opp ? Filtrer først, så prosesser
    data_statistikk = preprocess_data_statistikk(
        raw_data_statistikk=raw_data_statistikk,
        adm_enheter=adm_enheter,
    )

    if resultatområde is not None:
        data_statistikk = data_statistikk[
            data_statistikk["resultatomrade"] == resultatområde.value
        ]

    return data_statistikk


statistikk_dtypes: dict[str, Any] = {
    "saksnummer": pd.StringDtype(storage="pyarrow"),  # REQUIRED
    "orgnr": pd.StringDtype(storage="pyarrow"),  # REQUIRED
    "eierAvSak": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "status": pd.StringDtype(storage="pyarrow"),  # REQUIRED
    "endretAvHendelseId": pd.StringDtype(storage="pyarrow"),  # REQUIRED
    "ikkeAktuelBegrunnelse": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "antallPersoner": pd.Int64Dtype(),  # NULLABLE
    "tapteDagsverk": pd.Float64Dtype(),  # NULLABLE
    "muligeDagsverk": pd.Float64Dtype(),  # NULLABLE
    "sykefraversprosent": pd.Float64Dtype(),  # NULLABLE
    "arstall": pd.Int64Dtype(),  # NULLABLE
    "kvartal": pd.Int64Dtype(),  # NULLABLE
    "tapteDagsverkSiste4Kvartal": pd.Float64Dtype(),  # NULLABLE
    "muligeDagsverkSiste4Kvartal": pd.Float64Dtype(),  # NULLABLE
    "sykefraversprosentSiste4Kvartal": pd.Float64Dtype(),  # NULLABLE
    "sektor": pd.StringDtype(storage="pyarrow"),  # NULLABLEE
    "bransjeprogram": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "postnummer": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "kommunenummer": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "fylkesnummer": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "endretAv": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "endretAvRolle": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "enhetsnummer": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "enhetsnavn": pd.StringDtype(storage="pyarrow"),  # NULLABLE
    "tapteDagsverkGradert": pd.Float64Dtype(),  # NULLABLE
    "graderingsprosent": pd.Float64Dtype(),  # NULLABLE
    "tapteDagsverkGradertSiste4Kvartal": pd.Float64Dtype(),  # NULLABLE
    "graderingsprosentSiste4Kvartal": pd.Float64Dtype(),  # NULLABLE
}
