#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "python-gitlab>=4.0.0",
# ]
# ///
"""Batch log fetching with parallel processing and comprehensive reporting."""

import concurrent.futures
import json
import re
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional


class BatchLogFetcher:
    """Handles batch log retrieval with parallel processing and organized output."""

    def __init__(self, gl_client, project_id: int, pipeline_id: int, output_dir: str):
        """Initialize batch log fetcher.

        Args:
            gl_client: Authenticated python-gitlab client
            project_id: GitLab project ID
            pipeline_id: Pipeline ID
            output_dir: Output directory for logs
        """
        self.gl = gl_client
        self.project_id = project_id
        self.pipeline_id = pipeline_id
        self.output_dir = Path(output_dir)
        self.project = gl_client.projects.get(project_id)

    def sanitize_filename(self, name: str) -> str:
        """Sanitize job name for use in filenames.

        Args:
            name: Job name

        Returns:
            Sanitized filename
        """
        # Replace spaces and special characters with hyphens
        sanitized = re.sub(r'[^\w\-\.]', '-', name)
        # Remove consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        return sanitized

    def create_directory_structure(self, jobs: list):
        """Create organized directory structure.

        Args:
            jobs: List of jobs to process
        """
        # Create base directories
        (self.output_dir / "all").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "by-status").mkdir(exist_ok=True)
        (self.output_dir / "by-stage").mkdir(exist_ok=True)

        # Create status subdirectories
        statuses = set(job.status for job in jobs)
        for status in statuses:
            (self.output_dir / "by-status" / status).mkdir(exist_ok=True)

        # Create stage subdirectories
        stages = set(job.stage for job in jobs)
        for stage in stages:
            (self.output_dir / "by-stage" / stage).mkdir(exist_ok=True)

    def fetch_single_log(self, job, filters: Optional[dict] = None) -> dict:
        """Fetch log for a single job.

        Args:
            job: GitLab job object
            filters: Optional filters (tail, grep, ignore_case, context)

        Returns:
            Dictionary with job metadata and log content
        """
        result = {
            "job_id": job.id,
            "job_name": job.name,
            "status": job.status,
            "stage": job.stage,
            "duration": getattr(job, 'duration', None),
            "logs": None,
            "log_lines": 0,
            "log_size_bytes": 0,
            "error": None,
            "error_matches": 0
        }

        try:
            # Fetch full job object (list() returns partial without trace())
            full_job = self.project.jobs.get(job.id)
            logs = full_job.trace().decode('utf-8')

            # Apply filters
            if filters:
                logs = self._apply_filters(logs, filters)

            result["logs"] = logs
            result["log_lines"] = len(logs.split('\n')) if logs else 0
            result["log_size_bytes"] = len(logs.encode('utf-8')) if logs else 0

            # Count error matches if grep filter provided
            if filters and filters.get('grep'):
                pattern = filters['grep']
                flags = re.IGNORECASE if filters.get('ignore_case') else 0
                result["error_matches"] = len(re.findall(pattern, logs, flags=flags))

        except Exception as e:
            result["error"] = str(e)

        return result

    def _apply_filters(self, logs: str, filters: dict) -> str:
        """Apply filters to log content.

        Args:
            logs: Raw log content
            filters: Filters to apply (tail, grep, ignore_case, context)

        Returns:
            Filtered log content
        """
        if not logs:
            return logs

        lines = logs.split('\n')

        # Apply tail filter
        if filters.get('tail'):
            lines = lines[-filters['tail']:]

        # Apply grep filter
        if filters.get('grep'):
            pattern = filters['grep']
            flags = re.IGNORECASE if filters.get('ignore_case') else 0
            context = filters.get('context', 0)

            if context > 0:
                # Include context lines
                matching_indices = set()
                for i, line in enumerate(lines):
                    if re.search(pattern, line, flags=flags):
                        for j in range(max(0, i - context), min(len(lines), i + context + 1)):
                            matching_indices.add(j)
                lines = [lines[i] for i in sorted(matching_indices)]
            else:
                # Just matching lines
                lines = [line for line in lines if re.search(pattern, line, flags=flags)]

        return '\n'.join(lines)

    def fetch_logs_batch(
        self,
        jobs: list,
        parallel: int = 5,
        filters: Optional[dict] = None,
        skip_empty: bool = True
    ) -> dict:
        """Fetch logs for multiple jobs in parallel.

        Args:
            jobs: List of jobs to process
            parallel: Number of parallel fetches
            filters: Optional filters to apply to each log
            skip_empty: Skip jobs with no logs

        Returns:
            Dictionary with results and statistics
        """
        results = {
            "jobs": [],
            "statistics": {
                "total_jobs": len(jobs),
                "jobs_processed": 0,
                "jobs_skipped": 0,
                "jobs_failed": 0,
                "total_log_size_bytes": 0,
                "total_lines": 0,
                "processing_start": datetime.utcnow().isoformat(),
                "processing_end": None,
                "processing_time_seconds": 0
            }
        }

        start_time = datetime.utcnow()
        lock = Lock()
        progress = {"completed": 0, "total": len(jobs)}

        def fetch_with_progress(job):
            result = self.fetch_single_log(job, filters)
            with lock:
                progress["completed"] += 1
                status_icon = "✅" if result["logs"] is not None and not result["error"] else "⚠️" if result["error"] else "⊘"
                size_str = f"{result['log_size_bytes'] / 1024 / 1024:.1f} MB" if result["log_size_bytes"] > 0 else "no logs"
                print(f"  {status_icon} [{progress['completed']}/{progress['total']}] {job.name} ({size_str})")
            return result

        # Fetch logs in parallel
        print(f"\n📥 Fetching logs for {len(jobs)} jobs (parallel: {parallel})...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = [executor.submit(fetch_with_progress, job) for job in jobs]
            job_results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Process results
        for result in job_results:
            if skip_empty and result["logs"] is None:
                results["statistics"]["jobs_skipped"] += 1
                continue

            if result["error"]:
                results["statistics"]["jobs_failed"] += 1

            results["jobs"].append(result)
            results["statistics"]["jobs_processed"] += 1
            results["statistics"]["total_log_size_bytes"] += result["log_size_bytes"]
            results["statistics"]["total_lines"] += result["log_lines"]

        # Calculate processing time
        end_time = datetime.utcnow()
        results["statistics"]["processing_end"] = end_time.isoformat()
        results["statistics"]["processing_time_seconds"] = (end_time - start_time).total_seconds()

        return results

    def save_logs_to_files(self, results: dict):
        """Save logs to organized directory structure.

        Args:
            results: Results from fetch_logs_batch
        """
        for job_result in results["jobs"]:
            if not job_result["logs"]:
                continue

            job_id = job_result["job_id"]
            job_name = self.sanitize_filename(job_result["job_name"])
            status = job_result["status"]
            stage = job_result["stage"]

            filename = f"job-{job_id}-{job_name}.log"

            # Save to all/
            (self.output_dir / "all" / filename).write_text(job_result["logs"])

            # Save to by-status/
            (self.output_dir / "by-status" / status / filename).write_text(job_result["logs"])

            # Save to by-stage/
            (self.output_dir / "by-stage" / stage / filename).write_text(job_result["logs"])

    def create_aggregate_log(self, results: dict, project_name: str, branch: str) -> str:
        """Create single aggregated log file.

        Args:
            results: Results from fetch_logs_batch
            project_name: Project name
            branch: Branch name

        Returns:
            Path to aggregate log file
        """
        aggregate_path = self.output_dir / "aggregate.log"

        with open(aggregate_path, 'w') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write(f"Pipeline #{self.pipeline_id} - Batch Log Collection\n")
            f.write(f"Project: {project_name}\n")
            f.write(f"Branch: {branch}\n")
            f.write(f"Collection Time: {results['statistics']['processing_start']}\n")
            f.write(f"Total Jobs: {results['statistics']['jobs_processed']}\n")
            f.write("=" * 80 + "\n\n")

            # Individual job logs
            for job_result in results["jobs"]:
                if not job_result["logs"]:
                    continue

                f.write("#" * 80 + "\n")
                f.write(f"# Job: {job_result['job_name']} (ID: {job_result['job_id']})\n")
                f.write(f"# Status: {job_result['status']}\n")
                f.write(f"# Stage: {job_result['stage']}\n")
                if job_result['duration']:
                    f.write(f"# Duration: {job_result['duration']}s\n")
                f.write(f"# Log Lines: {job_result['log_lines']:,}\n")
                f.write("#" * 80 + "\n")
                f.write(job_result["logs"])
                f.write("\n\n")

        return str(aggregate_path)

    def generate_summary_report(self, results: dict, project_name: str, branch: str, filters: dict) -> str:
        """Generate comprehensive summary report.

        Args:
            results: Results from fetch_logs_batch
            project_name: Project name
            branch: Branch name
            filters: Filters applied during collection

        Returns:
            Path to summary report file
        """
        summary_path = self.output_dir / "summary.txt"
        stats = results["statistics"]

        with open(summary_path, 'w') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("GitLab Pipeline Log Collection Summary\n")
            f.write("=" * 80 + "\n")
            f.write(f"Pipeline: #{self.pipeline_id}\n")
            f.write(f"Project: {project_name} (ID: {self.project_id})\n")
            f.write(f"Branch: {branch}\n")
            f.write(f"Collection Time: {stats['processing_start']}\n")
            f.write(f"Output Directory: {self.output_dir}\n\n")

            # Collection Parameters
            f.write("=" * 80 + "\n")
            f.write("Collection Parameters\n")
            f.write("=" * 80 + "\n")
            if filters.get('status'):
                f.write(f"Filter: --status {' '.join(filters['status'])}\n")
            if filters.get('pattern'):
                f.write(f"Pattern: {filters['pattern']}\n")
            if filters.get('stage'):
                f.write(f"Stage: {filters['stage']}\n")
            if filters.get('grep'):
                f.write(f"Grep: {filters['grep']}\n")
            if filters.get('tail'):
                f.write(f"Tail: {filters['tail']} lines\n")
            f.write(f"Total Jobs in Pipeline: {stats['total_jobs']}\n")
            f.write(f"Jobs Processed: {stats['jobs_processed']}\n")
            f.write(f"Jobs Skipped (no logs): {stats['jobs_skipped']}\n")
            f.write(f"Jobs Failed to Fetch: {stats['jobs_failed']}\n\n")

            # Processing Statistics
            f.write("=" * 80 + "\n")
            f.write("Processing Statistics\n")
            f.write("=" * 80 + "\n")
            f.write(f"Total Log Size: {stats['total_log_size_bytes'] / 1024 / 1024:.1f} MB\n")
            f.write(f"Total Lines: {stats['total_lines']:,}\n")
            f.write(f"Processing Time: {stats['processing_time_seconds']:.1f}s\n\n")

            # Jobs by Status
            status_breakdown = {}
            for job in results["jobs"]:
                status = job["status"]
                if status not in status_breakdown:
                    status_breakdown[status] = {"count": 0, "size": 0}
                status_breakdown[status]["count"] += 1
                status_breakdown[status]["size"] += job["log_size_bytes"]

            if status_breakdown:
                f.write("=" * 80 + "\n")
                f.write("Jobs by Status\n")
                f.write("=" * 80 + "\n")
                for status, data in sorted(status_breakdown.items()):
                    size_mb = data["size"] / 1024 / 1024
                    f.write(f"{status:15} {data['count']:3} jobs   {size_mb:6.1f} MB\n")
                f.write("\n")

            # Jobs by Stage
            stage_breakdown = {}
            for job in results["jobs"]:
                stage = job["stage"]
                if stage not in stage_breakdown:
                    stage_breakdown[stage] = {"count": 0, "size": 0}
                stage_breakdown[stage]["count"] += 1
                stage_breakdown[stage]["size"] += job["log_size_bytes"]

            if stage_breakdown:
                f.write("=" * 80 + "\n")
                f.write("Jobs by Stage\n")
                f.write("=" * 80 + "\n")
                for stage, data in sorted(stage_breakdown.items()):
                    size_mb = data["size"] / 1024 / 1024
                    f.write(f"{stage:20} {data['count']:3} jobs   {size_mb:6.1f} MB\n")
                f.write("\n")

            # Error Analysis (if grep filter used)
            if filters.get('grep'):
                jobs_with_errors = [j for j in results["jobs"] if j["error_matches"] > 0]
                if jobs_with_errors:
                    f.write("=" * 80 + "\n")
                    f.write(f"Error Analysis (pattern: {filters['grep']})\n")
                    f.write("=" * 80 + "\n")
                    for job in sorted(jobs_with_errors, key=lambda x: x["error_matches"], reverse=True)[:10]:
                        f.write(f"\nJob: {job['job_name']} (ID: {job['job_id']})\n")
                        f.write(f"  Error matches: {job['error_matches']} lines\n")
                    f.write("\n")

            # Top 10 Largest Logs
            f.write("=" * 80 + "\n")
            f.write("Top 10 Largest Logs\n")
            f.write("=" * 80 + "\n")
            sorted_jobs = sorted(results["jobs"], key=lambda x: x["log_size_bytes"], reverse=True)[:10]
            for i, job in enumerate(sorted_jobs, 1):
                size_mb = job["log_size_bytes"] / 1024 / 1024
                filename = f"job-{job['job_id']}-{self.sanitize_filename(job['job_name'])}.log"
                f.write(f"{i:2}. {filename:50} {size_mb:6.1f} MB  ({job['log_lines']:,} lines)\n")
            f.write("\n")

            # Jobs Without Logs (if any were skipped)
            if stats["jobs_skipped"] > 0:
                f.write("=" * 80 + "\n")
                f.write(f"Jobs Without Logs ({stats['jobs_skipped']} skipped)\n")
                f.write("=" * 80 + "\n")
                f.write("(Jobs not started, manual, or no output)\n\n")

            # Quick Access Commands
            f.write("=" * 80 + "\n")
            f.write("Quick Access Commands\n")
            f.write("=" * 80 + "\n")
            f.write(f"# View organized logs\n")
            f.write(f"cd {self.output_dir}/by-status && ls -lh\n")
            f.write(f"cd {self.output_dir}/by-stage && ls -lh\n\n")
            f.write(f"# Search across all logs\n")
            f.write(f"grep -r 'ERROR' {self.output_dir}/all/\n\n")
            f.write(f"# View aggregate log\n")
            f.write(f"less {self.output_dir}/aggregate.log\n\n")

        return str(summary_path)

    def save_manifest(self, results: dict, project_path: str, branch: str, filters: dict):
        """Save batch operation metadata as JSON.

        Args:
            results: Results from fetch_logs_batch
            project_path: Project path
            branch: Branch name
            filters: Filters applied
        """
        manifest_path = self.output_dir / "manifest.json"

        manifest = {
            "pipeline_id": self.pipeline_id,
            "project_id": self.project_id,
            "project_path": project_path,
            "branch": branch,
            "collection_time": results["statistics"]["processing_start"],
            "output_dir": str(self.output_dir),
            "filters": filters,
            "statistics": results["statistics"],
            "jobs": [
                {
                    "job_id": j["job_id"],
                    "job_name": j["job_name"],
                    "status": j["status"],
                    "stage": j["stage"],
                    "duration": j["duration"],
                    "log_file": f"all/job-{j['job_id']}-{self.sanitize_filename(j['job_name'])}.log",
                    "log_size_bytes": j["log_size_bytes"],
                    "log_lines": j["log_lines"],
                    "error_matches": j["error_matches"]
                }
                for j in results["jobs"]
            ]
        }

        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        return str(manifest_path)
