"""
Consolidated API router for the application.
"""
from fastapi import APIRouter
from backend.app.routes import health, resumes, skills, db_resumes, jobs, auth, history

api_router = APIRouter()

# Include authentication routes (Phase 18)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Include user history routes (Phase 20)
api_router.include_router(history.router, prefix="/history", tags=["User History"])

# Include health routes
api_router.include_router(health.router)

# Include resume handling routes
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])

# Include skill normalization routes (Phase 10)
api_router.include_router(skills.router, prefix="/skills", tags=["Skills"])

# Include PostgreSQL database persistence routes (Phase 11)
api_router.include_router(db_resumes.router, prefix="/resumes/db", tags=["Database Resumes"])

# Include Job Description parsing routes (Phase 14)
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])


