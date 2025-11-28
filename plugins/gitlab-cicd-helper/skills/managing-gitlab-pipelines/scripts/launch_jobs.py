#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "python-gitlab>=4.0.0",
#     "pyyaml>=6.0",
# ]
# ///
"""
Launch manual jobs in a GitLab pipeline.

Usage:
    launch_jobs.py --pipeline PIPELINE_ID --job-id JOB_ID [--var KEY=VALUE]...
    launch_jobs.py --pipeline PIPELINE_ID --job-name "job name" [--var KEY=VALUE]...
    launch_jobs.py --pipeline PIPELINE_ID --batch [--pattern PATTERN] [--status STATUS]
    launch_jobs.py --auto --pipeline PIPELINE_ID --job-name "job name"

Examples:
    # Launch specific job by ID
    launch_jobs.py --pipeline 12345 --job-id 67890

    # Launch specific job by name
    launch_jobs.py --pipeline 12345 --job-name "deploy-production"

    # Launch all manual jobs (PROPERLY PAGINATED - finds ALL jobs, not just 20!)
    launch_jobs.py --pipeline 12345 --batch

    # Launch jobs matching pattern
    launch_jobs.py --pipeline 12345 --batch --pattern "deploy-*"

    # Launch all manual jobs with specific status
    launch_jobs.py --pipeline 12345 --batch --status manual
"""

import sys
import argparse
import fnmatch
import subprocess
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from gitlab_config import GitLabConfig
from pipeline_analyzer import PipelineAnalyzer
from project_resolver import ProjectResolver


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Launch manual jobs in a GitLab pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Project specification
    project_group = parser.add_mutually_exclusive_group()
    project_group.add_argument(
        "--auto",
        action="store_true",
        help="Auto-resolve project from current git repository"
    )
    project_group.add_argument(
        "--project",
        type=str,
        help="Project ID or path"
    )

    # Pipeline specification
    parser.add_argument(
        "--pipeline",
        type=int,
        required=True,
        help="Pipeline ID"
    )

    # Job specification (mutually exclusive)
    job_group = parser.add_mutually_exclusive_group(required=True)
    job_group.add_argument(
        "--job-id",
        type=int,
        help="Job ID to launch"
    )
    job_group.add_argument(
        "--job-name",
        type=str,
        help="Job name to launch"
    )
    job_group.add_argument(
        "--batch",
        action="store_true",
        help="Launch multiple jobs (use with --pattern or --status)"
    )

    # Batch options
    parser.add_argument(
        "--pattern",
        type=str,
        help="Job name pattern (e.g., 'deploy-*', 'ca-cert:*')"
    )

    parser.add_argument(
        "--status",
        type=str,
        default="manual",
        choices=["manual", "pending", "created", "skipped"],
        help="Job status filter for batch operations (default: manual)"
    )

    # Job variables
    parser.add_argument(
        "--var",
        action="append",
        dest="variables",
        metavar="KEY=VALUE",
        help="Job variable (can be specified multiple times)"
    )

    return parser.parse_args()


def parse_variables(var_list):
    """Parse variable list from KEY=VALUE format."""
    if not var_list:
        return {}

    variables = {}
    for var in var_list:
        if '=' not in var:
            print(f"⚠️  Warning: Ignoring invalid variable format: {var}")
            continue

        key, value = var.split('=', 1)
        variables[key] = value

    return variables


def launch_job(project, job_id, variables=None):
    """Launch a job using python-gitlab.

    Args:
        project: GitLab project object
        job_id: Job ID to launch
        variables: Optional dictionary of job variables

    Returns:
        Launched job object
    """
    job = project.jobs.get(job_id)

    # Prepare variables if provided
    if variables:
        job_variables = [{"key": k, "value": v} for k, v in variables.items()]
        job.play(job_variables_attributes=job_variables)
    else:
        job.play()

    # Refresh job to get updated status
    job.refresh()
    return job


