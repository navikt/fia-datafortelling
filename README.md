# fia-datafortelling

Datafortelling basert på data fra [Fia](https://github.com/navikt/lydia-api).

# Komme i gang (WiP)

### Pre requisites

Installer quarto ved å følge guiden [på quarto sine nettsider](https://quarto.org/docs/get-started/).

Installer [python3.12](https://www.python.org/downloads/).

Som en god praksis, opprett et virtuelt pythonmiljø i root til prosjektet:\
`python3.12 -m venv env`\
`source env/bin/activate`

Installer requirements med `pip3 install -r requirements.txt`.

# Komme i gang (Poetry)
## Installasjon

Poetry kan installeres via [homebrew](https://formulae.brew.sh/formula/poetry)
```bash
brew install poetry
```

Andre alternativer finnes også i Poetry sin [dokumentasjon](https://python-poetry.org/docs/#installation)

## Opprette virtuelt miljø i prosjektet
Anbefaler å konfigurere poetry til å lage virtuelt miljø i prosjektmappen så det ikke legges i cache, det gjør man ved å bruke kommandoen:

```bash
poetry config virtualenvs.in-project true
```

Deretter kan man opprette virtuelt miljø med kommandoen:

```bash
poetry install
```
Denne lager virtuelt miljø basert på `pyproject.toml`-filen i prosjektet.

For å få informasjon om hvilken python versjon som brukes og hvor den ligger (det virtuelle miljøet) kan du skrive: `poetry env info`

## Ta i bruk virtuelt miljø:


### Shell
For å åpne et shell i det virtuelle miljøet bruker du kommandoen:

```bash
poetry shell
```

Fra shell i virtuelt miljø kan du f.eks. kjøre tester med:
```bash
pytest
```

eller lage notebooks med:

```bash
jupyter notebook
```

For å komme deg ut av shell for det virtuelle miljøet bruker du:
```bash
exit
```


### Kjør fra Poetry
`Poetry run` lar deg også kjøre kommandoer i virtuelt miljø, f.eks:

```bash
poetry run python -V
```

Scripts definert under [`[tool.poetry.scripts]`](https://python-poetry.org/docs/cli/#run) i `pyproject.toml` kan også kjøres med 

```bash
poetry run my-script
```

## Administrere avhengigheter:

### Legge til
Avhengigheter kan legges til med:

```bash
poetry add numpy
```
Avhengigheter legges automatisk til i `pyproject.toml` med versjon lik `numpy = "^2.1.3"`. Det finnes flere alternativer [i dokumentasjonen](https://python-poetry.org/docs/cli/#add) som eksplisitt versjon med `poetry add numpy==2.1.3`

For å legge til dependency i en optional gruppe av avhengigheter som f.eks. dev eller testing kan man bruke:

```bash
poetry add --group test pytest
```
eller 

```bash
poetry add --group dev notebook
```

### Fjerne
Avhengigheter kan fjernes med:

```bash
poetry remove numpy
```

## Oppdatere avhengigheter
Man kan liste ut alle avhengigheter og nyeste tilgjengelige versjon:
```bash
poetry show --latest
```

for å oppdatere pakker innenfor constraints på versjonsnummer kan man bruke:
```bash
poetry update
```

For å oppdatere avhengighet og constraint bruker man:
```bash
poetry add jupyterlab@latest
```

For en full oversikt av alle avhengigheter kan man også bruke:
```bash
poetry show --tree
``` 

# Git pre-commit hooks

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
## Oversikt fra Pia-hub:
- Script for å finne pythonversjon brukt i
  dockerfil https://github.com/navikt/pia-hub/blob/main/scripts/pythonversions.sh
  - Oppdater pythonversjon om nødvendig
- Script for å finne utdaterte pythonpakker https://github.com/navikt/pia-hub/blob/main/scripts/pythonpackageversions.sh
  - Oppdater requirements.txt om nødvendig

## Manuelt:
- Oppdater python:
  - Sjekk versjon i Dockerfile opp mot Python sin siste versjon [her](https://www.python.org/downloads/).
  - Dersom kom ny versjon, lag et lokalt virtual miljø på nytt.
- Oppdater python pakker:
  - `pip3 install --upgrade pip`
  - `pip3 install --upgrade <pakke>`
  - Oppdater `requirements.txt` manuelt (eller bruk `pip3 freeze > requirements.txt`)
  - Kjør datafortellingene lokalt på nytt og sammenlign med prod

---

# Linting & formatering
Bruker [Ruff](https://docs.astral.sh/ruff/) som skal ha "drop-in parity" med flake8, isort og Black

Kjør linting med:
```bash
ruff check --fix
```

Formater prosjekt med:
```bash
ruff format
```

# Henvendelser

Spørsmål knyttet til koden eller prosjektet kan stilles som et [issue her på GitHub](https://github.com/navikt/ia-datafortelling/issues).

## For NAV-ansatte

Interne henvendelser kan sendes via Slack i kanalen #team-pia.

## Kode generert av GitHub Copilot

Dette repoet bruker GitHub Copilot til å generere kode.