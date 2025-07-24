# BetterGit 🚀

> A modern, intuitive interface for Git that makes version control easy and enjoyable

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Why BetterGit? See The Difference

**Traditional Git workflow** (confusing, error-prone):
```bash
git add .
git commit -m "fix login bug"
git checkout -b new-feature
git branch -d old-branch
git log --oneline --graph --all
git reset --soft HEAD~1
```

**BetterGit workflow** (intuitive, safe):
```bash
bit save "fix login bug"           # Smart add + commit
bit switch new-feature -c          # Create and switch in one command  
bit undo old-branch                # Delete with safety checks
bit list saves                     # Human-readable history
bit undo                           # Smart undo with confirmation
```

## 🚀 Get Started in 30 Seconds

```bash
# Clone and setup
git clone https://github.com/musairul/bettergit.git && cd bettergit
pip install -r requirements.txt

# Your first BetterGit experience
python -m bettergit.cli tutorial    # Interactive learning
```

**Or jump right in:**
```bash
bit init my-project                 # Create repo (+ optional GitHub repo)
bit save "Initial commit"           # Save your changes
bit switch feature-branch -c        # Create and switch to new branch
bit save "Add cool feature"         # Save feature work
bit undo                           # Oops! Undo that last save
```

---

## ✨ What Makes BetterGit Special

BetterGit transforms Git from a cryptic command-line tool into an intuitive, safe, and powerful version control system that actually makes sense.

## ✨ What Makes BetterGit Special

BetterGit transforms Git from a cryptic command-line tool into an intuitive, safe, and powerful version control system that actually makes sense.

**🎯 For Everyone:** Intuitive commands like `bit save` and `bit switch` make version control accessible  
**🛡️ Safety First:** Smart undo system and confirmations prevent costly mistakes  
**🚀 Productivity:** Interactive menus and auto-completion speed up common tasks  
**🎓 Learning Built-in:** Comprehensive tutorial system teaches best practices  

## 🛠️ Essential Commands

| What You Want To Do | BetterGit Command | Traditional Git |
|---------------------|-------------------|-----------------|
| Save your changes | `bit save "message"` | `git add . && git commit -m "message"` |
| Create new branch | `bit switch new-branch -c` | `git checkout -b new-branch` |
| See what's changed | `bit status` | `git status` |
| View commit history | `bit list saves` | `git log --oneline` |
| Undo last action | `bit undo` | `git reset --soft HEAD~1` (maybe?) |
| Clone a repository | `bit clone` | `git clone <url>` (if you know the URL) |

## 🎓 Learn As You Go

BetterGit includes a complete interactive tutorial system:

```bash
bit tutorial                        # Interactive menu of all topics
bit tutorial -t basics              # Learn the fundamentals
bit tutorial -t saving              # Master the save command
bit tutorial -t undo                # Learn to fix mistakes safely
```

Seven comprehensive topics cover everything from basics to advanced workflows.

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

BetterGit includes a comprehensive tutorial system with 7 interactive topics, run: `bit tutorial`

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

## 🎯 Use Cases - Who Benefits?

**🆕 New Developers:** Skip the Git learning curve with intuitive commands and built-in tutorials  
**👨‍💻 Experienced Developers:** Save time with streamlined workflows and powerful features  
**👥 Teams:** Consistent interface and enhanced collaboration tools  
**🌟 Open Source Contributors:** Easy repo management and multi-account support  

## ⚙️ Quick Configuration

```bash
bit config                          # Opens config in your editor
```

BetterGit stores settings in `~/.bettergit/config.yml` for easy customization.

---

## 📚 Detailed Documentation

<details>
<summary><strong>🔧 Advanced Workflows & Features</strong></summary>

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

</details>

<details>
<summary><strong>🛡️ Safety Features & GitHub Integration</strong></summary>

### Safety Features

BetterGit prioritizes safety without sacrificing power:

- **Confirmation prompts** for destructive operations
- **Protected branches** (main, master, develop) require extra confirmation  
- **Action history** tracks all operations for easy undo
- **Dry run modes** for preview before execution
- **Smart error messages** with suggested solutions

### GitHub Integration

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

</details>

<details>
<summary><strong>📊 Traditional Git vs BetterGit Comparison</strong></summary>

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

</details>

<details>
<summary><strong>🔍 Troubleshooting & Development</strong></summary>

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

### Contributing

1. Fork the repository
2. Create a feature branch: `bit switch feature-name -c`
3. Make your changes and test thoroughly
4. Save your changes: `bit save "Add feature description"`
5. Push and create a pull request: `bit push && bit pr create`

</details>

---

Made with ❤️ for developers who want Git to be simple and powerful.

*Star ⭐ this repository if BetterGit helped you!*

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

**[⭐ Star this project](https://github.com/musairul/bettergit)** • **[🐛 Report Bug](https://github.com/musairul/bettergit/issues)** • **[💡 Request Feature](https://github.com/musairul/bettergit/issues)**

Made with ❤️ by developers, for developers

*Transform your Git workflow today*

</div>
