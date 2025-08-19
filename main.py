import logging
import os
import subprocess

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def render_quarto(file_to_render: str) -> None:
    logging.info("Kjører quarto render for forside til datafortellingene")
    try:
        result = subprocess.run(
            ["uv", "run", "quarto", "render", file_to_render + ".qmd"],
            check=True,
            capture_output=True,
            text=True,
        )
        logging.debug(f"Output fra quarto: \n{result.stdout} \n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Feil ved rendering av quarto dokument: {e.stderr}")
        raise


def render_samarbeid_per_resultatområde(resultatområde: str) -> None:
    logging.info(
        f"Kjører quarto render for datafortelling om samarbeid - {resultatområde}"
    )
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "quarto",
                "render",
                f"fia_{resultatområde}_samarbeid.qmd",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        logging.debug(f"Output fra quarto: \n{result.stdout} \n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Feil ved rendering av quarto dokument: {e.stderr}")
        raise


def render_samarbeidsplan_per_resultatområde(resultatområde: str) -> None:
    logging.info(
        f"Kjører quarto render for datafortelling om samarbeidsplaner - {resultatområde}"
    )
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "quarto",
                "render",
                f"fia_{resultatområde}_samarbeidsplan.qmd",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        logging.debug(f"Output fra quarto: \n{result.stdout} \n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Feil ved rendering av quarto dokument: {e.stderr}")
        raise


def render_fia_per_resultatområde(resultatområde: str) -> None:
    logging.info(f"Kjører quarto render for datafortelling om Fia - {resultatområde}")
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "quarto",
                "render",
                f"fia_{resultatområde}.qmd",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        logging.debug(f"Output fra quarto: \n{result.stdout} \n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Feil ved rendering av quarto dokument: {e.stderr}")
        raise


def render_ia_tjenester_per_resultatområde(resultatområde: str) -> None:
    try:
        logging.info("IA-tjenester")
        result = subprocess.run(
            [
                "uv",
                "run",
                "quarto",
                "render",
                f"ia_tjenester_{resultatområde}.qmd",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        logging.debug(f"Output fra quarto: \n{result.stdout} \n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Feil ved rendering av quarto dokument: {e.stderr}")
        raise


def update_quarto(files_to_upload: list[str]) -> None:
    multipart_form_data: dict[str, tuple[str, bytes]] = {}
    for file_path in files_to_upload:
        file_name: str = file_path.replace("pages/", "", 1)
        with open(file_path, "rb") as file:
            file_contents: bytes = file.read()
            multipart_form_data[file_name] = (file_name, file_contents)
            logging.info(f"Fil klar for opplasting: {file_name}")

    logging.info("multipart form data prepared.")

    try:
        response: requests.Response = requests.put(
            url=f"https://{os.environ['NADA_ENV']}/quarto/update/{os.environ['QUARTO_ID']}",
            headers={"Authorization": f"Bearer {os.environ['QUARTO_TOKEN']}"},
            files=multipart_form_data,
        )
        response.raise_for_status()
        logging.info("Quarto update completed successfully.")
    except requests.RequestException as e:
        logging.error(f"Error updating Quarto document: {e}")
        raise


if __name__ == "__main__":
    logging.info("Starter render av datafortellinger.")
    try:
        render_quarto(file_to_render="index")

        for resultatområde in [
            "norge",
            "agder",
            "innlandet",
            "more_og_romsdal",
            "nordland",
            "oslo",
            "ost-viken",
            "rogaland",
            "troms_og_finnmark",
            "trondelag",
            "vest-viken",
            "vestfold_og_telemark",
            "vestland",
        ]:
            render_fia_per_resultatområde(resultatområde=resultatområde)
            render_samarbeid_per_resultatområde(resultatområde=resultatområde)
            render_samarbeidsplan_per_resultatområde(resultatområde=resultatområde)

        logging.info("Henter filer å laste opp til NADA")

        total_file_size_bytes: int = 0
        files_to_upload: list[str] = []
        for root, dirs, files in os.walk("pages"):
            for file in files:
                files_to_upload.append(os.path.join(root, file))
                file_size_bytes: int = os.path.getsize(os.path.join(root, file))
                total_file_size_bytes += file_size_bytes
                file_size_kb: float = file_size_bytes / 1024
                logging.info(
                    f"Fil '{os.path.join(root, file)}' på {file_size_kb:.2f} KB lagt til i liste for opplasting"
                )

        file_size_mb: float = total_file_size_bytes / 1024 / 1024
        logging.info(
            f"Fant {len(files_to_upload)} filer å laste opp på totalt {file_size_mb:.2f} MB."
        )

        if total_file_size_bytes > 100000000:
            logging.warning(
                f"Total filstørrelse: {file_size_mb:.2f} MB overstiger 100 MB. Opplasting vil sannsynligvis feile pga begrensning i NADA. Sjekk at vi ikke embedder resources"
            )

        update_quarto(files_to_upload=files_to_upload)

    except Exception as e:
        logging.error(f"Script feilet: {e}")
    logging.info("Oppdatering av datafortellinger ferdig")
