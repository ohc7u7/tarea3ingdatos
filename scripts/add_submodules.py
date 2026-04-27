import json
import os
import subprocess

def add_submodules():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    json_path = os.path.join(root_dir, "data", "repos.json")
    repos_dir = os.path.join(root_dir, "data", "repos")
    
    if not os.path.exists(json_path):
        print(f"Error: No se encontró el archivo {json_path}")
        print("Asegúrate de ejecutar discover_repos.py primero.")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        repos = json.load(f)
        
    os.makedirs(repos_dir, exist_ok=True)
    
    # Asegurarnos de tener un repositorio git principal
    if not os.path.exists(os.path.join(root_dir, ".git")):
        print("Inicializando repositorio git principal en la raíz...")
        subprocess.run(["git", "init"], cwd=root_dir, check=True)
        
    for repo in repos:
        nombre = repo["nombre"]
        url = repo["url"]
        target_path = f"data/repos/{nombre}"
        
        print(f"Añadiendo submódulo para {nombre} desde {url}...")
        try:
            # Añadir submodule forzando por si acaso y evitando errores si ya existe
            subprocess.run(["git", "submodule", "add", "-f", url, target_path], cwd=root_dir, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Advertencia/Error al añadir el submódulo {nombre}: {e}")
            
    print("Actualizando submódulos...")
    subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=root_dir, check=True)
    print("Proceso de clonación (submódulos) completado.")

if __name__ == "__main__":
    add_submodules()
