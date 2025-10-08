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
from typing import Dict, Optional, Tuple, List
import re

# Version Information
VERSION = "1.2.0"  # 원래 버전으로 복원
RELEASE_DATE = "2025-10-09"
MIN_PYTHON_VERSION = "3.8"

# Cache Configuration
CACHE_FILE = "version_cache.json"
DEFAULT_CACHE_DURATION = 3600  # 1 hour in seconds
MAX_CACHE_AGE = 86400  # 24 hours maximum

# Release Notes Configuration
RELEASE_NOTES_DIR = "release-notes"
RELEASE_NOTES_CACHE_FILE = "release_notes_cache.json"
RELEASE_NOTES_CACHE_DURATION = 7200  # 2 hours for release notes

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

# --- Cache Management Functions ---

def save_cache(data: Dict[str, any], duration: int = DEFAULT_CACHE_DURATION) -> bool:
    """Save data to cache file with timestamp and TTL"""
    try:
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "data": data
        }
        
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CACHE_FILE)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, default=str)
        
        return True
    except Exception as e:
        print(f"Warning: Failed to save cache: {e}")
        return False

def load_cache() -> Optional[Dict[str, any]]:
    """Load cache data if valid, return None if expired or invalid"""
    try:
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CACHE_FILE)
        
        if not os.path.exists(cache_path):
            return None
            
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Check if cache structure is valid
        if not all(key in cache_data for key in ['timestamp', 'duration', 'data']):
            return None
        
        # Check if cache is expired
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        now = datetime.now()
        age_seconds = (now - cache_time).total_seconds()
        
        # Use configured duration, but respect maximum age
        max_age = min(cache_data.get('duration', DEFAULT_CACHE_DURATION), MAX_CACHE_AGE)
        
        if age_seconds > max_age:
            return None  # Cache expired
            
        return cache_data['data']
        
    except Exception as e:
        print(f"Warning: Failed to load cache: {e}")
        return None

def clear_cache() -> bool:
    """Clear cache file"""
    try:
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CACHE_FILE)
        if os.path.exists(cache_path):
            os.remove(cache_path)
        return True
    except Exception as e:
        print(f"Warning: Failed to clear cache: {e}")
        return False

def get_cache_info() -> Dict[str, any]:
    """Get cache information for debugging"""
    try:
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CACHE_FILE)
        
        if not os.path.exists(cache_path):
            return {
                "exists": False,
                "path": cache_path
            }
            
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        now = datetime.now()
        age_seconds = (now - cache_time).total_seconds()
        duration = cache_data.get('duration', DEFAULT_CACHE_DURATION)
        
        return {
            "exists": True,
            "path": cache_path,
            "timestamp": cache_data['timestamp'],
            "age_seconds": age_seconds,
            "duration": duration,
            "expired": age_seconds > duration,
            "data_keys": list(cache_data.get('data', {}).keys())
        }
        
    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }

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

def get_comprehensive_update_status(force_refresh: bool = False) -> Dict[str, any]:
    """
    Get comprehensive update status including GitHub latest version
    Supports caching to reduce API calls
    
    Args:
        force_refresh: If True, bypass cache and fetch fresh data
        
    Returns:
        Dict containing update status information
    """
    try:
        # Try to use cached data first (unless force refresh)
        if not force_refresh:
            cached_data = load_cache()
            if cached_data is not None:
                # Add cache hit information
                cached_data["cache_hit"] = True
                cached_data["cache_info"] = get_cache_info()
                return cached_data
        
        # Get current version info
        current_version = VERSION
        current_info = get_version_info()
        
        # Check internet connection first
        if not check_internet_connection():
            # Try to return cached data even if expired when offline
            cached_data = load_cache()
            if cached_data is not None:
                cached_data["status"] = "offline_cached"
                cached_data["message"] = "Offline: Using cached data"
                cached_data["cache_hit"] = True
                cached_data["cache_expired"] = True
                return cached_data
                
            return {
                "status": "offline",
                "message": "Offline: Unable to check for remote updates", 
                "current_version": current_version,
                "current_info": current_info,
                "cache_hit": False
            }
        
        # Get latest version from GitHub
        github_info = get_github_latest_version()
        
        if github_info["status"] != "success":
            # Try cached data on GitHub API failure
            cached_data = load_cache()
            if cached_data is not None:
                cached_data["status"] = "api_error_cached"
                cached_data["message"] = f"API Error: {github_info.get('message', 'Unknown error')}, using cached data"
                cached_data["cache_hit"] = True
                cached_data["api_error"] = github_info
                return cached_data
                
            return {
                "status": github_info["status"],
                "message": github_info.get("message", "Failed to get latest version"),
                "current_version": current_version,
                "current_info": current_info,
                "error_details": github_info,
                "cache_hit": False
            }
        
        # Compare versions
        latest_version = github_info["version"]
        comparison = compare_versions(current_version, latest_version)
        
        # Prepare result
        result = {
            "status": "success",
            "current_version": current_version,
            "latest_version": latest_version,
            "github_info": github_info,
            "comparison": comparison,
            "current_info": current_info,
            "last_checked": datetime.now().isoformat(),
            "cache_hit": False
        }
        
        # Save to cache
        save_cache(result)
        
        return result
        
    except Exception as e:
        # Try cached data on unexpected error
        cached_data = load_cache()
        if cached_data is not None:
            cached_data["status"] = "error_cached"
            cached_data["message"] = f"Unexpected error: {str(e)}, using cached data"
            cached_data["cache_hit"] = True
            cached_data["error"] = str(e)
            return cached_data
            
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "current_version": VERSION,
            "last_checked": datetime.now().isoformat(),
            "cache_hit": False
        }
        
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


