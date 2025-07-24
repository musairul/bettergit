# BetterGit (Bit): A Modern Version Control System

## Specification v1.3

### 1. Core Philosophy

BetterGit is a command-line version control system designed to be intuitive, safe, and powerful. It builds upon the robust foundation of Git but reimagines the user experience to reduce friction, prevent common errors, and streamline modern development workflows.

- **Intuitiveness:** Commands are named for clarity (e.g., `bit save` instead of `git commit`) and feature intelligent, context-aware behaviors to minimize cognitive load. Interactive modes guide users through complex operations.
- **Safety:** Destructive operations require explicit confirmation, a comprehensive `undo` command provides a safety net, and a "dry run" mode allows for consequence-free previews. Secure credential management is prioritized.
- **Power:** Simplification does not come at the cost of capability. BetterGit provides powerful commands to automate complex, repetitive tasks.
- **Universal List Shortcut (`l`, `-list`):** As a consistent shortcut, most commands can be run with a `l` or `-list` flag to display a list of relevant items without performing an action.

### 2. Configuration (`bit config`)

BetterGit uses a clean, human-readable YAML file for configuration, located at `~/.config/bettergit/config.yml`.

### 2.1. Secure Credential Management

**Passwords and tokens will never be stored in plain text.** BetterGit integrates with the native OS credential manager to securely store Personal Access Tokens (PATs) and other secrets for services like GitHub and GitLab.

### 2.2. `config.yml` Structure

```yaml
# ~/.config/bettergit/config.yml
accounts:
  personal:
    name: "Your Name"
    email: "personal@example.com"
    ssh_key: "~/.ssh/id_rsa_personal"
  work:
    name: "Your Work Name"
    email: "work@company.com"
    ssh_key: "~/.ssh/id_rsa_work"

# The currently active account for authoring new saves.
current_account: personal

# Default settings for new projects.
defaults:
  remote_service: "github"
  repo_visibility: "private"
  main_branch_name: "main"

# Optional integration with an issue tracker.
issue_tracker:
  platform: "github" # or "jira"
  api_url: "https://api.github.com"
  project_key: "PROJ"

```

### 3. Core Commands

### `bit init [project-name]`

Initializes a new project and repository, with an interactive prompt to create and link a remote repository.

### `bit save "Your save message"`

Creates a "save" (equivalent to a Git commit). Automatically stages all changes by default. Interactive mode is triggered if no message is provided.

### `bit list`

Provides a quick overview of repository components: `branches`, `saves`, `remotes`, `accounts`, and `stashes`.

### `bit switch [target]`

Intelligently navigates the repository, switching between branches, saves (detached HEAD), or accounts.

### `bit push` & `bit pull`

Standard push and pull commands with smart defaults.

### `bit merge`

Combines branches with an intuitive `source -> destination` syntax and an interactive mode.

### `bit stash`

Manually saves uncommitted changes to a temporary area.

### 4. Smart Features

### 5. Safety & Recovery Commands

### `bit undo`

Reverts the most recent state-changing action recorded in the history. It is context-aware and provides strong safeguards for destructive operations like undoing a push.

### `bit history`

Maintains an immutable, numbered audit log of all state-changing actions, which powers the `undo` command.

### `bit status`

Provides a clear summary of the repository's state.

### `bit what-if` (Dry Run Mode)

Allows a user to preview the outcome of a command without making any changes.

- **`bit what-if merge [branch]`**: Reports potential merge conflicts.
- **`bit what-if sync`**: Details the sequence of pull, rebase, and push actions it will perform.

### 6. Enhanced Workflow Commands

### `bit pr` (Pull Request Management)

Integrates with remote platforms like GitHub and GitLab to manage pull/merge requests.

- **`bit pr create`**: An interactive command that guides the user through creating a new pull request from their current branch.
- **`bit pr list`**: Shows open pull requests for the repository.
- **`bit pr checkout [number]`**: Checks out the branch associated with a specific pull request for easy review.

### `bit workon [issue-id]` (Task-Oriented Workflows)

Streamlines the process of working on a specific task from an issue tracker.

1. Connects to the issue tracker specified in `config.yml`.
2. Fetches the issue title (e.g., "Fix user login button").
3. Automatically creates and switches to a new branch with a descriptive, consistent name (e.g., `feature/PROJ-123-fix-user-login-button`).

### `bit sync`

A single command to fully synchronize local and remote states (stashes, pulls with rebase, pushes, and unstashes).

### `bit graph`

Displays a text-based graph of the branch and merge history.

### `bit cleanup`

Performs housekeeping tasks like pruning stale branches and running garbage collection.

### `bit fixup [save-reference]`

Allows a user to easily amend an older save via a guided interactive rebase.