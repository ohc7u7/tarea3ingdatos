# Security Data Engineering - Análisis Automatizado

Este pipeline descubre, clona y analiza repositorios activos de una organización usando Syft (SBOM), Grype (SCA) y CodeQL (SAST). El análisis cuantitativo final se presenta cruzando los datos en un Jupyter Notebook.

> **Nota sobre el límite de Repositorios (50 vs 5):**
> Por requerimientos, el script `discover_repos.py` escanea un máximo de **50 repositorios** por defecto. Para fines de demostración rápida y para asegurar que la descarga de las bases de datos de vulnerabilidades (Grype) o CodeQL no colapsen por tiempo, puedes añadir el flag `--limit 5` para acotar la búsqueda a 5 repos.

## Comandos de Ejecución Resumidos

Todo el proceso está dockerizado.

```bash
# 1. Levantar e ingresar al entorno de Docker
docker-compose run --rm security-app bash

# 2. Descubrir repositorios activos (usando límite de 5 para la demostración)
python scripts/discover_repos.py Netflix --limit 5

# 3. Clonar los repositorios como submódulos
python scripts/add_submodules.py

# 4. Ejecutar el escaneo completo (SBOM, SCA, SAST)
# *Nota: Si Grype se queda pegado en "Vulnerability DB", presiona Ctrl+C, ejecuta "grype db update" y repite este paso.
python scripts/generate_all.py

# 5. Salir de la terminal interactiva del Docker
exit
```

## Análisis Cuantitativo en Jupyter

Para explorar gráficamente los hallazgos:

```bash
docker-compose up
```

Copia la ruta de la terminal (similar a `http://127.0.0.1:8888/?token=...`), pégalo en el navegador web, abre `nbs/analysis.ipynb` y dale a "Run All" (Ejecutar todo).
