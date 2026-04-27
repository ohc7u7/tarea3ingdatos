import json
import os
import subprocess
import logging
import csv
import datetime
import re

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
        langs = {"python": False, "javascript": False, "java": False, "cpp": False, "go": False}
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith(".py"): langs["python"] = True
                elif file.endswith(".js") or file.endswith(".ts"): langs["javascript"] = True
                elif file.endswith(".java"): langs["java"] = True
                elif file.endswith(".cpp") or file.endswith(".c") or file.endswith(".h"): langs["cpp"] = True
                elif file.endswith(".go"): langs["go"] = True
                
        for lang, is_present in langs.items():
            if is_present: return lang
        return "python" 
        
    def analyze(self, repo_path, repo_name):
        lang = self._detect_language(repo_path)
        logging.info(f"Lenguaje detectado para SAST en {repo_name}: {lang}")
        
        db_path = os.path.join(self.output_dir, f"{repo_name}_codeql_db")
        output_file = os.path.join(self.output_dir, f"{repo_name}_codeql.sarif")
        
        try:
            logging.info(f"Creando DB CodeQL para {repo_name}...")
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
            if e.stderr: logging.error(e.stderr.decode('utf-8'))
        return None

class CICDAnalyzer:
    def scan(self, repo_path, repo_name):
        findings = []
        workflows_dir = os.path.join(repo_path, ".github", "workflows")
        
        if not os.path.exists(workflows_dir):
            logging.info(f"No se detectaron flujos CI/CD en {repo_name}.")
            return findings
            
        logging.info(f"Escaneando flujos CI/CD (Dimensión 3) para {repo_name}...")
        for file in os.listdir(workflows_dir):
            if file.endswith(".yml") or file.endswith(".yaml"):
                filepath = os.path.join(workflows_dir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Riesgo de Inyección/Permisos
                        if "pull_request_target" in content:
                            findings.append({
                                'dimension': 'CI-CD',
                                'tool': 'Manual Scanner',
                                'finding_id': 'PR_TARGET_RISK',
                                'severity': 'High',
                                'category': 'Excessive Permissions',
                                'file/path': f".github/workflows/{file}",
                                'workflow': file
                            })
                            
                        # Secretos explícitos
                        if re.search(r'\$\{\{\s*secrets\.', content):
                            findings.append({
                                'dimension': 'CI-CD',
                                'tool': 'Manual Scanner',
                                'finding_id': 'SECRETS_EXPOSURE',
                                'severity': 'Medium',
                                'category': 'Secrets Management',
                                'file/path': f".github/workflows/{file}",
                                'workflow': file
                            })
                            
                        # Unpinned Actions
                        if "uses:" in content:
                            for line in content.split('\n'):
                                if "uses:" in line and "@" in line:
                                    version = line.split("@")[1].strip()
                                    if len(version) < 40:
                                        findings.append({
                                            'dimension': 'CI-CD',
                                            'tool': 'Manual Scanner',
                                            'finding_id': 'UNPINNED_ACTION_VERSION',
                                            'severity': 'Low',
                                            'category': 'Supply Chain Risk',
                                            'file/path': f".github/workflows/{file}",
                                            'workflow': file
                                        })
                except Exception as e:
                    logging.warning(f"No se pudo parsear {file} en {repo_name}: {e}")
                    
        return findings

class DatasetBuilder:
    def __init__(self, output_dir):
        self.dataset_path = os.path.join(output_dir, "final_dataset.csv")
        self.headers = ['org', 'repo', 'dimension', 'tool', 'finding_id', 'severity', 'category', 'file/path', 'workflow', 'timestamp']
        
        with open(self.dataset_path, "w", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)
            
    def append_grype_findings(self, org, repo, grype_json):
        if not grype_json: return
        try:
            with open(grype_json, 'r', encoding='utf-8') as f:
                content = json.load(f)
                rows = []
                now = datetime.datetime.now().isoformat()
                for match in content.get('matches', []):
                    vuln = match.get('vulnerability', {})
                    artifact = match.get('artifact', {})
                    rows.append([
                        org, repo, 'SCA', 'Grype',
                        vuln.get('id', 'Unknown'),
                        vuln.get('severity', 'Unknown'),
                        'Dependency Vulnerability',
                        artifact.get('name', 'N/A'),
                        'N/A', now
                    ])
                self._write_rows(rows)
        except Exception:
            pass

    def append_codeql_findings(self, org, repo, sarif_json):
        if not sarif_json: return
        try:
            with open(sarif_json, 'r', encoding='utf-8') as f:
                content = json.load(f)
                rows = []
                now = datetime.datetime.now().isoformat()
                runs = content.get('runs', [])
                for run in runs:
                    for result in run.get('results', []):
                        locations = result.get('locations', [])
                        file_path = 'N/A'
                        if locations:
                            phys_loc = locations[0].get('physicalLocation', {})
                            art_loc = phys_loc.get('artifactLocation', {})
                            file_path = art_loc.get('uri', 'N/A')
                        
                        rows.append([
                            org, repo, 'SAST', 'CodeQL',
                            result.get('ruleId', 'Unknown'),
                            'High',
                            'Static Analysis Weakness',
                            file_path, 'N/A', now
                        ])
                self._write_rows(rows)
        except Exception:
            pass
            
    def append_cicd_findings(self, org, repo, findings):
        if not findings: return
        rows = []
        now = datetime.datetime.now().isoformat()
        for f in findings:
            rows.append([
                org, repo, f['dimension'], f['tool'], f['finding_id'],
                f['severity'], f['category'], f['file/path'], f['workflow'], now
            ])
        self._write_rows(rows)
            
    def _write_rows(self, rows):
        with open(self.dataset_path, "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)


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
    cicd_analyzer = CICDAnalyzer()
    dataset_builder = DatasetBuilder(results_dir)
    
    repos = [d for d in os.listdir(repos_dir) if os.path.isdir(os.path.join(repos_dir, d))]
    logging.info(f"Arrancando el orquestador de seguridad para {len(repos)} repositorios.")
    
    ORG_NAME = "FlowiseAI"
    
    for repo_name in repos:
        repo_path = os.path.join(repos_dir, repo_name)
        logging.info("-" * 40)
        logging.info(f"Iniciando análisis para: {repo_name}")
        
        # 1. Dimensión 1: SAST CodeQL
        codeql_path = codeql_analyzer.analyze(repo_path, repo_name)
        
        # 2. Dimensión 2: SBOM/SCA
        sbom_path = sbom_gen.generate(repo_path, repo_name)
        grype_path = None
        if sbom_path:
            grype_path = grype_analyzer.scan(sbom_path, repo_name)
            
        # 3. Dimensión 3: CI/CD
        cicd_findings = cicd_analyzer.scan(repo_path, repo_name)
        
        # Consolidation Dataset Final CSV
        if grype_path: dataset_builder.append_grype_findings(ORG_NAME, repo_name, grype_path)
        if codeql_path: dataset_builder.append_codeql_findings(ORG_NAME, repo_name, codeql_path)
        dataset_builder.append_cicd_findings(ORG_NAME, repo_name, cicd_findings)
        
    logging.info("=" * 40)
    logging.info("Análisis de las 3 Dimensiones Finalizado Exitosamente.")
    logging.info("El dataset consolidado está ubicado en: data/results/final_dataset.csv")

if __name__ == "__main__":
    main()
