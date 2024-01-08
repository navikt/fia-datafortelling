# fia-datafortelling

Datafortelling basert på data fra [Fia](https://github.com/navikt/lydia-api).

# Komme i gang (WiP)

### Pre requisites

Installer quarto ved å følge guiden [på quarto sine nettsider](https://quarto.org/docs/get-started/).

Installer [python3.11](https://www.python.org/downloads/).

Som en god praksis, opprett et virtuelt pythonmiljø i root til prosjektet:\
`python3.11 -m venv env`\
`source env/bin/activate`

Installer requirements med `pip3 install -r requirements.txt`.

### Git pre-commit hooks

Installer pre-commit pakke med `pip3 install pre-commit`.

Installer git hook-skriptene med `pre-commit install`.

### Lokal utvikling

Logg inn i gcp med `gcloud auth login --update-adc`.

Kjør opp datafortellingene lokalt med følgende kommandoer:

`export GCP_PROJECT=<prosjekt> && export DATASET=<dataset> && quarto render <datafortelling>.qmd`

`export RESULTATOMRADE="<resultatområde>" && export GCP_PROJECT=<prosjekt> && export DATASET=<dataset> && quarto render datafortelling_per_resultatområde.qmd --output "datafortelling_per_resultatområde_$RESULTATOMRADE.html"`

### Bygg docker image på M1:

`docker build . --platform=linux/amd64`

# Bygg og deploy

Bygges med github [workflow](.github/workflows/deploy.yml) og deployes til nais som en [naisjob](.nais/nais.yaml).

Jobben kjører i intervaller som er definert i cron-utrykket `spec.schedule` i [nais.yaml](.nais/nais.yaml).

Naisjobben spinner opp quarto (render html) og oppdaterer datafortellingen.
Dette er definert i [run.sh](run.sh).

# Ad hoc kjøring

For å regenerere datafortellingen manuelt, gjør følgende:

- Logg inn i gcp med `gcloud auth login --update-adc`
- Gå til cluster prod-gcp i kubectl `kubectx prod-gcp`
- Sett namespace til pia `kubens pia`
- Finn cronjobben for datafortellingen ( `kubectl get cronjobs | grep fia-datafortelling` )
- Kjør jobben manuelt ( `kubectl create job --from=cronjob/fia-datafortelling fia-datafortelling-ad-hoc` )

# Oppdater avhengigheter

- Oppdater python:
  - Sjekk versjon i Dockerfile opp mot Python sin siste versjon [her](https://www.python.org/downloads/).
  - Dersom kom ny versjon, lag et lokalt virtual miljø på nytt.
- Oppdater python pakker:
  - `pip3 install --upgrade pip`
  - `pip3 install --upgrade <pakke>`
  - Oppdater `requirements.txt` manuelt (eller bruk `pip3 freeze > requirements.txt`)
  - Kjør datafortellingene lokalt på nytt og sammenlign med prod

---

# Henvendelser

Spørsmål knyttet til koden eller prosjektet kan stilles som issues her på GitHub.

## For NAV-ansatte

Interne henvendelser kan sendes via Slack i kanalen #team-pia.

## Kode generert av GitHub Copilot

Dette repoet bruker GitHub Copilot til å generere kode.
