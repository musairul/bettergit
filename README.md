# BetterGit 🚀

> Git that actually makes sense - interactive, intelligent, and impossibly simple

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)


BetterGit transforms the Git experience with intuitive commands, interactive menus, and human-readable output. Say goodbye to cryptic Git commands and hello to a version control system that actually makes sense.




## 🎯 Why BetterGit? See The Difference

**One command, multiple superpowers:**

| Traditional Git | BetterGit Magic |
|----------------|-----------------|
| `git init` + `git remote add origin...` + `gh repo create...` | `bit init` does ALL of this + GitHub repo creation + automatic setup |
| `git reset --soft HEAD~1` + `git branch -d name` + `git revert abc123` | `bit undo` handles ALL reversals + safe confirmations + interactive recovery |
| `git checkout main` + `git checkout -b feature` + `git checkout abc123` | `bit switch` handles ALL of these + account switching + interactive menus |
| `git log --oneline` + `git branch -a` + `git stash list` | `bit list` shows everything + command history + interactive selection |

**Workflows that just work:**

```bash
# Start a new project (Traditional Git: 5+ commands)
bit init my-project                # → Creates repo locally AND on GitHub
                                  # → Sets up remote automatically  
                                  # → Opens in your editor

# Work on any issue (Traditional Git: lookup issue, create branch manually)
bit workon 123                     # → Auto-creates descriptive branch
                                  # → Links to GitHub issue
                                  # → Switches you there instantly

# Clone anything (Traditional Git: find URL, clone, setup)
bit clone                         # → Shows YOUR repos with descriptions
                                  # → Detects GitHub URL in clipboard
                                  # → Auto-opens in editor after clone
```

**Every command is interactive** 

Never guess what to do again. Just type the command by itself

```bash
bit switch                         # Interactive menu: branches, commits, accounts
bit list                          # Choose: saves, branches, history, accounts  
bit undo -i                          # Smart menu: undo commits, delete branches, fix ANY mistake
bit clone                         # Your repos + clipboard detection + auto-setup
```

## 🎯 Core Superpowers

### 🔄 `bit switch` - The Ultimate Navigation

**Never remember syntax again.** One command handles everything:

```bash
bit switch                        # Interactive menu shows:
                                 # ✅ All branches (local & remote)
                                 # ✅ Recent commits  
                                 # ✅ Account switching
                                 # ✅ Create new branch option

# Or be specific if you want:
bit switch main                   # Switch to main branch
bit switch new-feature -c         # Create and switch to new branch
bit switch work-account           # Switch to work GitHub account
bit switch abc123                 # Go to specific commit
```

### 📋 `bit list` - Universal Explorer  

**One command to see everything** in your repository:

```bash
bit list                         # Interactive menu:
                                # ✅ Recent saves (commits)
                                # ✅ All branches
                                # ✅ Your command history
                                # ✅ Configured accounts
                                # ✅ Stashed changes

# Or jump directly:
bit list saves                   # Beautiful commit history
bit list branches               # All branches with descriptions
bit list accounts               # Switch between work/personal
```

### 🏗️ `bit init` - Project Creation Wizard

**Stop wrestling with setup.** From idea to working repo in one command:

```bash
bit init my-amazing-project      # Does EVERYTHING:
                                # ✅ Creates local Git repo
                                # ✅ Creates GitHub repository
                                # ✅ Sets up remote connection
                                # ✅ Creates initial commit
                                # ✅ Opens in your editor
```

### ↩️ `bit undo` - The Ultimate Safety Net

**Made a mistake? No problem.** BetterGit can undo ANYTHING safely:

```bash
bit undo                         # Interactive menu shows:
                                # ✅ Recent commits to undo
                                # ✅ Branches to delete
                                # ✅ Actions to reverse
                                # ✅ Safe revert options

# Undo specific things:
bit undo abc123                  # Undo a specific commit (safely)
bit undo feature-branch          # Delete a branch (with protection)
bit undo -i                      # Interactive mode - choose what to undo
```

