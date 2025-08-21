# Fia datafortelling
## Beskrivelse
Datafortelling basert på data fra fagsystemet [Fia](https://github.com/navikt/lydia-api).
Prosjektet bygges med github [workflow](https://docs.github.com/en/actions/writing-workflows/about-workflows) og deployes til NAIS som en [NAIS job](https://docs.nais.io/workloads/job/).

## Innhold
- [Oppsett](#oppsett)
	- [Installer Quarto](#installer-quarto)
	- [Installer uv](#installer-uv)
	- [Sett opp virtuelt miljø](#sett-opp-virtuelt-miljø)
	- [Git pre-commit hooks](#git-pre-commit-hooks)
- [Kjør prosjektet](#kjør-prosjektet)
- [Vedlikehold og videreutvikling](#vedlikehold-og-videreutvikling)
	- [Oppdatering av avhengigheter](#oppdatering-av-avhengigheter)
- [Henvendelser](#henvendelser)
- [Krediteringer](#krediteringer)
----

# Oppsett
Dette prosjektet bruker Quarto for å generere html filer for datafortellingene.

Som prosjekt- og avhengighetsmanager bruker vi [uv](https://docs.astral.sh/uv/).

## Installer Quarto
Installer Quarto ved å følge guiden [på quarto sine nettsider](https://quarto.org/docs/get-started/).

## Installer uv
[uv](https://docs.astral.sh/uv/) kan installeres med:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

evt med andre måter som forklart [på uv sine nettsider](https://docs.astral.sh/uv/getting-started/installation/#homebrew).

Om ønskelig kan uv også installere og [håndtere forskjellige Python versjoner for deg](https://docs.astral.sh/uv/guides/install-python/).

## Sett opp virtuelt miljø
Avhengigheter og oppsettet av prosjektet er definert i [pyproject.toml](pyproject.toml), denne og [uv.lock](uv.lock) brukes av uv for å lage det i virtuelle miljøet.

For å opprette det virtuelle miljøet og installere avhengighetene, kjør:
```bash
uv sync
```
output fra disse sier også hvor det virtuelle miljøet legges (default i en .venv mappe i roten av prosjektet), hvilken Python interpreter som ble brukt og versjonen av Python.

## Git pre-commit hooks
Installer git pre-commit hooks med
```bash
uv run pre-commit install
```

# Kjør prosjektet
Datafortellingene renderes og lastes opp til NADA med [main.py](main.py). Ferdig rendret filer blir lagt i mappen `pages` og lastes opp til NADA av scriptet.
1. Logg på Google Cloud CLI `nais login`
2. Kjør `uv run main.py` for å rendere alle datafortellingene. Kjører du scriptet lokalt på maskinen vil det feile ved opplastning, men det er uproblematisk.
3. Åpne output filen i [index.html](pages/index.html) i en nettleser.

## Bygg datafortellinger i docker lokalt
For å teste at datafortellingen kjører i docker lokalt må man supplere docker-imaget med en Application Default Credentials (ADC) fil. Denne genererer man på forhånd og limer inn i variabelen `ADC` i scriptet.

1. Sett riktig prosjekt for gcloud
```bash
gcloud config set project <PROSJEKT>
```

2. Generer ADC
```bash
gcloud auth application-default login
```

3. eksporter path til `ADC` (output fra kommando over)
```bash
export ADC=path/til/adc.json
```

4. Kjør docker imaget, med ADC filen som et volume. -e `LOCAL=1` Gjør så python scriptet main.py ikke laster opp til NADA.
```bash
docker run -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/adc.json -v $ADC:/tmp/keys/adc.json:ro datafortelling
```

## Kjør kun én datafortelling
For å rendere en individuell quarto fil kan man kjøre f.eks:
```bash
source .venv/bin/activate
quarto render datafortelling/sak/norge.qmd
```

Eller ved å bruke uv for å aktivere miljøet:
```bash
uv run quarto render datafortelling/sak/norge.qmd
```

## Kjør NAIS job manuelt
Prosjektet bygges med github [workflow](https://docs.github.com/en/actions/writing-workflows/about-workflows) og deployes til NAIS som en [NAIS job](https://docs.nais.io/workloads/job/).

Jobben kjører daglige, i intervaller som er definert i cron-utrykket `spec.schedule` i [nais.yaml](.nais/nais.yaml). Når jobben spinner opp kjører den [main.py](main.py).

Velg "Trigger run" fra [NAIS console](https://console.nav.cloud.nais.io/team/pia/prod-gcp/job/fia-datafortelling) og gi gjenkjennelig navn, feks: "ad-hoc".

# Vedlikehold og videreutvikling

## Oppdatering av avhengigheter
1. Se etter utdaterte avhengigheter med: `uv tree --outdated --depth 1` 
2. Oppdater disse avhengighetene i [pyproject.toml](pyproject.toml) til nyeste versjon.
3. Kjør `uv sync --upgrade` for å oppdatere lock-filen og installere de nye avhengighetene, dette oppdaterer også indirekte avhengigheter. Man kan se alle med `uv tree --outdated`
4. Kjør datafortellingene for å sjekke at de fortsatt fungerer som forventet.

## Oppdatering av Python
Ved oppdatering av Python må versjonstallet oppdateres flere steder. Python sin siste versjon finner du [her](https://www.python.org/downloads/).

Om du vil oppdatere versjonen av python bør den oppdateres i:
1. [.python-version](.python-version) (Hvilken python versjon som vil bli brukt av uv og må oppdateres ved versjonsendring)
2. Versjonen som brukes i [Dockerfile](Dockerfile) bør være det samme som i [.python-version](.python-version)
3. Om versjonsnummeret endres til noe som er utenfor kravet i [pyproject.toml](pyproject.toml) må det også oppdateres.
4. Kjør `uv lock --check` for å sjekke om lock-filen er oppdatert, om ikke vil `uv sync`oppdatere den.

## Linting og formatering
Dette prosjektet bruker [ruff](https://docs.astral.sh/ruff/) som [linter](https://docs.astral.sh/ruff/linter/) og [formaterer](https://docs.astral.sh/ruff/formatter/) koden. For å kjøre ruff kan du bruke:
```bash
ruff check
```
for linting, og

```bash
ruff format
```

for å formatere koden.


# Henvendelser
Spørsmål knyttet til koden eller prosjektet kan stilles som et [issue her på GitHub](https://github.com/navikt/fia-datafortelling/issues).
## For NAV-ansatte
Interne henvendelser kan sendes via Slack i kanalen #team-pia.

# Krediteringer
## Kode generert av GitHub Copilot
Dette repoet bruker GitHub Copilot til å generere kode.
