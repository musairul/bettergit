# BetterGit

A modern, intuitive version control system built on Git.

## Overview

BetterGit reimagines the Git user experience to be more intuitive, safe, and powerful. It provides a clean command-line interface that simplifies common Git operations while maintaining full Git compatibility.

## Features

- **Intuitive Commands**: Use `bit save` instead of `git commit`, with smart defaults and interactive modes
- **Safety First**: Comprehensive undo system and confirmation prompts for dangerous operations
- **Modern Workflows**: Built-in support for pull requests, issue tracking, and team collaboration
- **Secure Credentials**: Native OS credential storage - no more plain text tokens
- **Smart Automation**: Automatic conflict detection, intelligent branch switching, and streamlined sync operations

## Installation

```bash
pip install bettergit
```

## Quick Start

```bash
# Initialize a new project with remote repository
bit init my-project

# Save your changes with an interactive prompt
bit save

# List everything in your repository
bit list

# Switch between branches, commits, or accounts intelligently
bit switch feature-branch

# Create a pull request
bit pr create

# Start working on an issue
bit workon 123

# Sync everything with one command
bit sync

# Undo the last action
bit undo
```

## Core Commands

### Repository Management
- `bit init [project-name]` - Initialize repository with optional remote creation
- `bit save "message"` - Commit changes with smart staging
- `bit switch [target]` - Switch between branches, commits, or accounts
- `bit sync` - Full synchronization (stash, pull, rebase, push, unstash)
- `bit status` - Clean, formatted repository status

### Information & History
- `bit list [type]` - List branches, saves, remotes, accounts, or stashes
- `bit graph` - Visual commit history graph
- `bit history` - Action history for undo functionality
- `bit undo` - Undo the last state-changing action

### Pull Request Management
- `bit pr create` - Create a new pull request
- `bit pr list` - List pull requests
- `bit pr checkout [number]` - Check out a PR branch

### Workflow Commands
- `bit workon [issue-id]` - Start working on an issue (creates branch)
- `bit cleanup` - Repository housekeeping
- `bit stash [message]` - Manual stash with optional message

## Configuration

BetterGit uses a YAML configuration file at `~/.config/bettergit/config.yml`:

```yaml
accounts:
  personal:
    name: "Your Name"
    email: "personal@example.com"
    ssh_key: "~/.ssh/id_rsa_personal"
  work:
    name: "Work Name"
    email: "work@company.com"
    ssh_key: "~/.ssh/id_rsa_work"

current_account: personal

defaults:
  remote_service: "github"
  repo_visibility: "private"
  main_branch_name: "main"

issue_tracker:
  platform: "github"
  api_url: "https://api.github.com"
  project_key: "PROJ"
```

### Secure Credential Management

BetterGit never stores passwords or tokens in plain text. Instead, it uses your operating system's native credential manager:

- **macOS**: Keychain
- **Windows**: Windows Credential Manager
- **Linux**: Secret Service API

When you first use a command that requires authentication, BetterGit will prompt for your token and store it securely.

## Safety Features

### Undo System
Every state-changing action is logged and can be undone:
- `bit undo` - Undo the last action
- `bit history` - View action history

### Confirmation Prompts
Dangerous operations require explicit confirmation, with varying levels based on risk:
- **Low**: Proceed automatically
- **Medium**: Simple yes/no prompt
- **High**: Clear warning with confirmation
- **Extreme**: Require typing the target name

## Development

### Setting up for Development

```bash
# Clone the repository
git clone https://github.com/bettergit/bettergit.git
cd bettergit

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=bettergit
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_git.py

# Run with coverage report
pytest --cov=bettergit --cov-report=html
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://docs.bettergit.dev)
- 🐛 [Bug Reports](https://github.com/bettergit/bettergit/issues)
- 💬 [Discussions](https://github.com/bettergit/bettergit/discussions)
