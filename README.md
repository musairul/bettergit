# BetterGit 🚀

> A modern, intuitive interface for Git that makes version control easy and enjoyable

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

BetterGit transforms the Git experience with intuitive commands, interactive menus, and human-readable output. Say goodbye to cryptic Git commands and hello to a version control system that actually makes sense.

## ✨ Features

### 🎯 **Intuitive Commands**
- `bit save` instead of complex `git add` + `git commit` workflows
- `bit switch` for seamless branch and commit navigation with auto-creation
- `bit undo` with smart detection of what to reverse
- `bit list` with interactive menus for everything

### 🔄 **Smart Branch Management**
- **Auto-creation**: Switch to non-existent branches with automatic creation prompts
- **Interactive switching**: Navigate between branches, commits, and user accounts
- **Branch protection**: Safety checks for critical branches (main, master, develop)

### 📋 **Comprehensive History**
- **Dual tracking**: Both Git history and action history
- **Smart formatting**: Relative timestamps and readable output
- **Interactive selection**: Choose from recent actions with arrow keys

### 🌐 **Seamless Remote Integration**
- **Smart cloning**: Auto-detect clipboard URLs and list your repositories
- **GitHub integration**: Create repos, manage PRs, work on issues
- **Multi-account support**: Switch between work and personal accounts effortlessly

### ↩️ **Powerful Undo System**
- **Targeted undo**: Undo specific commits or delete specific branches
- **Interactive undo**: Visual timeline to select what to reverse
- **Safety first**: Confirmation prompts and protected operations

### 🎓 **Built-in Learning**
- **Interactive tutorial**: Learn BetterGit with hands-on examples
- **Contextual help**: Every command has detailed help text
- **Progressive complexity**: From basics to advanced workflows

### ⚡ **Advanced Features**
- **Stash management**: Temporary change storage with descriptive messages
- **Force operations**: When you need the power (with safety warnings)
- **Repository maintenance**: Automated cleanup and optimization
- **Configuration management**: Customizable defaults and preferences

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/bettergit.git
cd bettergit

# Install dependencies
pip install -r requirements.txt

# Make BetterGit available globally (optional)
pip install -e .
```

### Your First Repository

```bash
# Create a new project
bit init my-awesome-project

# Save your first changes
bit save "Initial commit"

# Learn more with the tutorial
bit tutorial
```

## 📖 Core Concepts

### 💾 Saves (Commits)
Think of saves like checkpoints in a video game:

```bash
bit save "Fixed login bug"           # Save all changes
bit save file.py "Updated logic"     # Save specific files
bit save                             # Interactive mode
```

### 🔄 Switching
Navigate between different states of your project:

```bash
bit switch main                      # Switch to main branch
bit switch feature-login             # Switch to feature branch
bit switch new-feature -c            # Create and switch to new branch
bit switch abc123                    # Go to specific commit
```

### 📋 Listing
Explore your project with interactive menus:

```bash
bit list                             # Interactive menu
bit list saves                       # Recent commits
bit list branches                    # All branches
bit list history                     # Your recent actions
```

### ↩️ Undoing
Fix mistakes with confidence:

```bash
bit undo                             # Undo last action
bit undo -i                          # Interactive undo menu
bit undo abc123                      # Undo specific commit
bit undo feature-branch              # Delete specific branch
```

## 🛠️ Command Reference

### Core Commands

| Command | Description | Examples |
|---------|-------------|----------|
| `bit init` | Initialize repository | `bit init my-project` |
| `bit save` | Create saves (commits) | `bit save "message"` |
| `bit switch` | Change branches/commits | `bit switch main`, `bit switch new-branch -c` |
| `bit status` | Show repository status | `bit status` |
| `bit list` | List repository components | `bit list saves`, `bit list` |
| `bit undo` | Undo actions | `bit undo -i`, `bit undo abc123` |

### Remote Operations

| Command | Description | Examples |
|---------|-------------|----------|
| `bit clone` | Clone repositories | `bit clone` (interactive), `bit clone <url>` |
| `bit push` | Push to remote | `bit push`, `bit push -f` |
| `bit pull` | Pull from remote | `bit pull`, `bit pull --rebase` |
| `bit sync` | Sync with remote | `bit sync` |

### Advanced Features

| Command | Description | Examples |
|---------|-------------|----------|
| `bit stash` | Temporary storage | `bit stash "WIP"` |
| `bit pr` | Pull request management | `bit pr create`, `bit pr list` |
| `bit cleanup` | Repository maintenance | `bit cleanup --dry-run` |
| `bit tutorial` | Interactive learning | `bit tutorial -t basics` |
| `bit config` | Open configuration | `bit config` |

## 🎓 Learning Path

BetterGit includes a comprehensive tutorial system with 7 interactive topics:

1. **Getting Started**: `bit tutorial -t basics`
   - Core concepts and essential commands
   - Your first repository setup

2. **Saving Changes**: `bit tutorial -t saving`
   - Understanding saves vs commits
   - Interactive and batch saving

3. **Switching & Branches**: `bit tutorial -t switching`
   - Branch navigation and creation
   - Account switching

4. **History & Listing**: `bit tutorial -t history`
   - Reading project history
   - Using the list command

5. **Remote Repositories**: `bit tutorial -t remotes`
   - GitHub integration
   - Collaboration workflows

6. **Undoing Changes**: `bit tutorial -t undo`
   - Mistake recovery
   - Targeted undo operations

7. **Advanced Features**: `bit tutorial -t advanced`
   - Power user workflows
   - Configuration and optimization

## ⚙️ Configuration

BetterGit stores configuration in `~/.bettergit/config.yml`:

```yaml
# User accounts - seamlessly switch between identities
accounts:
  work:
    name: "John Smith"
    email: "john@company.com"
  personal:
    name: "John"
    email: "john@personal.com"

