#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "python-gitlab>=4.0.0",
#     "pyyaml>=6.0",
# ]
# ///
"""
Monitor GitLab pipeline or job status.

Usage:
    monitor_status.py --pipeline PIPELINE_ID [--auto | --project PROJECT_ID]
    monitor_status.py --job JOB_ID [--auto | --project PROJECT_ID]
    monitor_status.py --pipeline PIPELINE_ID --watch [--interval SECONDS]
    monitor_status.py --job JOB_ID --watch [--interval SECONDS]

Examples:
    # Show pipeline status
    monitor_status.py --pipeline 12345 --auto

    # Show job status
    monitor_status.py --job 67890 --auto

    # Watch pipeline with auto-refresh
    monitor_status.py --pipeline 12345 --auto --watch --interval 10

    # Watch job until completion
    monitor_status.py --job 67890 --auto --watch

    # Show full pipeline structure
    monitor_status.py --pipeline 12345 --auto --structure

    # Compare config vs actual state
    monitor_status.py --pipeline 12345 --auto --compare
"""

import sys
import argparse
import time
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from gitlab_config import GitLabConfig
from pipeline_analyzer import PipelineAnalyzer
from project_resolver import ProjectResolver


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Monitor GitLab pipeline or job status",
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

    # Target specification (mutually exclusive)
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--pipeline",
        type=int,
        help="Pipeline ID to monitor"
    )
    target_group.add_argument(
        "--job",
        type=int,
        help="Job ID to monitor"
    )

    # Watch options
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch with auto-refresh until completion"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Refresh interval in seconds for watch mode (default: 5)"
    )

    parser.add_argument(
        "--watch-pattern",
        type=str,
        help="Job name pattern for targeted watch (stops when matching jobs reach terminal status)"
    )

    parser.add_argument(
        "--show-jobs",
        action="store_true",
        help="Show jobs list for pipeline monitoring"
    )

    # Pipeline awareness options
    parser.add_argument(
        "--structure",
        action="store_true",
        help="Show full pipeline structure (uses PipelineAnalyzer)"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare .gitlab-ci.yml config vs actual pipeline state"
    )

    return parser.parse_args()


def format_job_status_emoji(status):
    """Get emoji for job status."""
    emojis = {
        'success': '✅',
        'failed': '❌',
        'running': '▶️',
        'pending': '⏳',
        'canceled': '⊗',
        'skipped': '⊘',
        'manual': '⚙️',
        'created': '◯'
    }
    return emojis.get(status, '❓')


