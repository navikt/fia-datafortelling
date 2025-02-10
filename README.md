# Fia datafortelling
## Beskrivelse
Datafortelling basert på data fra fagsystemet [Fia](https://github.com/navikt/lydia-api).
Prosjektet bygges med github [workflow](https://docs.github.com/en/actions/writing-workflows/about-workflows) og deployes til NAIS som en [NAIS job](https://docs.nais.io/workloads/job/).

## Innhold
- [Oppsett](#oppsett)
	- [Hvordan installere](#hvordan-installere-prosjektet)
- [Kjør prosjektet](#kjør-prosjektet)
- [Vedlikehold og videreutvikling](#vedlikehold-og-videreutvikling)
	- [Oppdatering av avhengigheter](#oppdatering-av-avhengigheter)
- [Henvendelser](#henvendelser)
- [Krediteringer](#krediteringer)
----

# Oppsett
## Installer Quarto
Installer Quarto CLI ved å følge guiden [på quarto sine nettsider](https://quarto.org/docs/get-started/).
## Installer uv
[uv](https://docs.astral.sh/uv/) kan installeres med:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

evt med andre måter som forklart [på uv sine nettsider](https://docs.astral.sh/uv/getting-started/installation/#homebrew).

Om ønskelig kan uv også installere og håndtere forskjellige Python versjoner [for deg](https://docs.astral.sh/uv/guides/install-python/)

## Sett opp virtuelt miljø
Avhengigheter og oppsettet av prosjektet er definert i [pyproject.toml](pyproject.toml), denne og [uv.lock](uv.lock) brukes av uv for å lage det i virtuelle miljøet.

```bash
uv sync
```

For å ikke oppdatere lock-filen kan du alternativt bruke:
```bash
uv sync --frozen
```

output fra disse sier også hvor det virtuelle miljøet legges (default i en .venv mappe i roten av prosjektet)

## Aktiver virtuelt miljø
For å aktivere det virtuelle miljøet bruker du:
```bash
source .venv/bin/activate
```
det er aktivt når du ser navnet på det virtuelle miljøet i parantes i terminalvinduet:
```
fia-datafortelling~$ source .venv/bin/activate
(src) fia-datafortelling~$
```

## Git pre-commit hooks
Installer git pre-commit hooks med
```bash
uv run pre-commit install
```

# Kjør prosjektet
## Logg på Google Cloud CLI {#gcloud}
Logg inn med:
```bash
gcloud auth login --update-adc
```
eller:
```bash
nais login
```

## Kjør én datafortelling
> [!Tip]
> Pass på å aktivere det virtuelle miljøet før du kjører `quarto render` eller
> `quarto preview` da det avhenger av avhengighetene.

For å få en forhåndsvisning som endrer seg når du oppdaterer .qmd filen bør du bruke f.eks:
```bash
quarto preview src/index.qmd
```

For å bygge en ferdig html fil av en datafortelling kan du bruke:

```bash
quarto render src/<datafortelling>.qmd
```

Noen datafortellinger er avhengige av miljøvariabler, de kan settes og kjøres med:

```bash
export RESULTATOMRADE="<resultatområde>" && quarto preview src/datafortelling_per_resultatområde.qmd
```

## Script for å bygge alle datafortellinger
Datafortellingene renderes og lastes opp til NADA med [main.py](main.py). Ferdig rendret filer eksporteres til mappen `_site` og lastes opp til NADA. Om du ønsker kan du kontrollere at alt ser bra ut før du laster opp til NADA ved å kjøre:

```bash
uv run main.py
```
Og åpne [index.html](_site/index.html) i en nettleser.

> [!Tip]
> TODO: Lokal kjøring med flagg for å unngå å laste opp til Nada

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

## Kjør NAIS job manuelt
Prosjektet bygges med github [workflow](https://docs.github.com/en/actions/writing-workflows/about-workflows) og deployes til NAIS som en [NAIS job](https://docs.nais.io/workloads/job/).

Jobben kjører i intervaller som er definert i cron-utrykket `spec.schedule` i [nais.yaml](.nais/nais.yaml). Når jobben spinner opp kjører den [run.sh](run.sh).

### Fra NAIS console

Velg "Trigger run" fra [NAIS console](https://console.nav.cloud.nais.io/team/pia/prod-gcp/job/fia-datafortelling) og gi gjenkjennelig navn, feks: "ad-hoc".

### Manuell kjøring

For å kjøre Jobben manuelt (utenfor intervallet som kjører automatisk):

1. Logge på nais:
```bash
nais login
```
2. Sett namespace til pia:
```bash
kubens pia
```
3. Sett cluster til prod-gcp: ``
```bash
kubectx prod-gcp
```
4. Kjør NAIS jobben manuelt med:
```bash
kubectl create job --from=cronjob/fia-datafortelling fia-datafortelling-ad-hoc
```

> [!tip]
> Om du vil finne cronjobben finner man den med: `kubectl get cronjobs | grep fia-datafortelling`

# Vedlikehold og videreutvikling

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

## Oppdatering av Python
Ved oppdatering av Python må versjonen oppdateres flere steder. Python sin siste versjon finner du [her](https://www.python.org/downloads/).

Om du vil oppdatere versjonen av python bør den oppdateres i:
1. [.python-version](.python-version) (Hvilken python versjon som vil bli brukt av uv og må oppdateres ved versjonsendring)
2. Versjonen som brukes i [Dockerfile](Dockerfile) bør være det samme som i [.python-version](.python-version)
3. Om versjonsnummeret endres til noe som er utenfor kravet i [pyproject.toml](pyproject.toml) må det også oppdateres.
4. Kjør `uv lock --check` for å sjekke om lock-filen er oppdatert, om ikke vil `uv sync`oppdatere den.

## Oppdatering av avhengigheter

Akkurat nå *(Sist oppdatert 15.01.2025)* er det ikke veldig lett å se hvilke avhengigheter det finnes oppdateringer innebygd i uv. Man kan oppdatere lock filen innenfor begrensningene satt i [pyproject.toml](pyproject.toml) ved å bruke `uv lock --upgrade`.

En mulig bedre måte å oppdatere avhengigheter er å pinne alle versjoner i [pyproject.toml](pyproject.toml), feks:
```
dependencies = [
    "pandas==2.2.3",
    "plotly==5.23.0",
]
```
Da kan man se hvilke avhengigheter det finnes oppdateringer til ved å bruke:
```bash
uv pip list --outdated
```
Endre pinned versjon i [pyproject.toml](pyproject.toml) til ny versjon og bruke:
```bash
uv sync
```
til å oppdatere versjonen.

> [!Tip]
> Om `uv pip list --outdated` viser en indirekte avhengighet som ikke ligger i pyproject.toml (men er i `uv tree`) bør disse kunne oppgraderes med `uv lock --upgrade`

Dependabot støtter desverre ikke uv.lock-filen enda, men det er planlagt [for første kvartal (Jan - Mar, 2025)](https://github.com/dependabot/dependabot-core/issues/10478)

# Henvendelser
Spørsmål knyttet til koden eller prosjektet kan stilles som et [issue her på GitHub](https://github.com/navikt/fia-datafortelling/issues).
## For NAV-ansatte
Interne henvendelser kan sendes via Slack i kanalen #team-pia.
# Krediteringer
## Kartdata
Data brukt for kommunesgrenser i `src/data/Kommuner-s.geojson` er basert på [dette repoet](https://github.com/robhop/fylker-og-kommuner)
## Kommunedata
Data brukt for kommuneinndelinger er basert på [kartverkets data](https://www.kartverket.no/til-lands/fakta-om-norge/norske-fylke-og-kommunar)
## Kode generert av GitHub Copilot
Dette repoet bruker GitHub Copilot til å generere kode.
