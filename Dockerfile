# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ACCEPT_EULA=Y

# System deps for pyodbc + MS ODBC 18
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg apt-transport-https ca-certificates \
    unixodbc unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repo for msodbcsql18
RUN set -eux; \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg; \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
      > /etc/apt/sources.list.d/mssql-release.list; \
    apt-get update && apt-get install -y --no-install-recommends msodbcsql18 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.docker.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy source
COPY . /app

# Dash will bind to 0.0.0.0:8050
ENV DASH_HOST=0.0.0.0 \
    DASH_PORT=8050 \
    DB_HOST=host.docker.internal \
    DB_PORT=1433 \
    DB_NAME=sdud \
    DB_USER=sa \
    DB_PASSWORD=StrongPassword123! \
    ODBC_DRIVER="ODBC Driver 18 for SQL Server" \
    DB_TRUST_SERVER_CERTIFICATE=yes
EXPOSE 8050

CMD ["python", "app/dashboard.py"]
