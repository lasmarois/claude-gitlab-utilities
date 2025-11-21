"""Auto-resolve GitLab project IDs from git remotes."""

import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple


class ProjectResolver:
    """Resolve GitLab project IDs from git remotes or project paths."""

    def __init__(self, gitlab_client=None, gitlab_url: str = "https://gitlab.pitchblackcompany.com"):
        """Initialize project resolver.

        Args:
            gitlab_client: Authenticated python-gitlab client (optional)
            gitlab_url: GitLab instance URL (used if client not provided)
        """
        self.gitlab_client = gitlab_client
        self.gitlab_url = gitlab_url
        self._cache = {}

    def resolve_from_repo(self, repo_path: Optional[str] = None) -> Tuple[int, str, str]:
        """Resolve project ID from git repository using GitLab API.

        Args:
            repo_path: Path to git repository (defaults to current directory)

        Returns:
            Tuple of (project_id, project_name, project_path)

        Raises:
            ValueError: If git remote not found or invalid
            RuntimeError: If GitLab API lookup fails
        """
        if repo_path is None:
            repo_path = "."

        cache_key = str(Path(repo_path).resolve())
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Get git remote URL
        try:
            remote_url = subprocess.check_output(
                ["git", "-C", repo_path, "remote", "get-url", "origin"],
                text=True,
                stderr=subprocess.PIPE
            ).strip()
        except subprocess.CalledProcessError as e:
            raise ValueError(
                f"❌ Failed to get git remote URL\n"
                f"   Error: {e.stderr}\n"
                f"   Make sure you're in a git repository with a remote configured"
            )

        # Extract project path from URL
        project_path = self._parse_git_remote_url(remote_url)

        print(f"📂 Git remote found: {remote_url}")
        print(f"📂 Detected project path: {project_path}")

        # If we have a GitLab client, resolve to numeric project ID
        if self.gitlab_client:
            try:
                # First try direct path lookup (python-gitlab handles encoding internally)
                project = self.gitlab_client.projects.get(project_path)

                result = (project.id, project.name, project.path_with_namespace)
                print(f"✅ Resolved to project ID: {project.id}")

                self._cache[cache_key] = result
                return result

            except Exception as path_error:
                # Fallback: Search for project by name (enhancement for restricted tokens)
                try:
                    print(f"   Direct lookup failed, searching by project name...")
                    projects = self.gitlab_client.projects.list(
                        search=project_path.split('/')[-1],  # Search by project name
                        get_all=False
                    )

                    # Find exact match by full path
                    for proj in projects:
                        if proj.path_with_namespace == project_path:
                            result = (proj.id, proj.name, proj.path_with_namespace)
                            print(f"✅ Resolved via search to project ID: {proj.id}")

                            self._cache[cache_key] = result
                            return result

                    raise ValueError(f"Project not found in search results")

                except Exception as search_error:
                    raise RuntimeError(
                        f"❌ Failed to resolve project from GitLab API\n"
                        f"   Project path: {project_path}\n"
                        f"   Direct lookup error: {path_error}\n"
                        f"   Search error: {search_error}\n"
                        f"   Make sure the PAT token has access to this project"
                    )
        else:
            # Fallback: return path-based info (caller must resolve)
            result = (0, project_path.split('/')[-1], project_path)
            self._cache[cache_key] = result
            return result

    def _parse_git_remote_url(self, remote_url: str) -> str:
        """Parse project path from git remote URL.

        Args:
            remote_url: Git remote URL (HTTPS or SSH)

        Returns:
            Project path (e.g., 'operations/infrastructure/misc/runner-troubleshooter')

        Raises:
            ValueError: If URL format is not recognized
        """
        # HTTPS format: https://gitlab.example.com/group/subgroup/project.git
        https_match = re.match(r'https://[^/]+/(.+?)(?:\.git)?$', remote_url)
        if https_match:
            return https_match.group(1).rstrip('.git')

        # SSH format: git@gitlab.example.com:group/subgroup/project.git
        ssh_match = re.match(r'git@[^:]+:(.+?)(?:\.git)?$', remote_url)
        if ssh_match:
            return ssh_match.group(1).rstrip('.git')

        raise ValueError(
            f"❌ Unrecognized git remote URL format: {remote_url}\n"
            f"   Expected HTTPS (https://...) or SSH (git@...) format"
        )

    def clear_cache(self) -> None:
        """Clear the resolution cache."""
        self._cache.clear()
