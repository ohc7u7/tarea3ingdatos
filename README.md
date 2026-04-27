# Security Data Engineering - Análisis Automatizado

Este pipeline descubre, clona y analiza repositorios activos de una organización usando Syft (SBOM), Grype (SCA) y CodeQL (SAST). El análisis cuantitativo final se presenta cruzando los datos en un Jupyter Notebook.

> **Nota sobre el límite de Repositorios (50 vs 5):**
> Por requerimientos, el script `discover_repos.py` escanea un máximo de **50 repositorios** por defecto. Para fines de demostración rápida y para asegurar que la descarga de las bases de datos de vulnerabilidades (Grype) o CodeQL no colapsen por tiempo, puedes añadir el flag `--limit 5` para acotar la búsqueda a 5 repos.

## Ejecución 

Todo el proceso está dockerizado en un solo contenedor. Con este comando se ejecuta el pipeline completo (descubrimiento, submódulos, SBOM/SCA/SAST) y al finalizar queda abierto Jupyter Notebook:

```bash
docker compose up --build
```

Luego copia la URL de la terminal (similar a `http://127.0.0.1:8888/?token=...`) y abre `nbs/analysis.ipynb`.

## Variables de configuración (.env)

Puedes copiar `.env.example` como `.env` y ajustar:

- `GITHUB_TOKEN`: token de GitHub para aumentar límite de API.
- `ORG_NAME`: organización a analizar (default `Netflix`).
- `REPO_LIMIT`: número máximo de repositorios (default `5`).
- `DAYS_ACTIVE`: ventana de actividad en días (default `30`).
- `SKIP_IF_RESULTS_EXIST`: si vale `1`, salta el pipeline si detecta `data/results/.pipeline_completed`.

## Ejecución manual opcional

Si quieres correr scripts individualmente:

```bash
docker compose run --rm security-app bash
python scripts/discover_repos.py Netflix --limit 5 --days-active 30
python scripts/add_submodules.py
python scripts/generate_all.py
```
