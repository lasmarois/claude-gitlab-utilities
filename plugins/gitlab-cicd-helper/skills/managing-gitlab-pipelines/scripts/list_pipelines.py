#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "python-gitlab>=4.0.0",
# ]
# ///
"""
List GitLab pipelines for a project.

Usage:
    list_pipelines.py --auto [--limit N] [--ref REF] [--status STATUS]
    list_pipelines.py --project PROJECT_ID [--limit N] [--ref REF] [--status STATUS]
    list_pipelines.py --auto --latest [--ref REF]

Examples:
    # List recent pipelines (default: 10)
    list_pipelines.py --auto

    # List more pipelines
    list_pipelines.py --auto --limit 20

    # List pipelines on specific branch
    list_pipelines.py --auto --ref main

    # List failed pipelines
    list_pipelines.py --auto --status failed

    # List running pipelines
    list_pipelines.py --auto --status running

    # Get the latest pipeline ID only (for scripting)
    list_pipelines.py --auto --latest

    # Get latest pipeline on specific branch
    list_pipelines.py --auto --latest --ref main

    # Combine filters
    list_pipelines.py --auto --ref main --status success --limit 5
"""

import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from gitlab_config import GitLabConfig
from project_resolver import ProjectResolver


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="List GitLab pipelines for a project",
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

    # Filter options
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of pipelines to list (default: 10)"
    )

    parser.add_argument(
        "--ref",
        type=str,
        help="Filter by branch or tag name"
    )

    parser.add_argument(
        "--status",
        type=str,
        choices=[
            "created", "waiting_for_resource", "preparing", "pending",
            "running", "success", "failed", "canceled", "skipped",
            "manual", "scheduled"
        ],
        help="Filter by pipeline status"
    )

    parser.add_argument(
        "--source",
        type=str,
        choices=[
            "push", "web", "trigger", "schedule", "api", "external",
            "pipeline", "chat", "webide", "merge_request_event",
            "external_pull_request_event", "parent_pipeline",
            "ondemand_dast_scan", "ondemand_dast_validation"
        ],
        help="Filter by pipeline source"
    )

    parser.add_argument(
        "--username",
        type=str,
        help="Filter by username who triggered the pipeline"
    )

    # Output options
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Output only the latest pipeline ID (for scripting)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Output only pipeline IDs, one per line"
    )

    return parser.parse_args()


def format_pipeline_status_emoji(status):
    """Get emoji for pipeline status."""
    emojis = {
        'success': '✅',
        'failed': '❌',
        'running': '▶️',
        'pending': '⏳',
        'canceled': '⊗',
        'skipped': '⊘',
        'manual': '⚙️',
        'created': '◯',
        'waiting_for_resource': '⏸️',
        'preparing': '🔧',
        'scheduled': '📅'
    }
    return emojis.get(status, '❓')


def format_time_ago(dt_str):
    """Format datetime string as relative time."""
    if not dt_str:
        return "unknown"

    try:
        # Parse ISO format datetime
        if dt_str.endswith('Z'):
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(dt_str)

        # Make sure we have timezone-aware datetime
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        diff = now - dt

        seconds = diff.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}d ago"
        else:
            weeks = int(seconds / 604800)
            return f"{weeks}w ago"
    except Exception:
        return dt_str[:10] if len(dt_str) >= 10 else dt_str


def list_pipelines(project, limit=10, ref=None, status=None, source=None, username=None):
    """List pipelines for a project.

    Args:
        project: GitLab project object
        limit: Maximum number of pipelines to return
        ref: Filter by branch/tag name
        status: Filter by pipeline status
        source: Filter by pipeline source
        username: Filter by username

    Returns:
        List of pipeline objects
    """
    # Build filter kwargs
    kwargs = {'per_page': limit}

    if ref:
        kwargs['ref'] = ref
    if status:
        kwargs['status'] = status
    if source:
        kwargs['source'] = source
    if username:
        kwargs['username'] = username

    # Get pipelines (already ordered by ID desc by default)
    pipelines = project.pipelines.list(**kwargs)

    return pipelines


