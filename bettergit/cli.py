"""Command-line interface for BetterGit."""

import click
import os
import sys
import logging
from pathlib import Path
from typing import Optional

from .config import config_manager, ConfigError
from .history import history_manager, HistoryError
from .core.git import (
    run_git_command, GitError, is_git_repository, 
    check_git_available, get_current_branch, has_uncommitted_changes
)
from .ui import (
    print_success, print_error, print_warning, print_info,
    confirm, prompt_text, prompt_password, select_from_list, 
    select_multiple, display_table, display_list, display_panel,
    display_git_graph, display_status_summary, require_confirmation,
    SYMBOLS
)
from .integrations import GitHubClient, IntegrationError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="BetterGit")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(verbose: bool):
    """BetterGit: A modern, intuitive version control system built on Git."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if git is available
    if not check_git_available():
        print_error("Git is not installed or not in PATH. Please install Git first.")
        sys.exit(1)


@main.command()
@click.argument('project_name', required=False)
@click.option('--no-remote', is_flag=True, help='Skip remote repository creation')
def init(project_name: Optional[str], no_remote: bool):
    """Initialize a new Git repository and optionally create a remote."""
    try:
        if project_name:
            # Create directory if it doesn't exist
            project_path = Path(project_name)
            if project_path.exists() and any(project_path.iterdir()):
                if not confirm(f"Directory '{project_name}' exists and is not empty. Continue?"):
                    return
            else:
                project_path.mkdir(exist_ok=True)
            
            os.chdir(project_path)
            print_info(f"Created and entered directory: {project_name}")
        
        # Initialize git repository
        if is_git_repository():
            print_warning("Already in a Git repository.")
            return
        
        run_git_command(['init'])
        print_success("Initialized Git repository")
        
        # Create initial commit structure
        readme_path = Path("README.md")
        if not readme_path.exists():
            project_title = project_name or Path.cwd().name
            readme_content = f"# {project_title}\n\nA new project created with BetterGit.\n"
            readme_path.write_text(readme_content, encoding='utf-8')
            print_info("Created README.md")
        
        # Set up remote if requested
        if not no_remote:
            if confirm("Would you like to create a remote repository?", default=True):
                _create_remote_repository()
        
        # Log the action
        history_manager.log_action(
            "init",
            {"project_name": project_name or str(Path.cwd().name)},
            undo_command="rm -rf .git",
            undo_details={"destructive": True}
        )
        
    except (GitError, ConfigError) as e:
        print_error(f"Failed to initialize repository: {e}")
        sys.exit(1)


def _create_remote_repository():
    """Helper function to create a remote repository."""
    try:
        # Get current account configuration
        current_account = config_manager.get_current_account()
        
        # Get or prompt for token
        token = config_manager.get_credential(current_account)
        if not token:
            print_info(f"No stored credential found for account '{current_account}'")
            token = prompt_password(f"Enter GitHub token for {current_account}: ")
            if token:
                config_manager.store_credential(current_account, token)
                print_success("Token stored securely for future use")
            else:
                print_warning("No token provided, skipping remote creation")
                return
        
        # Create GitHub client
        github = GitHubClient(token)
        
        # Get repository details
        repo_name = Path.cwd().name
        description = prompt_text("Repository description (optional): ")
        
        defaults = config_manager.config.get('defaults', {})
        default_visibility = defaults.get('repo_visibility', 'private')
        is_private = default_visibility == 'private'
        
        if not confirm(f"Create {'private' if is_private else 'public'} repository '{repo_name}'?"):
            return
        
        # Create the repository
        print_info("Creating remote repository...")
        repo_data = github.create_repository(repo_name, description, is_private)
        clone_url = repo_data['clone_url']
        
        # Add remote and push
        run_git_command(['remote', 'add', 'origin', clone_url])
        
        # Create initial commit if needed
        if not has_uncommitted_changes():
            run_git_command(['add', '.'])
            run_git_command(['commit', '-m', 'Initial commit'])
        
        # Push to remote
        main_branch = defaults.get('main_branch_name', 'main')
        run_git_command(['branch', '-M', main_branch])
        run_git_command(['push', '-u', 'origin', main_branch])
        
        print_success(f"Created remote repository: {repo_data['html_url']}")
        
    except IntegrationError as e:
        print_error(f"Failed to create remote repository: {e}")
    except GitError as e:
        print_error(f"Git operation failed: {e}")


@main.command('save')
@click.argument('args', nargs=-1)
def commit_save(args):
    """Create a save (commit) with your changes.
    
    Usage: 
      bit save [files] "message"
      bit save  (interactive mode)
    
    Examples:
      bit save file1.py file2.py "created app"
      bit save . "fixed all bugs"
      bit save "initial commit"
      bit save
    """
    try:
        if not is_git_repository():
            print_error("Not in a Git repository. Use 'bit init' first.")
            return
        
        # Check if there are any changes
        status_output, _, _ = run_git_command(['status', '--porcelain'])
        if not status_output:
            print_info("No changes to save.")
            return
        
        files = []
        message = ""
        
        if not args:
            # Interactive mode - no arguments provided
            files = _select_files_to_stage()
            if not files:
                print_info("No files selected.")
                return
                
            message = prompt_text("Enter commit message: ")
            if not message:
                print_error("Commit message is required.")
                return
        else:
            # Parse arguments to separate files from message
            # Message is always the last argument and should be in quotes
            message = args[-1]
            files = list(args[:-1]) if len(args) > 1 else ['.']
        
        if not message:
            print_error("Commit message is required.")
            return
        
        # Stage the specified files
        for file_pattern in files:
            try:
                run_git_command(['add', file_pattern])
                print_info(f"Staged: {file_pattern}")
            except GitError as e:
                print_warning(f"Could not stage {file_pattern}: {e}")
        
        # Check if anything was actually staged
        staged_output, _, _ = run_git_command(['diff', '--cached', '--name-only'])
        if not staged_output:
            print_warning("No files were staged. Nothing to commit.")
            return
        
        # Create the commit
        run_git_command(['commit', '-m', message])
        print_success(f"Saved changes: {message}")
        
        # Log the action to history
        history_manager.log_action(
            "save",
            {"message": message, "files": files},
            undo_command="git reset --soft HEAD~1",
            undo_details={"commit_message": message, "staged_files": files}
        )
        
    except GitError as e:
        print_error(f"Failed to save changes: {e}")
    except (HistoryError, ConfigError) as e:
        print_warning(f"Could not log to history: {e}")


def _show_git_status():
    """Show a formatted git status."""
    try:
        # Get detailed status
        status_output, _, _ = run_git_command(['status', '--porcelain'])
        
        staged = []
        modified = []
        untracked = []
        
        for line in status_output.split('\n'):
            if not line:
                continue
            
            status_code = line[:2]
            filename = line[3:]
            
            if status_code[0] in 'MADRC':
                staged.append(filename)
            elif status_code[1] in 'MD':
                modified.append(filename)
            elif status_code == '??':
                untracked.append(filename)
        
        # Display status summary
        status_info = {
            'branch': get_current_branch(),
            'staged': staged,
            'modified': modified,
            'untracked': untracked
        }
        
        display_status_summary(status_info)
        
    except GitError as e:
        print_warning(f"Could not get status: {e}")


def _select_files_to_stage():
    """Interactive file selection for staging."""
    try:
        status_output, _, _ = run_git_command(['status', '--porcelain'])
        
        files = []
        file_choices = []
        
        for line in status_output.split('\n'):
            if not line:
                continue
            
            status_code = line[:2]
            filename = line[3:]
            
            # Skip already staged files
            if status_code[0] not in ' ?':
                continue
            
            status_desc = {
                ' M': 'modified',
                ' D': 'deleted',
                '??': 'untracked',
                'MM': 'modified (partially staged)'
            }.get(status_code, 'changed')
            
            files.append(filename)
            file_choices.append((filename, f"{filename} ({status_desc})"))
        
        if not files:
            print_info("No unstaged files to select.")
            return []
        
        selected = select_multiple("Select files to stage:", file_choices)
        return selected
        
    except GitError as e:
        print_error(f"Failed to get file list: {e}")
        return []


@main.command('list')
@click.argument('list_type', required=False, 
                type=click.Choice(['branches', 'saves', 'remotes', 'accounts', 'stashes']))
def list_command(list_type: Optional[str]):
    """List repository components (branches, saves, remotes, accounts, stashes)."""
    try:
        if not list_type:
            # Show all lists
            _list_branches()
            _list_recent_saves()
            _list_accounts()
            return
        
        if list_type == 'branches':
            _list_branches()
        elif list_type == 'saves':
            _list_saves()
        elif list_type == 'remotes':
            _list_remotes()
        elif list_type == 'accounts':
            _list_accounts()
        elif list_type == 'stashes':
            _list_stashes()
            
    except (GitError, ConfigError) as e:
        print_error(f"Failed to list {list_type}: {e}")


def _list_branches():
    """List all branches."""
    if not is_git_repository():
        return
    
    try:
        output, _, _ = run_git_command(['branch', '-a'])
        branches = []
        current_branch = None
        
        for line in output.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('* '):
                current_branch = line[2:]
                branches.append(f"{SYMBOLS['success']} {current_branch} (current)")
            else:
                branch_name = line.replace('remotes/', '')
                branches.append(f"  {branch_name}")
        
        if branches:
            display_list(f"{SYMBOLS['clipboard']} Branches", branches, numbered=False)
        else:
            print_info("No branches found.")
            
    except GitError as e:
        print_warning(f"Could not list branches: {e}")


def _list_saves(limit: int = 10):
    """List recent saves (commits)."""
    if not is_git_repository():
        return
    
    try:
        output, _, _ = run_git_command([
            'log', f'-{limit}', '--pretty=format:%h|%an|%ar|%s'
        ])
        
        if not output:
            print_info("No commits found.")
            return
        
        headers = ["Hash", "Author", "When", "Message"]
        rows = []
        
        for line in output.split('\n'):
            if line:
                parts = line.split('|', 3)
                if len(parts) == 4:
                    rows.append(parts)
        
        if rows:
            display_table(f"{SYMBOLS['save']} Recent Saves", headers, rows)
        
    except GitError as e:
        print_warning(f"Could not list saves: {e}")


def _list_recent_saves():
    """List recent saves with limited output."""
    _list_saves(5)


def _list_remotes():
    """List remote repositories."""
    if not is_git_repository():
        return
    
    try:
        output, _, _ = run_git_command(['remote', '-v'])
        
        if not output:
            print_info("No remotes configured.")
            return
        
        remotes = []
        for line in output.split('\n'):
            if line:
                remotes.append(line)
        
        display_list(f"{SYMBOLS['remote']} Remotes", remotes, numbered=False)
        
    except GitError as e:
        print_warning(f"Could not list remotes: {e}")


def _list_accounts():
    """List configured accounts."""
    try:
        accounts = config_manager.get_accounts()
        current = config_manager.get_current_account()
        
        if not accounts:
            print_info("No accounts configured.")
            return
        
        account_list = []
        for alias, account in accounts.items():
            marker = SYMBOLS['success'] if alias == current else " "
            name = account.get('name', 'Unknown')
            email = account.get('email', 'No email')
            has_cred = SYMBOLS['key'] if config_manager.get_credential(alias) else SYMBOLS['lock']
            account_list.append(f"{marker} {alias}: {name} <{email}> {has_cred}")
        
        display_list(f"{SYMBOLS['user']} Accounts", account_list, numbered=False)
        
    except ConfigError as e:
        print_warning(f"Could not list accounts: {e}")


def _list_stashes():
    """List stashes."""
    if not is_git_repository():
        return
    
    try:
        output, _, _ = run_git_command(['stash', 'list'])
        
        if not output:
            print_info("No stashes found.")
            return
        
        stashes = output.split('\n')
        display_list(f"{SYMBOLS['stash']} Stashes", stashes, numbered=False)
        
    except GitError as e:
        print_warning(f"Could not list stashes: {e}")


@main.command()
@click.argument('target')
def switch(target: str):
    """Switch between branches, saves (commits), or accounts."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        # Determine what type of target this is
        target_type = _identify_switch_target(target)
        
        if target_type == 'branch':
            _switch_branch(target)
        elif target_type == 'commit':
            _switch_commit(target)
        elif target_type == 'account':
            _switch_account(target)
        else:
            print_error(f"Could not identify target '{target}'. "
                       "It should be a branch name, commit hash, or account alias.")
            
    except (GitError, ConfigError) as e:
        print_error(f"Failed to switch: {e}")