def main():
    """Main entry point."""
    args = parse_args()

    try:
        # Initialize configuration and client
        print("🔐 Validating tokens...")
        config = GitLabConfig()
        gl = config.get_gitlab_client()
        print("✅ Tokens validated")

        # Determine project identifier
        if args.auto:
            print("🔍 Auto-resolving project...")
            resolver = ProjectResolver(gitlab_client=gl)
            project_id, project_name, project_path = resolver.resolve_from_repo()
            project = gl.projects.get(project_id)
            print(f"✅ Project: {project_name} (ID: {project.id})")
        elif args.project:
            project_identifier = args.project
            project = gl.projects.get(project_identifier)
            print(f"✅ Project: {project.name} (ID: {project.id})")
        else:
            # Auto-resolve from current directory
            print("🔍 Auto-resolving project from current directory...")
            resolver = ProjectResolver(gitlab_client=gl)
            project_id, project_name, project_path = resolver.resolve_from_repo()
            project = gl.projects.get(project_id)
            print(f"✅ Project: {project_name} (ID: {project.id})")

        # Initialize pipeline analyzer
        analyzer = PipelineAnalyzer(gl, project.id)

        # Parse variables
        variables = parse_variables(args.variables)

        # Single job launch by ID
        if args.job_id:
            print(f"\n🚀 Launching job {args.job_id}...")
            job = launch_job(project, args.job_id, variables)
            print(f"✅ Job {job.id} ({job.name}) launched - Status: {job.status}")
            return 0

        # Launch by job name
        elif args.job_name:
            print(f"\n🔍 Finding job '{args.job_name}'...")

            # Use analyzer to find jobs with proper pagination
            jobs = analyzer.find_job_by_name(args.pipeline, args.job_name)

            if not jobs:
                print(f"❌ Job '{args.job_name}' not found in pipeline {args.pipeline}")
                return 1

            if len(jobs) > 1:
                print(f"⚠️  Found {len(jobs)} jobs with name '{args.job_name}':")
                for job in jobs:
                    print(f"   - ID: {job.id}, Status: {job.status}")
                print(f"\n   Launching all {len(jobs)} jobs...")

            # Launch all matching jobs
            launched = []
            for job in jobs:
                print(f"\n🚀 Launching job {job.id} ({job.name})...")
                result = launch_job(project, job.id, variables)
                launched.append(result)
                print(f"   ✅ Status: {result.status}")

            print(f"\n✅ Successfully launched {len(launched)} job(s)")
            return 0

        # Batch launch
        elif args.batch:
            print(f"\n🔍 Finding {args.status} jobs in pipeline {args.pipeline}...")
            if args.pattern:
                print(f"   Pattern: {args.pattern}")

            # CRITICAL FIX: Use analyzer.get_all_jobs() with proper pagination
            # This fixes the bug where only 20 jobs were found instead of 90!
            if args.status == "manual":
                all_jobs = analyzer.get_all_jobs(args.pipeline, scope=[args.status])
            else:
                # For other statuses, get all jobs and filter
                all_jobs = analyzer.get_all_jobs(args.pipeline)
                all_jobs = [j for j in all_jobs if j.status == args.status]

            # Apply pattern filter if specified
            if args.pattern:
                jobs = [j for j in all_jobs if fnmatch.fnmatch(j.name, args.pattern)]
            else:
                jobs = all_jobs

            if not jobs:
                print(f"⚠️  No {args.status} jobs found")
                if args.pattern:
                    print(f"   (matching pattern: {args.pattern})")
                print(f"\n   Total jobs in pipeline: {len(analyzer.get_all_jobs(args.pipeline))}")
                return 0

            print(f"\n📋 Found {len(jobs)} jobs to launch:")
            for job in jobs:
                print(f"   - {job.name} [ID: {job.id}]")

            # Confirm batch launch
            print(f"\n🚀 Launching {len(jobs)} jobs...")

            launched = []
            failed = []
            for job in jobs:
                try:
                    result = launch_job(project, job.id, variables)
                    launched.append(result)
                    print(f"   ✅ {job.name} [ID: {job.id}]")
                except Exception as e:
                    failed.append((job, str(e)))
                    print(f"   ❌ {job.name} [ID: {job.id}]: {e}")

            # Summary
            print(f"\n{'='*60}")
            print(f"Batch Launch Summary:")
            print(f"{'='*60}")
            print(f"✅ Successfully launched: {len(launched)}")
            if failed:
                print(f"❌ Failed: {len(failed)}")

                # Check if failures are due to unplayable jobs
                unplayable_count = sum(1 for _, err in failed if "Unplayable Job" in err or "400" in err)
                if unplayable_count > 0:
                    print(f"\n💡 Tip: {unplayable_count} jobs are not launchable yet.")
                    print(f"   Jobs with status '{args.status}' may be waiting for dependencies.")

                    # Check for manual jobs using proper pagination
                    manual_jobs = analyzer.get_all_jobs(args.pipeline, scope=['manual'])
                    if manual_jobs:
                        print(f"\n   ✅ Found {len(manual_jobs)} jobs with status 'manual' that CAN be launched:")
                        for job in manual_jobs[:5]:  # Show first 5
                            print(f"      - {job.name} [ID: {job.id}]")
                        if len(manual_jobs) > 5:
                            print(f"      ... and {len(manual_jobs) - 5} more")
                        print(f"\n   Try: --batch --status manual")
                    else:
                        print(f"\n   No jobs with status 'manual' found in this pipeline yet.")
                        print(f"   Wait for previous stages to complete, or add 'needs: []' to job definitions.")

                # Show first few errors
                print(f"\n   Errors:")
                for job, error in failed[:3]:
                    # Extract just the error message
                    error_msg = error.split('\n')[-1] if '\n' in error else error
                    print(f"   - {job.name}: {error_msg}")
                if len(failed) > 3:
                    print(f"   ... and {len(failed) - 3} more errors")
            print(f"{'='*60}\n")

            return 0 if not failed else 1

    except Exception as e:
        print(f"❌ Job launch failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