# ====================================
# RELEASE NOTES MANAGEMENT SYSTEM
# ====================================

def get_github_release_notes(version: str = None) -> Dict[str, any]:
    """
    Get release notes from GitHub API
    
    Args:
        version: Specific version to get notes for, or None for latest
        
    Returns:
        Dict containing release notes information
    """
    try:
        if version:
            # Get specific release by tag
            url = f"https://api.github.com/repos/KwangryeolPark/ImageCrop/releases/tags/v{version}"
        else:
            # Get latest release
            url = "https://api.github.com/repos/KwangryeolPark/ImageCrop/releases/latest"
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'ImageCrop-Version-Checker'
        }
        
        request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                
                return {
                    "status": "success",
                    "source": "github_api",
                    "version": data.get("tag_name", "").replace("v", ""),
                    "title": data.get("name", ""),
                    "body": data.get("body", ""),
                    "published_at": data.get("published_at", ""),
                    "html_url": data.get("html_url", ""),
                    "download_url": data.get("zipball_url", ""),
                    "prerelease": data.get("prerelease", False),
                    "draft": data.get("draft", False)
                }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status}"
                }
                
    except urllib.error.URLError as e:
        return {
            "status": "network_error",
            "message": f"Network error: {str(e)}"
        }
    except json.JSONDecodeError as e:
        return {
            "status": "parse_error", 
            "message": f"JSON parse error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }

def parse_release_notes(content: str) -> Dict[str, any]:
    """
    Parse release notes content and extract structured information
    
    Args:
        content: Raw release notes content (markdown)
        
    Returns:
        Dict containing parsed release notes
    """
    if not content:
        return {
            "sections": [],
            "summary": "",
            "highlights": []
        }
    
    # Split into sections by headers
    sections = []
    current_section = None
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect headers (### or ##)
        if line.startswith('###'):
            if current_section:
                sections.append(current_section)
            current_section = {
                "title": line.replace('###', '').strip(),
                "level": 3,
                "items": []
            }
        elif line.startswith('##'):
            if current_section:
                sections.append(current_section)
            current_section = {
                "title": line.replace('##', '').strip(),
                "level": 2,
                "items": []
            }
        elif line.startswith('- ') or line.startswith('* '):
            if current_section:
                item = line[2:].strip()
                # Categorize items
                category = "other"
                if any(keyword in item.lower() for keyword in ['new', 'add', 'feature', 'implement']):
                    category = "new"
                elif any(keyword in item.lower() for keyword in ['fix', 'bug', 'resolve', 'correct']):
                    category = "fix"
                elif any(keyword in item.lower() for keyword in ['improve', 'enhance', 'update', 'optimize']):
                    category = "improvement"
                elif any(keyword in item.lower() for keyword in ['security', 'vulnerability', 'safe']):
                    category = "security"
                
                current_section["items"].append({
                    "text": item,
                    "category": category
                })
        else:
            # Regular text, could be summary
            if current_section and not current_section["items"]:
                current_section["summary"] = line
    
    # Add last section
    if current_section:
        sections.append(current_section)
    
    # Extract highlights (important items)
    highlights = []
    for section in sections:
        for item in section.get("items", []):
            if item["category"] in ["new", "security"] or "important" in item["text"].lower():
                highlights.append({
                    "text": item["text"],
                    "category": item["category"],
                    "section": section["title"]
                })
    
    # Generate summary
    summary = ""
    if sections:
        first_section = sections[0]
        if "summary" in first_section:
            summary = first_section["summary"]
        elif first_section.get("items"):
            summary = f"{len(first_section['items'])} changes in {first_section['title']}"
    
    return {
        "sections": sections,
        "summary": summary,
        "highlights": highlights,
        "total_changes": sum(len(s.get("items", [])) for s in sections)
    }

def get_local_release_notes(version: str) -> Dict[str, any]:
    """
    Get release notes from local files
    
    Args:
        version: Version to get release notes for
        
    Returns:
        Dict containing release notes information
    """
    try:
        # Try different file naming patterns
        possible_files = [
            f"RELEASE_NOTES_v{version}.md",
            f"release_notes_v{version}.md", 
            f"v{version}.md",
            f"{version}.md"
        ]
        
        release_notes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), RELEASE_NOTES_DIR)
        
        for filename in possible_files:
            filepath = os.path.join(release_notes_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                parsed = parse_release_notes(content)
                
                return {
                    "status": "success",
                    "source": "local_file",
                    "version": version,
                    "filepath": filepath,
                    "content": content,
                    "parsed": parsed
                }
        
        return {
            "status": "not_found",
            "message": f"No local release notes found for version {version}",
            "searched_files": possible_files
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading local release notes: {str(e)}"
        }

def get_release_notes(version: str = None, prefer_local: bool = False) -> Dict[str, any]:
    """
    Get release notes for a specific version, trying multiple sources
    
    Args:
        version: Version to get notes for, or None for latest
        prefer_local: If True, try local files first
        
    Returns:
        Dict containing release notes information
    """
    if version is None:
        # For latest, always use GitHub API first
        github_result = get_github_release_notes()
        if github_result["status"] == "success":
            # Also parse the content
            github_result["parsed"] = parse_release_notes(github_result.get("body", ""))
            return github_result
        
        # Fallback to local latest
        return {
            "status": "fallback",
            "message": "Using current version info as latest",
            "version": VERSION,
            "content": f"# ImageCrop v{VERSION}\n\nCurrent development version.",
            "parsed": parse_release_notes(f"Current development version v{VERSION}")
        }
    
    # For specific version, try based on preference
    if prefer_local:
        local_result = get_local_release_notes(version)
        if local_result["status"] == "success":
            return local_result
        
        # Fallback to GitHub
        github_result = get_github_release_notes(version)
        if github_result["status"] == "success":
            github_result["parsed"] = parse_release_notes(github_result.get("body", ""))
            return github_result
    else:
        # Try GitHub first
        github_result = get_github_release_notes(version)
        if github_result["status"] == "success":
            github_result["parsed"] = parse_release_notes(github_result.get("body", ""))
            return github_result
        
        # Fallback to local
        local_result = get_local_release_notes(version)
        if local_result["status"] == "success":
            return local_result
    
    return {
        "status": "not_found",
        "message": f"No release notes found for version {version}",
        "version": version
    }

def compare_release_notes(from_version: str, to_version: str) -> Dict[str, any]:
    """
    Compare release notes between two versions
    
    Args:
        from_version: Starting version
        to_version: Target version
        
    Returns:
        Dict containing comparison information
    """
    try:
        from_notes = get_release_notes(from_version)
        to_notes = get_release_notes(to_version)
        
        changes = []
        if to_notes["status"] == "success" and "parsed" in to_notes:
            parsed = to_notes["parsed"]
            for section in parsed["sections"]:
                for item in section["items"]:
                    changes.append({
                        "text": item["text"],
                        "category": item["category"],
                        "section": section["title"]
                    })
        
        return {
            "status": "success",
            "from_version": from_version,
            "to_version": to_version,
            "changes": changes,
            "total_changes": len(changes),
            "highlights": to_notes.get("parsed", {}).get("highlights", []),
            "from_notes": from_notes,
            "to_notes": to_notes
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error comparing release notes: {str(e)}"
        }

def get_latest_release_notes() -> Dict[str, any]:
    """
    Get the latest release notes
    
    Returns:
        Dict containing latest release notes
    """
    return get_release_notes(version=None)

# --- Legacy function for backward compatibility ---

if __name__ == "__main__":
    print_version_info()
    print_comprehensive_update_notification()