def _identify_switch_target(target: str) -> str:
    """Identify whether target is a branch, commit, or account."""
    # Check if it's a branch
    try:
        branches_output, _, _ = run_git_command(['branch', '-a'])
        for line in branches_output.split('\n'):
            branch_name = line.strip().lstrip('* ').replace('remotes/origin/', '')
            if branch_name == target:
                return 'branch'
    except GitError:
        pass
    
    # Check if it's an account
    accounts = config_manager.get_accounts()
    if target in accounts:
        return 'account'
    
    # Check if it looks like a commit hash
    if len(target) >= 4 and all(c in '0123456789abcdef' for c in target.lower()):
        return 'commit'
    
    return 'unknown'


def _switch_branch(branch_name: str):
    """Switch to a branch."""
    try:
        # Switch to the branch
        current_branch = get_current_branch()
        run_git_command(['switch', branch_name])
        print_success(f"Switched to branch '{branch_name}'")
        
        # Log the action
        history_manager.log_action(
            "switch",
            {"from_branch": current_branch, "to_branch": branch_name},
            undo_command=f"git switch {current_branch}" if current_branch else None
        )
        
    except GitError as e:
        print_error(f"Failed to switch branch: {e}")


def _switch_commit(commit_hash: str):
    """Switch to a specific commit (detached HEAD)."""
    try:
        current_branch = get_current_branch()
        run_git_command(['checkout', commit_hash])
        print_success(f"Switched to commit {commit_hash}")
        print_warning("You are now in 'detached HEAD' state. "
                     "Changes will not be saved to any branch unless you create a new branch.")
        
        # Log the action
        history_manager.log_action(
            "switch",
            {"from_branch": current_branch, "to_commit": commit_hash},
            undo_command=f"git switch {current_branch}" if current_branch else None
        )
        
    except GitError as e:
        print_error(f"Failed to switch to commit: {e}")


