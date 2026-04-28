import json
import os
import shutil
import subprocess


def _normalize_path(path):
    return path.replace("\\", "/")


def _ensure_git_repo(root_dir):
    if not os.path.exists(os.path.join(root_dir, ".git")):
        print("Inicializando repositorio git principal en la raiz...")
        subprocess.run(["git", "init"], cwd=root_dir, check=True)


def _load_repos(json_path):
    if not os.path.exists(json_path):
        print(f"Error: No se encontro el archivo {json_path}")
        print("Asegurate de ejecutar discover_repos.py primero.")
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_existing_submodules(root_dir):
    gitmodules_path = os.path.join(root_dir, ".gitmodules")
    if not os.path.exists(gitmodules_path):
        return {}

    result = subprocess.run(
        ["git", "config", "--file", gitmodules_path, "--get-regexp", r"^submodule\..*\.path$"],
        cwd=root_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {}

    submodules = {}
    for line in result.stdout.strip().splitlines():
        key, path = line.split(None, 1)
        name = key[len("submodule.") : -len(".path")]
        url_result = subprocess.run(
            ["git", "config", "--file", gitmodules_path, "--get", f"submodule.{name}.url"],
            cwd=root_dir,
            capture_output=True,
            text=True,
        )
        url = url_result.stdout.strip() if url_result.returncode == 0 else None
        submodules[_normalize_path(path.strip())] = {"name": name, "url": url}

    return submodules


def _remove_submodule(root_dir, path):
    print(f"Eliminando submodulo fuera de la lista: {path}")
    subprocess.run(["git", "submodule", "deinit", "-f", "--", path], cwd=root_dir, check=False)

    rm_result = subprocess.run(["git", "rm", "-f", "--", path], cwd=root_dir, capture_output=True, text=True)
    if rm_result.returncode != 0:
        print(f"Aviso: git rm fallo para {path}, se limpiara manualmente.")
        if rm_result.stderr:
            print(rm_result.stderr.strip())

    if os.path.exists(os.path.join(root_dir, path)):
        shutil.rmtree(os.path.join(root_dir, path), ignore_errors=True)

    modules_dir = os.path.join(root_dir, ".git", "modules", *path.split("/"))
    if os.path.exists(modules_dir):
        shutil.rmtree(modules_dir, ignore_errors=True)


def add_submodules():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_path = os.path.join(root_dir, "data", "repos.json")
    repos_dir = os.path.join(root_dir, "data", "repos")

    repos = _load_repos(json_path)
    if repos is None:
        return

    os.makedirs(repos_dir, exist_ok=True)

    _ensure_git_repo(root_dir)

    desired = {}
    for repo in repos:
        nombre = repo.get("nombre") or repo.get("name")
        url = repo.get("url") or repo.get("clone_url")

        if not nombre or not url:
            print(f"Saltando registro invalido en repos.json: {repo}")
            continue
        desired[nombre] = url

    desired_paths = {f"data/repos/{name}" for name in desired}
    existing = _get_existing_submodules(root_dir)

    for path in sorted(existing):
        if not path.startswith("data/repos/"):
            continue
        if path not in desired_paths:
            try:
                _remove_submodule(root_dir, path)
            except Exception as exc:
                print(f"Aviso: no se pudo eliminar completamente {path}: {exc}")

    for nombre, url in desired.items():
        target_path = f"data/repos/{nombre}"
        existing_entry = existing.get(target_path)

        if existing_entry and existing_entry.get("url") and existing_entry["url"] != url:
            print(f"Actualizando URL del submodulo {nombre} -> {url}")
            set_url_result = subprocess.run(
                ["git", "submodule", "set-url", "--", target_path, url],
                cwd=root_dir,
                capture_output=True,
                text=True,
            )
            if set_url_result.returncode != 0:
                print(f"Aviso: no se pudo actualizar la URL de {target_path}.")
                if set_url_result.stderr:
                    print(set_url_result.stderr.strip())

        if target_path not in existing:
            print(f"Anadiendo submodulo para {nombre} desde {url}...")
            try:
                subprocess.run(
                    ["git", "submodule", "add", "-f", url, target_path],
                    cwd=root_dir,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                print(f"Advertencia/Error al anadir el submodulo {nombre}: {e}")

    if desired_paths:
        print("Sincronizando submodulos...")
        sync_result = subprocess.run(
            ["git", "submodule", "sync", "--recursive", "--", *sorted(desired_paths)],
            cwd=root_dir,
            capture_output=True,
            text=True,
        )
        if sync_result.returncode != 0:
            print("Aviso: git submodule sync devolvio error, pero el pipeline continuara.")
            if sync_result.stderr:
                print(sync_result.stderr.strip())

        print("Actualizando submodulos...")
        update_result = subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive", "--", *sorted(desired_paths)],
            cwd=root_dir,
            capture_output=True,
            text=True,
        )
        if update_result.returncode != 0:
            print("Aviso: git submodule update devolvio error, pero el pipeline continuara.")
            if update_result.stderr:
                print(update_result.stderr.strip())
    else:
        print("No hay repositorios para clonar.")

    print("Proceso de clonacion (submodulos) completado.")

if __name__ == "__main__":
    add_submodules()
