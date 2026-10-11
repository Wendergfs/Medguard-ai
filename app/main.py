from fastapi import FastAPI

app = FastAPI(
    title="MedGuard AI",
    description=(
        "Evidence-grounded medication safety research and interaction analysis."
    ),
    version="0.1.0",
)


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    """Return basic application information."""
    return {
        "name": "MedGuard AI",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Check whether the API process is responding."""
    return {
        "status": "ok",
        "service": "medguard-ai",
        "version": "0.1.0",
    }
