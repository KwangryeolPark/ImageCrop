"""
ImageCrop Version Management System
Centralized version information and Git comparison utilities
"""

import subprocess
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

# Version Information
VERSION = "1.2.0"
RELEASE_DATE = "2025-10-09"
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

# --- Update Check Functions ---

import socket

def check_internet_connection(timeout: int = 3) -> bool:
    """Check if internet connection is available"""
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=timeout)
        return True
    except OSError:
        return False

def fetch_remote_master_info() -> Dict[str, any]:
    """Fetch latest master branch information from remote"""
    try:
        # Try to fetch latest remote information
        fetch_result = run_git_command("git fetch origin master")
        if fetch_result is None:
            # If fetch fails, try to get remote info without fetching
            pass
        
        # Get remote master commit
        remote_master_commit = run_git_command("git rev-parse origin/master")
        current_commit = run_git_command("git rev-parse HEAD")
        
        if not remote_master_commit or not current_commit:
            return {"status": "error", "message": "Failed to get commit information"}
        
        # Compare commits
        if remote_master_commit == current_commit:
            return {
                "status": "up_to_date",
                "message": "You're on the latest master commit",
                "remote_commit": remote_master_commit[:7]
            }
        
        # Check if current branch is ahead/behind remote master
        ahead_behind = run_git_command(f"git rev-list --count --left-right origin/master...HEAD")
        if ahead_behind:
            try:
                behind, ahead = map(int, ahead_behind.split('\t'))
            except ValueError:
                behind, ahead = 0, 0
        else:
            behind, ahead = 0, 0
        
        git_info = get_git_info()
        current_branch = git_info.get("branch", "unknown")
        
        if current_branch == "master":
            if behind > 0:
                return {
                    "status": "behind",
                    "message": f"Master branch is {behind} commits behind remote",
                    "suggestion": "git pull origin master",
                    "commits_behind": behind
                }
            else:
                return {
                    "status": "up_to_date",
                    "message": "Master branch is up to date"
                }
        else:
            # On feature branch
            if behind > 0:
                return {
                    "status": "master_updated",
                    "message": f"Remote master has {behind} new commits",
                    "suggestion": f"Consider merging master into {current_branch}",
                    "commits_behind": behind,
                    "commits_ahead": ahead
                }
            else:
                return {
                    "status": "feature_ahead",
                    "message": f"Feature branch '{current_branch}' is {ahead} commits ahead",
                    "suggestion": "Consider creating a pull request"
                }
    
    except Exception as e:
        return {"status": "error", "message": f"Update check failed: {str(e)}"}

def get_update_status() -> Dict[str, any]:
    """Get comprehensive update status"""
    # Check internet connection first
    if not check_internet_connection():
        git_info = get_git_info()
        master_comparison = get_master_comparison()
        
        return {
            "status": "offline",
            "message": "Offline: Unable to check for remote updates",
            "local_info": {
                "branch": git_info.get("branch", "unknown"),
                "status": master_comparison.get("message", "Unknown status")
            }
        }
    
    # Online - check remote updates
    return fetch_remote_master_info()

def print_update_notification():
    """Print update notification with appropriate styling"""
    try:
        update_info = get_update_status()
        status = update_info.get("status", "unknown")
        
        if status == "offline":
            print("📡 Offline: Unable to check for updates")
            local_info = update_info.get("local_info", {})
            if local_info.get("branch"):
                print(f"ℹ️  Current: {local_info['branch']} ({local_info.get('status', 'Unknown status')})")
        
        elif status == "up_to_date":
            print("✅ You're running the latest version!")
        
        elif status == "behind":
            commits = update_info.get("commits_behind", 0)
            print(f"💡 Update Available: Master branch has {commits} new commits")
            if update_info.get("suggestion"):
                print(f"   💻 Run: {update_info['suggestion']}")
        
        elif status == "master_updated":
            behind = update_info.get("commits_behind", 0)
            ahead = update_info.get("commits_ahead", 0)
            print(f"💡 Master Updated: Remote master has {behind} new commits")
            print(f"ℹ️  Your feature branch is {ahead} commits ahead of master")
            if update_info.get("suggestion"):
                print(f"   💡 Consider: {update_info['suggestion']}")
        
        elif status == "feature_ahead":
            print("🚀 Development Version: Your feature branch has new features!")
            if update_info.get("suggestion"):
                print(f"   💡 Next step: {update_info['suggestion']}")
        
        elif status == "error":
            print("⚠️  Update check failed - continuing with local version")
        
        else:
            print("ℹ️  Update status unknown")
        
        print()  # Add spacing
        
    except Exception as e:
        # Silent failure - don't interrupt server startup
        print("ℹ️  Update check unavailable")
        print()

if __name__ == "__main__":
    print_version_info()
    print_update_notification()
