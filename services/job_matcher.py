"""
Re-export of JobMatcher for top-level services.job_matcher package import compatibility.
"""
from backend.app.services.job_matcher import (
    JobMatcher,
    job_matcher,
    DEGREE_RANKS,
)

__all__ = [
    "JobMatcher",
    "job_matcher",
    "DEGREE_RANKS",
]