def _switch_account(account_alias: str):
    """Switch to a different account configuration."""
    try:
        config_manager.set_current_account(account_alias)
        account = config_manager.get_account(account_alias)
        print_success(f"Switched to account '{account_alias}' ({account['name']})")
        
        # Update git config for this repository
        if is_git_repository():
            run_git_command(['config', 'user.name', account['name']])
            run_git_command(['config', 'user.email', account['email']])
            print_info("Updated git user configuration for this repository")
        
    except (ConfigError, GitError) as e:
        print_error(f"Failed to switch account: {e}")


@main.command()
def status():
    """Show repository status."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        _show_git_status()
        
    except GitError as e:
        print_error(f"Failed to get status: {e}")


@main.command()
@click.option('--force', '-f', is_flag=True, help='Force push (dangerous)')
def push(force: bool):
    """Push changes to remote repository."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        current_branch = get_current_branch()
        if not current_branch:
            print_error("Cannot push from detached HEAD state.")
            return
        
        if force:
            if not require_confirmation("force push", current_branch, "extreme"):
                return
            
            run_git_command(['push', '--force'])
            print_success("Force pushed to remote (dangerous operation completed)")
        else:
            run_git_command(['push'])
            print_success("Pushed to remote")
        
        # Log the action
        history_manager.log_action(
            "push",
            {"branch": current_branch, "force": force},
            undo_command="git push --force" if force else None,
            undo_details={"dangerous": True} if force else None
        )
        
    except GitError as e:
        print_error(f"Failed to push: {e}")


