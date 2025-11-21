#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "python-gitlab>=4.0.0",
#     "pyyaml>=6.0",
# ]
# ///
"""Pipeline structure analysis and state management."""

import yaml
from typing import Optional
from collections import defaultdict
import gitlab
from gitlab.v4.objects import Project, ProjectPipeline


class PipelineAnalyzer:
    """Provides holistic pipeline awareness and state management."""

    def __init__(self, gl_client: gitlab.Gitlab, project_id: str):
        """Initialize pipeline analyzer.

        Args:
            gl_client: Authenticated python-gitlab client
            project_id: Project ID or path (e.g., "1603" or "group/project")
        """
        self.gl = gl_client
        self.project = self.gl.projects.get(project_id)
        self._config_cache = {}

    def get_pipeline(self, pipeline_id: int) -> ProjectPipeline:
        """Get pipeline object.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Pipeline object
        """
        return self.project.pipelines.get(pipeline_id)

    def get_all_jobs(self, pipeline_id: int, scope: Optional[list[str]] = None) -> list:
        """Get ALL jobs in a pipeline with proper pagination.

        This is the KEY method that fixes the pagination bug.

        Args:
            pipeline_id: Pipeline ID
            scope: Optional list of job statuses to filter by
                   (e.g., ['manual'], ['created'], ['success', 'failed'])

        Returns:
            List of ALL job objects (not just first 20!)

        Example:
            # Get all manual jobs (not just first 20!)
            manual_jobs = analyzer.get_all_jobs(pipeline_id, scope=['manual'])
        """
        pipeline = self.get_pipeline(pipeline_id)

        if scope:
            # python-gitlab API: scope parameter filters jobs
            # get_all=True ensures ALL pages are fetched
            jobs = pipeline.jobs.list(scope=scope, get_all=True)
        else:
            # Get ALL jobs regardless of status
            jobs = pipeline.jobs.list(get_all=True)

        return jobs

    def get_jobs_by_status(self, pipeline_id: int) -> dict[str, list]:
        """Get jobs grouped by status.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Dictionary mapping status to list of jobs
            Example: {'manual': [...], 'created': [...], 'success': [...]}
        """
        all_jobs = self.get_all_jobs(pipeline_id)

        jobs_by_status = defaultdict(list)
        for job in all_jobs:
            jobs_by_status[job.status].append(job)

        return dict(jobs_by_status)

    def get_jobs_by_stage(self, pipeline_id: int) -> dict[str, list]:
        """Get jobs grouped by stage.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Dictionary mapping stage name to list of jobs
        """
        all_jobs = self.get_all_jobs(pipeline_id)

        jobs_by_stage = defaultdict(list)
        for job in all_jobs:
            jobs_by_stage[job.stage].append(job)

        return dict(jobs_by_stage)

    def get_executable_jobs(self, pipeline_id: int) -> dict[str, list]:
        """Get jobs that can be executed now.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Dictionary with categorized jobs:
            {
                'manual': [...],      # Ready to launch manually
                'pending': [...],     # Queued, waiting for runner
                'created': [...]      # Waiting for dependencies
            }
        """
        jobs_by_status = self.get_jobs_by_status(pipeline_id)

        return {
            'manual': jobs_by_status.get('manual', []),
            'pending': jobs_by_status.get('pending', []),
            'created': jobs_by_status.get('created', [])
        }

    def find_job_by_name(self, pipeline_id: int, job_name: str) -> Optional[list]:
        """Find job(s) by name.

        Note: Multiple jobs can have the same name (retries, parallel jobs)

        Args:
            pipeline_id: Pipeline ID
            job_name: Exact job name to search for

        Returns:
            List of matching jobs (empty list if not found)
        """
        all_jobs = self.get_all_jobs(pipeline_id)
        matching_jobs = [job for job in all_jobs if job.name == job_name]
        return matching_jobs

    def find_jobs_by_pattern(self, pipeline_id: int, pattern: str) -> list:
        """Find jobs matching a name pattern (glob-style).

        Args:
            pipeline_id: Pipeline ID
            pattern: Pattern to match (e.g., 'deploy-*', '*test*', 'ca-cert:*')

        Returns:
            List of matching jobs
        """
        import fnmatch

        all_jobs = self.get_all_jobs(pipeline_id)
        matching_jobs = [job for job in all_jobs if fnmatch.fnmatch(job.name, pattern)]
        return matching_jobs

    def get_pipeline_summary(self, pipeline_id: int) -> dict:
        """Get comprehensive pipeline summary.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Dictionary with pipeline statistics:
            {
                'pipeline_id': int,
                'status': str,
                'ref': str,
                'created_at': str,
                'total_jobs': int,
                'jobs_by_status': {...},
                'jobs_by_stage': {...},
                'stages': [...]
            }
        """
        pipeline = self.get_pipeline(pipeline_id)
        all_jobs = self.get_all_jobs(pipeline_id)
        jobs_by_status = self.get_jobs_by_status(pipeline_id)
        jobs_by_stage = self.get_jobs_by_stage(pipeline_id)

        # Count jobs per status
        status_counts = {status: len(jobs) for status, jobs in jobs_by_status.items()}

        # Count jobs per stage
        stage_counts = {stage: len(jobs) for stage, jobs in jobs_by_stage.items()}

        # Get stage names in order
        stages = list(jobs_by_stage.keys())

        return {
            'pipeline_id': pipeline.id,
            'status': pipeline.status,
            'ref': pipeline.ref,
            'created_at': pipeline.created_at,
            'updated_at': pipeline.updated_at,
            'web_url': pipeline.web_url,
            'total_jobs': len(all_jobs),
            'jobs_by_status': status_counts,
            'jobs_by_stage': stage_counts,
            'stages': stages
        }

    def display_pipeline_summary(self, pipeline_id: int) -> None:
        """Display formatted pipeline summary.

        Args:
            pipeline_id: Pipeline ID
        """
        summary = self.get_pipeline_summary(pipeline_id)

        print(f"\n{'='*60}")
        print(f"Pipeline #{summary['pipeline_id']}")
        print(f"{'='*60}")
        print(f"Status: {summary['status']}")
        print(f"Branch: {summary['ref']}")
        print(f"Created: {summary['created_at']}")
        print(f"Total Jobs: {summary['total_jobs']}")
        print(f"\nURL: {summary['web_url']}")

        print(f"\n📊 Jobs by Status:")
        for status, count in sorted(summary['jobs_by_status'].items()):
            print(f"   {status:12} {count:3} jobs")

        print(f"\n📋 Jobs by Stage:")
        for stage in summary['stages']:
            count = summary['jobs_by_stage'][stage]
            print(f"   {stage:20} {count:3} jobs")

        print(f"{'='*60}\n")

    def parse_gitlab_ci_config(self, ref: str = 'main') -> Optional[dict]:
        """Parse .gitlab-ci.yml configuration.

        Note: This uses GitLab's CI Lint API to get the fully expanded configuration
        including all includes, variables, and anchors resolved.

        Args:
            ref: Branch/tag reference to get config from

        Returns:
            Parsed configuration dictionary or None if parsing fails
        """
        # Check cache first
        cache_key = f"{self.project.id}:{ref}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]

        try:
            # Get .gitlab-ci.yml content
            ci_file = self.project.files.get(file_path='.gitlab-ci.yml', ref=ref)
            ci_content = ci_file.decode().decode('utf-8')

            # Use GitLab CI Lint API to get fully expanded configuration
            # This resolves all includes, variables, extends, anchors, etc.
            lint_result = self.project.ci_lint.create({
                'content': ci_content,
                'include_jobs': True,
                'ref': ref
            })

            if lint_result.valid:
                # Parse the merged YAML
                config = yaml.safe_load(lint_result.merged_yaml)
                self._config_cache[cache_key] = config
                return config
            else:
                print(f"⚠️  Warning: .gitlab-ci.yml validation failed:")
                for error in lint_result.errors:
                    print(f"   - {error}")
                return None

        except gitlab.GitlabGetError as e:
            print(f"⚠️  Warning: Could not fetch .gitlab-ci.yml: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Warning: Error parsing .gitlab-ci.yml: {e}")
            return None

    def get_job_config(self, job_name: str, ref: str = 'main') -> Optional[dict]:
        """Get job configuration from .gitlab-ci.yml.

        Args:
            job_name: Job name to look up
            ref: Branch/tag reference

        Returns:
            Job configuration dictionary or None if not found
        """
        config = self.parse_gitlab_ci_config(ref)
        if not config:
            return None

        # Jobs are top-level keys (excluding special keys starting with .)
        if job_name in config and not job_name.startswith('.'):
            return config[job_name]

        return None

    def get_job_dependencies(self, job_name: str, ref: str = 'main') -> dict:
        """Get job dependencies from configuration.

        Args:
            job_name: Job name
            ref: Branch/tag reference

        Returns:
            Dictionary with dependency information:
            {
                'needs': [...],           # Explicit needs
                'dependencies': [...],    # Artifact dependencies
                'stage': str,             # Job stage
                'when': str               # When to run (manual, on_success, etc.)
            }
        """
        job_config = self.get_job_config(job_name, ref)
        if not job_config:
            return {
                'needs': [],
                'dependencies': [],
                'stage': 'unknown',
                'when': 'on_success'
            }

        return {
            'needs': job_config.get('needs', []),
            'dependencies': job_config.get('dependencies', []),
            'stage': job_config.get('stage', 'test'),
            'when': job_config.get('when', 'on_success')
        }
