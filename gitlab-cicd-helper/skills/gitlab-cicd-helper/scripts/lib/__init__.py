"""GitLab CI/CD Helper Library - python-gitlab based"""

__version__ = "2.0.0"

# Import refactored modules using python-gitlab
from .gitlab_config import GitLabConfig
from .pipeline_analyzer import PipelineAnalyzer
from .project_resolver import ProjectResolver

__all__ = [
    "GitLabConfig",
    "PipelineAnalyzer",
    "ProjectResolver",
]