def main():
    """Main entry point."""
    args = parse_args()

    try:
        # Initialize configuration and client
        if not args.quiet and not args.latest and not args.json:
            print("🔐 Validating tokens...")

        config = GitLabConfig()
        gl = config.get_gitlab_client()

        if not args.quiet and not args.latest and not args.json:
            print("✅ Tokens validated")

        # Determine project identifier
        if args.auto:
            if not args.quiet and not args.latest and not args.json:
                print("🔍 Auto-resolving project...")
            resolver = ProjectResolver(gitlab_client=gl)
            project_id, project_name, project_path = resolver.resolve_from_repo()
            project = gl.projects.get(project_id)
            if not args.quiet and not args.latest and not args.json:
                print(f"✅ Project: {project_name} (ID: {project.id})\n")
        elif args.project:
            project = gl.projects.get(args.project)
            if not args.quiet and not args.latest and not args.json:
                print(f"✅ Project: {project.name} (ID: {project.id})\n")
        else:
            # Try to auto-resolve
            if not args.quiet and not args.latest and not args.json:
                print("🔍 Auto-resolving project from current directory...")
            resolver = ProjectResolver(gitlab_client=gl)
            project_id, project_name, project_path = resolver.resolve_from_repo()
            project = gl.projects.get(project_id)
            if not args.quiet and not args.latest and not args.json:
                print(f"✅ Project: {project_name} (ID: {project.id})\n")

        # Get pipelines
        pipelines = list_pipelines(
            project,
            limit=args.limit,
            ref=args.ref,
            status=args.status,
            source=args.source,
            username=args.username
        )

        if not pipelines:
            if args.latest:
                print("")  # Empty output for scripting
                return 1
            elif args.json:
                print("[]")
                return 0
            elif args.quiet:
                return 0
            else:
                print("⚠️  No pipelines found matching criteria")
                return 0

        # Output based on format
        if args.latest:
            # Just output the latest pipeline ID
            print(pipelines[0].id)
            return 0

        elif args.json:
            import json
            output = []
            for p in pipelines:
                output.append({
                    'id': p.id,
                    'status': p.status,
                    'ref': p.ref,
                    'sha': p.sha[:8] if hasattr(p, 'sha') and p.sha else None,
                    'source': p.source if hasattr(p, 'source') else None,
                    'created_at': p.created_at,
                    'updated_at': p.updated_at,
                    'web_url': p.web_url
                })
            print(json.dumps(output, indent=2))
            return 0

        elif args.quiet:
            # Just output pipeline IDs
            for p in pipelines:
                print(p.id)
            return 0

        else:
            # Pretty formatted output
            # Build filter description
            filters = []
            if args.ref:
                filters.append(f"ref={args.ref}")
            if args.status:
                filters.append(f"status={args.status}")
            if args.source:
                filters.append(f"source={args.source}")
            if args.username:
                filters.append(f"user={args.username}")

            filter_str = f" ({', '.join(filters)})" if filters else ""

            print(f"{'='*80}")
            print(f"📋 Recent Pipelines{filter_str}")
            print(f"{'='*80}")

            for p in pipelines:
                emoji = format_pipeline_status_emoji(p.status)
                time_ago = format_time_ago(p.created_at)
                sha_short = p.sha[:8] if hasattr(p, 'sha') and p.sha else "--------"
                source = p.source if hasattr(p, 'source') else "unknown"

                # Main line
                print(f"\n{emoji} Pipeline #{p.id}")
                print(f"   Branch: {p.ref}")
                print(f"   Status: {p.status}")
                print(f"   Commit: {sha_short}")
                print(f"   Source: {source}")
                print(f"   Created: {time_ago}")
                print(f"   🔗 {p.web_url}")

            print(f"\n{'='*80}")
            print(f"Total: {len(pipelines)} pipeline(s)")

            # Show helpful commands
            if pipelines:
                latest_id = pipelines[0].id
                print(f"\n💡 Quick actions for latest pipeline #{latest_id}:")
                print(f"   Monitor:  ./scripts/monitor_status.py --pipeline {latest_id} --auto --watch")
                print(f"   Jobs:     ./scripts/launch_jobs.py --pipeline {latest_id} --auto --batch")
                print(f"   Logs:     ./scripts/get_logs.py --pipeline {latest_id} --auto --batch --failed-only --summary")

            print(f"{'='*80}\n")

            return 0

    except Exception as e:
        print(f"❌ Failed to list pipelines: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
