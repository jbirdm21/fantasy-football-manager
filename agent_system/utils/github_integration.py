"""GitHub integration utilities for committing agent changes."""
import os
import time
from typing import Dict, List, Optional
from pathlib import Path

from github import Github, GithubException
from github.Repository import Repository
from github.ContentFile import ContentFile

from agent_system.config import GITHUB_TOKEN, GITHUB_REPO


def get_github_repo() -> Repository:
    """Get the GitHub repository object.
    
    Returns:
        A GitHub repository object.
    """
    if not GITHUB_TOKEN:
        raise ValueError("GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
    
    g = Github(GITHUB_TOKEN)
    return g.get_repo(GITHUB_REPO)


def get_file_content(repo: Repository, file_path: str, ref: str = "main") -> Optional[str]:
    """Get the content of a file from the repository.
    
    Args:
        repo: GitHub repository object.
        file_path: Path to the file, relative to repo root.
        ref: Branch name or commit SHA to fetch from.
        
    Returns:
        The file content as a string, or None if the file doesn't exist.
    """
    try:
        file_content = repo.get_contents(file_path, ref=ref)
        if isinstance(file_content, List):
            # This is a directory, not a file
            return None
        return file_content.decoded_content.decode("utf-8")
    except GithubException as e:
        if e.status == 404:
            return None
        raise


def create_branch(repo: Repository, branch_name: str, base_branch: str = "main") -> None:
    """Create a new branch in the repository.
    
    Args:
        repo: GitHub repository object.
        branch_name: Name of the branch to create.
        base_branch: Name of the branch to base the new branch on.
    """
    try:
        base_ref = repo.get_git_ref(f"heads/{base_branch}")
        repo.create_git_ref(f"refs/heads/{branch_name}", base_ref.object.sha)
    except GithubException as e:
        if e.status == 422:  # Branch already exists
            # Get the latest commit on the base branch
            base_ref = repo.get_git_ref(f"heads/{base_branch}")
            # Force update the branch to the latest commit on the base branch
            branch_ref = repo.get_git_ref(f"heads/{branch_name}")
            branch_ref.edit(base_ref.object.sha, force=True)
        else:
            raise


def commit_file_changes(
    repo: Repository,
    file_changes: Dict[str, str],
    commit_message: str,
    branch_name: str
) -> None:
    """Commit changes to files in the repository.
    
    Args:
        repo: GitHub repository object.
        file_changes: Dictionary mapping file paths to new content.
        commit_message: Commit message.
        branch_name: Branch to commit to.
    """
    for file_path, new_content in file_changes.items():
        try:
            # Check if file exists
            file_content = repo.get_contents(file_path, ref=branch_name)
            
            # Update existing file
            repo.update_file(
                path=file_path,
                message=f"{commit_message} - Update {file_path}",
                content=new_content,
                sha=file_content.sha,
                branch=branch_name
            )
        except GithubException as e:
            if e.status == 404:  # File doesn't exist
                # Create new file
                repo.create_file(
                    path=file_path,
                    message=f"{commit_message} - Create {file_path}",
                    content=new_content,
                    branch=branch_name
                )
            else:
                raise


def create_pull_request(
    repo: Repository,
    branch_name: str,
    base_branch: str,
    title: str,
    body: str
) -> str:
    """Create a pull request in the repository.
    
    Args:
        repo: GitHub repository object.
        branch_name: Head branch name (the branch with changes).
        base_branch: Base branch name (the branch to merge into).
        title: Pull request title.
        body: Pull request description.
        
    Returns:
        URL of the created pull request.
    """
    pr = repo.create_pull(
        title=title,
        body=body,
        head=branch_name,
        base=base_branch
    )
    return pr.html_url


def commit_agent_changes(
    agent_id: str,
    file_changes: Dict[str, str],
    commit_message: str,
    pr_description: str = ""
) -> str:
    """Commit changes made by an agent to GitHub.
    
    Args:
        agent_id: ID of the agent making the changes.
        file_changes: Dictionary mapping file paths to new content.
        commit_message: Commit message.
        pr_description: Description for the pull request.
    
    Returns:
        URL of the created pull request.
    """
    repo = get_github_repo()
    
    # Create a branch for this agent's changes
    branch_name = f"{agent_id}-{int(time.time())}"
    create_branch(repo, branch_name)
    
    # Commit the changes
    commit_file_changes(repo, file_changes, commit_message, branch_name)
    
    # Create a pull request
    pr_title = f"{commit_message} (by {agent_id})"
    if not pr_description:
        pr_description = f"Changes made by agent {agent_id}"
    
    pr_url = create_pull_request(repo, branch_name, "main", pr_title, pr_description)
    return pr_url 