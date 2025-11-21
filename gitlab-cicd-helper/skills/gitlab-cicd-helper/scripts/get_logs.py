#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "python-gitlab>=4.0.0",
#     "pyyaml>=6.0",
# ]
# ///
"""
Retrieve GitLab job logs/traces (single job or batch mode).

Single Job Usage:
    get_logs.py --job JOB_ID [--auto | --project PROJECT_ID]
    get_logs.py --pipeline PIPELINE_ID --job-name "job name" [--auto]
    get_logs.py --job JOB_ID --tail N
    get_logs.py --job JOB_ID --grep PATTERN

Batch Mode Usage:
    get_logs.py --pipeline PIPELINE_ID --batch --failed-only [--auto]
    get_logs.py --pipeline PIPELINE_ID --batch --status failed --status canceled
    get_logs.py --pipeline PIPELINE_ID --batch --pattern "test-*" --summary
    get_logs.py --pipeline PIPELINE_ID --batch --all --aggregate

Single Job Examples:
    # Get full job logs by ID
    get_logs.py --job 67890 --auto

    # Get logs by job name
    get_logs.py --pipeline 12345 --job-name "deploy-production" --auto

    # Get last 50 lines
    get_logs.py --job 67890 --auto --tail 50

    # Filter for errors
    get_logs.py --job 67890 --auto --grep "ERROR"

Batch Mode Examples:
    # Get logs from all failed jobs
    get_logs.py --pipeline 12345 --batch --failed-only --summary

    # Get logs from specific stage
    get_logs.py --pipeline 12345 --batch --stage test

    # Get logs matching pattern with error highlighting
    get_logs.py --pipeline 12345 --batch --pattern "integration-*" --grep "FAIL"

    # Complete pipeline log archive
    get_logs.py --pipeline 12345 --batch --all --aggregate --summary
"""

import sys
import argparse
import re
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from gitlab_config import GitLabConfig
from pipeline_analyzer import PipelineAnalyzer
from project_resolver import ProjectResolver
from batch_log_fetcher import BatchLogFetcher


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Retrieve GitLab job logs/traces (single job or batch mode)",
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

    # Job specification (mutually exclusive)
    job_group = parser.add_mutually_exclusive_group(required=False)
    job_group.add_argument(
        "--job",
        type=int,
        help="Job ID (single job mode)"
    )
    job_group.add_argument(
        "--job-name",
        type=str,
        help="Job name (requires --pipeline, single job mode)"
    )
    job_group.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: retrieve logs from multiple jobs"
    )

    # Pipeline (required for job-name and batch mode)
    parser.add_argument(
        "--pipeline",
        type=int,
        help="Pipeline ID (required for --job-name or --batch)"
    )

    # Batch mode job selection (only used with --batch)
    parser.add_argument(
        "--all",
        action="store_true",
        help="[Batch] Get logs from ALL jobs in pipeline"
    )

    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="[Batch] Shortcut for --status failed"
    )

    parser.add_argument(
        "--status",
        action="append",
        choices=["created", "pending", "running", "manual", "success", "failed", "canceled", "skipped"],
        help="[Batch] Filter jobs by status (can be used multiple times)"
    )

    parser.add_argument(
        "--stage",
        type=str,
        help="[Batch] Filter jobs by stage name"
    )

    parser.add_argument(
        "--pattern",
        type=str,
        help="[Batch] Job name pattern (glob-style, e.g., 'test-*', '*integration*')"
    )

    parser.add_argument(
        "--max-jobs",
        type=int,
        help="[Batch] Maximum number of jobs to process (safety limit)"
    )

    # Batch mode output options
    parser.add_argument(
        "--output-dir",
        type=str,
        help="[Batch] Output directory for batch logs (default: /tmp/gitlab-logs-{pipeline_id})"
    )

    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="[Batch] Create single aggregated log file with all jobs"
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="[Batch] Generate summary report with statistics"
    )

    parser.add_argument(
        "--no-empty",
        action="store_true",
        default=True,
        help="[Batch] Skip jobs with no logs (default: true)"
    )

    parser.add_argument(
        "--parallel",
        type=int,
        default=5,
        help="[Batch] Number of parallel log fetches (default: 5, max: 10)"
    )

    # Output filtering (applies to both single and batch mode)
    parser.add_argument(
        "--tail",
        type=int,
        metavar="N",
        help="Show only last N lines (per job in batch mode)"
    )

    parser.add_argument(
        "--grep",
        type=str,
        metavar="PATTERN",
        help="Filter lines matching pattern (regex, applies per job in batch mode)"
    )

    parser.add_argument(
        "--ignore-case",
        "-i",
        action="store_true",
        help="Case-insensitive pattern matching"
    )

    parser.add_argument(
        "--context",
        "-C",
        type=int,
        metavar="N",
        default=0,
        help="Show N lines of context around matches"
    )

    # Single job mode only options
    parser.add_argument(
        "--line-numbers",
        "-n",
        action="store_true",
        help="[Single job] Show line numbers"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        metavar="FILE",
        help="[Single job] Save logs to file"
    )

    args = parser.parse_args()

    # Validation
    if args.batch:
        if not args.pipeline:
            parser.error("--batch requires --pipeline")
        if args.parallel > 10:
            parser.error("--parallel cannot exceed 10 (API rate limit protection)")
    else:
        # Single job mode
        if not args.job and not args.job_name:
            parser.error("Single job mode requires --job or --job-name")
        if args.job_name and not args.pipeline:
            parser.error("--job-name requires --pipeline")

        # Batch-only options in single job mode
        if args.all or args.failed_only or args.status or args.stage or args.pattern:
            parser.error("--all, --failed-only, --status, --stage, --pattern require --batch")
        if args.output_dir or args.aggregate or args.summary:
            parser.error("--output-dir, --aggregate, --summary require --batch")

    return args