# Default settings for new repositories
defaults:
  editor: "code"                    # Your preferred editor
  main_branch_name: "main"          # Default branch name
  repo_visibility: "private"        # Default repo visibility

# Current active account
current_account: "work"
```

Edit configuration:
```bash
bit config                          # Opens config in your default editor
```

## 🔧 Advanced Workflows

### Multi-Account Development

Perfect for developers juggling work and personal projects:

```bash
# Switch between work and personal accounts
bit switch work-account
bit switch personal

# Each switch updates git config for the repository
# Credentials are stored securely per account
```

### Interactive Clone Workflow

```bash
bit clone                           # Shows smart menu with:
                                   # ✅ Auto-detected clipboard URLs
                                   # ✅ Your GitHub repositories
                                   # ✅ Auto-opens in configured editor
```

### Targeted Undo Operations

```bash
# Undo specific commits
bit undo abc123                     # Interactive options:
                                   # - Revert commit (safe, keeps history)
                                   # - Interactive rebase (rewrites history)

# Delete specific branches  
bit undo feature-branch             # Smart deletion with:
                                   # - Current branch protection
                                   # - Protected branch warnings
                                   # - Remote branch cleanup
```

### Repository Maintenance

```bash
bit cleanup                         # Interactive cleanup:
                                   # - Delete merged branches
                                   # - Prune stale remotes  
                                   # - Run garbage collection

bit cleanup --dry-run               # Preview what would be cleaned
```

## 🛡️ Safety Features

BetterGit prioritizes safety without sacrificing power:

- **Confirmation prompts** for destructive operations
- **Protected branches** (main, master, develop) require extra confirmation  
- **Action history** tracks all operations for easy undo
- **Dry run modes** for preview before execution
- **Smart error messages** with suggested solutions

### Safety Levels
- **Low**: Proceed automatically
- **Medium**: Simple yes/no prompt  
- **High**: Clear warning with confirmation
- **Extreme**: Require typing the target name

## 🤝 GitHub Integration

### Repository Management
```bash
bit init my-project                 # Creates local repo and offers GitHub creation
bit clone                           # Lists your repositories with descriptions
```

### Pull Request Workflow
```bash
bit pr create -t "Fix bug"          # Create PR with title and body
bit pr list                         # List all PRs with status
bit pr checkout 42                  # Checkout PR #42 locally
```

### Issue Workflow
```bash
bit workon 123                      # Create branch for issue #123
                                   # Auto-generates descriptive branch name
