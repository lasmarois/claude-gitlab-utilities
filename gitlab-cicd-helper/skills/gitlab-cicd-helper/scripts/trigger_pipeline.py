#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#     "python-gitlab>=4.0.0",
#     "pyyaml>=6.0",
# ]
# ///
"""
Trigger a GitLab pipeline with optional variables.

Usage:
    trigger_pipeline.py --auto [--ref REF] [--var KEY=VALUE]...
    trigger_pipeline.py --project PROJECT_ID [--ref REF] [--var KEY=VALUE]...
    trigger_pipeline.py --project-path PATH [--ref REF] [--var KEY=VALUE]...

Examples:
    # Auto-resolve from current git repo
    trigger_pipeline.py --auto --ref main

    # With variables
    trigger_pipeline.py --auto --ref main --var ENVIRONMENT=production --var DEBUG=true

    # Explicit project ID
    trigger_pipeline.py --project 1603 --ref main

    # Explicit project path
    trigger_pipeline.py --project-path operations/infrastructure/misc/runner-troubleshooter --ref main
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
        description="Trigger a GitLab pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Project specification (mutually exclusive)
    project_group = parser.add_mutually_exclusive_group(required=True)
    project_group.add_argument(
        "--auto",
        action="store_true",
        help="Auto-resolve project from current git repository"
    )
    project_group.add_argument(
        "--project",
        type=str,
        help="Project ID (numeric)"
    )
    project_group.add_argument(
        "--project-path",
        type=str,
        help="Project path (e.g., 'group/subgroup/project')"
    )

    # Pipeline options
    parser.add_argument(
        "--ref",
        type=str,
        default="main",
        help="Branch or tag name (default: main)"
    )

    parser.add_argument(
        "--var",
        action="append",
        dest="variables",
        metavar="KEY=VALUE",
        help="Pipeline variable (can be specified multiple times)"
    )

    parser.add_argument(
        "--show-structure",
        action="store_true",
        help="Show pipeline structure after triggering"
    )

    return parser.parse_args()


def parse_variables(var_list):
    """Parse variable list from KEY=VALUE format.

    Args:
        var_list: List of 'KEY=VALUE' strings

    Returns:
        Dictionary of variables
    """
    if not var_list:
        return {}

    variables = {}
    for var in var_list:
        if '=' not in var:
            print(f"⚠️  Warning: Ignoring invalid variable format: {var}")
            print(f"   Expected format: KEY=VALUE")
            continue

        key, value = var.split('=', 1)
        variables[key] = value

    return variables


def trigger_pipeline(project, ref, variables=None, trigger_token=None):
    """Trigger pipeline using python-gitlab.

    Args:
        project: GitLab project object
        ref: Branch or tag to trigger on
        variables: Optional dictionary of pipeline variables
        trigger_token: Optional trigger token (if None, uses pipeline create endpoint)

    Returns:
        Created pipeline object
    """
    # Prepare variables for GitLab API format
    if variables:
        var_list = [{"key": k, "value": v} for k, v in variables.items()]
    else:
        var_list = []

    # Create pipeline
    pipeline = project.pipelines.create({'ref': ref, 'variables': var_list})

    return pipeline


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
            print("🔍 Auto-resolving project from git remote...")
            resolver = ProjectResolver(gitlab_client=gl)
            project_id, project_name, project_path = resolver.resolve_from_repo()
            project = gl.projects.get(project_id)
            print(f"✅ Project resolved: {project_name} (ID: {project.id})")

        elif args.project:
            project_identifier = args.project
            project = gl.projects.get(project_identifier)
            print(f"✅ Using project: {project.name} (ID: {project.id})")

        elif args.project_path:
            # Use direct path lookup (python-gitlab handles encoding)
            project = gl.projects.get(args.project_path)
            print(f"✅ Using project: {project.name} (ID: {project.id})")

        # Parse variables
        variables = parse_variables(args.variables)
        if variables:
            print(f"\n📋 Pipeline variables:")
            for key, value in variables.items():
                print(f"   {key}={value}")

        # Trigger pipeline
        print(f"\n🚀 Triggering pipeline on '{args.ref}'...")

        # Get trigger token if available (for trigger endpoint)
        try:
            trigger_token = config.get_trigger_token()
            has_trigger_token = True
        except ValueError:
            trigger_token = None
            has_trigger_token = False

        pipeline = trigger_pipeline(project, args.ref, variables, trigger_token)

        # Display result
        print(f"\n{'='*60}")
        print(f"✅ Pipeline #{pipeline.id} created successfully")
        print(f"{'='*60}")
        print(f"Pipeline ID: {pipeline.id}")
        print(f"Status: {pipeline.status}")
        print(f"Branch: {pipeline.ref}")
        print(f"Created: {pipeline.created_at}")
        print(f"🔗 Monitor at: {pipeline.web_url}")
        print(f"{'='*60}\n")

        # Show pipeline structure if requested
        if args.show_structure:
            print("⏳ Waiting for pipeline to initialize (2 seconds)...")
            time.sleep(2)

            analyzer = PipelineAnalyzer(gl, project.id)
            analyzer.display_pipeline_summary(pipeline.id)

            # Show executable jobs
            executable = analyzer.get_executable_jobs(pipeline.id)
            if executable['manual']:
                print(f"🎯 {len(executable['manual'])} manual jobs ready to launch")
                print(f"   Use: ./scripts/launch_jobs.py --pipeline {pipeline.id} --batch\n")

        return 0

    except Exception as e:
        print(f"❌ Pipeline trigger failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