def monitor_pipeline(analyzer, pipeline_id, show_jobs=False, previous_jobs=None):
    """Monitor pipeline status using PipelineAnalyzer.

    Args:
        analyzer: PipelineAnalyzer instance
        pipeline_id: Pipeline ID
        show_jobs: Show jobs list
        previous_jobs: Dict of previous job statuses for change tracking

    Returns:
        Tuple of (pipeline_status, current_jobs_dict)
    """
    pipeline = analyzer.get_pipeline(pipeline_id)

    # Display pipeline info
    print(f"\n{'='*60}")
    print(f"Pipeline #{pipeline.id}")
    print(f"{'='*60}")
    print(f"Status: {pipeline.status}")
    print(f"Branch: {pipeline.ref}")
    print(f"Created: {pipeline.created_at}")
    print(f"Updated: {pipeline.updated_at}")
    print(f"🔗 {pipeline.web_url}")

    # Get pipeline summary for progress stats
    summary = analyzer.get_pipeline_summary(pipeline_id)
    jobs_by_status = summary.get('jobs_by_status', {})
    total_jobs = summary.get('total_jobs', 0)

    # Calculate completion info
    completed_jobs = jobs_by_status.get('success', 0) + jobs_by_status.get('failed', 0) + jobs_by_status.get('canceled', 0) + jobs_by_status.get('skipped', 0)
    completion_pct = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0

    # Show progress summary
    print(f"\n📊 Progress: {completed_jobs}/{total_jobs} jobs ({completion_pct:.0f}%)")

    # Show job counts by status
    status_line_parts = []
    if jobs_by_status.get('running', 0) > 0:
        status_line_parts.append(f"▶️  {jobs_by_status['running']} running")
    if jobs_by_status.get('pending', 0) > 0:
        status_line_parts.append(f"⏳ {jobs_by_status['pending']} pending")
    if jobs_by_status.get('success', 0) > 0:
        status_line_parts.append(f"✅ {jobs_by_status['success']} success")
    if jobs_by_status.get('failed', 0) > 0:
        status_line_parts.append(f"❌ {jobs_by_status['failed']} failed")
    if jobs_by_status.get('manual', 0) > 0:
        status_line_parts.append(f"⚙️  {jobs_by_status['manual']} manual")
    if jobs_by_status.get('created', 0) > 0:
        status_line_parts.append(f"◯ {jobs_by_status['created']} created")

    if status_line_parts:
        print(f"   {' | '.join(status_line_parts)}")

    # Get all jobs for tracking and display
    all_jobs = analyzer.get_all_jobs(pipeline_id)

    # Build current jobs dict for tracking
    current_jobs = {job.id: {'name': job.name, 'status': job.status} for job in all_jobs}

    # Detect running jobs
    running_jobs = [job for job in all_jobs if job.status == 'running']

    # Detect changed jobs (if we have previous state)
    changed_jobs = []
    if previous_jobs:
        for job in all_jobs:
            if job.id in previous_jobs:
                prev_status = previous_jobs[job.id]['status']
                if prev_status != job.status:
                    changed_jobs.append({
                        'job': job,
                        'prev_status': prev_status,
                        'current_status': job.status
                    })

    # Show running jobs prominently
    if running_jobs:
        print(f"\n🔄 Currently Running ({len(running_jobs)}):")
        for job in running_jobs:
            # Try to get duration if available
            duration_str = ""
            if hasattr(job, 'duration') and job.duration:
                minutes = int(job.duration) // 60
                seconds = int(job.duration) % 60
                duration_str = f" ({minutes}m {seconds}s)"
            print(f"   ▶️  {job.name} [{job.stage}]{duration_str}")

    # Show recently changed jobs
    if changed_jobs:
        print(f"\n✨ Recently Changed ({len(changed_jobs)}):")
        for change in changed_jobs:
            job = change['job']
            prev_emoji = format_job_status_emoji(change['prev_status'])
            curr_emoji = format_job_status_emoji(change['current_status'])
            print(f"   {curr_emoji} {job.name} → {change['current_status']} (was {prev_emoji} {change['prev_status']})")

    # Show jobs if requested
    if show_jobs:
        # Use proper pagination to get ALL jobs (already fetched above)
        jobs_by_stage = analyzer.get_jobs_by_stage(pipeline_id)

        print(f"\n📋 Jobs ({len(all_jobs)} total):")
        for stage, jobs in jobs_by_stage.items():
            print(f"\n  {stage}:")
            for job in sorted(jobs, key=lambda j: j.name):
                emoji = format_job_status_emoji(job.status)
                print(f"    {emoji} {job.name} [{job.status}]")

    print(f"{'='*60}\n")

    return pipeline.status, current_jobs


def monitor_job(project, job_id):
    """Monitor job status using python-gitlab.

    Args:
        project: GitLab project object
        job_id: Job ID

    Returns:
        Job status string
    """
    job = project.jobs.get(job_id)

    # Display job info
    print(f"\n{'='*60}")
    print(f"Job #{job.id}: {job.name}")
    print(f"{'='*60}")
    emoji = format_job_status_emoji(job.status)
    print(f"Status: {emoji} {job.status}")
    print(f"Stage: {job.stage}")
    print(f"Pipeline: #{job.pipeline['id']}")

    # Show timing information
    if hasattr(job, 'started_at') and job.started_at:
        print(f"Started: {job.started_at}")
    if hasattr(job, 'finished_at') and job.finished_at:
        print(f"Finished: {job.finished_at}")
    if hasattr(job, 'duration') and job.duration:
        print(f"Duration: {job.duration}s")

    if hasattr(job, 'web_url'):
        print(f"🔗 {job.web_url}")

    print(f"{'='*60}\n")

    return job.status


def is_terminal_status(status):
    """Check if status is terminal (completed, no more updates expected).

    Args:
        status: Job or pipeline status

    Returns:
        True if terminal, False otherwise
    """
    terminal_statuses = ['success', 'failed', 'canceled', 'skipped']
    return status in terminal_statuses


