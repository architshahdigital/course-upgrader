"""Course Upgrader — find courses that teach you something new, not something you already know."""

__version__ = "0.1.0"

from course_upgrader.models import CandidateProfile, Course, CourseAnalysis, Platform, Verdict

__all__ = [
    "__version__",
    "CandidateProfile",
    "Course",
    "CourseAnalysis",
    "Platform",
    "Verdict",
]
