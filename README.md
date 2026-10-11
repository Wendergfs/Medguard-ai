
# MedGuard AI

Evidence-grounded medication safety research and
drug interaction analysis.

## Objectives

- Normalize medication names using RxNorm.
- Retrieve medication safety evidence from reliable sources.
- Analyze potential drug interactions.
- Build a drug knowledge graph with Neo4j.
- Add GraphRAG retrieval and a LangGraph workflow.
- Verify evidence before generating user-facing reports.

## Current status

Milestone 1: Backend foundation.

The current version exposes basic health endpoints.
It does not perform medical analysis.

## Requirements

- Python 3.12 or a compatible Python version
- Git

## Setup on Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run the API

```powershell
uvicorn app.main:app --reload
```

## Run tests

```powershell
python -m pytest -q
```

## Run code quality checks

```powershell
python -m ruff check .
python -m ruff format --check .
```

## API documentation

- Health: http://127.0.0.1:8000/health
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json

## Safety scope

This initial version is infrastructure only. It does not
provide medication recommendations or clinical conclusions.
