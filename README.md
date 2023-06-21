fia-datafortelling
================

Datafortelling basert på data fra [Fia](https://github.com/navikt/lydia-api).

# Komme i gang (WiP)

### Pre requisites

Installer quarto ved å følge guiden [på quarto sine nettsider](https://quarto.org/docs/get-started/).

Installer [python3.11](https://www.python.org/downloads/).

Som en god praksis, opprett et virtuelt pythonmiljø i root til prosjektet:\
`python3.11 -m venv env`\
`source env/bin/activate`

Installer requirements `pip3 install -r requirements.txt`.

Installer [black](https://pypi.org/project/black/), en python-kode formatter, med `pip install black`.

(noe mer?)

### Lokal utvikling

Logg inn i gcp med `gcloud auth login --update-adc`.

Kjør opp quarto i preview mode med følgende kommando:

`export GCP_PROJECT=<prosjekt> && export DATASET=<dataset> && quarto preview <datafortelling>.qmd`

hvor datafortelling feks kan være `main`.

### Bygg docker image på M1:

`docker build . --platform=linux/amd64`


# Bygg og deploy

Bygges med github [workflow](.github/workflows/deploy.yml) og deployes til nais som en [naisjob](.nais/nais.yaml).

Jobben kjører i intervaller som er definert i cron-utrykket `spec.schedule` i [nais.yaml](.nais/nais.yaml).

Naisjobben spinner opp quarto (render html) og oppdaterer datafortellingen.
Dette er definert i [run.sh](run.sh).

# Oppdater avhengigheter

- Oppdater python:
    - Sjekk versjon i Dockerfile opp mot Python sin siste versjon [her](https://www.python.org/downloads/)
    - Dersom kom ny versjon, lag et lokal virtual miljø på nytt
- Oppdater python pakker:
    - pip3 install --upgrade pip
    - pip3 install <pakke>
    - pip3 freeze > requirements.txt
    - rydd opp i requirements.txt
    - kjør datafortellingene lokalt på nytt og sammenlign med prod

---

# Henvendelser

Spørsmål knyttet til koden eller prosjektet kan stilles som issues her på GitHub.


## For NAV-ansatte

Interne henvendelser kan sendes via Slack i kanalen #team-pia.
