import logging
import os
import subprocess

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def render_quarto(file_to_render: str):
    try:
        logging.info(f"Kjører quarto render {file_to_render}.qmd")

        result = subprocess.run(
            ["quarto", "render", file_to_render + ".qmd"],
            check=True,
            capture_output=True,
            text=True,
        )
        logging.debug(f"Output fra quarto: \n{result.stdout} \n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Feil ved rendering av quarto dokument: {e.stderr}")
        raise


def render_fia_per_resultatområde(resultatområde: str):
    try:
        logging.info("Bruk av Fia")
        result = subprocess.run(
            [
                "quarto",
                "render",
                f"datafortellinger/fia/{resultatområde}.qmd",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        logging.debug(f"Output fra quarto: \n{result.stdout} \n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Feil ved rendering av quarto dokument: {e.stderr}")
        raise


def render_ia_tjenester_per_resultatområde(resultatområde: str):
    try:
        logging.info("IA-tjenester")
        result = subprocess.run(
            [
                "quarto",
                "render",
                f"datafortellinger/ia_tjenester/{resultatområde}.qmd",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        logging.debug(f"Output fra quarto: \n{result.stdout} \n{result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Feil ved rendering av quarto dokument: {e.stderr}")
        raise


def update_quarto(output_dir: str):
    logging.info("Starting Quarto update process.")
    files_to_upload = []
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            files_to_upload.append(os.path.join(root, file))

    multipart_form_data = {}
    for file_path in files_to_upload:
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as file:
            # Read the file contents and store them in the dictionary
            file_contents = file.read()
            multipart_form_data[file_name] = (file_name, file_contents)
            logging.debug(f"Prepared file for upload: {file_name}")

    try:
        # Send the request with all files in the dictionary
        response = requests.put(
            f"https://{os.environ['NADA_ENV']}/quarto/update/{os.environ['QUARTO_ID_HELSESJEKK']}",
            headers={"Authorization": f"Bearer {os.environ['QUARTO_TOKEN']}"},
            files=multipart_form_data,
        )
        response.raise_for_status()
        logging.info("Quarto update completed successfully.")
    except requests.RequestException as e:
        logging.error(f"Error updating Quarto document: {e}")
        raise


if __name__ == "__main__":
    logging.info("Starter kjøring av datafortellinger.")

    files = [
        "index",
        "datafortellinger/datakvalitet",
        # "datafortellinger/endret_prosess", //TODO: Legg inn i datakvalitet eller fjern helt
    ]

    resultatområder = [
        "norge",
        "agder",
        "innlandet",
        "møre_og_romsdal",
        "nordland",
        "oslo",
        "øst-viken",
        "rogaland",
        "troms_og_finnmark",
        "trøndelag",
        "vest-viken",
        "vestfold_og_telemark",
        "vestland",
    ]
    try:
        for file in files:
            render_quarto(file_to_render=file)

        for resultatområde in resultatområder:
            logging.info(f"Kjører quarto render for resultatområde: {resultatområde}")
            render_fia_per_resultatområde(resultatområde=resultatområde)
            render_ia_tjenester_per_resultatområde(resultatområde=resultatområde)
        update_quarto(output_dir="_site")
    except Exception as e:
        logging.error(f"Script feilet: {e}")
    logging.info("Oppdatering av datafortellinger ferdig")
