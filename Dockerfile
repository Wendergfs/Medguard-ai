# Python 3.12
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installer une version précise de uv depuis PyPI
RUN python -m pip install --no-cache-dir uv==0.13.0

# Copier les fichiers de configuration
COPY pyproject.toml uv.lock README.md ./

# Installer les dépendances verrouillées, y compris les outils de développement
RUN uv sync --locked --extra dev

# Copier le code et les tests
COPY app/ ./app/
COPY tests/ ./tests/

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Démarrer FastAPI
CMD ["uv", "run", "--locked", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]