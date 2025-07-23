"""Tests for BetterGit core functionality."""

import pytest
import subprocess
from unittest.mock import patch, MagicMock
from bettergit.core.git import run_git_command, GitError, check_git_available


class TestGitWrapper:
    """Test the core Git wrapper functionality."""
    
    def test_check_git_available_success(self):
        """Test git availability check when git is available."""
        with patch('shutil.which', return_value='/usr/bin/git'):
            assert check_git_available() is True
    
    def test_check_git_available_failure(self):
        """Test git availability check when git is not available."""
        with patch('shutil.which', return_value=None):
            assert check_git_available() is False
    
    def test_run_git_command_success(self):
        """Test successful git command execution."""
        mock_result = MagicMock()
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('bettergit.core.git.check_git_available', return_value=True):
                stdout, stderr, returncode = run_git_command(['status'])
                
                assert stdout == "test output"
                assert stderr == ""
                assert returncode == 0
    
    def test_run_git_command_failure(self):
        """Test git command execution failure."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repository"
        mock_result.returncode = 128
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('bettergit.core.git.check_git_available', return_value=True):
                with pytest.raises(GitError) as exc_info:
                    run_git_command(['status'])
                
                assert "fatal: not a git repository" in str(exc_info.value)
    
    def test_run_git_command_no_check(self):
        """Test git command execution without error checking."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "error"
        mock_result.returncode = 1
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('bettergit.core.git.check_git_available', return_value=True):
                stdout, stderr, returncode = run_git_command(['status'], check=False)
                
                assert stdout == ""
                assert stderr == "error"
                assert returncode == 1
    
    def test_run_git_command_git_not_available(self):
        """Test git command when git is not available."""
        with patch('bettergit.core.git.check_git_available', return_value=False):
            with pytest.raises(GitError) as exc_info:
                run_git_command(['status'])
            
            assert "Git is not installed" in str(exc_info.value)
