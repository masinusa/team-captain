

from fastapi import FastAPI

from fastapi_infrastructure.api_models import HealthCheckResponse

description = """
Team Captain helps you pick balanced teams for your next pickup soccer game!
"""

app = FastAPI(
    title="Team Captain",
    description=description,
    summary="Pick balanced teams for your next pickup soccer game",
    version="0.0.1",
    contact={
        "name": "masinusa",
        "url": "https://github.com/masinusa",
        "email": "masinusa@gmail.com",
    }
)


@app.get("/", tags=["Health Check"])
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="Running")