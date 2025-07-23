#!/usr/bin/env python3
"""
Setup script for BetterGit development and testing.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr.strip()}")
        return False


def main():
    """Main setup function."""
    print("🚀 BetterGit Development Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Error: pyproject.toml not found. Please run this from the project root.")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Install the package in development mode
    if not run_command("pip install -e .", "Installing BetterGit in development mode"):
        print("⚠️  Installation failed. Trying with --user flag...")
        if not run_command("pip install -e . --user", "Installing BetterGit with --user"):
            print("❌ Installation failed. Please check your Python environment.")
            sys.exit(1)
    
    # Install development dependencies
    if not run_command("pip install pytest pytest-cov", "Installing development dependencies"):
        print("⚠️  Failed to install dev dependencies, but core installation succeeded.")
    
    # Run tests if pytest is available
    try:
        subprocess.run(["pytest", "--version"], check=True, capture_output=True)
        print("\n🧪 Running tests...")
        run_command("pytest -v", "Running test suite")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n⚠️  pytest not available, skipping tests")
    
    # Check if git command is available
    print("\n🔍 Checking installation...")
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        if "BetterGit" in result.stdout or result.returncode == 0:
            print("✅ BetterGit command is available")
            print(f"Output: {result.stdout.strip()}")
        else:
            print("⚠️  git command available but may not be BetterGit")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️  Could not verify git command installation")
    
    print("\n🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Try running: git --version")
    print("2. Initialize a test repository: git init test-repo")
    print("3. Run the test suite: pytest")
    print("4. Read the documentation in README.md")


if __name__ == "__main__":
    main()
