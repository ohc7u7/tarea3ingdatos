# Security Data Engineering - Analisis Automatizado

Este pipeline descubre, clona y analiza repositorios de una organizacion de GitHub usando Syft (SBOM), Grype (SCA) y CodeQL (SAST). El analisis final se realiza en `nbs/analysis.ipynb`.

## Justificacion de organizacion

La elección de Flowise se justifica por su alta relevancia y creciente adopción como plataforma líder de código abierto para el desarrollo de Inteligencia Artificial. Además, la existencia de una vulnerabilidad de impacto crítico, como la ejecución remota de código (RCE) de nivel máximo, demuestra un riesgo severo de compromiso total en instancias expuestas. Este escenario representa un caso de estudio ideal para aplicar un análisis SBOM, ya que permite rastrear y auditar eficazmente las complejas dependencias subyacentes que introducen este tipo de fallos.

## Seleccion de repositorios

El script `scripts/discover_repos.py` selecciona el top de repositorios mas populares de la organizacion usando API de GitHub y ranking por:

1. `stargazers_count`
2. `forks_count`
3. `watchers_count`

Por defecto:

- excluye repositorios `fork`
- excluye repositorios `archived`
- limita a los 5 repositorios mas populares

Salidas generadas:

- `data/repos.json`: lista para el pipeline de clonacion/analisis
- `data/datasets/security_dataset.json`: dataset estructurado en JSON para comparacion de repositorios

## Ejecucion

Todo el proceso esta dockerizado en un solo contenedor. Con este comando se ejecuta el pipeline completo (descubrimiento, submodulos, SBOM/SCA/SAST) y al finalizar queda abierto Jupyter Notebook:

```bash
docker compose up --build
```

Luego copia la URL de la terminal (similar a `http://127.0.0.1:8888/?token=...`) y abre `nbs/analysis.ipynb`.

## Variables de configuracion (.env)

Puedes copiar `.env.example` como `.env` y ajustar:

- `GITHUB_TOKEN`: token de GitHub para aumentar limite de API.
- `ORG_NAME`: organizacion a analizar (default `FlowiseAI`).
- `REPO_LIMIT`: numero maximo de repositorios (default `5`).
- `SKIP_IF_RESULTS_EXIST`: si vale `1`, salta el pipeline si detecta `data/results/.pipeline_completed`.

## Ejecucion manual opcional

Si quieres correr scripts individualmente:

```bash
docker compose run --rm security-app bash
python scripts/discover_repos.py FlowiseAI --limit 5
python scripts/add_submodules.py
python scripts/generate_all.py
```
