import json
import os
import subprocess
import logging

# Configurar logging en español
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

class SBOMGenerator:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate(self, repo_path, repo_name):
        output_file = os.path.join(self.output_dir, f"{repo_name}_sbom.json")
        logging.info(f"Generando SBOM para {repo_name} usando Syft...")
        try:
            # Comando syft <path> -o json
            cmd = ["syft", repo_path, "-o", "json"]
            with open(output_file, "w", encoding="utf-8") as f:
                subprocess.run(cmd, stdout=f, check=True)
            logging.info(f"SBOM generado exitosamente: {output_file}")
            return output_file
        except FileNotFoundError:
            logging.error("No se encontró Syft instalado en el sistema.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error al generar SBOM para {repo_name}: {e}")
        return None

class GrypeAnalyzer:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def scan(self, sbom_path, repo_name):
        output_file = os.path.join(self.output_dir, f"{repo_name}_grype.json")
        logging.info(f"Escaneando vulnerabilidades para {repo_name} con Grype...")
        try:
            cmd = ["grype", f"sbom:{sbom_path}", "-o", "json"]
            with open(output_file, "w", encoding="utf-8") as f:
                subprocess.run(cmd, stdout=f, check=True)
            logging.info(f"Reporte de Grype generado exitosamente: {output_file}")
            return output_file
        except FileNotFoundError:
            logging.error("No se encontró Grype instalado en el sistema.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error al escanear vulnerabilidades en {repo_name}: {e}")
        return None

class CodeQLAnalyzer:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _detect_language(self, repo_path):
        # Detección básica buscando extensiones
        langs = {"python": False, "javascript": False, "java": False, "cpp": False, "go": False}
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"): langs["python"] = True
                elif file.endswith(".js") or file.endswith(".ts"): langs["javascript"] = True
                elif file.endswith(".java"): langs["java"] = True
                elif file.endswith(".cpp") or file.endswith(".c") or file.endswith(".h"): langs["cpp"] = True
                elif file.endswith(".go"): langs["go"] = True
                
        # Por default retorna python si no está seguro o encuentra varios
        for lang, is_present in langs.items():
            if is_present:
                return lang
        return "python" 
        
    def analyze(self, repo_path, repo_name):
        lang = self._detect_language(repo_path)
        logging.info(f"Lenguaje detectado para SAST en {repo_name}: {lang}")
        
        db_path = os.path.join(self.output_dir, f"{repo_name}_codeql_db")
        output_file = os.path.join(self.output_dir, f"{repo_name}_codeql.sarif")
        
        try:
            logging.info(f"Creando DB CodeQL para {repo_name}...")
            # Limpiar si la DB ya existe
            if os.path.exists(db_path):
                import shutil
                shutil.rmtree(db_path)
                
            cmd_create = ["codeql", "database", "create", db_path, f"--language={lang}", f"--source-root={repo_path}"]
            subprocess.run(cmd_create, check=True, capture_output=True)
            
            logging.info(f"Analizando DB CodeQL para {repo_name}...")
            cmd_analyze = ["codeql", "database", "analyze", db_path, f"{lang}-security-extended.qls", "--format=sarif-latest", f"--output={output_file}"]
            subprocess.run(cmd_analyze, check=True, capture_output=True)
            
            logging.info(f"Análisis CodeQL completado: {output_file}")
            return output_file
        except FileNotFoundError:
            logging.error("No se encontró CodeQL instalado en el sistema.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error en CodeQL para {repo_name}.")
            if e.stderr:
                 logging.error(e.stderr.decode('utf-8'))
        return None

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    repos_dir = os.path.join(root_dir, "data", "repos")
    results_dir = os.path.join(root_dir, "data", "results")
    
    if not os.path.exists(repos_dir):
        logging.error("No hay bibliotecas repositorios clonados. Ejecuta add_submodules.py primero.")
        return
        
    os.makedirs(results_dir, exist_ok=True)
    
    sbom_gen = SBOMGenerator(results_dir)
    grype_analyzer = GrypeAnalyzer(results_dir)
    codeql_analyzer = CodeQLAnalyzer(results_dir)
    
    repos = [d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d))]
    logging.info(f"Arrancando el orquestador de seguridad para {len(repos)} repositorios.")
    
    stats = {"exitosos": 0, "fallidos": 0}
    
    for repo_name in repos:
        repo_path = os.path.join(repos_dir, repo_name)
        logging.info("-" * 40)
        logging.info(f"Iniciando análisis para: {repo_name}")
        
        # 1. Generar SBOM
        sbom_path = sbom_gen.generate(repo_path, repo_name)
        
        # 2. Análisis SCA
        if sbom_path:
            grype_analyzer.scan(sbom_path, repo_name)
            stats["exitosos"] += 1
        else:
            stats["fallidos"] += 1
            
        # 3. Análisis SAST
        codeql_analyzer.analyze(repo_path, repo_name)
        
    logging.info("=" * 40)
    logging.info("Resumen de Ejecución:")
    logging.info(f"Repositorios Escaneados Exitosamente: {stats['exitosos']}")
    logging.info(f"Repositorios con Errores SCA: {stats['fallidos']}")
    logging.info(f"Los resultados json y sarif se encuentran en data/results/")

if __name__ == "__main__":
    main()
