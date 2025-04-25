#!/usr/bin/env python3
"""
Script to fix all console.logger references in the codebase.
"""
import sys
import os
from pathlib import Path
import re


def fix_console_logger(directory: Path):
    """
    Replace all instances of console.logger.info with console.print

    Args:
        directory: Root directory to search
    """
    print(f"Searching for files in {directory}...")

    # Find all Python files
    py_files = list(directory.glob("**/*.py"))
    print(f"Found {len(py_files)} Python files")

    # Pattern to match
    pattern = r'console\.logger\.info\('
    replacement = 'console.print('

    # Count of replacements
    total_files = 0
    total_replacements = 0

    # Process each file
    for file_path in py_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if pattern exists
        if re.search(pattern, content):
            # Replace the pattern
            new_content = re.sub(pattern, replacement, content)
            total_changes = content.count('console.print(')

            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            total_files += 1
            total_replacements += total_changes
            print(f"Fixed {total_changes} occurrences in {file_path}")

    print(f"\nSummary:")
    print(f"- Modified {total_files} files")
    print(f"- Made {total_replacements} replacements")


if __name__ == "__main__":
    # Get directory to search
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
    else:
        directory = Path(__file__).parent

    fix_console_logger(directory)
