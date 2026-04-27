import requests
import json
import os
from datetime import datetime, timedelta

def discover_repos(org_name, max_repos=50, days_active=30):
    url = f"https://api.github.com/orgs/{org_name}/repos"
    
    # Agregar token si existe en variables de entorno para tener mayor límite de peticiones
    headers = {"Accept": "application/vnd.github.v3+json"}
    if "GITHUB_TOKEN" in os.environ:
        headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"
        
    params = {
        "type": "public",
        "sort": "updated",
        "direction": "desc",
        "per_page": 100
    }
    
    print(f"Buscando repositorios para la organización: {org_name}")
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    repos = response.json()
    
    active_repos = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_active)
    
    for repo in repos:
        pushed_at = datetime.strptime(repo["pushed_at"], "%Y-%m-%dT%H:%M:%SZ")
        if pushed_at >= cutoff_date:
            active_repos.append({
                "nombre": repo["name"],
                "url": repo["clone_url"],
                "ultima_actualizacion": repo["pushed_at"]
            })
            if len(active_repos) >= max_repos:
                break
                
    # Asegurarnos de que el directorio data exista en la raíz del proyecto
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(root_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    output_path = os.path.join(data_dir, "repos.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(active_repos, f, indent=4, ensure_ascii=False)
        
    print(f"Se encontraron y guardaron {len(active_repos)} repositorios activos en data/repos.json")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Descubre repositorios activos de una organización en GitHub.")
    parser.add_argument("organizacion", help="Nombre de la organización de GitHub (ej. Netflix)")
    parser.add_argument("--limit", type=int, default=50, help="Límite de repositorios a buscar")
    args = parser.parse_args()
    
    discover_repos(args.organizacion, max_repos=args.limit)
