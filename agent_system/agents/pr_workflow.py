from rich.console import Console
import subprocess
from pathlib import Path
import os
import sys
from agent_system.validate_code_quality import check_code_quality, display_results
from agent_system.code_quality_autofix import fix_files_in_directory
import logging

logger = logging.getLogger(__name__)
#!/usr/bin/env python3


# Add parent directory to path to access utilities
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))


console = Console()


def run_quality_check(changed_files=None, autofix=True):
    """
    Run code quality checks on changed files before PR submission

    Args:
        changed_files: List of file paths that were changed
        autofix: Whether to attempt automatic fixes for common issues

    Returns:
        Boolean indicating if the check passed
    """
    # If no specific files are provided, check the entire repo
    if not changed_files:
        console.print("[blue]No specific files provided. Checking entire repository...[/blue]")
        backend_dir = parent_dir / "app"
        frontend_dir = parent_dir / "app"

        # First attempt to fix common issues
        if autofix:
            console.print("[yellow]Attempting to fix common code quality issues...[/yellow]")
            fixed_backend, _ = fix_files_in_directory(backend_dir)
            fixed_frontend, _ = fix_files_in_directory(frontend_dir)
            console.print(f"[green]Fixed {fixed_backend + fixed_frontend} files automatically[/green]")

        # Now check quality
        backend_results = check_code_quality(backend_dir)
        frontend_results = check_code_quality(frontend_dir)

        # Merge results
        all_results = {
            "total_files": backend_results["total_files"] + frontend_results["total_files"],
            "issues_by_severity": {
                "error": backend_results["issues_by_severity"]["error"] + frontend_results["issues_by_severity"]["error"],
                "warning": backend_results["issues_by_severity"]["warning"] + frontend_results["issues_by_severity"]["warning"],
                "info": backend_results["issues_by_severity"]["info"] + frontend_results["issues_by_severity"]["info"]
            },
            "issues_by_language": {},
            "files_with_issues": backend_results["files_with_issues"] + frontend_results["files_with_issues"],
            "passed_files": backend_results["passed_files"] + frontend_results["passed_files"]
        }

        # Merge language issues
        for results in [backend_results, frontend_results]:
            for lang, counts in results["issues_by_language"].items():
                if lang not in all_results["issues_by_language"]:
                    all_results["issues_by_language"][lang] = counts.copy()
                else:
                    for key, value in counts.items():
                        all_results["issues_by_language"][lang][key] += value

        # Display results with detailed output
        return display_results(all_results, detailed=True)
    else:
        # Check only changed files
        console.print(f"[blue]Checking {len(changed_files)} changed files...[/blue]")

        # Group files by directory
        directories = {}
        for file_path in changed_files:
            file_path = Path(file_path)
            directory = file_path.parent
            if directory not in directories:
                directories[directory] = []
            directories[directory].append(file_path)

        # Fix and check each directory
        all_results = {
            "total_files": len(changed_files),
            "issues_by_severity": {"error": 0, "warning": 0, "info": 0},
            "issues_by_language": {},
            "files_with_issues": [],
            "passed_files": []
        }

        for directory, files in directories.items():
            if autofix:
                fix_files_in_directory(directory)

            # Check quality
            results = check_code_quality(directory)

            # Filter results to only include changed files
            filtered_files_with_issues = []
            for file_data in results["files_with_issues"]:
                file_path = Path(file_data["file"])
                full_path = directory / file_path
                if full_path in files:
                    filtered_files_with_issues.append(file_data)

            filtered_passed_files = []
            for file_path in results["passed_files"]:
                full_path = directory / Path(file_path)
                if full_path in files:
                    filtered_passed_files.append(file_path)

            # Update results
            all_results["files_with_issues"].extend(filtered_files_with_issues)
            all_results["passed_files"].extend(filtered_passed_files)

            # Update counts
            for file_data in filtered_files_with_issues:
                for issue in file_data["issues"]:
                    severity = issue.get("severity", "info")
                    all_results["issues_by_severity"][severity] += 1

                    lang = file_data["language"]
                    if lang not in all_results["issues_by_language"]:
                        all_results["issues_by_language"][lang] = {"total": 0, "error": 0, "warning": 0, "info": 0}

                    all_results["issues_by_language"][lang][severity] += 1
                    all_results["issues_by_language"][lang]["total"] += 1

        # Display results with detailed output
        return display_results(all_results, detailed=True)


def main():
    """Entry point for pre-commit hook"""
    # Get list of changed files from git
    try:
        result = subprocess.run(
            ["git", "diff", "--staged", "--name-only"],
            capture_output=True,
            text=True,
            check=True
        )

        changed_files = [file.strip() for file in result.stdout.split("\n") if file.strip()]

        # Filter for code files only
        code_extensions = [".py", ".js", ".jsx", ".ts", ".tsx"]
        changed_code_files = [
            file for file in changed_files
            if any(file.endswith(ext) for ext in code_extensions)
        ]

        if not changed_code_files:
            console.print("[green]No code files changed. Skipping quality checks.[/green]")
            return 0

        # Run quality checks
        passed = run_quality_check(changed_code_files)

        if not passed:
            console.print("[bold red]Code quality checks failed! Fix issues before submitting PR.[/bold red]")
            console.print(
                "[yellow]You can try running 'python agent_system/code_quality_autofix.py' to fix common issues.[/yellow]")
            return 1

        return 0

    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error getting changed files: {e}[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
