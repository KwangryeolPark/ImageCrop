"""
ImageCrop Version Management System
Centralized version information and Git comparison utilities
"""

import subprocess
import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Optional, Tuple

# Version Information
VERSION = "1.2.0"  # 원래 버전으로 복원
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

# --- GitHub API Integration ---

def get_github_latest_version() -> Dict[str, any]:
    """
    Get latest version info from GitHub master branch
    Handles cases where version.py might not exist on master
    """
    try:
        # GitHub repository info
        owner = "KwangryeolPark"
        repo = "ImageCrop"
        
        # First, try to get version.py from master branch
        version_info = _get_version_from_github(owner, repo)
        if version_info:
            return {
                "status": "success",
                "source": "github_version_file",
                "version": version_info["version"],
                "release_date": version_info.get("release_date"),
                "min_python_version": version_info.get("min_python_version"),
                "last_checked": datetime.now().isoformat()
            }
        
        # If version.py doesn't exist, try to get info from latest release/tag
        release_info = _get_latest_release_from_github(owner, repo)
        if release_info:
            return {
                "status": "success",
                "source": "github_release",
                "version": release_info["version"],
                "release_date": release_info.get("published_at"),
                "release_notes": release_info.get("body"),
                "last_checked": datetime.now().isoformat()
            }
        
        # If no releases, try to infer from tags
        tag_info = _get_latest_tag_from_github(owner, repo)
        if tag_info:
            return {
                "status": "success", 
                "source": "github_tag",
                "version": tag_info["version"],
                "commit_sha": tag_info.get("commit_sha"),
                "last_checked": datetime.now().isoformat()
            }
        
        return {
            "status": "no_version_info",
            "message": "No version information found on GitHub",
            "last_checked": datetime.now().isoformat()
        }
        
    except urllib.error.URLError as e:
        return {
            "status": "network_error",
            "message": f"Network error: {str(e)}",
            "last_checked": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching version info: {str(e)}",
            "last_checked": datetime.now().isoformat()
        }

def _get_version_from_github(owner: str, repo: str) -> Optional[Dict[str, str]]:
    """Try to get version info from version.py file on GitHub master branch"""
    try:
        # GitHub API URL for version.py file content
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/version.py?ref=master"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                
                # Decode base64 content
                import base64
                content = base64.b64decode(data['content']).decode('utf-8')
                
                # Extract version info using simple parsing
                version_info = {}
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('VERSION = '):
                        version_info['version'] = line.split('=')[1].strip().strip('"\'')
                    elif line.startswith('RELEASE_DATE = '):
                        version_info['release_date'] = line.split('=')[1].strip().strip('"\'')
                    elif line.startswith('MIN_PYTHON_VERSION = '):
                        version_info['min_python_version'] = line.split('=')[1].strip().strip('"\'')
                
                if version_info.get('version'):
                    return version_info
                    
    except (urllib.error.HTTPError, KeyError, json.JSONDecodeError):
        # File doesn't exist or parsing failed
        pass
    except Exception:
        # Any other error
        pass
    
    return None

def _get_latest_release_from_github(owner: str, repo: str) -> Optional[Dict[str, str]]:
    """Get latest release info from GitHub releases API"""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                
                tag_name = data.get('tag_name', '')
                # Extract version number (remove 'v' prefix if present)
                version = tag_name.lstrip('v')
                
                return {
                    "version": version,
                    "published_at": data.get('published_at'),
                    "body": data.get('body'),
                    "html_url": data.get('html_url')
                }
                
    except (urllib.error.HTTPError, KeyError, json.JSONDecodeError):
        pass
    except Exception:
        pass
        
    return None

def _get_latest_tag_from_github(owner: str, repo: str) -> Optional[Dict[str, str]]:
    """Get latest tag info from GitHub tags API"""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/tags"
        
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                
                if data and len(data) > 0:
                    latest_tag = data[0]  # First item is the latest
                    tag_name = latest_tag.get('name', '')
                    version = tag_name.lstrip('v')
                    
                    return {
                        "version": version,
                        "commit_sha": latest_tag.get('commit', {}).get('sha')
                    }
                    
    except (urllib.error.HTTPError, KeyError, json.JSONDecodeError):
        pass
    except Exception:
        pass
        
    return None

