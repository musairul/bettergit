"""Core Git wrapper functionality."""

import subprocess
import shutil
import sys
from typing import Tuple, List, Optional
import logging


logger = logging.getLogger(__name__)


class GitError(Exception):
    """Raised when a Git command fails."""
    
    def __init__(self, command: List[str], returncode: int, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"Git command failed: {' '.join(command)}\n{stderr}")


def check_git_available() -> bool:
    """Check if Git is available in the system PATH."""
    return shutil.which("git") is not None


def run_git_command(command: List[str], cwd: Optional[str] = None, 
                   check: bool = True) -> Tuple[str, str, int]:
    """
    Execute a Git command using subprocess.
    
    Args:
        command: List of command arguments (e.g., ['status', '--porcelain'])
        cwd: Working directory for the command
        check: If True, raise GitError on non-zero exit code
        
    Returns:
        Tuple of (stdout, stderr, returncode)
        
    Raises:
        GitError: If the command fails and check=True
    """
    if not check_git_available():
        raise GitError(["git"], 1, "Git is not installed or not in PATH")
    
    full_command = ["git"] + command
    logger.debug(f"Running Git command: {' '.join(full_command)}")
    
    try:
        # Use bytes mode and decode manually to handle encoding issues robustly
        result = subprocess.run(
            full_command,
            capture_output=True,
            cwd=cwd
        )
        
        # Try to decode stdout/stderr with multiple encodings
        def safe_decode(data):
            if not data:
                return ""
            for encoding in ['utf-8', 'cp1252', 'latin1']:
                try:
                    return data.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # Last resort: decode with replacement characters
            return data.decode('utf-8', errors='replace')
        
        stdout = safe_decode(result.stdout).strip()
        stderr = safe_decode(result.stderr).strip()
        returncode = result.returncode
        
        logger.debug(f"Git command completed with return code {returncode}")
        if stdout:
            logger.debug(f"stdout: {stdout}")
        if stderr:
            logger.debug(f"stderr: {stderr}")
            
        if check and returncode != 0:
            raise GitError(command, returncode, stderr)
            
        return stdout, stderr, returncode
        
    except FileNotFoundError:
        raise GitError(["git"], 1, "Git executable not found")
    except Exception as e:
        raise GitError(command, 1, str(e))


def is_git_repository(path: Optional[str] = None) -> bool:
    """Check if the current directory (or specified path) is a Git repository."""
    try:
        _, _, returncode = run_git_command(
            ["rev-parse", "--git-dir"], 
            cwd=path, 
            check=False
        )
        return returncode == 0
    except GitError:
        return False


def get_current_branch() -> Optional[str]:
    """Get the current branch name, or None if in detached HEAD state."""
    try:
        stdout, _, _ = run_git_command(["branch", "--show-current"])
        return stdout if stdout else None
    except GitError:
        return None


def get_repository_root(path: Optional[str] = None) -> Optional[str]:
    """Get the root directory of the Git repository."""
    try:
        stdout, _, _ = run_git_command(
            ["rev-parse", "--show-toplevel"], 
            cwd=path
        )
        return stdout
    except GitError:
        return None


def has_uncommitted_changes() -> bool:
    """Check if there are uncommitted changes in the working directory."""
    try:
        stdout, _, _ = run_git_command(["status", "--porcelain"])
        return bool(stdout)
    except GitError:
        return False


def get_remote_url(remote: str = "origin") -> Optional[str]:
    """Get the URL of a remote repository."""
    try:
        stdout, _, _ = run_git_command(["remote", "get-url", remote])
        return stdout
    except GitError:
        return None
