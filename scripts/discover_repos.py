import argparse
import json
import os
from datetime import datetime, timezone

import requests


def _build_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def _fetch_repos_page(org_name, page, headers):
    url = f"https://api.github.com/orgs/{org_name}/repos"
    params = {
        "type": "public",
        "sort": "stars",
        "direction": "desc",
        "per_page": 100
    }
    
    print(f"Buscando repositorios para la organización: {org_name} (Top {max_repos} por popularidad)")
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    repos = response.json()
    
    top_repos = []
    
    for repo in repos:
        top_repos.append({
            "nombre": repo["name"],
            "url": repo["clone_url"],
            "ultima_actualizacion": repo["pushed_at"],
            "estrellas": repo["stargazers_count"]
        })
        if len(top_repos) >= max_repos:
            break
                
    # Asegurarnos de que el directorio data exista en la raíz del proyecto
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(root_dir, "data")
    datasets_dir = os.path.join(data_dir, "datasets")

    os.makedirs(data_dir, exist_ok=True)
    
    output_path = os.path.join(data_dir, "repos.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(top_repos, f, indent=4, ensure_ascii=False)
        
    print(f"Se encontraron y guardaron los {len(top_repos)} repositorios más populares en data/repos.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descubre repositorios de una organización en GitHub por popularidad."
    )
    parser.add_argument(
        "organizacion", help="Nombre de la organización de GitHub (ej. FlowiseAI)"
    )
    parser.add_argument("--limit", type=int, default=5, help="Límite de repositorios")
    parser.add_argument(
        "--include-forks",
        action="store_true",
        help="Incluye repositorios que son forks",
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        help="Incluye repositorios archivados",
    )
    args = parser.parse_args()

    repos = discover_repos(
        args.organizacion,
        max_repos=args.limit,
        include_forks=args.include_forks,
        include_archived=args.include_archived,
    )
    write_outputs(
        args.organizacion,
        args.limit,
        repos,
        include_forks=args.include_forks,
        include_archived=args.include_archived,
    )
