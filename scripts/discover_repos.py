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
        "per_page": 100,
        "page": page,
    }
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _to_repo_record(repo, rank):
    return {
        "rank": rank,
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "html_url": repo.get("html_url"),
        "clone_url": repo.get("clone_url"),
        "stargazers_count": repo.get("stargazers_count", 0),
        "forks_count": repo.get("forks_count", 0),
        "watchers_count": repo.get("watchers_count", 0),
        "open_issues_count": repo.get("open_issues_count", 0),
        "language": repo.get("language"),
        "archived": repo.get("archived", False),
        "fork": repo.get("fork", False),
        "pushed_at": repo.get("pushed_at"),
        "created_at": repo.get("created_at"),
        "updated_at": repo.get("updated_at"),
        # Campos legacy para mantener compatibilidad con add_submodules.py
        "nombre": repo.get("name"),
        "url": repo.get("clone_url"),
        "ultima_actualizacion": repo.get("pushed_at"),
    }


def discover_repos(org_name, max_repos=5, include_forks=False, include_archived=False):
    print(
        "Buscando repositorios para la organización: "
        f"{org_name} (Top {max_repos} por popularidad)"
    )

    headers = _build_headers()
    candidates = []
    page = 1

    while True:
        repos_page = _fetch_repos_page(org_name, page, headers)
        if not repos_page:
            break

        for repo in repos_page:
            if not include_forks and repo.get("fork", False):
                continue
            if not include_archived and repo.get("archived", False):
                continue
            candidates.append(repo)

        page += 1

    ranked = sorted(
        candidates,
        key=lambda repo: (
            repo.get("stargazers_count", 0),
            repo.get("forks_count", 0),
            repo.get("watchers_count", 0),
        ),
        reverse=True,
    )

    selected = []
    for index, repo in enumerate(ranked[:max_repos], start=1):
        selected.append(_to_repo_record(repo, index))

    return selected


def write_outputs(org_name, max_repos, repos, include_forks=False, include_archived=False):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(root_dir, "data")
    datasets_dir = os.path.join(data_dir, "datasets")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(datasets_dir, exist_ok=True)

    repos_output_path = os.path.join(data_dir, "repos.json")
    dataset_output_path = os.path.join(datasets_dir, "security_dataset.json")

    with open(repos_output_path, "w", encoding="utf-8") as repos_file:
        json.dump(repos, repos_file, indent=2, ensure_ascii=False)

    dataset = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "organization": org_name,
            "selection_criteria": {
                "sort_by": "stargazers_count",
                "direction": "desc",
                "exclude_archived": not include_archived,
                "exclude_forks": not include_forks,
                "repo_limit": max_repos,
            },
            "repository_count": len(repos),
        },
        "repos": repos,
    }

    with open(dataset_output_path, "w", encoding="utf-8") as dataset_file:
        json.dump(dataset, dataset_file, indent=2, ensure_ascii=False)

    print(f"Repositorios seleccionados: {len(repos)}")
    print(f"Salida para pipeline: {repos_output_path}")
    print(f"Dataset estructurado: {dataset_output_path}")


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