```

## 📊 Why BetterGit?

### Before (Traditional Git)
```bash
git add .
git commit -m "message"
git checkout -b feature
git branch -d old-branch  
git log --oneline --graph
git reset --soft HEAD~1
```

### After (BetterGit)
```bash
bit save "message"                  # Replaces add + commit
bit switch feature -c               # Create and switch in one command
bit undo old-branch                 # Delete with safety checks
bit list saves                      # Human-readable history
bit undo                            # Smart undo with history
```

## 🎯 Use Cases

### **New Developers**
- Intuitive commands reduce Git learning curve
- Interactive tutorials teach best practices  
- Safety features prevent common mistakes

### **Experienced Developers**  
- Streamlined workflows save time
- Advanced features for power users
- Multi-account support for complex setups

### **Teams**
- Consistent command interface across members
- Built-in collaboration tools
- Enhanced pull request workflows

### **Open Source Contributors**
- Easy repository cloning and management
- GitHub integration for issues and PRs
- Account switching for multiple projects

## 🔍 Troubleshooting

### Common Issues

**Q: Command not found**
```bash
# Option 1: Run from BetterGit directory
cd path/to/bettergit
python -m bettergit.cli --help

# Option 2: Install globally
pip install -e .
bit --help
```

**Q: Git not found**
```bash
# Install Git first:
# Windows: Download from git-scm.com
# macOS: brew install git  
# Linux: sudo apt install git
```

**Q: GitHub integration not working**
```bash
# Configure your GitHub token
bit config                          # Add token to accounts section
# Or authenticate through first PR creation
bit pr create
```

### Getting Help

1. **Built-in help**: `bit --help` or `bit <command> --help`
2. **Tutorial system**: `bit tutorial` or `bit tutorial -t <topic>`
3. **Check status**: `bit status` (always start here for issues)
4. **View history**: `bit list history` (see what you did recently)
5. **Undo mistakes**: `bit undo -i` (interactive recovery)

## 🏗️ Development

### Project Structure
```
bettergit/
├── cli.py              # Main command interface with all commands
├── config.py           # Configuration management
├── history.py          # Action history tracking  
├── ui.py              # User interface utilities
├── core/
│   └── git.py         # Git operations wrapper
└── integrations/
    ├── base.py        # Integration base classes
    └── github.py      # GitHub API integration
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=bettergit

# Run specific test file
python -m pytest tests/test_git.py -v
```

### Contributing

1. Fork the repository
2. Create a feature branch: `bit switch feature-name -c`
3. Make your changes and test thoroughly
4. Save your changes: `bit save "Add feature description"`
5. Push and create a pull request: `bit push && bit pr create`

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Git**: The powerful version control system that BetterGit enhances
- **Click**: Excellent command-line interface framework  
- **Rich**: Beautiful terminal output formatting
- **PyYAML**: Configuration file handling
- **Inquirer**: Interactive command-line interfaces

## 🗺️ Roadmap

### Upcoming Features
- [ ] **Visual diff viewer** with syntax highlighting
- [ ] **Conflict resolution assistant** for merge conflicts
- [ ] **Plugin system** for custom workflows
- [ ] **Team collaboration features** (shared configurations)
- [ ] **Repository templates** for quick project setup
- [ ] **Integration with more platforms** (GitLab, Bitbucket)
- [ ] **Performance optimizations** for large repositories
- [ ] **Desktop GUI companion** for visual operations

### Recent Updates
- ✅ **v1.3.0**: Interactive tutorial system with 7 comprehensive topics
- ✅ **v1.2.0**: GitHub integration and multi-account support  
- ✅ **v1.1.0**: Enhanced undo system with targeted operations
- ✅ **v1.0.0**: Core functionality with intuitive commands

---

<div align="center">

**[⭐ Star this project](https://github.com/yourusername/bettergit)** • **[🐛 Report Bug](https://github.com/yourusername/bettergit/issues)** • **[💡 Request Feature](https://github.com/yourusername/bettergit/issues)**

Made with ❤️ by developers, for developers

*Transform your Git workflow today*

</div>
