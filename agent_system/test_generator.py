#!/usr/bin/env python
"""Script to automatically generate tests for agent-created code."""
from agent_system.config import OPENAI_API_KEY
from agent_system.utils.github_integration import commit_agent_changes
from agent_system.agents.models import TaskStatus, Task
from agent_system.utils.persistence import get_all_tasks, get_task, save_task
import argparse
import logging
import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from rich.console import Console
from rich.logging import RichHandler
import openai

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Set up environment
os.environ["PYTHONPATH"] = str(parent_dir)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("test_generator")
console = Console()


# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)


def detect_file_language(file_path: str) -> str:
    """Detect the programming language of a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        The detected language
    """
    extension = Path(file_path).suffix.lower()

    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sql': 'sql',
        '.java': 'java',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
    }

    return language_map.get(extension, 'unknown')


def extract_file_changes_from_pr(pr_url: str) -> List[str]:
    """Extract file changes from a PR URL (GitHub).

    Args:
        pr_url: URL of the PR

    Returns:
        List of changed file paths
    """
    # In a real implementation, this would use the GitHub API
    # For now, we'll return a list of sample files for testing

    # Extract PR number from URL
    match = re.search(r'/pull/(\d+)', pr_url)
    if not match:
        return []

    pr_number = match.group(1)
    repo_parts = re.search(r'github\.com/([^/]+/[^/]+)', pr_url)
    if not repo_parts:
        return []

    repo = repo_parts.group(1)

    # Use GitHub CLI if available
    try:
        result = subprocess.run(
            ["gh", "pr", "view", pr_number, "--repo", repo, "--json", "files"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            files_data = json.loads(result.stdout)
            return [file['path'] for file in files_data.get('files', [])]
    except Exception as e:
        logger.warning(f"Error using GitHub CLI: {e}")

    # Fallback to manual parsing or return empty list
    return []


def get_file_content(file_path: str) -> str:
    """Get the content of a file.

    Args:
        file_path: Path to the file

    Returns:
        The file content as a string
    """
    try:
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                return f.read()
        else:
            # Try with project root prefix
            full_path = parent_dir / file_path
            if full_path.exists():
                with open(full_path, 'r') as f:
                    return f.read()
            else:
                logger.warning(f"File not found: {file_path}")
                return ""
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""


def generate_test_for_file(file_path: str, file_content: str) -> Tuple[str, str]:
    """Generate a test file for the given source file.

    Args:
        file_path: Path to the source file
        file_content: Content of the source file

    Returns:
        A tuple of (test_file_path, test_file_content)
    """
    language = detect_file_language(file_path)
    if language == 'unknown':
        logger.warning(f"Could not determine language for file: {file_path}")
        return None, None

    # Create test file path
    path_obj = Path(file_path)
    filename = path_obj.stem

    if language == 'python':
        test_filename = f"test_{filename}.py"
        if "tests" in str(path_obj):
            # Already a test file
            return None, None
        elif path_obj.parent.name == "tests":
            test_file_path = str(path_obj.parent / test_filename)
        else:
            # Create tests directory next to the file
            test_file_path = str(path_obj.parent / "tests" / test_filename)

    elif language in ['javascript', 'typescript']:
        test_filename = f"{filename}.test.{path_obj.suffix}"
        if ".test." in str(path_obj) or ".spec." in str(path_obj):
            # Already a test file
            return None, None
        elif path_obj.parent.name == "tests" or path_obj.parent.name == "__tests__":
            test_file_path = str(path_obj.parent / test_filename)
        else:
            # Create tests directory next to the file
            test_file_path = str(path_obj.parent / "__tests__" / test_filename)

    else:
        logger.warning(f"Test generation not supported for language: {language}")
        return None, None

    # Generate test content with OpenAI
    test_content = generate_test_content(file_path, file_content, language)

    return test_file_path, test_content


def generate_test_content(file_path: str, file_content: str, language: str) -> str:
    """Generate test content using OpenAI.

    Args:
        file_path: Path to the source file
        file_content: Content of the source file
        language: Programming language

    Returns:
        Generated test content
    """
    console.print(f"[bold blue]Generating tests for {file_path} ({language})[/bold blue]")

    # Create a system prompt based on the language
    system_prompt = f"""You are an expert test writer for {language} code.
Your task is to generate comprehensive tests for the provided code file.
Follow these guidelines:
1. Create thorough tests covering all functionality
2. Include both unit tests and integration tests where appropriate
3. Use the appropriate testing framework for {language}
4. Follow best practices for {language} testing
5. Focus on edge cases and error conditions
6. Include setup and teardown code as needed
7. Add explanatory comments for complex test cases
8. Ensure high test coverage
"""

    test_framework = ""
    if language == 'python':
        test_framework = "Use pytest for testing."
    elif language == 'javascript':
        test_framework = "Use Jest for testing."
    elif language == 'typescript':
        test_framework = "Use Jest with TypeScript for testing."

    user_prompt = f"""Please generate tests for the following {language} code file:

Filename: {file_path}

```{language}
{file_content}
```

{test_framework}
Return ONLY the test code, with no explanations before or after.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )

        test_content = response.choices[0].message.content.strip()

        # Clean up the response (remove markdown code blocks if present)
        if test_content.startswith("```") and test_content.endswith("```"):
            # Extract content inside code block
            lines = test_content.split('\n')
            if language in lines[0]:
                # Remove first and last lines (markdown code block markers)
                test_content = '\n'.join(lines[1:-1])
            else:
                # Just remove the triple backticks
                test_content = test_content[3:-3]

        return test_content

    except Exception as e:
        logger.error(f"Error generating test content: {e}")
        return f"# Error generating tests: {str(e)}\n# Please create tests manually."


def process_task_for_tests(task_id: str) -> None:
    """Process a task to generate tests for its code changes.

    Args:
        task_id: ID of the task to process
    """
    task = get_task(task_id)
    if not task:
        console.print(f"[red]Task {task_id} not found[/red]")
        return

    console.print(f"[bold]Generating tests for task: {task.title} ({task.task_id})[/bold]")

    # Get PRs from task artifacts
    pr_urls = task.artifacts if hasattr(task, 'artifacts') and task.artifacts else []

    # Filter out non-PR URLs
    pr_urls = [url for url in pr_urls if "github.com" in url and "/pull/" in url]

    if not pr_urls:
        console.print("[yellow]No PRs found for this task, skipping[/yellow]")
        return

    all_file_changes = []
    for pr_url in pr_urls:
        file_changes = extract_file_changes_from_pr(pr_url)
        all_file_changes.extend(file_changes)

    if not all_file_changes:
        console.print("[yellow]No file changes found in PRs, skipping[/yellow]")
        return

    console.print(f"Found {len(all_file_changes)} changed files")

    # Generate tests for each file
    test_files = {}
    for file_path in all_file_changes:
        # Skip certain files and directories
        if (any(skip in file_path for skip in ['test_', '.test.', '.spec.', 'node_modules/', 'venv/']) or
            file_path.startswith('tests/') or
                Path(file_path).suffix in ['.md', '.txt', '.json', '.yml', '.yaml']):
            continue

        file_content = get_file_content(file_path)
        if not file_content:
            continue

        test_file_path, test_content = generate_test_for_file(file_path, file_content)
        if test_file_path and test_content:
            test_files[test_file_path] = test_content

    if not test_files:
        console.print("[yellow]No test files were generated[/yellow]")
        return

    console.print(f"[green]Generated {len(test_files)} test files[/green]")

    # Create PR with the generated tests
    try:
        pr_url = commit_agent_changes(
            agent_id="qa-eng-1",
            file_changes=test_files,
            commit_message=f"Add tests for task: {task.title}",
            pr_description=f"This PR adds automatically generated tests for task {task.task_id}: {task.title}\n\nThese tests should be reviewed and adjusted as needed before merging."
        )

        console.print(f"[bold green]Created PR with generated tests: {pr_url}[/bold green]")

        # Update task artifacts
        if hasattr(task, 'artifacts') and task.artifacts:
            task.artifacts.append(pr_url)
        else:
            task.artifacts = [pr_url]

        # Save task
        save_task(task)

    except Exception as e:
        logger.error(f"Error creating PR with tests: {e}")
        console.print(f"[red]Error creating PR: {str(e)}[/red]")

        # Fallback to local files
        test_dir = parent_dir / "generated_tests"
        test_dir.mkdir(parents=True, exist_ok=True)

        for test_file_path, test_content in test_files.items():
            local_path = test_dir / Path(test_file_path).name
            with open(local_path, 'w') as f:
                f.write(test_content)

        console.print(f"[yellow]Created local test files in: {test_dir}[/yellow]")


def process_all_completed_tasks() -> None:
    """Process all completed tasks to generate tests for their code."""
    all_tasks = get_all_tasks()
    completed_tasks = [
        t for t in all_tasks
        if t.status == TaskStatus.COMPLETED and
        (not hasattr(t, 'has_tests_generated') or not t.has_tests_generated)
    ]

    if not completed_tasks:
        console.print("[yellow]No completed tasks found that need test generation[/yellow]")
        return

    console.print(f"[bold]Found {len(completed_tasks)} completed tasks that need tests[/bold]")

    for task in completed_tasks:
        process_task_for_tests(task.task_id)

        # Mark task as having tests generated
        task.has_tests_generated = True
        save_task(task)


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Test generator for agent-created code")
    parser.add_argument(
        "--task",
        type=str,
        help="ID of a specific task to generate tests for"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Generate tests for a specific file"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all completed tasks"
    )

    args = parser.parse_args()

    if args.task:
        process_task_for_tests(args.task)
    elif args.file:
        file_path = args.file
        file_content = get_file_content(file_path)

        if file_content:
            test_file_path, test_content = generate_test_for_file(file_path, file_content)

            if test_file_path and test_content:
                # Ensure directory exists
                Path(test_file_path).parent.mkdir(parents=True, exist_ok=True)

                # Write test file
                with open(test_file_path, 'w') as f:
                    f.write(test_content)

                console.print(f"[green]Generated test file: {test_file_path}[/green]")
            else:
                console.print("[yellow]Could not generate test for this file[/yellow]")
        else:
            console.print(f"[red]Could not read file: {file_path}[/red]")
    elif args.all:
        process_all_completed_tasks()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
