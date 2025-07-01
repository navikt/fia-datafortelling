import json
from typing import Any

import pandas as pd

from src.utils.datahandler import (
    load_data_deduplicate,
)
from src.utils.konstanter import (
    Resultatområde,
    fylker,
    resultatområder,
    rogaland_lund,
    viken_akershus,
)


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

    data_samarbeid: pd.DataFrame = raw_data_samarbeid[
        raw_data_samarbeid["status"] != "SLETTET"
    ]

    data_statistikk = data_statistikk.sort_values("endretTidspunkt").drop_duplicates(
        "saksnummer", keep="last"
    )

    data_samarbeid = data_samarbeid.merge(
        (
            data_statistikk[
                [
                    "saksnummer",
                    "kommunenummer 2024",
                    "antallPersoner",
                    "resultatomrade",
                    "hoved_nering",
                    "sektor",
                ]
            ].rename(columns={"kommunenummer 2024": "kommunenummer"})
        ),
        on="saksnummer",
        how="left",
    )

    # BUG 10 av 3 200 mangler sektor, usikker hvorfor. Fjerner disse
    data_samarbeid = data_samarbeid[data_samarbeid["sektor"].notna()]

    if resultatområde is not None:
        data_samarbeid = data_samarbeid[
            data_samarbeid["resultatomrade"] == resultatområde.value
        ]

    data_samarbeid["opprettet"] = pd.to_datetime(data_samarbeid["opprettet"])

    dato_samarbeid_lansert = "2024-10-01"
    target_date: pd.Timestamp = pd.to_datetime(dato_samarbeid_lansert, utc=True)
    data_samarbeid = data_samarbeid[data_samarbeid["opprettet"] >= target_date]

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
    data_statistikk = load_data_deduplicate(
        project=project,
        dataset=dataset,
        table="ia-sak-statistikk-v1",
        distinct_colunms="endretAvHendelseId",
        dtypes=statistikk_dtypes,
    )

    kolonner_ikke_i_bruk_i_datafortellinger: list[str] = [
        "arstall",
        "kvartal",
        "kvartaler",
        "tapteDagsverkGradert",
        "graderingsprosent",
        "enhetsnummer",
        "postnummer",
        "muligeDagsverkSiste4Kvartal",
        "sykefraversprosentSiste4Kvartal",
        "tapteDagsverkSiste4Kvartal",
        "tapteDagsverkGradertSiste4Kvartal",
        "graderingsprosentSiste4Kvartal",
    ]

    data_statistikk = data_statistikk.drop(
        columns=kolonner_ikke_i_bruk_i_datafortellinger
    ).reset_index(drop=True)

    # BUG: 6 rader mangler neringer, dropper disse
    data_statistikk: pd.DataFrame = data_statistikk[data_statistikk["neringer"] != "[]"]

    data_statistikk: pd.DataFrame = data_statistikk.sort_values(
        "endretTidspunkt", ascending=True
    ).reset_index(drop=True)

    data_statistikk["endretTidspunkt_måned"] = data_statistikk[
        "endretTidspunkt"
    ].dt.strftime("%Y-%m")

    data_statistikk = legg_til_regional_tilhørighet(
        data=data_statistikk,
        adm_enheter=adm_enheter,
    )

    data_statistikk["hoved_nering"] = data_statistikk["neringer"].apply(parse_næring)

    # TODO: Bruker vi egentlig bare hoved_nering_truncated for printing?
    # kan vi heller ta kolonnen inn i en funksjon før output? Hvorfor pre-processere noe som ikke alltid brukes
    data_statistikk["hoved_nering_truncated"] = data_statistikk["hoved_nering"]
    data_statistikk.loc[
        data_statistikk["hoved_nering"].str.len() > 50, "hoved_nering_truncated"
    ] = data_statistikk["hoved_nering"].str[:47] + "..."

    # Gruppering av virksomheter per antall ansatte
    col_name = "antallPersoner_gruppe"
    data_statistikk.loc[data_statistikk["antallPersoner"] == 0, col_name] = "0"
    data_statistikk.loc[data_statistikk["antallPersoner"].between(1, 4), col_name] = (
        "1-4"
    )
    data_statistikk.loc[data_statistikk["antallPersoner"].between(5, 19), col_name] = (
        "5-19"
    )
    data_statistikk.loc[data_statistikk["antallPersoner"].between(20, 49), col_name] = (
        "20-49"
    )
    data_statistikk.loc[data_statistikk["antallPersoner"].between(50, 99), col_name] = (
        "50-99"
    )
    data_statistikk.loc[data_statistikk["antallPersoner"] >= 100, col_name] = "100+"
    data_statistikk.loc[data_statistikk["antallPersoner"].isna(), col_name] = "Ukjent"

    if resultatområde is not None:
        data_statistikk = data_statistikk[
            data_statistikk["resultatomrade"] == resultatområde.value
        ]

    return data_statistikk


def parse_næring(json_string: str) -> str:
    data = json.loads(json_string)

    if len(data) < 1:
        raise Exception("Feil ved innhenting av hovednæring, mangler næring")
    else:
        return data[0]["navn"]


def legg_til_regional_tilhørighet(
    data: pd.DataFrame,
    adm_enheter: pd.DataFrame,
) -> pd.DataFrame:
    # BUG: noen kolonner mangler data, dropper disse for å unngå følgefeil i utledede kolonner som resultatområde
    # Dette gjelder (per 2025-06-04): 6 rader uten kommunenummer, 22 rader uten fylkesnummer
    data_statistikk = data.copy()
    data_statistikk = data_statistikk.dropna(subset=["kommunenummer", "fylkesnummer"])

    # Legger til en kolonne fylkesnavn basert på fylkesnummer
    data_statistikk["fylkesnavn"] = data_statistikk["fylkesnummer"].map(fylker)

    # Legger til en kolonne resultatomrade basert på fylkesnummer (før og etter 2024 kommune- og fylkesendringer)
    data_statistikk["resultatomrade"] = data_statistikk["fylkesnummer"].map(
        resultatområder
    )

    # Akershus fylke (fylkesnummer 32), må deles i øst- og vest-viken for å få rett grenser i resultatområde
    data_statistikk.loc[data_statistikk["fylkesnummer"] == "32", "resultatomrade"] = (
        data_statistikk["kommunenummer"].map(viken_akershus)
    )

    # Lund kommune i Rogaland følges opp av resultatområdet Agder, så regnes som en del av Agder resultatområde
    data_statistikk.loc[data_statistikk["fylkesnummer"] == "11", "resultatomrade"] = (
        data_statistikk["kommunenummer"].map(rogaland_lund)
    )

    data_statistikk["resultatomrade"] = data_statistikk["resultatomrade"].apply(
        lambda x: str(x).replace(" ", "_").lower()
    )

    # Leser alle kommunenummer og mapper til 2024 kommunenummer
    # TODO: Bør dette skje før vi ordner fylkesnavn og resultatområde?
    # Kan gjøre mapping enklere
    alle_kommunenummer = adm_enheter[["kommunenummer", "kommunenummer 2023"]]

    data_statistikk["kommunenummer 2024"] = (
        data_statistikk["kommunenummer"]
        .map(alle_kommunenummer.set_index("kommunenummer 2023")["kommunenummer"])
        .fillna(data_statistikk["kommunenummer"])
    )

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
