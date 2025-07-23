# BetterGit (bit) Usage Guide

## 🎯 **Overview**

**BetterGit** is now available as the `bit` command to avoid conflicts with regular Git. All the power of modern version control without interfering with your existing Git workflow!

## 🚀 **Quick Start**

### **Installation**
The package is already installed! You can use `bit` commands immediately.

### **Basic Usage**
```bash
# Check if you're in a git repository
bit status

# Initialize a new repository
bit init my-project

# Save your changes (better than git commit)
bit save "Your commit message"

# List everything in your repository
bit list

# View history and undo if needed
bit history
bit undo
```

## 📋 **Command Reference**

### **Core Operations**
| Command | Description | Example |
|---------|-------------|---------|
| `bit init [name]` | Initialize repository | `bit init my-app` |
| `bit save "msg"` | Smart commit with staging | `bit save "Add login feature"` |
| `bit status` | Repository status | `bit status` |
| `bit switch target` | Switch branches/commits | `bit switch main` |
| `bit push` | Push to remote | `bit push` |
| `bit pull` | Pull from remote | `bit pull` |

### **Information & History**
| Command | Description | Example |
|---------|-------------|---------|
| `bit list [type]` | List branches/saves/accounts | `bit list branches` |
| `bit graph` | Visual commit history | `bit graph` |
| `bit history` | Action history | `bit history` |
| `bit undo` | Undo last action | `bit undo` |

### **Advanced Workflow**
| Command | Description | Example |
|---------|-------------|---------|
| `bit sync` | Full synchronization | `bit sync` |
| `bit workon 123` | Start working on issue | `bit workon 123` |
| `bit pr create` | Create pull request | `bit pr create` |
| `bit cleanup` | Repository maintenance | `bit cleanup --dry-run` |

## 🛡️ **Safety Features**

### **Automatic Protection**
- **Auto-stashing**: Automatically stashes changes during risky operations
- **Undo system**: Every action can be undone with `bit undo`
- **Confirmation prompts**: Dangerous operations require confirmation
- **Dry-run mode**: Preview changes with `--dry-run` flag

### **Smart Defaults**
- **Interactive staging**: `bit save` without arguments prompts for file selection
- **Intelligent switching**: `bit switch` works with branches, commits, or accounts
- **Safe merging**: Automatic conflict detection and resolution guidance

## 💡 **Workflow Examples**

### **Daily Development**
```bash
# Start your day
bit status                          # See what's changed
bit list                           # Overview of everything

# Make changes and save
echo "new feature" > feature.py
bit save "Add new feature"         # Interactive file selection
bit save "Add new feature" --all   # Stage all changes

# Work with branches
bit switch -c feature/auth         # Create and switch to new branch
bit save "Implement authentication"
bit switch main                    # Switch back to main
bit list branches                  # See all branches
```

### **Collaboration**
```bash
# Sync with team
bit sync                           # Stash, pull, rebase, push, unstash

# Work on issues
bit workon 42                      # Creates branch issue-42
bit save "Fix user login bug"
bit pr create                      # Create pull request

# Review others' work
bit pr list                        # List open PRs
bit pr checkout 15                 # Check out PR #15
```

### **Maintenance**
```bash
# Keep repository clean
bit cleanup --dry-run              # Preview cleanup actions
bit cleanup                        # Actually clean up

# History and recovery
bit history                        # See recent actions
bit undo                          # Undo last action
bit graph                         # Visual commit history
```

## 🔧 **Configuration**

### **Account Management**
```bash
# BetterGit automatically detects your git config
# View current accounts
bit list accounts

# Switch between accounts (if you have multiple)
bit switch account@domain.com
```

### **Secure Credentials**
- **Never stores passwords in plain text**
- **Uses OS credential managers** (Windows Credential Manager, macOS Keychain, etc.)
- **Prompts for tokens only when needed**

## 🆚 **bit vs git**

| **Task** | **Regular Git** | **BetterGit (bit)** |
|----------|-----------------|---------------------|
| Commit changes | `git add . && git commit -m "msg"` | `bit save "msg"` |
| View status | `git status` | `bit status` (cleaner output) |
| See history | `git log --oneline --graph` | `bit graph` |
| Undo commit | `git reset --soft HEAD~1` | `bit undo` |
| Switch branch | `git checkout branch` | `bit switch branch` |
| Full sync | `git stash && git pull --rebase && git push && git stash pop` | `bit sync` |

## 🎯 **Key Benefits**

1. **✅ No Conflicts**: Uses `bit` command, so your existing `git` commands still work
2. **🛡️ Safer**: Automatic stashing, undo system, confirmation prompts
3. **🚀 Faster**: Single commands for complex operations (`bit sync`)
4. **🎨 Cleaner**: Beautiful, readable output with proper formatting
5. **🔒 Secure**: Never stores credentials in plain text
6. **📚 Intuitive**: Commands that make sense (`bit save` instead of `git commit`)

## 🆘 **Getting Help**

```bash
# General help
bit --help

# Command-specific help
bit save --help
bit pr --help

# View all available commands
bit --help
```

## 🎉 **Ready to Use!**

BetterGit is fully installed and ready to use. Start with:

```bash
bit status    # Check your current repository
bit list      # See everything at a glance
bit --help    # Explore all commands
```

**Happy coding with BetterGit!** 🚀