@main.command()
@click.option('--rebase', is_flag=True, help='Use rebase instead of merge')
def pull(rebase: bool):
    """Pull changes from remote repository."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        current_branch = get_current_branch()
        if not current_branch:
            print_error("Cannot pull in detached HEAD state.")
            return
        
        # Pull with optional rebase
        if rebase:
            run_git_command(['pull', '--rebase'])
        else:
            run_git_command(['pull'])
        
        print_success("Pulled changes from remote")
        
        # Log the action
        history_manager.log_action(
            "pull",
            {"branch": current_branch, "rebase": rebase},
            undo_command="git reset --hard HEAD@{1}"
        )
        
    except GitError as e:
        print_error(f"Failed to pull: {e}")


@main.command()
@click.argument('message', required=False)
def stash(message: Optional[str]):
    """Manually stash uncommitted changes."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        if not has_uncommitted_changes():
            print_info("No changes to stash.")
            return
        
        if message:
            run_git_command(['stash', 'push', '-m', message])
        else:
            run_git_command(['stash', 'push'])
        
        print_success("Stashed uncommitted changes")
        
        # Log the action
        history_manager.log_action(
            "stash",
            {"message": message},
            undo_command="git stash pop"
        )
        
    except GitError as e:
        print_error(f"Failed to stash changes: {e}")


@main.command()
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode to select which action to undo')
def undo(interactive: bool):
    """Undo the last state-changing action or interactively select which action to undo."""
    try:
        if interactive:
            _interactive_undo()
        else:
            _single_undo()
            
    except (GitError, HistoryError) as e:
        print_error(f"Failed to undo: {e}")


