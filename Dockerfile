FROM python:3.10-slim

# Configuración interactiva para evitar que apt-get pida confirmación
ENV DEBIAN_FRONTEND=noninteractive

# 1. Instalar utilidades del sistema
RUN apt-get update && \
    apt-get install -y curl wget git unzip && \
    rm -rf /var/lib/apt/lists/*

# 2. Instalar Syft (SBOM)
RUN curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# 3. Instalar Grype (Vulnerabilidades)
RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# 4. Instalar CodeQL (SAST)
ENV CODEQL_HOME=/opt/codeql
RUN wget https://github.com/github/codeql-action/releases/latest/download/codeql-bundle-linux64.tar.gz -O /tmp/codeql.tar.gz && \
    mkdir -p ${CODEQL_HOME} && \
    tar -xvzf /tmp/codeql.tar.gz -C ${CODEQL_HOME} --strip-components=1 && \
    rm /tmp/codeql.tar.gz && \
    ln -s ${CODEQL_HOME}/codeql /usr/local/bin/codeql

# Asegurarse de que git sepa que /app está a salvo
RUN git config --global --add safe.directory '*'

WORKDIR /app

# 5. Instalar dependencias de Python (Jupyter, Pandas, etc.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Iniciar una terminal por defecto
CMD ["/bin/bash"]
