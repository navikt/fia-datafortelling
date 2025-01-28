import logging
import os
import subprocess

import requests

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def render_quarto(file_to_render: str):
    try:
        logging.info(
            f"Starting Quarto render process, rendering file: {file_to_render}"
        )
        # Run the quarto render command
        result = subprocess.run(
            ["quarto", "render", file_to_render + ".qmd"],
            check=True,
            capture_output=True,
            text=True,
        )
        logging.debug(f"Quarto render output: {result.stdout} \n {result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error rendering Quarto document: {e.stderr}")
        raise


def render_resultatområder(resultatområde: str):
    try:
        logging.info(f"Starting Quarto render process, rendering {resultatområde}")
        result = subprocess.run(
            [
                "quarto",
                "render",
                f"resultatområder/{resultatområde}.qmd",
                "-P",
                f"resultatområde:{resultatområde}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        logging.debug(f"Quarto render output: {result.stdout} \n {result.stderr}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error rendering Quarto document: {e.stderr}")
        raise


def update_quarto(files_to_upload: list[str]):
    logging.info("Starting Quarto update process.")
    multipart_form_data = {}
    for file_path in files_to_upload:
        file_name = os.path.basename(file_path + ".html")
        with open(file_path, "rb") as file:
            # Read the file contents and store them in the dictionary
            file_contents = file.read()
            multipart_form_data[file_name] = (file_name, file_contents)
            logging.debug(f"Prepared file for upload: {file_name}")

    try:
        # Send the request with all files in the dictionary
        response = requests.put(
            f"https://{os.environ['ENV']}/quarto/update/{os.environ['QUARTO_ID']}",
            headers={"Authorization": f"Bearer {os.environ['NADA_TOKEN']}"},
            files=multipart_form_data,
        )
        response.raise_for_status()
        logging.info("Quarto update completed successfully.")
    except requests.RequestException as e:
        logging.error(f"Error updating Quarto document: {e}")
        raise


if __name__ == "__main__":
    logging.info("Script started.")
    files = ["index", "ia_tjenester", "datakvalitet"]
    resultatområder = [
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
            render_resultatområder(resultatområde=resultatområde)

        logging.debug("Reading files in _site")
        for root, dirs, files in os.walk("_site"):
            for file in files:
                logging.debug(f"File: {os.path.join(root, file)}")

        # update_quarto(files_to_upload=["_site/index.html"])
    except Exception as e:
        logging.error(f"Script failed: {e}")
    logging.info("Script finished.")