def check_pattern_completion(analyzer, pipeline_id, pattern):
    """Check if all jobs matching a pattern have reached terminal status.

    Args:
        analyzer: PipelineAnalyzer instance
        pipeline_id: Pipeline ID
        pattern: Job name pattern (glob-style, e.g., 'ca-cert:*')

    Returns:
        Tuple of (all_complete: bool, stats: dict)
        stats contains: {
            'total': int,
            'completed': int,
            'terminal_jobs': list,
            'non_terminal_jobs': list,
            'error': str (optional, 'no_matches' if pattern matches nothing)
        }
    """
    # Get jobs matching pattern
    matching_jobs = analyzer.find_jobs_by_pattern(pipeline_id, pattern)

    if not matching_jobs:
        # No jobs match pattern - could be edge case
        return False, {
            'total': 0,
            'completed': 0,
            'terminal_jobs': [],
            'non_terminal_jobs': [],
            'error': 'no_matches'
        }

    # Check terminal status for each matching job
    terminal_jobs = []
    non_terminal_jobs = []

    for job in matching_jobs:
        if is_terminal_status(job.status):
            terminal_jobs.append({'id': job.id, 'name': job.name, 'status': job.status})
        else:
            non_terminal_jobs.append({'id': job.id, 'name': job.name, 'status': job.status})

    total = len(matching_jobs)
    completed = len(terminal_jobs)
    all_complete = (completed == total)

    return all_complete, {
        'total': total,
        'completed': completed,
        'terminal_jobs': terminal_jobs,
        'non_terminal_jobs': non_terminal_jobs
    }


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
            print(f"✅ Project: {project_name} (ID: {project.id})\n")
        elif args.project:
            project_identifier = args.project
            project = gl.projects.get(project_identifier)
            print(f"✅ Project: {project.name} (ID: {project.id})\n")
        else:
            # Try to auto-resolve
            print("🔍 Auto-resolving project from current directory...")
            resolver = ProjectResolver(gitlab_client=gl)
            project_id, project_name, project_path = resolver.resolve_from_repo()
            project = gl.projects.get(project_id)
            print(f"✅ Project: {project_name} (ID: {project.id})\n")

        # Initialize pipeline analyzer
        analyzer = PipelineAnalyzer(gl, project.id)

        # Monitor pipeline or job
        if args.pipeline:
            # Show full structure if requested
            if args.structure:
                analyzer.display_pipeline_summary(args.pipeline)
                return 0

            # Show config comparison if requested
            if args.compare:
                print("📊 Comparing .gitlab-ci.yml config vs pipeline state...\n")

                # Get pipeline info
                pipeline = analyzer.get_pipeline(args.pipeline)
                ref = pipeline.ref

                # Parse config
                print(f"🔍 Parsing .gitlab-ci.yml from {ref}...")
                config_data = analyzer.parse_gitlab_ci_config(ref)

                if config_data:
                    print("✅ Config parsed successfully")

                    # Get actual pipeline state with proper pagination
                    all_jobs = analyzer.get_all_jobs(args.pipeline)
                    summary = analyzer.get_pipeline_summary(args.pipeline)

                    print(f"\n📋 Pipeline Summary:")
                    print(f"   Total jobs: {summary['total_jobs']}")
                    print(f"   Stages: {len(summary['stages'])}")
                    print(f"\n   Jobs by status:")
                    for status, count in sorted(summary['jobs_by_status'].items()):
                        emoji = format_job_status_emoji(status)
                        print(f"      {emoji} {status:12} {count:3} jobs")
                else:
                    print("⚠️  Could not parse .gitlab-ci.yml")

                return 0

            # Standard monitoring
            if args.watch:
                print(f"👁️  Watching pipeline {args.pipeline} (refresh every {args.interval}s, Ctrl+C to stop)")

                # Pattern-aware watch setup
                if args.watch_pattern:
                    print(f"🎯 Pattern-aware watch: monitoring jobs matching '{args.watch_pattern}'")
                    print(f"   Watch will stop when all matching jobs reach terminal status")

                    # Initial pattern validation
                    initial_matches = analyzer.find_jobs_by_pattern(args.pipeline, args.watch_pattern)
                    if not initial_matches:
                        print(f"⚠️  Warning: No jobs currently match pattern '{args.watch_pattern}'")
                        print(f"   Watching for jobs to appear (pattern matching is dynamic)...")

                print()  # blank line

                iteration = 0
                previous_jobs = None
                no_match_iterations = 0  # Track iterations with no pattern matches

                while True:
                    if iteration > 0:
                        # Clear screen for better readability
                        print("\n" + "="*60)
                        print(f"Refresh #{iteration} at {time.strftime('%H:%M:%S')}")
                        print("="*60 + "\n")

                    status, current_jobs = monitor_pipeline(analyzer, args.pipeline, show_jobs=args.show_jobs or args.watch, previous_jobs=previous_jobs)

                    # Check termination conditions
                    if args.watch_pattern:
                        # Pattern-aware termination
                        all_complete, stats = check_pattern_completion(
                            analyzer, args.pipeline, args.watch_pattern
                        )

                        if stats.get('error') == 'no_matches':
                            no_match_iterations += 1
                            if no_match_iterations >= 5:  # Give 5 iterations for jobs to appear
                                print(f"\n⚠️  No jobs match pattern '{args.watch_pattern}' after {no_match_iterations} checks")
                                print(f"   Stopping watch (pattern may be incorrect or jobs not yet created)")
                                print(f"\n💡 Tip: Check available jobs with:")
                                print(f"   ./scripts/monitor_status.py --pipeline {args.pipeline} --show-jobs")
                                break
                        elif all_complete:
                            # All pattern-matching jobs are done!
                            print(f"\n✅ All jobs matching '{args.watch_pattern}' completed!")
                            print(f"   {stats['completed']}/{stats['total']} jobs reached terminal status")
                            print(f"\n📊 Final Status Breakdown:")

                            # Group by status
                            status_groups = {}
                            for job in stats['terminal_jobs']:
                                job_status = job['status']
                                if job_status not in status_groups:
                                    status_groups[job_status] = []
                                status_groups[job_status].append(job['name'])

                            for job_status in sorted(status_groups.keys()):
                                emoji = format_job_status_emoji(job_status)
                                count = len(status_groups[job_status])
                                print(f"   {emoji} {job_status}: {count} job(s)")
                                for job_name in status_groups[job_status]:
                                    print(f"      - {job_name}")

                            # Note about non-matching jobs
                            all_jobs = analyzer.get_all_jobs(args.pipeline)
                            other_jobs = len(all_jobs) - stats['total']
                            if other_jobs > 0:
                                print(f"\nℹ️  Note: {other_jobs} other pipeline jobs are still running/pending")
                                print(f"   Use --watch without --watch-pattern to monitor entire pipeline")

                            break
                        else:
                            # Still waiting on some jobs
                            no_match_iterations = 0  # Reset counter since we found matches
                            print(f"\n🎯 Pattern Watch Progress: {stats['completed']}/{stats['total']} jobs complete")
                            if stats['non_terminal_jobs']:
                                print(f"   Still waiting on {len(stats['non_terminal_jobs'])} job(s):")
                                for job in stats['non_terminal_jobs'][:5]:  # Show first 5
                                    emoji = format_job_status_emoji(job['status'])
                                    print(f"      {emoji} {job['name']} [{job['status']}]")
                                if len(stats['non_terminal_jobs']) > 5:
                                    print(f"      ... and {len(stats['non_terminal_jobs']) - 5} more")
                    else:
                        # Standard pipeline-level termination (existing behavior)
                        if is_terminal_status(status):
                            print(f"\n✅ Pipeline reached terminal status: {status}")
                            break

                    # Update previous_jobs for next iteration
                    previous_jobs = current_jobs
                    iteration += 1
                    time.sleep(args.interval)
            else:
                status, _ = monitor_pipeline(analyzer, args.pipeline, show_jobs=args.show_jobs)

        elif args.job:
            if args.watch:
                print(f"👁️  Watching job {args.job} (refresh every {args.interval}s, Ctrl+C to stop)\n")
                iteration = 0
                while True:
                    if iteration > 0:
                        print("\n" + "="*60)
                        print(f"Refresh #{iteration} at {time.strftime('%H:%M:%S')}")
                        print("="*60 + "\n")

                    status = monitor_job(project, args.job)

                    if is_terminal_status(status):
                        print(f"\n✅ Job reached terminal status: {status}")
                        break

                    iteration += 1
                    time.sleep(args.interval)
            else:
                status = monitor_job(project, args.job)

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