def _interactive_undo():
    """Interactive undo that lets user select which action to undo."""
    try:
        # Get recent actions that can be undone
        actions = history_manager.get_history(20)  # Get more actions for selection
        
        if not actions:
            print_info("No actions to undo.")
            return
        
        # Filter actions that can be undone (have undo commands or are known types)
        undoable_actions = []
        for action in reversed(actions):  # Most recent first
            action_type = action['action_type']
            has_undo_command = action.get('undo_command') is not None
            
            # Actions we know how to undo
            known_undoable = action_type in ['save', 'merge', 'push', 'pull', 'stash', 'switch']
            
            if has_undo_command or known_undoable:
                undoable_actions.append(action)
        
        if not undoable_actions:
            print_info("No undoable actions found.")
            return
        
        # Format actions for selection with human-readable details
        from datetime import datetime
        choices = []
        
        for i, action in enumerate(undoable_actions):
            action_id = action['id']
            action_type = action['action_type']
            
            # Calculate relative time
            timestamp_str = action['timestamp'][:19].replace('T', ' ')
            try:
                action_time = datetime.fromisoformat(timestamp_str)
                now = datetime.now()
                diff = now - action_time
                total_seconds = diff.total_seconds()
                
                if diff.days > 7:
                    time_str = timestamp_str.split(' ')[0]
                elif diff.days > 0:
                    time_str = f"{diff.days}d ago"
                elif total_seconds > 3600:
                    hours = int(total_seconds // 3600)
                    time_str = f"{hours}h ago"
                elif total_seconds > 60:
                    minutes = int(total_seconds // 60)
                    time_str = f"{minutes}m ago"
                else:
                    time_str = "just now"
            except:
                time_str = timestamp_str
            
            # Format details
            details_dict = action.get('details', {})
            if action_type == 'save':
                message = details_dict.get('message', '')
                details = f'"{message}"'
            elif action_type == 'switch':
                from_branch = details_dict.get('from_branch', '')
                to_branch = details_dict.get('to_branch', '')
                to_commit = details_dict.get('to_commit', '')
                if to_commit:
                    details = f"{from_branch} → {to_commit[:8]}"
                else:
                    details = f"{from_branch} → {to_branch}"
            elif action_type == 'push':
                branch = details_dict.get('branch', '')
                force = details_dict.get('force', False)
                details = f"to {branch}" + (" (force)" if force else "")
            elif action_type == 'pull':
                branch = details_dict.get('branch', '')
                rebase = details_dict.get('rebase', False)
                details = f"from {branch}" + (" (rebase)" if rebase else "")
            elif action_type == 'stash':
                message = details_dict.get('message', '')
                details = f'"{message}"' if message else "untitled"
            else:
                details = str(details_dict)[:50]
            
            # Create choice display
            choice_text = f"{action_type.upper()}: {details} ({time_str})"
            choices.append((action, choice_text))
        
        if not choices:
            print_info("No undoable actions found.")
            return
        
        # Show selection menu with rewind explanation
        print_info("Select how far back to undo (arrow keys select all actions from top down to selection):")
        selected_action = select_from_list(
            "Choose undo point (will undo all actions from most recent down to this one):",
            [choice[1] for choice in choices]
        )
        
        if selected_action is None:
            print_info("Undo cancelled.")
            return
        
        # Find the selected action
        selected_index = next(i for i, (_, text) in enumerate(choices) if text == selected_action)
        
        # Actions to undo (from most recent down to selected one)
        actions_to_undo = undoable_actions[:selected_index + 1]
        
        # Show what will be undone
        print_info(f"This will undo {len(actions_to_undo)} action(s):")
        for i, action in enumerate(actions_to_undo):
            action_type = action['action_type']
            details_dict = action.get('details', {})
            if action_type == 'save':
                message = details_dict.get('message', '')
                details = f'"{message}"'
            elif action_type == 'switch':
                from_branch = details_dict.get('from_branch', '')
                to_branch = details_dict.get('to_branch', '')
                to_commit = details_dict.get('to_commit', '')
                if to_commit:
                    details = f"{from_branch} → {to_commit[:8]}"
                else:
                    details = f"{from_branch} → {to_branch}"
            elif action_type == 'push':
                branch = details_dict.get('branch', '')
                force = details_dict.get('force', False)
                details = f"to {branch}" + (" (force)" if force else "")
            else:
                details = str(details_dict)[:30]
            
            print_info(f"  {i+1}. {action_type.upper()}: {details}")
        
        # Confirm the undo
        if not confirm(f"Undo these {len(actions_to_undo)} actions?", default=True):
            print_info("Undo cancelled.")
            return
        
        # Perform the undos in reverse order (newest first, as they depend on each other)
        successful_undos = 0
        for action in actions_to_undo:
            try:
                _perform_undo(action)
                successful_undos += 1
            except Exception as e:
                print_warning(f"Failed to undo {action['action_type']}: {e}")
                break
        
        # Remove all successfully undone actions from history
        if successful_undos > 0:
            for action in actions_to_undo[:successful_undos]:
                history_manager.remove_action(action['id'])
            
            if successful_undos == len(actions_to_undo):
                print_success(f"Successfully undid {successful_undos} actions.")
            else:
                print_warning(f"Undid {successful_undos} of {len(actions_to_undo)} actions before encountering an error.")
        
    except Exception as e:
        print_error(f"Interactive undo failed: {e}")


def _single_undo():
    """Undo just the last action (original behavior)."""
    last_action = history_manager.get_last_action()
    if not last_action:
        print_info("No actions to undo.")
        return
    
    action_type = last_action['action_type']
    print_info(f"Last action: {action_type}")
    if not confirm(f"Undo this action?", default=True):
        return
    
    _perform_undo(last_action)
    
    # Remove the action from history
    history_manager.remove_last_action()


def _perform_undo(action):
    """Perform the actual undo operation for a given action."""
    action_type = action['action_type']
    details = action['details']
    undo_command = action.get('undo_command')
    undo_details = action.get('undo_details', {})
    
    # Handle different undo scenarios
    if action_type == 'save':
        run_git_command(['reset', '--soft', 'HEAD~1'])
        print_success("Undid last save (commit)")
    
    elif action_type == 'merge':
        run_git_command(['reset', '--hard', 'ORIG_HEAD'])
        print_success("Undid last merge")
    
    elif action_type == 'push':
        if undo_details.get('dangerous'):
            if not require_confirmation("undo push", details.get('branch', ''), "extreme"):
                return
        
        run_git_command(['push', '--force'])
        print_success("Undid push (forced remote update)")
    
    elif action_type == 'pull':
        run_git_command(['reset', '--hard', 'HEAD@{1}'])
        print_success("Undid last pull")
    
    elif action_type == 'stash':
        run_git_command(['stash', 'pop'])
        print_success("Undid stash (restored changes)")
    
    elif action_type == 'switch' and undo_command:
        # Extract branch name from undo command
        if 'git switch' in undo_command:
            branch = undo_command.split()[-1]
            run_git_command(['switch', branch])
            print_success(f"Switched back to {branch}")
    
    else:
        print_warning(f"Don't know how to undo action type: {action_type}")


@main.group()
def pr():
    """Manage pull requests."""
    pass


@pr.command('create')
@click.option('--title', '-t', help='Pull request title')
@click.option('--body', '-b', help='Pull request body')
@click.option('--base', default='main', help='Base branch for the pull request')
def pr_create(title: Optional[str], body: Optional[str], base: str):
    """Create a new pull request."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        current_branch = get_current_branch()
        if not current_branch or current_branch == base:
            print_error(f"Cannot create PR from {base} branch. Switch to a feature branch first.")
            return
        
        # Push current branch first
        print_info(f"Pushing branch '{current_branch}'...")
        run_git_command(['push', '-u', 'origin', current_branch])
        
        # Get repository info
        remote_url = run_git_command(['remote', 'get-url', 'origin'])[0]
        repo_info = GitHubClient.parse_repo_url(remote_url)
        if not repo_info:
            print_error("Could not parse repository URL. Only GitHub repositories are supported.")
            return
        
        repo_owner, repo_name = repo_info
        
        # Get credentials
        current_account = config_manager.get_current_account()
        token = config_manager.get_credential(current_account)
        if not token:
            token = prompt_password(f"Enter GitHub token for {current_account}: ")
            if token:
                config_manager.store_credential(current_account, token)
            else:
                print_error("No token provided.")
                return
        
        # Create GitHub client
        github = GitHubClient(token)
        
        # Get PR details interactively if not provided
        if not title:
            title = prompt_text("Pull request title: ")
        if not title:
            print_error("Title is required for pull request.")
            return
        
        if not body:
            body = prompt_text("Pull request body (optional): ")
        
        # Create the pull request
        print_info("Creating pull request...")
        pr_data = github.create_pull_request(
            repo_owner, repo_name, title, body or "", current_branch, base
        )
        
        print_success(f"Created pull request #{pr_data['number']}: {pr_data['html_url']}")
        
    except (GitError, IntegrationError, ConfigError) as e:
        print_error(f"Failed to create pull request: {e}")


@pr.command('list')
@click.option('--state', default='open', type=click.Choice(['open', 'closed', 'all']))
def pr_list(state: str):
    """List pull requests."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        # Get repository info
        remote_url = run_git_command(['remote', 'get-url', 'origin'])[0]
        repo_info = GitHubClient.parse_repo_url(remote_url)
        if not repo_info:
            print_error("Could not parse repository URL.")
            return
        
        repo_owner, repo_name = repo_info
        
        # Get credentials
        current_account = config_manager.get_current_account()
        token = config_manager.get_credential(current_account)
        if not token:
            print_error("No stored credentials. Run 'bit pr create' first or configure token.")
            return
        
        # Create GitHub client and list PRs
        github = GitHubClient(token)
        prs = github.list_pull_requests(repo_owner, repo_name, state)
        
        if not prs:
            print_info(f"No {state} pull requests found.")
            return
        
        headers = ["#", "Title", "Author", "Status"]
        rows = []
        
        for pr in prs:
            number = str(pr['number'])
            title = pr['title'][:50]
            author = pr['user']['login']
            status = pr['state']
            
            rows.append([number, title, author, status])
        
        display_table(f"Pull Requests ({state})", headers, rows)
        
    except (GitError, IntegrationError) as e:
        print_error(f"Failed to list pull requests: {e}")


@pr.command('checkout')
@click.argument('pr_number', type=int)
def pr_checkout(pr_number: int):
    """Checkout the branch for a specific pull request."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        # Get repository info
        remote_url = run_git_command(['remote', 'get-url', 'origin'])[0]
        repo_info = GitHubClient.parse_repo_url(remote_url)
        if not repo_info:
            print_error("Could not parse repository URL.")
            return
        
        repo_owner, repo_name = repo_info
        
        # Get credentials
        current_account = config_manager.get_current_account()
        token = config_manager.get_credential(current_account)
        if not token:
            print_error("No stored credentials.")
            return
        
        # Get PR details
        github = GitHubClient(token)
        pr_data = github.get_pull_request(repo_owner, repo_name, pr_number)
        
        branch_name = pr_data['head']['ref']
        print_info(f"Checking out PR #{pr_number}: {pr_data['title']}")
        
        # Fetch and checkout the branch
        run_git_command(['fetch', 'origin', f'{branch_name}:{branch_name}'])
        run_git_command(['switch', branch_name])
        
        print_success(f"Checked out branch '{branch_name}' for PR #{pr_number}")
        
    except (GitError, IntegrationError) as e:
        print_error(f"Failed to checkout pull request: {e}")


@main.command()
@click.argument('issue_id', type=int)
def workon(issue_id: int):
    """Start working on a specific issue."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        # Get repository info
        remote_url = run_git_command(['remote', 'get-url', 'origin'])[0]
        repo_info = GitHubClient.parse_repo_url(remote_url)
        if not repo_info:
            print_error("Could not parse repository URL.")
            return
        
        repo_owner, repo_name = repo_info
        
        # Get credentials
        current_account = config_manager.get_current_account()
        token = config_manager.get_credential(current_account)
        if not token:
            token = prompt_password(f"Enter GitHub token for {current_account}: ")
            if token:
                config_manager.store_credential(current_account, token)
            else:
                print_error("No token provided.")
                return
        
        # Get issue details and create branch
        github = GitHubClient(token)
        
        print_info(f"Fetching issue #{issue_id}...")
        issue = github.get_issue(repo_owner, repo_name, issue_id)
        
        print_info(f"Issue: {issue['title']}")
        
        # Create branch name from issue
        branch_name = github.create_branch_from_issue(repo_owner, repo_name, issue_id)
        
        print_info(f"Creating and switching to branch: {branch_name}")
        
        # Create and switch to the new branch
        run_git_command(['switch', '-c', branch_name])
        
        print_success(f"Started working on issue #{issue_id}")
        print_info(f"Branch: {branch_name}")
        print_info(f"Issue: {issue['title']}")
        
    except (GitError, IntegrationError, ConfigError) as e:
        print_error(f"Failed to start working on issue: {e}")


@main.command()
def sync():
    """Synchronize local and remote repository state."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        current_branch = get_current_branch()
        if not current_branch:
            print_error("Cannot sync in detached HEAD state.")
            return
        
        print_info("Starting sync operation...")
        
        # Step 1: Pull with rebase
        print_info("Pulling latest changes...")
        try:
            run_git_command(['pull', '--rebase'])
        except GitError as e:
            print_error(f"Pull failed: {e}")
            return
        
        # Step 2: Push changes
        print_info("Pushing changes...")
        try:
            run_git_command(['push'])
        except GitError as e:
            print_warning(f"Push failed: {e}")
            print_info("This is normal if you have no local commits to push.")
        
        print_success("Sync completed successfully!")
        
        # Log the action
        history_manager.log_action(
            "sync",
            {"branch": current_branch},
            undo_command="git reset --hard HEAD@{1}"
        )
        
    except GitError as e:
        print_error(f"Sync failed: {e}")


@main.command()
@click.option('--all', '-a', is_flag=True, help='Show all branches including remotes')
def graph(all: bool):
    """Display a text-based graph of branch and merge history."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        # Build git log command
        cmd = ['log', '--graph', '--pretty=format:%h|%an|%ar|%s', '--abbrev-commit']
        if all:
            cmd.append('--all')
        else:
            cmd.extend(['-10'])  # Limit to 10 commits for readability
        
        output, _, _ = run_git_command(cmd)
        
        if not output:
            print_info("No commits found.")
            return
        
        print(f"\n{SYMBOLS['graph']} Repository Graph:")
        print("=" * 60)
        
        for line in output.split('\n'):
            if '|' in line:
                # Split the graph part from the commit info
                graph_part = line.split('|')[0] if line.count('|') >= 4 else line
                commit_info = '|'.join(line.split('|')[1:]) if line.count('|') >= 4 else ''
                
                if commit_info:
                    parts = commit_info.split('|')
                    if len(parts) >= 3:
                        hash_part, author, time_ago = parts[0], parts[1], parts[2]
                        message = '|'.join(parts[3:]) if len(parts) > 3 else ''
                        
                        print(f"{graph_part}[yellow]{hash_part}[/yellow] "
                              f"[green]{author}[/green] [dim]{time_ago}[/dim] {message}")
                    else:
                        print(line)
                else:
                    print(line)
            else:
                print(line)
        
        print("=" * 60)
        
    except GitError as e:
        print_error(f"Failed to show graph: {e}")


@main.command()
@click.option('--limit', '-n', default=10, help='Number of recent actions to show')
def history(limit: int):
    """Show history of state-changing actions."""
    try:
        actions = history_manager.get_history(limit)
        
        if not actions:
            print_info("No actions in history.")
            return
        
        # Use the same formatting as interactive undo
        from datetime import datetime
        
        print(f"\n{SYMBOLS['clipboard']} Action History:")
        print("=" * 80)
        
        # Get recent actions (most recent first, like undo)
        recent_actions = list(reversed(actions))[:limit]
        
        for i, action in enumerate(recent_actions):
            action_type = action['action_type']
            
            # Calculate relative time (same logic as interactive undo)
            timestamp_str = action['timestamp'][:19].replace('T', ' ')
            try:
                action_time = datetime.fromisoformat(timestamp_str)
                now = datetime.now()
                diff = now - action_time
                total_seconds = diff.total_seconds()
                
                if diff.days > 7:
                    time_str = timestamp_str.split(' ')[0]
                elif diff.days > 0:
                    time_str = f"{diff.days}d ago"
                elif total_seconds > 3600:
                    hours = int(total_seconds // 3600)
                    time_str = f"{hours}h ago"
                elif total_seconds > 60:
                    minutes = int(total_seconds // 60)
                    time_str = f"{minutes}m ago"
                else:
                    time_str = "just now"
            except:
                time_str = timestamp_str
            
            # Format details (same logic as interactive undo)
            details_dict = action.get('details', {})
            if action_type == 'save':
                message = details_dict.get('message', '')
                details = f'"{message}"'
            elif action_type == 'switch':
                from_branch = details_dict.get('from_branch', '')
                to_branch = details_dict.get('to_branch', '')
                to_commit = details_dict.get('to_commit', '')
                if to_commit:
                    details = f"{from_branch} → {to_commit[:8]}"
                else:
                    details = f"{from_branch} → {to_branch}"
            elif action_type == 'push':
                branch = details_dict.get('branch', '')
                force = details_dict.get('force', False)
                details = f"to {branch}" + (" (force)" if force else "")
            elif action_type == 'pull':
                branch = details_dict.get('branch', '')
                rebase = details_dict.get('rebase', False)
                details = f"from {branch}" + (" (rebase)" if rebase else "")
            elif action_type == 'stash':
                message = details_dict.get('message', '')
                details = f'"{message}"' if message else "untitled"
            elif action_type == 'init':
                project_name = details_dict.get('project_name', '')
                details = f"project: {project_name}"
            else:
                details = str(details_dict)[:50]
            
            # Display in the same format as interactive undo
            choice_text = f"{action_type.upper()}: {details} ({time_str})"
            print(f"  {i+1:2d}. {choice_text}")
        
        print("=" * 80)
        
    except HistoryError as e:
        print_error(f"Failed to get history: {e}")


@main.command()
@click.option('--dry-run', is_flag=True, help='Show what would be cleaned without doing it')
def cleanup(dry_run: bool):
    """Perform repository housekeeping tasks."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        if dry_run:
            print_info("Dry run mode - showing what would be cleaned:")
        else:
            print_info("Starting repository cleanup...")
        
        tasks = []
        
        # Check for merged branches that can be deleted
        try:
            merged_output, _, _ = run_git_command(['branch', '--merged'])
            merged_branches = []
            for line in merged_output.split('\n'):
                branch = line.strip().lstrip('* ')
                if branch and branch not in ['main', 'master', 'develop']:
                    merged_branches.append(branch)
            
            if merged_branches:
                tasks.append(("Delete merged branches", merged_branches))
        except GitError:
            pass
        
        # Check for stale remote branches
        try:
            run_git_command(['remote', 'prune', 'origin', '--dry-run'])
            tasks.append(("Prune stale remote branches", ["git remote prune origin"]))
        except GitError:
            pass
        
        # Git garbage collection
        tasks.append(("Run garbage collection", ["git gc"]))
        
        if not tasks:
            print_info("Nothing to clean up.")
            return
        
        if dry_run:
            for task_name, items in tasks:
                print(f"\n{task_name}:")
                for item in items:
                    print(f"  - {item}")
            return
        
        # Execute cleanup tasks
        for task_name, items in tasks:
            if task_name == "Delete merged branches":
                if confirm(f"Delete {len(items)} merged branches?"):
                    for branch in items:
                        run_git_command(['branch', '-d', branch])
                        print(f"  Deleted branch: {branch}")
            
            elif task_name == "Prune stale remote branches":
                run_git_command(['remote', 'prune', 'origin'])
                print("  Pruned stale remote branches")
            
            elif task_name == "Run garbage collection":
                run_git_command(['gc'])
                print("  Ran garbage collection")
        
        print_success("Cleanup completed!")
        
    except GitError as e:
        print_error(f"Cleanup failed: {e}")


@main.command()
def config():
    """Open the BetterGit configuration file for editing."""
    try:
        config_file_path = config_manager.config_file
        
        # Ensure config file exists
        if not config_file_path.exists():
            print_info("Configuration file doesn't exist. Creating default configuration...")
            config_manager._ensure_config_exists()
        
        print_info(f"Opening configuration file: {config_file_path}")
        
        # Try to open with the system's default editor
        import subprocess
        import platform
        
        system = platform.system()
        if system == "Windows":
            # On Windows, use the default associated program
            os.startfile(str(config_file_path))
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(config_file_path)])
        else:  # Linux and other Unix-like systems
            # Try common editors in order of preference
            editors = [
                os.environ.get("EDITOR"),  # User's preferred editor
                "code",      # VS Code
                "nano",      # Nano (usually available)
                "vim",       # Vim
                "gedit",     # GNOME Text Editor
                "kate",      # KDE Text Editor
                "xdg-open"   # Default application
            ]
            
            for editor in editors:
                if editor and subprocess.run(["which", editor], capture_output=True).returncode == 0:
                    subprocess.run([editor, str(config_file_path)])
                    break
            else:
                print_warning("Could not find a suitable text editor. Please edit the file manually:")
                print(f"  {config_file_path}")
                return
        
        print_success(f"Configuration file opened! Make your changes and save the file.")
        print_info("The configuration will be automatically reloaded when you run the next bit command.")
        
    except Exception as e:
        print_error(f"Failed to open configuration file: {e}")
        print_info(f"You can manually edit the configuration file at: {config_manager.config_file}")


if __name__ == '__main__':
    main()