def compare_versions(current: str, latest: str) -> Dict[str, any]:
    """
    Compare two version strings (semantic versioning)
    Returns comparison result and recommendation
    """
    try:
        def parse_version(version_str: str) -> Tuple[int, int, int]:
            """Parse version string into major, minor, patch integers"""
            # Remove 'v' prefix if present and clean up
            clean_version = version_str.lstrip('v').split('-')[0]  # Remove pre-release suffixes
            parts = clean_version.split('.')
            
            # Pad with zeros if needed
            while len(parts) < 3:
                parts.append('0')
                
            return tuple(int(part) for part in parts[:3])
        
        current_tuple = parse_version(current)
        latest_tuple = parse_version(latest)
        
        if current_tuple < latest_tuple:
            # Calculate difference
            major_diff = latest_tuple[0] - current_tuple[0]
            minor_diff = latest_tuple[1] - current_tuple[1] 
            patch_diff = latest_tuple[2] - current_tuple[2]
            
            if major_diff > 0:
                urgency = "high"
                recommendation = "Major update available with significant changes"
            elif minor_diff > 0:
                urgency = "medium" 
                recommendation = "Feature update available"
            else:
                urgency = "low"
                recommendation = "Bug fixes and improvements available"
                
            return {
                "status": "outdated",
                "urgency": urgency,
                "recommendation": recommendation,
                "current_version": current,
                "latest_version": latest,
                "version_diff": {
                    "major": major_diff,
                    "minor": minor_diff, 
                    "patch": patch_diff
                }
            }
        elif current_tuple > latest_tuple:
            return {
                "status": "ahead",
                "message": "You're running a newer version than released",
                "current_version": current,
                "latest_version": latest
            }
        else:
            return {
                "status": "up_to_date",
                "message": "You're running the latest version",
                "current_version": current,
                "latest_version": latest
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error comparing versions: {str(e)}",
            "current_version": current,
            "latest_version": latest
        }

def get_comprehensive_update_status() -> Dict[str, any]:
    """
    Get comprehensive update status including GitHub latest version
    This replaces the old get_update_status function
    """
    try:
        # Get current version info
        current_version = VERSION
        current_info = get_version_info()
        
        # Check internet connection first
        if not check_internet_connection():
            return {
                "status": "offline",
                "message": "Offline: Unable to check for remote updates", 
                "current_version": current_version,
                "current_info": current_info
            }
        
        # Get latest version from GitHub
        github_info = get_github_latest_version()
        
        if github_info["status"] != "success":
            return {
                "status": github_info["status"],
                "message": github_info.get("message", "Failed to get latest version"),
                "current_version": current_version,
                "current_info": current_info,
                "error_details": github_info
            }
        
        # Compare versions
        latest_version = github_info["version"]
        comparison = compare_versions(current_version, latest_version)
        
        return {
            "status": "success",
            "current_version": current_version,
            "latest_version": latest_version,
            "github_info": github_info,
            "comparison": comparison,
            "current_info": current_info,
            "last_checked": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "current_version": VERSION,
            "last_checked": datetime.now().isoformat()
        }

def print_comprehensive_update_notification():
    """Enhanced update notification with GitHub integration"""
    try:
        update_status = get_comprehensive_update_status()
        status = update_status.get("status", "unknown")
        
        if status == "offline":
            print("📡 Offline: Unable to check for updates")
            print(f"ℹ️  Current Version: {update_status.get('current_version', 'Unknown')}")
            
        elif status == "success":
            comparison = update_status.get("comparison", {})
            current_ver = update_status.get("current_version")
            latest_ver = update_status.get("latest_version")
            github_info = update_status.get("github_info", {})
            
            comp_status = comparison.get("status", "unknown")
            
            if comp_status == "up_to_date":
                print(f"✅ You're running the latest version! (v{current_ver})")
                
            elif comp_status == "outdated":
                urgency = comparison.get("urgency", "unknown")
                recommendation = comparison.get("recommendation", "Update available")
                
                if urgency == "high":
                    print(f"🚨 Major Update Available: v{current_ver} → v{latest_ver}")
                elif urgency == "medium":
                    print(f"💡 Feature Update Available: v{current_ver} → v{latest_ver}")
                else:
                    print(f"🔧 Bug Fix Update Available: v{current_ver} → v{latest_ver}")
                
                print(f"   📋 {recommendation}")
                print(f"   📁 Source: {github_info.get('source', 'unknown')}")
                
            elif comp_status == "ahead":
                print(f"🚀 Development Version: v{current_ver} (Latest: v{latest_ver})")
                print("   ℹ️  You're running a newer version than released")
                
        elif status == "network_error":
            print("🌐 Network Error: Unable to connect to GitHub")
            print(f"ℹ️  Current Version: {update_status.get('current_version', 'Unknown')}")
            
        elif status == "no_version_info":
            print("❓ No version information found on GitHub")
            print(f"ℹ️  Current Version: {update_status.get('current_version', 'Unknown')}")
            
        else:
            print("⚠️  Update check failed")
            if update_status.get("message"):
                print(f"   🔍 Details: {update_status['message']}")
            print(f"ℹ️  Current Version: {update_status.get('current_version', 'Unknown')}")
        
        print()  # Add spacing
        
    except Exception as e:
        print("ℹ️  Update check unavailable")
        print(f"ℹ️  Current Version: {VERSION}")
        print()

# --- Legacy function for backward compatibility ---

if __name__ == "__main__":
    print_version_info()
    print_comprehensive_update_notification()
