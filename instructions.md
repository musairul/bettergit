# Prompt: Implementing the BetterGit Specification

**Role:** You are a senior principal software engineer with 30 years of experience, specializing in Python, system architecture, and the deep internals of Git. Your task is to architect and implement "BetterGit," a new version control system, based on the provided specification.

**Core Objective:** Create a robust, maintainable, and user-centric command-line tool in Python. The final product must be a wrapper around the standard Git command-line tool, enhancing its functionality rather than replacing its core. Prioritize clean architecture, comprehensive error handling, and a seamless user experience.

## Phase 1: Foundation & Project Architecture

Before writing any feature-specific code, establish a solid foundation.

1. **Project Structure:**
    - `bettergit/`: The main source directory.
    - `bettergit/cli.py`: Entry point for the command-line interface.
    - `bettergit/core/`: For core logic wrapping Git commands.
    - `bettergit/config.py`: Manages loading and saving the YAML configuration.
    - `bettergit/history.py`: Manages the action history for the `undo` command.
    - `bettergit/ui.py`: Contains all logic for interactive prompts, lists, and tables.
    - `bettergit/integrations/`: For third-party API clients (GitHub, Jira, etc.).
    - `tests/`: The directory for our unit and integration tests.
    - `setup.py` or `pyproject.toml`: For packaging and distribution.
2. **Dependencies:**
    - **Command-Line Interface:** Use `click` or `typer` for robust command, argument, and option parsing. This is non-negotiable for creating a clean CLI.
    - **Git Interaction:** Use the `subprocess` module to call the standard `git` executable. Do **not** use a third-party Git library initially, as we need direct, unfiltered access to Git's output and error streams to build our custom logic.
    - **Configuration:** Use `PyYAML` for handling the `config.yml` file.
    - **Interactive UI:** Use `inquirer` or `rich` to build the interactive lists, prompts, and beautifully formatted output (e.g., for `bit graph` and `bit list`).
    - **Credential Management:** Use the `keyring` library. It provides a cross-platform abstraction over native OS credential managers (macOS Keychain, etc.) and is the industry standard for this task.
3. **Core Git Wrapper (`bettergit/core/git.py`):**
    - Create a central function, e.g., `run_git_command(command: list) -> (str, str, int)`, that executes a Git command using `subprocess.run()`.
    - This function must capture `stdout`, `stderr`, and the `returncode` meticulously. All other parts of the application will use this function to interact with Git. This centralizes our interaction point for easy debugging and logging.

## Phase 2: Configuration & Credential Security (`bit config`)

This is a security-critical step.

1. **Configuration Logic (`config.py`):**
    - Implement a `ConfigManager` class. On initialization, it should find and load `~/.config/bettergit/config.yml`. If it doesn't exist, create it from a default template.
    - Provide methods to get and set values (e.g., `get_current_account()`, `set_current_account(alias)`).
    - When handling accounts, the `password` or `token` field from the user's original spec **must be ignored**. We will never read or write secrets to this file.
2. **Secure Credential Flow:**
    - When an operation requires authentication (e.g., `bit pr create`), the application must first try to retrieve the necessary token from the system's keychain using `keyring.get_password("bettergit", account_alias)`.
    - If the token is not found, *then* prompt the user for it.
    - After the user provides the token, immediately store it using `keyring.set_password("bettergit", account_alias, token)`. Inform the user that the token has been securely stored for future use.

## Phase 3: Implementing the Command Suite

Build out the commands one by one, ensuring each is thoroughly tested before moving to the next.

1. **`bit init`:**
    - Create the directory.
    - Run `git init` via our wrapper.
    - Use the `inquirer` library to ask the user if they want to create a remote.
    - If yes, use the `integrations` module (e.g., a `GitHubClient` class) with the stored credentials to create the repository via API.
    - Run `git remote add origin [url]` to link them.
2. **`bit save`:**
    - If a message is provided, run `git add .` followed by `git commit -m "message"`.
    - If no message is provided, fetch the output of `git status --porcelain`. Parse this to get a list of modified/untracked files.
    - Use `inquirer` to present a checkbox list to the user.
    - Once files are selected, run `git add [selected_files]` and then prompt for a commit message before running `git commit`.
3. **`bit list`:**
    - `list branches`: Run `git branch -a`. Parse the output to create a clean table using `rich`.
    - `list saves`: Run `git log --pretty=format:"%h|%an|%s"`. Parse this delimited string to populate a numbered list.
    - `list accounts`: Read the `accounts` section from `config.yml`.
4. **`bit switch`:**
    - Implement the core logic to intelligently detect the target type. A good strategy is to check in order:
        1. Is the target a known branch name (from `git branch`)?
        2. Is the target a known account alias (from `config.yml`)?
        3. Does the target look like a commit hash (check length and characters)?
    - If ambiguous, exit with a clear error message.
    - For switching saves, use `git checkout [hash]`. Be sure to inform the user they are in a "detached HEAD" state.
5. **`bit history` & `bit undo`:**
    - Create an `ActionHistory` class (`history.py`). It should manage a simple JSON file (e.g., `~/.config/bettergit/history.json`) that acts as a stack.
    - Every successful state-changing command (`save`, `push`, `merge`, etc.) must call `history.log_action(action_details)`.
    - The `bit undo` command reads the last action from this file and executes the inverse operation.
        - Undo `save`: `git reset --soft HEAD~1`.
        - Undo `merge`: `git reset --hard ORIG_HEAD`.
        - Undo `push`: This is the most dangerous. It requires a `git push --force` operation. You **must** implement a confirmation prompt that requires the user to type the branch name to proceed.

## Phase 4: Workflow & Integration Commands

These commands separate BetterGit from a simple wrapper to a true productivity tool.

1. **`bit pr`:**
    - Implement API client classes in the `integrations` directory for GitHub, GitLab, etc.
    - `pr create`: Get the current branch name and push it. Then, make an API call to create the PR, using interactive prompts to get the title and body.
    - `pr checkout`: Use the API to get the branch name for the PR number, then run `git fetch` and `git switch [branch-name]`.
2. **`bit workon`:**
    - This will heavily use the `integrations` client.
    - Call the API to get the issue details.
    - Construct the branch name from the issue ID and title (e.g., `feature/PROJ-123-a-clear-title`).
    - Execute `git switch -c [new_branch_name]`.
3. **`bit sync`:**
    - This is a carefully sequenced script of Git commands.
    - Execute `git stash push`.
    - Execute `git pull --rebase`.
    - Execute `git push`.
    - Execute `git stash pop`.
    - Each step must be checked for errors. If any step fails, halt and provide a clear status report to the user.

## Final Polish & Delivery

- **Error Handling:** Every `subprocess` call and API request must be wrapped in `try...except` blocks. If a Git command fails, print its `stderr` to the user in a readable format. Never let the application crash with an unhandled exception.
- **Testing:** Aim for high test coverage. Use `pytest`. Mock `subprocess` calls to test your logic without actually running Git. Mock API calls to test integrations.
- **Packaging:** Use `pyproject.toml` and a modern build backend like `flit` or `poetry` to define the project and its dependencies, and configure the `console_scripts` entry point to create the `bit` executable.

Execute this plan meticulously. The result should be a piece of software that feels professional, reliable, and genuinely helpful to developers.