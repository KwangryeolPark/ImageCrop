"""
ImageCrop Version Management System
Centralized version information and Git comparison utilities
"""

import subprocess
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

# Version Information
VERSION = "1.1.0"
RELEASE_DATE = "2025-10-08"
MIN_PYTHON_VERSION = "3.8"

def run_git_command(command: str) -> Optional[str]:
    """Execute git command and return output, or None if failed"""
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None

def get_git_info() -> Dict[str, Optional[str]]:
    """Get current Git information"""
    return {
        "commit_hash": run_git_command("git rev-parse HEAD"),
        "commit_short": run_git_command("git rev-parse --short HEAD"),
        "branch": run_git_command("git rev-parse --abbrev-ref HEAD"),
        "remote_url": run_git_command("git remote get-url origin"),
        "is_dirty": len(run_git_command("git status --porcelain") or "") > 0
    }

def get_master_comparison() -> Dict[str, any]:
    """Compare current branch with master branch"""
    git_info = get_git_info()
    current_branch = git_info.get("branch", "unknown")
    
    # Check if master branch exists
    master_exists = run_git_command("git show-ref --verify --quiet refs/heads/master") is not None
    if not master_exists:
        # Try 'main' branch as alternative
        main_exists = run_git_command("git show-ref --verify --quiet refs/heads/main") is not None
        master_branch = "main" if main_exists else None
    else:
        master_branch = "master"
    
    if not master_branch:
        return {
            "status": "no_master",
            "message": "No master/main branch found",
            "current_branch": current_branch,
            "master_branch": None,
            "commits_ahead": 0,
            "commits_behind": 0
        }
    
    # Get commits ahead/behind master
    ahead_behind = run_git_command(f"git rev-list --count --left-right {master_branch}...HEAD")
    
    if ahead_behind:
        try:
            behind, ahead = map(int, ahead_behind.split('\t'))
        except ValueError:
            behind, ahead = 0, 0
    else:
        behind, ahead = 0, 0
    
    # Determine version status
    if current_branch == master_branch:
        status = "on_master"
        message = f"On {master_branch} branch"
    elif ahead > 0 and behind == 0:
        status = "ahead"
        message = f"{ahead} commits ahead of {master_branch}"
    elif ahead == 0 and behind > 0:
        status = "behind"
        message = f"{behind} commits behind {master_branch}"
    elif ahead > 0 and behind > 0:
        status = "diverged"
        message = f"{ahead} commits ahead, {behind} commits behind {master_branch}"
    else:
        status = "synced"
        message = f"In sync with {master_branch}"
    
    return {
        "status": status,
        "message": message,
        "current_branch": current_branch,
        "master_branch": master_branch,
        "commits_ahead": ahead,
        "commits_behind": behind
    }

def get_version_info() -> Dict[str, any]:
    """Get complete version information"""
    git_info = get_git_info()
    master_comparison = get_master_comparison()
    
    # Determine version type
    if master_comparison["status"] == "on_master":
        version_type = "stable"
    elif master_comparison["status"] == "ahead":
        version_type = "development"
    elif master_comparison["status"] == "behind":
        version_type = "outdated"
    elif master_comparison["status"] == "diverged":
        version_type = "custom"
    elif master_comparison["status"] == "no_master":
        version_type = "unknown"
    else:
        version_type = "stable"
    
    return {
        "version": VERSION,
        "version_type": version_type,
        "release_date": RELEASE_DATE,
        "min_python_version": MIN_PYTHON_VERSION,
        "build_time": datetime.now().isoformat(),
        "git": git_info,
        "master_comparison": master_comparison
    }

def print_version_info():
    """Print formatted version information"""
    info = get_version_info()
    git = info["git"]
    comparison = info["master_comparison"]
    
    print(f"ImageCrop v{info['version']} ({info['version_type']})")
    print(f"Release Date: {info['release_date']}")
    
    if git["branch"]:
        print(f"Branch: {git['branch']}")
    if git["commit_short"]:
        dirty_marker = " (modified)" if git["is_dirty"] else ""
        print(f"Commit: {git['commit_short']}{dirty_marker}")
    
    if comparison["status"] != "no_master":
        print(f"Status: {comparison['message']}")
    
    print()

if __name__ == "__main__":
    print_version_info()
