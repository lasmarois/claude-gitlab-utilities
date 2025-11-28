#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "python-gitlab>=4.0.0",
# ]
# ///
"""GitLab configuration and client initialization with standard authentication."""

import os
import netrc
import re
from pathlib import Path
from typing import Optional, Tuple
import gitlab


class GitLabConfig:
    """Manage GitLab configuration and authentication using standard methods."""

    def __init__(self, gitlab_url: Optional[str] = None):
        """Initialize GitLab configuration.

        Args:
            gitlab_url: Optional GitLab instance URL (auto-detected if not provided)
        """
        self._gitlab_url = gitlab_url
        self._pat_token: Optional[str] = None
        self._trigger_token: Optional[str] = None

    def get_gitlab_url(self) -> str:
        """Get GitLab instance URL.

        Priority:
        1. URL passed to __init__
        2. GITLAB_URL environment variable
        3. Default: https://gitlab.com

        Returns:
            GitLab instance URL
        """
        if self._gitlab_url:
            return self._gitlab_url

        # Check environment variable
        if url := os.environ.get("GITLAB_URL"):
            return url

        # Try to detect from git remote (if available)
        try:
            import subprocess
            remote_url = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                text=True,
                stderr=subprocess.PIPE
            ).strip()

            # Parse domain from HTTPS or SSH URL
            # Handle URLs with embedded credentials: https://user:token@domain/path
            if match := re.match(r'https://(?:[^@]+@)?([^/]+)/', remote_url):
                domain = match.group(1)
                # Skip github.com - it's not a GitLab server
                if domain.lower() != "github.com":
                    return f"https://{domain}"
            elif match := re.match(r'git@([^:]+):', remote_url):
                domain = match.group(1)
                if domain.lower() != "github.com":
                    return f"https://{domain}"
        except:
            pass

        # Default to gitlab.com
        return "https://gitlab.com"

    def get_gitlab_domain(self) -> str:
        """Extract domain from GitLab URL.

        Returns:
            Domain (e.g., 'gitlab.com' or 'gitlab.pitchblackcompany.com')
        """
        url = self.get_gitlab_url()
        if match := re.match(r'https?://([^/]+)', url):
            return match.group(1)
        return url

    def get_pat_token(self) -> str:
        """Get GitLab PAT token using standard authentication hierarchy.

        Priority (first found wins):
        1. GITLAB_TOKEN environment variable (highest priority)
        2. PAT_TOKEN environment variable
        3. ~/.netrc file (standard HTTP authentication)
        4. ~/.git-credentials (Git credential helper)

        Returns:
            PAT token string

        Raises:
            ValueError: No valid token found
        """
        # 1. Check GITLAB_TOKEN environment variable
        if token := os.environ.get("GITLAB_TOKEN"):
            return token.strip()

        # 2. Check PAT_TOKEN environment variable
        if token := os.environ.get("PAT_TOKEN"):
            return token.strip()

        domain = self.get_gitlab_domain()

        # 3. Check ~/.netrc file
        try:
            netrc_file = os.environ.get("NETRC", str(Path.home() / ".netrc"))
            n = netrc.netrc(netrc_file)
            authenticator = n.authenticators(domain)
            if authenticator:
                # netrc returns (login, account, password)
                token = authenticator[2]  # password field
                if token:
                    return token.strip()
        except (FileNotFoundError, netrc.NetrcParseError):
            pass

        # 4. Check ~/.git-credentials
        try:
            git_creds_path = Path.home() / ".git-credentials"
            if git_creds_path.exists():
                with open(git_creds_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Format: https://username:token@domain
                        if domain in line:
                            if match := re.match(rf'https://[^:]+:([^@]+)@{re.escape(domain)}', line):
                                token = match.group(1)
                                if token:
                                    return token.strip()
        except (FileNotFoundError, PermissionError):
            pass

        # 5. Check git remote URL for embedded credentials
        try:
            import subprocess
            remote_url = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                text=True,
                stderr=subprocess.PIPE
            ).strip()

            # Format: https://username:token@domain/path
            if match := re.match(rf'https://[^:]+:([^@]+)@{re.escape(domain)}', remote_url):
                token = match.group(1)
                if token:
                    return token.strip()
        except:
            pass

        # No token found - provide helpful error message
        raise ValueError(
            f"❌ No GitLab PAT token found\n\n"
            f"Provide authentication using one of these methods:\n\n"
            f"1. Environment variable (recommended for CI/CD):\n"
            f"   export GITLAB_TOKEN='glpat-xxxxxxxxxxxxxxxxxxxxx'\n\n"
            f"2. ~/.netrc file (standard HTTP authentication):\n"
            f"   machine {domain}\n"
            f"   login oauth2\n"
            f"   password glpat-xxxxxxxxxxxxxxxxxxxxx\n"
            f"   \n"
            f"   chmod 600 ~/.netrc\n\n"
            f"3. ~/.git-credentials (Git credential helper):\n"
            f"   https://oauth2:glpat-xxxxxxxxxxxxxxxxxxxxx@{domain}\n"
            f"   \n"
            f"   chmod 600 ~/.git-credentials\n\n"
            f"Token must have 'api' scope for GitLab API operations.\n"
        )

    def get_trigger_token(self) -> str:
        """Get GitLab trigger token (project-specific, optional).

        Priority (first found wins):
        1. GITLAB_TRIGGER_TOKEN environment variable
        2. .gitlab-trigger-token in project root
        3. .gitlab-trigger-token in current directory

        Returns:
            Trigger token string

        Raises:
            ValueError: No trigger token found
        """
        # 1. Check GITLAB_TRIGGER_TOKEN environment variable
        if token := os.environ.get("GITLAB_TRIGGER_TOKEN"):
            return token.strip()

        # 2. Check project root .gitlab-trigger-token
        try:
            import subprocess
            # Get git repository root
            git_root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                text=True,
                stderr=subprocess.PIPE
            ).strip()

            trigger_file = Path(git_root) / ".gitlab-trigger-token"
            if trigger_file.exists():
                token = trigger_file.read_text().strip()
                if token:
                    return token
        except:
            pass

        # 3. Check current directory .gitlab-trigger-token
        trigger_file = Path(".gitlab-trigger-token")
        if trigger_file.exists():
            token = trigger_file.read_text().strip()
            if token:
                return token

        # No trigger token found
        raise ValueError(
            f"❌ No GitLab trigger token found\n\n"
            f"Trigger tokens are project-specific. Provide one using:\n\n"
            f"1. Environment variable:\n"
            f"   export GITLAB_TRIGGER_TOKEN='glptt-xxxxxxxxxxxxxxxxxxxxx'\n\n"
            f"2. Project-specific file (recommended):\n"
            f"   echo 'glptt-xxxxxxxxxxxxxxxxxxxxx' > .gitlab-trigger-token\n"
            f"   chmod 600 .gitlab-trigger-token\n"
            f"   echo '.gitlab-trigger-token' >> .gitignore\n\n"
            f"Note: Trigger tokens are optional. Most operations use PAT tokens.\n"
        )

    def get_gitlab_client(self) -> gitlab.Gitlab:
        """Get authenticated GitLab client.

        Returns:
            Authenticated python-gitlab client

        Raises:
            ValueError: No valid PAT token found
            gitlab.GitlabAuthenticationError: Authentication failed
        """
        gitlab_url = self.get_gitlab_url()
        pat_token = self.get_pat_token()

        gl = gitlab.Gitlab(url=gitlab_url, private_token=pat_token)

        # Authenticate to verify token is valid
        try:
            gl.auth()
        except gitlab.exceptions.GitlabAuthenticationError as e:
            raise ValueError(
                f"❌ GitLab authentication failed\n\n"
                f"   GitLab URL: {gitlab_url}\n"
                f"   Token: {pat_token[:10]}...\n"
                f"   Error: {e}\n\n"
                f"Verify:\n"
                f"1. Token hasn't expired\n"
                f"2. Token has 'api' scope\n"
                f"3. GitLab URL is correct\n"
            )

        return gl

    def display_config(self) -> None:
        """Display current configuration (for debugging)."""
        print("🔐 GitLab Configuration:")
        print(f"   GitLab URL: {self.get_gitlab_url()}")
        print(f"   GitLab Domain: {self.get_gitlab_domain()}")

        try:
            token = self.get_pat_token()
            print(f"   PAT Token: {token[:10]}..." if len(token) > 10 else "   PAT Token: (too short)")
        except ValueError as e:
            print(f"   PAT Token: ❌ Not found")

        try:
            trigger = self.get_trigger_token()
            print(f"   Trigger Token: {trigger[:10]}..." if len(trigger) > 10 else "   Trigger Token: (too short)")
        except ValueError:
            print(f"   Trigger Token: (not configured - optional)")
