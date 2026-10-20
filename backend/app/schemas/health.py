"""
Health check Pydantic schemas.
"""
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Application health status")