def filter_logs(logs, pattern=None, ignore_case=False, context=0):
    """Filter log lines by pattern.

    Args:
        logs: Log text
        pattern: Regex pattern to match
        ignore_case: Case-insensitive matching
        context: Number of context lines around matches

    Returns:
        Filtered log lines
    """
    if not pattern:
        return logs

    lines = logs.split('\n')
    flags = re.IGNORECASE if ignore_case else 0

    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        print(f"⚠️  Invalid regex pattern: {e}")
        return logs

    # Find matching line indices
    matching_indices = set()
    for i, line in enumerate(lines):
        if regex.search(line):
            # Add the matching line and context
            for j in range(max(0, i - context), min(len(lines), i + context + 1)):
                matching_indices.add(j)

    # Build filtered output
    filtered_lines = []
    for i in sorted(matching_indices):
        filtered_lines.append(lines[i])

    return '\n'.join(filtered_lines)


def tail_logs(logs, n):
    """Get last N lines of logs.

    Args:
        logs: Log text
        n: Number of lines

    Returns:
        Last N lines
    """
    lines = logs.split('\n')
    return '\n'.join(lines[-n:])


def add_line_numbers(logs):
    """Add line numbers to logs.

    Args:
        logs: Log text

    Returns:
        Logs with line numbers
    """
    lines = logs.split('\n')
    width = len(str(len(lines)))
    numbered = [f"{i+1:>{width}}│ {line}" for i, line in enumerate(lines)]
    return '\n'.join(numbered)