**Never fear Git again** - BetterGit tracks everything and can reverse any operation safely, with confirmations and protection for important branches.

## 📋 Essential Commands

| What You Want | BetterGit Magic | Why It's Better |
|---------------|-----------------|-----------------|
| Save changes | `bit save "message"` | Smart staging + commit in one |
| Navigate anywhere | `bit switch` | Branches, commits, accounts - all interactive |
| See everything | `bit list` | Commits, branches, history, accounts - one command |
| Start project | `bit init project` | Local + GitHub repo + setup automatically |
| Get any repo | `bit clone` | Your repos listed + clipboard detection |
| **Fix ANY mistake** | `bit undo` | **Safely reverse ANY operation - commits, branches, actions** |

## 🎓 Learn As You Go

Built-in interactive tutorial covers everything:

```bash
bit tutorial                     # Interactive learning menu
bit tutorial -t basics          # Specific topic
```

---

## 📚 Need More Details?

<details>
<summary><strong>🎯 Complete Command Reference</strong></summary>

### Core Commands

| Command | Description | Examples |
|---------|-------------|----------|
| `bit init` | Initialize repository + GitHub | `bit init my-project` |
| `bit save` | Smart add + commit | `bit save "message"` |
| `bit switch` | Navigate everything | `bit switch`, `bit switch main`, `bit switch -c new` |
| `bit status` | Repository status | `bit status` |
| `bit list` | List everything | `bit list`, `bit list saves` |
| `bit undo` | Safe undo operations | `bit undo`, `bit undo -i` |
| `bit clone` | Smart repository cloning | `bit clone` |
| `bit push` | Push with intelligence | `bit push` |
| `bit pull` | Pull with safety | `bit pull` |

### Advanced Features

| Command | Description | Examples |
|---------|-------------|----------|
| `bit pr` | Pull request management | `bit pr create`, `bit pr list` |
| `bit workon` | Issue branch creation | `bit workon 123` |
| `bit cleanup` | Repository maintenance | `bit cleanup --dry-run` |
| `bit tutorial` | Interactive learning | `bit tutorial -t basics` |
| `bit config` | Configuration | `bit config` |

</details>

<details>
<summary><strong>🚀 Advanced Workflows</strong></summary>

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

#### Repository Management
```bash
bit init my-project                 # Creates local repo and offers GitHub creation
bit clone                           # Lists your repositories with descriptions
```

#### Pull Request Workflow
```bash
bit pr create -t "Fix bug"          # Create PR with title and body
bit pr list                         # List all PRs with status
bit pr checkout 42                  # Checkout PR #42 locally
```

#### Issue Workflow
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

## 🌟 The Bottom Line

**BetterGit isn't just another Git wrapper.** It's a complete reimagining of version control that makes Git work the way it should have from the beginning.

### ✨ What You Get

- **🎯 Zero Learning Curve**: Interactive menus mean you never guess what to do
- **🚀 Supercharged Commands**: One command does what Git needs 3-5 commands for  
- **🛡️ Built-in Safety**: Confirmations, protections, and smart undo keep your work safe
- **↩️ Ultimate Undo Power**: `bit undo` can reverse ANY mistake - commits, merges, deletions, anything
- **🔗 GitHub Native**: Clone, PR, issues - all integrated seamlessly
- **⚡ Lightning Fast**: Get more done with fewer commands and less thinking

## 🚀 Get Started in 30 Seconds

```bash
# Clone and setup
git clone https://github.com/musairul/bettergit.git && cd bettergit
pip install -r requirements.txt
pip install -e .

bit tutorial    # Experience the magic!
```

### ⚠️ BetterGit is in beta so there will be bugs!

Please report any bugs you may find using the links below.

---




###  📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

**[⭐ Star this project](https://github.com/musairul/bettergit)** • **[🐛 Report Bug](https://github.com/musairul/bettergit/issues)** • **[💡 Request Feature](https://github.com/musairul/bettergit/issues)**

Made with ❤️ for developers who want Git to be simple and powerful. 

Star ⭐ this repository if BetterGit helped you!

*Transform your Git workflow today*

</div>