def handle_batch_mode(args, gl, project, analyzer):
    """Handle batch mode log retrieval.

    Args:
        args: Parsed arguments
        gl: GitLab client
        project: Project object
        analyzer: PipelineAnalyzer instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Determine output directory
    output_dir = args.output_dir or f"/tmp/gitlab-logs-{args.pipeline}"

    # Get pipeline info
    pipeline = project.pipelines.get(args.pipeline)
    branch = pipeline.ref

    print(f"\n📋 Batch Log Collection")
    print(f"   Pipeline: #{args.pipeline}")
    print(f"   Branch: {branch}")
    print(f"   Output: {output_dir}\n")

    # Determine job filters
    filters = {
        'status': args.status or [],
        'stage': args.stage,
        'pattern': args.pattern,
        'grep': args.grep,
        'tail': args.tail,
        'ignore_case': args.ignore_case,
        'context': args.context
    }

    # Handle --failed-only shortcut
    if args.failed_only:
        filters['status'] = ['failed']

    # Get jobs based on filters
    if args.all:
        print("🔍 Collecting logs from ALL jobs in pipeline...")
        jobs = analyzer.get_all_jobs(args.pipeline)
    elif filters['status']:
        print(f"🔍 Filtering jobs by status: {', '.join(filters['status'])}")
        jobs = analyzer.get_all_jobs(args.pipeline, scope=filters['status'])
    else:
        # Default: get all jobs, will filter later
        jobs = analyzer.get_all_jobs(args.pipeline)

    # Apply additional filters
    if filters['stage']:
        print(f"🔍 Filtering jobs by stage: {filters['stage']}")
        jobs = [j for j in jobs if j.stage == filters['stage']]

    if filters['pattern']:
        import fnmatch
        print(f"🔍 Filtering jobs by pattern: {filters['pattern']}")
        jobs = [j for j in jobs if fnmatch.fnmatch(j.name, filters['pattern'])]

    # Apply max-jobs limit
    if args.max_jobs and len(jobs) > args.max_jobs:
        print(f"⚠️  Limiting to first {args.max_jobs} jobs (total found: {len(jobs)})")
        jobs = jobs[:args.max_jobs]

    if not jobs:
        print("❌ No jobs found matching the specified filters")
        return 1

    print(f"✅ Found {len(jobs)} jobs to process\n")

    # Initialize batch fetcher
    fetcher = BatchLogFetcher(gl, project.id, args.pipeline, output_dir)

    # Create directory structure
    fetcher.create_directory_structure(jobs)

    # Prepare filters dict for log processing
    log_filters = None
    if args.grep or args.tail or args.ignore_case or args.context:
        log_filters = {
            'grep': args.grep,
            'tail': args.tail,
            'ignore_case': args.ignore_case,
            'context': args.context
        }

    # Fetch logs in batch
    results = fetcher.fetch_logs_batch(
        jobs,
        parallel=args.parallel,
        filters=log_filters,
        skip_empty=args.no_empty
    )

    # Save logs to files
    print("\n💾 Saving logs to files...")
    fetcher.save_logs_to_files(results)
    print(f"✅ Logs saved to: {output_dir}/")

    # Generate aggregate log if requested
    if args.aggregate:
        print("\n📑 Creating aggregate log file...")
        aggregate_path = fetcher.create_aggregate_log(results, project.name, branch)
        print(f"✅ Aggregate log: {aggregate_path}")

    # Generate summary report if requested
    if args.summary:
        print("\n📊 Generating summary report...")
        summary_path = fetcher.generate_summary_report(results, project.name, branch, filters)
        print(f"✅ Summary report: {summary_path}")

    # Save manifest
    manifest_path = fetcher.save_manifest(results, project.path_with_namespace, branch, filters)

    # Display final statistics
    stats = results['statistics']
    print("\n" + "=" * 60)
    print("Batch Log Collection Complete!")
    print("=" * 60)
    print(f"✅ Successfully fetched: {stats['jobs_processed']} jobs")
    if stats['jobs_skipped'] > 0:
        print(f"⚠️  No logs available: {stats['jobs_skipped']} jobs")
    if stats['jobs_failed'] > 0:
        print(f"❌ Failed to fetch: {stats['jobs_failed']} jobs")
    print(f"\n📁 Output directory: {output_dir}")
    print(f"📊 Total size: {stats['total_log_size_bytes'] / 1024 / 1024:.1f} MB")
    print(f"📄 Total lines: {stats['total_lines']:,}")
    print(f"⏱️  Processing time: {stats['processing_time_seconds']:.1f}s")

    if args.summary:
        print(f"\n💡 View summary report:")
        print(f"   cat {summary_path}")

    print(f"\n💡 Quick actions:")
    print(f"   • View failed jobs:  cd {output_dir}/by-status && ls -lh")
    print(f"   • Search all logs:   grep -r 'ERROR' {output_dir}/all/")
    if args.aggregate:
        print(f"   • View aggregate:    less {aggregate_path}")

    return 0


def handle_single_job(args, gl, project, analyzer):
    """Handle single job log retrieval (existing functionality).

    Args:
        args: Parsed arguments
        gl: GitLab client
        project: Project object
        analyzer: PipelineAnalyzer instance (optional, for job-name lookup)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Determine job ID
    if args.job_name:
        # Find job by name using pipeline analyzer
        print(f"🔍 Finding job '{args.job_name}' in pipeline {args.pipeline}...")
        jobs = analyzer.find_job_by_name(args.pipeline, args.job_name)

        if not jobs:
            print(f"❌ Job '{args.job_name}' not found in pipeline {args.pipeline}")
            return 1

        if len(jobs) > 1:
            print(f"⚠️  Found {len(jobs)} jobs with name '{args.job_name}':")
            for j in jobs:
                print(f"   - ID: {j.id}, Status: {j.status}")
            print(f"\n   Using most recent job (ID: {jobs[0].id})")

        job = project.jobs.get(jobs[0].id)
    else:
        # Get job by ID
        print(f"📋 Getting job {args.job} details...")
        job = project.jobs.get(args.job)

    print(f"✅ Job: {job.name} (Status: {job.status})\n")

    # Get job logs using python-gitlab
    print("📥 Downloading job trace...")
    try:
        logs = job.trace().decode('utf-8')
    except Exception as e:
        print(f"❌ Failed to get job trace: {e}")
        print(f"   Job may not have started yet or logs may not be available")
        return 1

    if not logs or not logs.strip():
        print("⚠️  No logs available for this job")
        return 0

    # Apply filters
    if args.grep:
        print(f"🔍 Filtering for pattern: {args.grep}")
        logs = filter_logs(logs, args.grep, args.ignore_case, args.context)

    if args.tail:
        print(f"📄 Showing last {args.tail} lines")
        logs = tail_logs(logs, args.tail)

    if args.line_numbers:
        logs = add_line_numbers(logs)

    # Output logs
    print("\n" + "="*60)
    print(f"Job Logs: {job.name} (ID: {job.id})")
    print("="*60 + "\n")

    if args.output:
        with open(args.output, 'w') as f:
            f.write(logs)
        print(f"✅ Logs saved to: {args.output}")
        print(f"\n📊 Log statistics:")
        print(f"   Total lines: {len(logs.split(chr(10)))}")
        print(f"   Total size: {len(logs)} bytes")
    else:
        print(logs)

        # Print statistics
        print("\n" + "="*60)
        print(f"📊 Log statistics:")
        print(f"   Total lines: {len(logs.split(chr(10)))}")
        print(f"   Total size: {len(logs)} bytes")

    return 0


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
            # Try to auto-resolve
            print("🔍 Auto-resolving project from current directory...")
            resolver = ProjectResolver(gitlab_client=gl)
            project_id, project_name, project_path = resolver.resolve_from_repo()
            project = gl.projects.get(project_id)
            print(f"✅ Project: {project_name} (ID: {project.id})")

        # Initialize pipeline analyzer (needed for both modes)
        analyzer = PipelineAnalyzer(gl, project.id) if args.batch or args.job_name else None

        # Route to appropriate handler
        if args.batch:
            return handle_batch_mode(args, gl, project, analyzer)
        else:
            return handle_single_job(args, gl, project, analyzer)

    except Exception as e:
        print(f"❌ Operation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
