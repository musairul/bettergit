"""Command-line interface for BetterGit."""

import click
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

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
        
        # Check if SSH keys are available and preferred
        use_ssh = _check_ssh_key_availability()
        
        # Get or prompt for token (still needed for API calls to create repo)
        token = config_manager.get_credential(current_account)
        if not token:
            print_info(f"No stored credential found for account '{current_account}'")
            print_info("GitHub token is needed to create the remote repository via API")
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

        # Create the repository
        print_info(f"Creating {'private' if is_private else 'public'} remote repository '{repo_name}'...")
        repo_data = github.create_repository(repo_name, description, is_private)
        
        # Choose the appropriate clone URL based on SSH availability
        if use_ssh:
            # Use SSH URL format: git@github.com:username/repo.git
            clone_url = repo_data.get('ssh_url') or f"git@github.com:{repo_data['full_name']}.git"
            print_info("Using SSH for repository connection")
        else:
            # Use HTTPS URL
            clone_url = repo_data['clone_url']
            print_info("Using HTTPS for repository connection")
        
        # Add remote and push
        run_git_command(['remote', 'add', 'origin', clone_url])
        
        # Create initial commit if repository is empty
        try:
            # Check if there are any commits at all
            run_git_command(['rev-parse', 'HEAD'])
            has_commits = True
        except GitError:
            # No commits exist yet
            has_commits = False
        
        if not has_commits:
            # Repository is empty, create initial commit
            # First check if there are any files to commit
            try:
                status_output, _, _ = run_git_command(['status', '--porcelain'])
                if status_output.strip():
                    # There are files to commit
                    run_git_command(['add', '.'])
                    run_git_command(['commit', '-m', 'Initial commit'])
                    print_info("Created initial commit")
                else:
                    # No files to commit, create a basic README
                    readme_path = Path("README.md")
                    if not readme_path.exists():
                        project_title = Path.cwd().name
                        readme_content = f"# {project_title}\n\nA new project created with BetterGit.\n"
                        readme_path.write_text(readme_content, encoding='utf-8')
                    
                    run_git_command(['add', '.'])
                    run_git_command(['commit', '-m', 'Initial commit'])
                    print_info("Created initial commit with README.md")
            except GitError as e:
                print_error(f"Failed to create initial commit: {e}")
                return
        
        # Push to remote
        main_branch = defaults.get('main_branch_name', 'main')
        run_git_command(['branch', '-M', main_branch])
        run_git_command(['push', '-u', 'origin', main_branch])
        
        print_success(f"Created remote repository: {repo_data['html_url']}")
        if use_ssh:
            print_info("🔑 Repository configured to use SSH keys for authentication")
        
    except IntegrationError as e:
        print_error(f"Failed to create remote repository: {e}")
    except GitError as e:
        print_error(f"Git operation failed: {e}")


def _check_ssh_key_availability() -> bool:
    """Check if SSH keys are available and can be used for GitHub."""
    try:
        import os
        import subprocess
        from pathlib import Path
        
        # Check for common SSH key locations
        ssh_dir = Path.home() / '.ssh'
        if not ssh_dir.exists():
            return False
        
        # Look for common SSH key files
        key_files = [
            'id_rsa', 'id_ed25519', 'id_ecdsa', 'id_dsa',
            'github_rsa', 'github_ed25519'
        ]
        
        found_keys = []
        for key_file in key_files:
            key_path = ssh_dir / key_file
            if key_path.exists():
                found_keys.append(key_path)
        
        if not found_keys:
            return False
        
        # Simple check - if keys exist, assume they work
        # The SSH test was causing hangs, so we'll be optimistic
        # Git operations will fail gracefully if SSH doesn't work
        return True
        
    except Exception as e:
        # If anything fails, fall back to HTTPS
        logger.debug(f"SSH key check failed: {e}")
        return False


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
                type=click.Choice(['branches', 'saves', 'remotes', 'accounts', 'stashes', 'history']))
@click.option('--limit', '-n', default=10, help='Number of recent actions to show (for history only)')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed timestamps (for history only)')
def list_command(list_type: Optional[str], limit: int, detailed: bool):
    """List repository components (branches, saves, remotes, accounts, stashes)."""
    try:
        if not list_type:
            # Show interactive menu to choose what to list
            _interactive_list_menu(limit, detailed)
            return
        
        if list_type == 'branches':
            _list_branches()
        elif list_type == 'saves':
            _list_saves(limit)
        elif list_type == 'remotes':
            _list_remotes()
        elif list_type == 'accounts':
            _list_accounts()
        elif list_type == 'stashes':
            _list_stashes()
        elif list_type == 'history':
            _list_history(limit, detailed)
            
    except (GitError, ConfigError) as e:
        print_error(f"Failed to list {list_type}: {e}")


def _interactive_list_menu(limit: int, detailed: bool):
    """Show interactive menu to choose what to list."""
    menu_options = [
        ("branches", "📁 Branches - Show all local and remote branches"),
        ("saves", "💾 Saves - Show recent commits/saves"),
        ("remotes", "🌐 Remotes - Show configured remote repositories"),
        ("accounts", "👤 Accounts - Show configured user accounts"),
        ("stashes", "📦 Stashes - Show stashed changes"),
        ("history", "📋 History - Show action history")
    ]
    
    choice_texts = [option[1] for option in menu_options]
    
    print_info("What would you like to list?")
    selected = select_from_list("Choose an option:", choice_texts)
    
    if selected is None:
        print_info("List cancelled.")
        return
    
    # Find the selected option
    selected_key = None
    for key, text in menu_options:
        if text == selected:
            selected_key = key
            break
    
    if not selected_key:
        print_error("Invalid selection.")
        return
    
    # Execute the selected list function
    if selected_key == 'branches':
        _list_branches()
    elif selected_key == 'saves':
        _list_saves(limit)
    elif selected_key == 'remotes':
        _list_remotes()
    elif selected_key == 'accounts':
        _list_accounts()
    elif selected_key == 'stashes':
        _list_stashes()
    elif selected_key == 'history':
        _list_history(limit, detailed)


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
        # Get commits with ISO timestamp for better time calculation
        output, _, _ = run_git_command([
            'log', f'-{limit}', '--pretty=format:%h|%an|%ai|%s'
        ])
        
        if not output:
            print_info("No commits found.")
            return
        
        # Use the same formatting as interactive undo
        from datetime import datetime
        
        print(f"\n{SYMBOLS['save']} Recent Saves:")
        print("=" * 80)
        
        for i, line in enumerate(output.split('\n')):
            if line:
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commit_hash, author, timestamp_str, message = parts
                    
                    # Calculate relative time (same logic as interactive undo)
                    try:
                        # Parse ISO timestamp, handle timezone offset
                        timestamp_clean = timestamp_str.split(' +')[0].split(' -')[0]  # Remove timezone
                        action_time = datetime.fromisoformat(timestamp_clean.replace(' ', 'T'))
                        now = datetime.now()
                        diff = now - action_time
                        total_seconds = diff.total_seconds()
                        
                        if diff.days > 7:
                            time_str = timestamp_clean.split('T')[0]
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
                        time_str = timestamp_str.split(' ')[0]
                    
                    # Display in the same format as interactive undo
                    choice_text = f"{commit_hash}: \"{message}\" by {author} ({time_str})"
                    print(f"  {i+1:2d}. {choice_text}")
                    # print(f"      {commit_hash} by {author}")
        
        print("=" * 80)
        
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


def _list_history(limit: int, detailed: bool):
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
            
            # Display in the same format as interactive undo, with optional timestamp
            choice_text = f"{action_type.upper()}: {details} ({time_str})"
            print(f"  {i+1:2d}. {choice_text}")
            
            # Only show timestamp if detailed flag is set
            if detailed:
                timestamp_display = timestamp_str.replace(' ', ' at ')  # Format: 2025-07-24 at 12:45:32
                print(f"      {timestamp_display}")
        
        print("=" * 80)
        
    except HistoryError as e:
        print_error(f"Failed to get history: {e}")


@main.command()
@click.argument('target')
@click.option('--create', '-c', is_flag=True, help='Create the branch if it does not exist')
def switch(target: str, create: bool):
    """Switch between branches, saves (commits), or accounts.
    
    If switching to a branch that doesn't exist, you will be prompted to create it,
    or use -c/--create to create it automatically.
    """
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        # Determine what type of target this is
        target_type = _identify_switch_target(target)
        
        if target_type == 'branch':
            _switch_branch(target, create)
        elif target_type == 'commit':
            _switch_commit(target)
        elif target_type == 'account':
            _switch_account(target)
        elif target_type == 'unknown':
            # Could be a new branch name
            if create or confirm(f"Branch '{target}' does not exist. Create it?", default=True):
                _create_and_switch_branch(target)
            else:
                print_info("Switch cancelled.")
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


def _switch_branch(branch_name: str, create: bool = False):
    """Switch to a branch, optionally creating it if it doesn't exist."""
    try:
        current_branch = get_current_branch()
        
        # Try to switch to the branch first
        try:
            run_git_command(['switch', branch_name])
            print_success(f"Switched to branch '{branch_name}'")
            
            # Log the action
            history_manager.log_action(
                "switch",
                {"from_branch": current_branch, "to_branch": branch_name},
                undo_command=f"git switch {current_branch}" if current_branch else None
            )
            
        except GitError as e:
            # If switch failed, it might be because the branch doesn't exist
            if "did not match any file(s) known to git" in str(e).lower() or "pathspec" in str(e).lower():
                if create or confirm(f"Branch '{branch_name}' does not exist. Create it?", default=True):
                    _create_and_switch_branch(branch_name)
                else:
                    print_info("Switch cancelled.")
            else:
                # Re-raise if it's a different error
                raise e
        
    except GitError as e:
        print_error(f"Failed to switch branch: {e}")


def _create_and_switch_branch(branch_name: str):
    """Create a new branch and switch to it."""
    try:
        current_branch = get_current_branch()
        
        # Create and switch to the new branch
        run_git_command(['switch', '-c', branch_name])
        print_success(f"Created and switched to new branch '{branch_name}'")
        
        # Log the action
        history_manager.log_action(
            "create_branch",
            {"from_branch": current_branch, "new_branch": branch_name},
            undo_command=f"git switch {current_branch} && git branch -d {branch_name}" if current_branch else f"git branch -d {branch_name}"
        )
        
    except GitError as e:
        print_error(f"Failed to create branch: {e}")


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
@click.argument('target', required=False)
def undo(interactive: bool, target: Optional[str]):
    """Undo the last state-changing action, or undo a specific commit/branch.
    
    Usage:
      bit undo                    # Undo last action
      bit undo -i                 # Interactive undo menu
      bit undo <commit_hash>      # Delete/undo specific commit
      bit undo <branch_name>      # Delete specific branch
    """
    try:
        if target:
            _targeted_undo(target)
        elif interactive:
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


def _targeted_undo(target: str):
    """Undo a specific commit or delete a specific branch."""
    try:
        if not is_git_repository():
            print_error("Not in a Git repository.")
            return
        
        # Determine what type of target this is
        target_type = _identify_undo_target(target)
        
        if target_type == 'commit':
            _undo_specific_commit(target)
        elif target_type == 'branch':
            _delete_branch(target)
        else:
            print_error(f"Could not identify target '{target}'. "
                       "It should be a commit hash or branch name.")
            
    except GitError as e:
        print_error(f"Failed to undo target '{target}': {e}")


def _identify_undo_target(target: str) -> str:
    """Identify whether target is a commit hash or branch name."""
    # Check if it's a branch (local or remote)
    try:
        branches_output, _, _ = run_git_command(['branch', '-a'])
        for line in branches_output.split('\n'):
            line = line.strip().lstrip('* ')
            # Check both local and remote branch names
            if line == target or line == f"remotes/origin/{target}":
                return 'branch'
            # Also check without the remotes/origin/ prefix
            if line.startswith('remotes/origin/') and line[15:] == target:
                return 'branch'
    except GitError:
        pass
    
    # Check if it looks like a commit hash (4+ hex characters)
    if len(target) >= 4 and all(c in '0123456789abcdef' for c in target.lower()):
        # Verify it's actually a valid commit
        try:
            run_git_command(['rev-parse', target])
            return 'commit'
        except GitError:
            pass
    
    return 'unknown'


def _undo_specific_commit(commit_hash: str):
    """Delete/undo a specific commit."""
    try:
        # First, let's see if this commit exists and get its details
        try:
            commit_info, _, _ = run_git_command(['log', '-1', '--pretty=format:%h|%s|%an', commit_hash])
            hash_part, message, author = commit_info.split('|', 2)
        except GitError:
            print_error(f"Commit '{commit_hash}' not found.")
            return
        
        print_info(f"Target commit: {hash_part} \"{message}\" by {author}")
        
        # Check if this is the HEAD commit (most recent)
        try:
            head_hash, _, _ = run_git_command(['rev-parse', 'HEAD'])
            head_short, _, _ = run_git_command(['rev-parse', '--short', 'HEAD'])
            
            # Check if the provided hash matches HEAD (either full or abbreviated)
            if (head_hash.lower().startswith(commit_hash.lower()) or 
                head_short.lower().startswith(commit_hash.lower()) or
                commit_hash.lower() == head_hash.lower() or 
                commit_hash.lower() == head_short.lower()):
                # This is the HEAD commit, use reset --soft like normal undo
                if not confirm(f"This will undo the most recent commit. Continue?", default=True):
                    return
                
                run_git_command(['reset', '--soft', 'HEAD~1'])
                print_success(f"Undid commit {hash_part} (changes moved to staging)")
                return
        except GitError:
            pass
        
        # For non-HEAD commits, we need to use revert or interactive rebase
        print_warning("This commit is not the most recent commit.")
        print_info("Choose how to handle this:")
        
        options = [
            "Create a revert commit (safer, keeps history)",
            "Remove from history with interactive rebase (dangerous, rewrites history)"
        ]
        
        selected = select_from_list("How do you want to undo this commit?", options)
        
        if selected is None:
            print_info("Undo cancelled.")
            return
        
        if "revert" in selected:
            # Create a revert commit
            if not confirm(f"Create a revert commit for {hash_part}?", default=True):
                return
            
            run_git_command(['revert', '--no-edit', commit_hash])
            print_success(f"Created revert commit for {hash_part}")
            
            # Log this action for potential undo
            history_manager.log_action(
                "revert",
                {"commit": commit_hash, "message": message},
                undo_command=f"git reset --hard HEAD~1"
            )
            
        else:
            # Interactive rebase to remove the commit
            print_warning("This will rewrite git history and may cause issues for collaborators!")
            if not require_confirmation("rewrite history", f"remove commit {hash_part}", "extreme"):
                return
            
            # Find the parent of the commit to rebase from
            try:
                parent_hash, _, _ = run_git_command(['rev-parse', f'{commit_hash}^'])
                run_git_command(['rebase', '--interactive', parent_hash])
                print_success(f"Started interactive rebase to remove commit {hash_part}")
                print_info("Complete the rebase by removing the target commit line and saving.")
            except GitError as e:
                print_error(f"Failed to start interactive rebase: {e}")
        
    except GitError as e:
        print_error(f"Failed to undo commit: {e}")


def _delete_branch(branch_name: str):
    """Delete a specific branch."""
    try:
        current_branch = get_current_branch()
        
        # Prevent deleting the current branch
        if branch_name == current_branch:
            print_error(f"Cannot delete the current branch '{branch_name}'. Switch to another branch first.")
            return
        
        # Prevent deleting main/master branches
        if branch_name in ['main', 'master', 'develop']:
            print_warning(f"Attempting to delete protected branch '{branch_name}'!")
            if not require_confirmation("delete protected branch", branch_name, "extreme"):
                return
        
        # Check if it's a local branch
        try:
            branches_output, _, _ = run_git_command(['branch'])
            local_branches = [line.strip().lstrip('* ') for line in branches_output.split('\n') if line.strip()]
            
            if branch_name in local_branches:
                # Check if branch has unmerged changes
                try:
                    run_git_command(['branch', '-d', branch_name])  # Try safe delete first
                    print_success(f"Deleted local branch '{branch_name}'")
                except GitError:
                    # Branch has unmerged changes
                    print_warning(f"Branch '{branch_name}' has unmerged changes!")
                    if confirm(f"Force delete branch '{branch_name}' and lose unmerged changes?", default=False):
                        run_git_command(['branch', '-D', branch_name])
                        print_success(f"Force deleted local branch '{branch_name}'")
                    else:
                        print_info("Branch deletion cancelled.")
                        return
                
                # Log the action
                history_manager.log_action(
                    "delete_branch",
                    {"branch": branch_name, "type": "local"},
                    undo_command=f"git switch -c {branch_name}"
                )
                
            else:
                print_error(f"Local branch '{branch_name}' not found.")
                return
        except GitError as e:
            print_error(f"Failed to delete branch: {e}")
        
        # Ask if they also want to delete the remote branch
        try:
            remote_branches_output, _, _ = run_git_command(['branch', '-r'])
            remote_branches = [line.strip().replace('origin/', '') for line in remote_branches_output.split('\n') 
                             if line.strip() and 'origin/' in line]
            
            if branch_name in remote_branches:
                if confirm(f"Also delete remote branch 'origin/{branch_name}'?", default=False):
                    run_git_command(['push', 'origin', '--delete', branch_name])
                    print_success(f"Deleted remote branch 'origin/{branch_name}'")
                    
                    # Log the remote deletion
                    history_manager.log_action(
                        "delete_branch",
                        {"branch": branch_name, "type": "remote"},
                        undo_command=f"git push origin {branch_name}"
                    )
        except GitError:
            # Remote branch doesn't exist or other error, that's ok
            pass
        
    except GitError as e:
        print_error(f"Failed to delete branch: {e}")


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
@click.argument('repository_url', required=False)
def clone(repository_url: Optional[str]):
    """Clone a repository with interactive selection if no URL provided."""
    try:
        if repository_url:
            # Direct clone with provided URL
            _perform_clone(repository_url)
        else:
            # Interactive clone selection
            _interactive_clone()
            
    except (GitError, IntegrationError, ConfigError) as e:
        print_error(f"Failed to clone repository: {e}")


def _interactive_clone():
    """Show interactive menu to select a repository to clone."""
    try:
        # Check clipboard for git URLs
        clipboard_url = _get_clipboard_git_url()
        
        # Get list of user's repositories
        repo_list = _get_user_repositories()
        
        # Build choices list
        choices = []
        
        # Add clipboard URL at the top if it's a valid git URL
        if clipboard_url:
            choices.append((clipboard_url, f"📋 From clipboard: {clipboard_url}"))
        
        # Add user repositories
        for repo in repo_list:
            repo_name = repo.get('name', 'Unknown')
            description = repo.get('description', 'No description')
            
            # Prefer SSH URL if available, fall back to HTTPS
            ssh_url = repo.get('ssh_url', '')
            https_url = repo.get('clone_url', '')
            
            # Choose URL based on SSH key availability
            if _check_ssh_key_availability() and ssh_url:
                clone_url = ssh_url
            else:
                clone_url = https_url
                
            visibility = "🔒 Private" if repo.get('private', False) else "🌐 Public"
            
            display_text = f"{visibility} {repo_name} - {description[:50]}"
            choices.append((clone_url, display_text))
        
        if not choices:
            print_error("No repositories found and no valid git URL in clipboard.")
            return
        
        # Show selection menu
        print_info("Select a repository to clone:")
        selected = select_from_list("Choose repository:", [choice[1] for choice in choices])
        
        if selected is None:
            print_info("Clone cancelled.")
            return
        
        # Find the selected repository URL
        selected_url = None
        for url, text in choices:
            if text == selected:
                selected_url = url
                break
        
        if not selected_url:
            print_error("Could not find repository URL.")
            return
        
        # Perform the clone
        _perform_clone(selected_url)
        
    except Exception as e:
        print_error(f"Interactive clone failed: {e}")


def _get_clipboard_git_url() -> Optional[str]:
    """Check clipboard for a valid git repository URL."""
    try:
        import subprocess
        import platform
        import re
        
        system = platform.system()
        
        # Get clipboard content based on OS
        if system == "Windows":
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                # Clean up Windows line endings
                data = data.strip().replace('\r\n', '').replace('\n', '')
            except ImportError:
                # Fallback to powershell if pywin32 not available
                result = subprocess.run(
                    ["powershell", "-command", "Get-Clipboard"],
                    capture_output=True, text=True
                )
                data = result.stdout.strip() if result.returncode == 0 else ""
        elif system == "Darwin":  # macOS
            result = subprocess.run(["pbpaste"], capture_output=True, text=True)
            data = result.stdout.strip() if result.returncode == 0 else ""
        else:  # Linux/Unix
            result = subprocess.run(["xclip", "-selection", "clipboard", "-o"], 
                                  capture_output=True, text=True)
            data = result.stdout.strip() if result.returncode == 0 else ""
        
        # Check if the clipboard content looks like a git URL
        if data:
            # Patterns for git URLs (more flexible)
            git_patterns = [
                r'^https://github\.com/[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+(?:\.git)?/?$',
                r'^git@github\.com:[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+(?:\.git)?$',
                r'^https://gitlab\.com/[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+(?:\.git)?/?$',
                r'^git@gitlab\.com:[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+(?:\.git)?$',
                r'^https://bitbucket\.org/[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+(?:\.git)?/?$',
                r'^git@bitbucket\.org:[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+(?:\.git)?$',
                # Generic git URL patterns
                r'^https://[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+(?:\.git)?/?$',
                r'^git@[a-zA-Z0-9\-_.]+:[a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+(?:\.git)?$'
            ]
            
            for pattern in git_patterns:
                if re.match(pattern, data):
                    return data
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get clipboard content: {e}")
        return None


def _get_user_repositories() -> List[Dict[str, Any]]:
    """Get list of user's repositories from GitHub."""
    try:
        # Get current account configuration
        current_account = config_manager.get_current_account()
        
        # Get token
        token = config_manager.get_credential(current_account)
        if not token:
            print_warning("No stored GitHub token found. Only clipboard option will be available.")
            return []
        
        # Create GitHub client
        github = GitHubClient(token)
        
        # Get user repositories (limit to recent ones)
        repos = github.list_user_repositories(limit=20)
        
        # Sort by updated_at (most recent first)
        repos.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        return repos
        
    except IntegrationError as e:
        print_warning(f"Could not fetch repositories: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to get user repositories: {e}")
        return []


def _perform_clone(repository_url: str):
    """Perform the actual git clone operation."""
    try:
        # Convert HTTPS GitHub URLs to SSH if SSH keys are available
        final_url = _convert_to_ssh_if_available(repository_url)
        
        # Extract repository name from URL for directory name
        import re
        
        # Extract repo name from various URL formats
        patterns = [
            r'.*/([\w\-\.]+)\.git/?$',
            r'.*/([\w\-\.]+)/?$',
            r'.*:([\w\-\.]+/[\w\-\.]+)\.git$',
            r'.*:([\w\-\.]+/[\w\-\.]+)$'
        ]
        
        repo_name = None
        for pattern in patterns:
            match = re.search(pattern, repository_url)
            if match:
                repo_name = match.group(1)
                if '/' in repo_name:
                    repo_name = repo_name.split('/')[-1]
                break
        
        if not repo_name:
            repo_name = "cloned-repo"
        
        if final_url != repository_url:
            print_info(f"🔑 Using SSH for cloning: {final_url}")
        else:
            print_info(f"Cloning {repository_url}...")
        
        # Perform the clone
        run_git_command(['clone', final_url])
        
        print_success(f"Successfully cloned repository to {repo_name}")
        
        # Change to the cloned directory
        cloned_path = Path(repo_name)
        if cloned_path.exists() and cloned_path.is_dir():
            # Store the absolute path before changing directories
            absolute_cloned_path = cloned_path.absolute()
            os.chdir(cloned_path)
            print_info(f"Changed directory to {absolute_cloned_path}")
            
            # Open in default text editor
            _open_in_editor(absolute_cloned_path)
        else:
            print_warning("Could not find cloned directory to change into.")
        
    except GitError as e:
        print_error(f"Git clone failed: {e}")
    except Exception as e:
        print_error(f"Clone operation failed: {e}")


def _convert_to_ssh_if_available(url: str) -> str:
    """Convert HTTPS GitHub URL to SSH if SSH keys are available."""
    import re
    
    # Only convert if SSH keys are available
    if not _check_ssh_key_availability():
        return url
    
    # Pattern to match GitHub HTTPS URLs
    https_pattern = r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
    match = re.match(https_pattern, url)
    
    if match:
        username, repo = match.groups()
        # Convert to SSH format, ensure .git extension
        if not repo.endswith('.git'):
            repo += '.git'
        ssh_url = f"git@github.com:{username}/{repo}"
        return ssh_url
    
    # Return original URL if not a GitHub HTTPS URL or already SSH
    return url


def _open_in_editor(directory_path: Path):
    """Open the directory in the user's configured default text editor."""
    try:
        import subprocess
        import platform
        
        # Get the configured editor from config
        editor = config_manager.get_default_editor()
        
        if not editor:
            print_info(f"Repository cloned to: {directory_path}")
            print_info("No editor configured. Set 'defaults.editor' in your config file.")
            return
        
        system = platform.system()
        
        # Check if the configured editor exists
        try:
            if system == "Windows":
                # Check if command exists
                result = subprocess.run(["where", editor], 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(["which", editor], 
                                      capture_output=True, text=True)
            
            if result.returncode != 0:
                print_info(f"Repository cloned to: {directory_path}")
                print_warning(f"Configured editor '{editor}' not found in PATH.")
                return
        except FileNotFoundError:
            print_info(f"Repository cloned to: {directory_path}")
            print_warning(f"Configured editor '{editor}' not found.")
            return
        
        # Try to open with the configured editor
        try:
            subprocess.run([editor, str(directory_path)], check=True)
            print_success(f"Opened in {editor}")
        except subprocess.CalledProcessError:
            print_info(f"Repository cloned to: {directory_path}")
            print_warning(f"Failed to open directory with '{editor}'.")
        except FileNotFoundError:
            print_info(f"Repository cloned to: {directory_path}")
            print_warning(f"Editor '{editor}' not found.")
        
    except Exception as e:
        logger.error(f"Failed to open editor: {e}")
        print_info(f"Repository cloned to: {directory_path}")
        print_warning("Could not open directory in text editor.")


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


@main.command()
@click.option('--topic', '-t', 
              type=click.Choice(['config', 'basics', 'saving', 'switching', 'history', 'remotes', 'undo', 'advanced']),
              help='Focus on a specific topic')
def tutorial(topic: Optional[str]):
    """Interactive tutorial to learn BetterGit commands and workflows.
    
    Learn how to use BetterGit with hands-on examples and explanations.
    """
    try:
        if topic:
            _show_tutorial_topic(topic)
        else:
            _interactive_tutorial()
    except KeyboardInterrupt:
        print_info("\nTutorial cancelled. Run 'bit tutorial' anytime to continue learning!")
    except Exception as e:
        print_error(f"Tutorial error: {e}")


def _interactive_tutorial():
    """Show interactive tutorial menu."""
    print_success("🎓 Welcome to the BetterGit Tutorial!")
    print_info("BetterGit makes version control intuitive and powerful. Let's learn the essentials!")
    
    topics = [
        ("config", "⚙️  Configuration Setup - Set up your identity and GitHub integration"),
        ("basics", "🏁 Getting Started - Basic concepts and setup"),
        ("saving", "💾 Saving Changes - Creating commits and managing files"),
        ("switching", "🔄 Switching & Branches - Navigate between branches and commits"),
        ("history", "📋 History & Listing - View commits, branches, and actions"),
        ("remotes", "🌐 Remote Repositories - Working with GitHub and remotes"),
        ("undo", "↩️  Undoing Changes - Fix mistakes and revert actions"),
        ("advanced", "⚡ Advanced Features - Power user tips and workflows")
    ]
    
    while True:
        print("\n" + "="*80)
        print_info("Choose a topic to learn about (or press Ctrl+C to exit):")
        
        topic_texts = [topic[1] for topic in topics]
        selected = select_from_list("Select a tutorial topic:", topic_texts)
        
        if selected is None:
            break
        
        # Find the selected topic
        selected_key = None
        for key, text in topics:
            if text == selected:
                selected_key = key
                break
        
        if selected_key:
            _show_tutorial_topic(selected_key)
            
            # Ask if they want to continue
            if not confirm("\nWould you like to learn about another topic?", default=True):
                break
    
    print_success("\n🎉 Thanks for using the BetterGit tutorial!")
    print_info("Remember: You can always run 'bit tutorial -t <topic>' to review specific topics.")


def _show_tutorial_topic(topic: str):
    """Show tutorial content for a specific topic."""
    if topic == 'config':
        _tutorial_config()
    elif topic == 'basics':
        _tutorial_basics()
    elif topic == 'saving':
        _tutorial_saving()
    elif topic == 'switching':
        _tutorial_switching()
    elif topic == 'history':
        _tutorial_history()
    elif topic == 'remotes':
        _tutorial_remotes()
    elif topic == 'undo':
        _tutorial_undo()
    elif topic == 'advanced':
        _tutorial_advanced()


def _tutorial_config():
    """Tutorial for setting up BetterGit configuration."""
    print_success("\n⚙️ Configuration Setup - Your BetterGit Identity")
    print("="*80)
    
    sections = [
        ("Why Configuration Matters", """
BetterGit needs to know who you are to properly track your changes:
• Your name and email appear in commit history
• GitHub token enables remote operations (push, pull, PRs)
• Multiple accounts let you switch between work/personal
• Default settings customize BetterGit behavior

Let's set this up step by step!
"""),
        ("Opening Configuration", """
BetterGit stores all settings in a YAML configuration file.

bit config    # Opens config file in your default editor

This creates a config file if it doesn't exist. The file location is:
• Windows: %APPDATA%\\BetterGit\\config.yml
• macOS/Linux: ~/.config/bettergit/config.yml
"""),
        ("Setting Up Your Identity", """
First, let's set up your basic identity. If it doesnt have it already, add this to your config file:

accounts:
  personal:
    name: "Your Full Name"
    email: "you@example.com"
    ssh_key: "~/.ssh/id_ed25519.pub"  # Optional, if you use SSH keys
  work:
    name: "Your Full Name" 
    email: "you@company.com"
    ssh_key: "~/.ssh/id_ed25519.pub"  # Optional, if you use SSH keys

current_account: "personal"

The accounts dont have to be named "personal" or "work". You can name them whatever you like.
You add an account by adding a new section under `accounts:` with a unique name and following
the same structure as the others.
This allows you to easily switch between different identities.

Replace with your actual information. You can have multiple accounts!
"""),
        ("GitHub Token Setup", """
To work with GitHub repositories, you need a Personal Access Token.

🔗 Step 1: Go to: https://github.com/settings/tokens
📝 Step 2: Click "Generate new token" → "Generate new token (classic)"
📅 Step 3: Set expiration (recommend: 90 days or No expiration for personal use)
✅ Step 4: Select these permissions:
   • repo (Full control of private repositories)
   • workflow (Update GitHub Action workflows) 
   • read:org (Read org membership)
   • delete_repo (Delete repositories - optional)

🔑 Step 5: Click "Generate token" and copy it immediately
   Token starts with 'ghp_' or 'github_pat_'
   ⚠️  You can only see it once - copy it now!

💾 BetterGit will help you store this securely in the next step.
"""),
        ("SSH Keys (Recommended)", """
SSH keys provide the best authentication method for Git operations:

🔐 Why use SSH keys?
• More secure than HTTPS + token
• No expiration (unless you set one)
• Automatically detected and used by BetterGit
• No need to enter credentials for Git operations

🛠️  Setup SSH Keys:
1. Generate key: ssh-keygen -t ed25519 -C "your@email.com"
2. Add to GitHub: https://github.com/settings/ssh
3. Update the config file with your SSH key path: (by default it is ~/.ssh/id_ed25519.pub)

✨ BetterGit will automatically detect your SSH keys and use them when:
   • Creating new repositories
   • Cloning repositories 
   • All Git operations (push, pull, etc.)

💡 You still need a token for GitHub API operations (creating repos, PRs).
   But Git operations will use your SSH key automatically!
"""),
        ("Default Settings", """
Customize BetterGit behavior with default settings:

defaults:
  editor: code              # Your preferred text editor (e.g., code, nano, vim)
  main_branch_name: main    # Default main branch name (e.g., main, master)
  remote_service: github    # Default remote service (github, gitlab, bitbucket)
  repo_visibility: private  # Default repository visibility (private, public)

These settings apply to all new repositories and operations.
""")
    ]
    
    for title, content in sections:
        print(f"\n📖 {title}")
        print("-" * 60)
        print(content.strip())
        if not confirm("\nContinue to next section?", default=True):
            break
    
    # Interactive token setup
    if confirm("\n🔧 Would you like to set up your GitHub token now?", default=True):
        _interactive_token_setup()
    else:
        print_info("💡 You can set up your token later with: bit tutorial -t config")
    
    print_info("\n✅ Configuration complete! Your BetterGit is ready to use.")
    print_info("💡 Tip: Run 'bit config' anytime to modify these settings.")
    print_info("🚀 Next: Try 'bit tutorial -t basics' to learn essential commands!")


def _interactive_token_setup():
    """Interactive setup for GitHub token."""
    try:
        print_success("\n🔐 GitHub Token Setup Wizard")
        print("="*50)
        print_info("This will help you save your GitHub token securely.")
        
        # Get current account
        try:
            current_account = config_manager.get_current_account()
            print_info(f"Setting up token for account: {current_account}")
        except:
            current_account = "personal"
            print_warning(f"Using default account: {current_account}")
        
        # Check if token already exists
        existing_token = config_manager.get_credential(current_account)
        if existing_token:
            print_warning(f"⚠️  A token already exists for {current_account}")
            if not confirm("Replace the existing token?", default=False):
                return
        
        # Reminder about token creation
        print_info("\n📋 Quick Reminder:")
        print("1. Go to: https://github.com/settings/tokens")
        print("2. Generate new token (classic)")
        print("3. Select: repo, workflow, read:org permissions")
        print("4. Copy the token (starts with 'ghp_' or 'github_pat_')")
        
        if not confirm("\nDo you have your GitHub token ready?", default=True):
            print_info("No problem! Come back when you have your token.")
            print_info("Run: bit tutorial -t config")
            return
        
        # Prompt for token
        print_info("\n🔑 Paste your GitHub token below:")
        print_warning("(The token will be hidden as you type)")
        token = prompt_password("GitHub Token: ")
        
        if not token:
            print_warning("No token entered. Skipping token setup.")
            return
        
        # Validate token format
        if not (token.startswith('ghp_') or token.startswith('github_pat_')):
            print_warning("⚠️  Token doesn't look like a GitHub token")
            print_info("Valid tokens start with 'ghp_' or 'github_pat_'")
            if not confirm("Continue anyway?", default=False):
                return
        
        # Store the token
        config_manager.store_credential(current_account, token)
        
        # Set environment variable for this session
        _set_environment_variable('GITHUB_TOKEN', token)
        
        print_success("✅ Token saved successfully!")
        print_info("� Token is stored securely in BetterGit's credential store")
        print_info("🌍 Environment variable GITHUB_TOKEN set for this session")
        
        # Test the token
        if confirm("\n🧪 Test the token now?", default=True):
            _test_github_token(token)
        else:
            print_info("💡 You can test it later with any GitHub operation (bit push, bit clone, etc.)")
            
    except KeyboardInterrupt:
        print_info("\n\nToken setup cancelled.")
    except Exception as e:
        print_error(f"Failed to set up token: {e}")
        print_info("💡 You can try again later with: bit tutorial -t config")


def _set_environment_variable(name: str, value: str):
    """Set environment variable for current session and provide instructions for persistence."""
    try:
        import os
        import platform
        
        # Set for current Python session
        os.environ[name] = value
        
        system = platform.system()
        
        if system == "Windows":
            print_info(f"💾 Setting {name} for Windows...")
            try:
                import subprocess
                # Try to use setx for persistent setting
                result = subprocess.run(['setx', name, value], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print_success(f"✅ {name} will be available in new terminal sessions")
                else:
                    print_warning(f"⚠️  Could not set persistent variable. Manual setup needed.")
                    print_info(f"To set manually: setx {name} \"{value}\"")
            except Exception:
                print_warning("Could not set persistent environment variable")
                print_info(f"💡 To set manually in PowerShell:")
                print(f"    setx {name} \"{value}\"")
                
        else:
            # For Unix systems, provide instructions
            shell = os.environ.get('SHELL', '/bin/bash')
            shell_name = shell.split('/')[-1]
            
            config_files = {
                'bash': ['~/.bashrc', '~/.bash_profile'],
                'zsh': ['~/.zshrc'],
                'fish': ['~/.config/fish/config.fish']
            }
            
            files = config_files.get(shell_name, ['~/.bashrc'])
            
            print_info(f"💡 To make {name} permanent, add this line to {files[0]}:")
            print(f"    export {name}='{value}'")
            
    except Exception as e:
        print_warning(f"Could not set environment variable: {e}")
        print_info(f"💡 Manual setup: Set {name}='{value}' in your system")


def _test_github_token(token: str):
    """Test GitHub token by making a simple API call."""
    try:
        print_info("🔍 Testing your GitHub token...")
        
        github = GitHubClient(token)
        
        # Make a simple API call to get user info
        user_info = github._make_request('GET', '/user')
        
        if user_info:
            username = user_info.get('login', 'Unknown')
            name = user_info.get('name', username)
            avatar = user_info.get('avatar_url', '')
            
            print_success(f"🎉 Token works perfectly!")
            print_info(f"👤 Connected as: {name} (@{username})")
            
            # Get some additional info
            public_repos = user_info.get('public_repos', 0)
            private_repos = user_info.get('total_private_repos', 0)
            print_info(f"📦 Repositories: {public_repos} public, {private_repos} private")
            
        else:
            print_warning("⚠️  Token test was inconclusive")
            print_info("The token might still work - this could be a network issue.")
            
    except Exception as e:
        print_error(f"❌ Token test failed: {e}")
        print_warning("This could mean:")
        print("• The token is invalid or expired")
        print("• Network connectivity issues")
        print("• GitHub API is temporarily unavailable")
        print_info("💡 Try using the token with a Git operation to verify it works.")


def _tutorial_basics():
    """Tutorial for basic concepts."""
    print_success("\n🏁 Getting Started with BetterGit")
    print("="*80)
    
    sections = [
        ("First Things First", """
⚠️  IMPORTANT: Before using BetterGit, you should set up your configuration!

Run: bit tutorial -t config

This sets up:
• Your name and email (required for commits)
• GitHub token (needed for remote operations)
• Multiple accounts (work/personal)
• Default settings

Don't worry - you can always come back to this tutorial after setup!
"""),
        ("What is BetterGit?", """
BetterGit is a modern, intuitive interface for Git that makes version control easy.
It uses familiar concepts:
• 'saves' instead of 'commits' - think of saving your game progress
• 'switch' to move between branches or states
• Interactive menus for complex operations
• Human-readable output and error messages
"""),
        ("Essential Commands", """
Here are the most important commands to know:

📋 bit status           - See what's changed in your project
💾 bit save            - Save your changes (like a game save point)
🔄 bit switch <branch> - Switch to a different branch or commit
📁 bit list            - Interactive menu to list things
↩️  bit undo           - Undo the last action
🎓 bit tutorial        - This tutorial!
"""),
        ("Your First Repository", """
To start using BetterGit:

1. In a new project:
   bit init my-project    # Creates new repository and folder
   
2. In an existing folder:
   bit init              # Initialize git in current folder
   
3. Check status:
   bit status            # See what files have changed
"""),
        ("Getting Help", """
Every command has built-in help:

bit --help              # Show all commands
bit save --help         # Help for specific command
bit tutorial -t config  # Learn about configuration setup
bit tutorial -t saving  # Learn about a specific topic

The interactive menus will guide you through complex operations!
""")
    ]
    
    for title, content in sections:
        print(f"\n📖 {title}")
        print("-" * 60)
        print(content.strip())
        if not confirm("\nContinue to next section?", default=True):
            break


def _tutorial_saving():
    """Tutorial for saving changes."""
    print_success("\n💾 Saving Changes - Your Progress Checkpoints")
    print("="*80)
    
    sections = [
        ("Understanding Saves", """
In BetterGit, 'saves' are like checkpoints in a video game:
• Each save captures the current state of all your files
• You can return to any save point later
• Saves include a message describing what changed
• Think: "I just fixed the login bug" → save it!
"""),
        ("Basic Saving", """
Simple ways to save your changes:

bit save "your message"     # Save all changes with a message
bit save                    # Interactive mode - choose files and message
bit save file.py "fix bug"  # Save specific files only

The message should describe WHAT you did, not how:
✅ "Fix login validation bug"
❌ "Changed line 45 in auth.py"
"""),
        ("Interactive Saving", """
When you run 'bit save' with no arguments, you get an interactive menu:

1. Select which files to include in your save
2. Enter a descriptive message
3. BetterGit creates your save point

This is perfect when you have multiple changes and want to save them separately.
"""),
        ("Advanced Saving", """
More powerful saving options:

bit save . "message"        # Save everything in current folder
bit save *.py "fix bugs"    # Save all Python files
bit save file1 file2 "msg"  # Save specific files

Pro tip: Save early and often! It's better to have many small saves
than few large ones. Each save should represent one logical change.
"""),
        ("What Gets Saved?", """
BetterGit saves:
✅ New files you've created
✅ Modified existing files
✅ Deleted files
❌ Files in .gitignore
❌ Very large files (over 100MB by default)

Check what will be saved with: bit status
""")
    ]
    
    for title, content in sections:
        print(f"\n📖 {title}")
        print("-" * 60)
        print(content.strip())
        if not confirm("\nContinue to next section?", default=True):
            break


def _tutorial_switching():
    """Tutorial for switching between branches and commits."""
    print_success("\n🔄 Switching & Branches - Navigate Your Project")
    print("="*80)
    
    sections = [
        ("What is Switching?", """
Switching lets you move between different versions of your project:
• Switch to different branches (parallel development lines)
• Go back to previous saves (commits)
• Switch between different user accounts
• Create new branches on the fly
"""),
        ("Basic Switching", """
Common switching commands:

bit switch main           # Switch to main branch
bit switch feature-login  # Switch to a feature branch
bit switch abc123         # Go to a specific commit (by hash)

If the branch doesn't exist, BetterGit will ask if you want to create it!
"""),
        ("Creating Branches", """
BetterGit makes branch creation easy:

bit switch new-feature -c    # Create and switch to new branch
bit switch new-feature       # Interactive prompt to create

Branches are perfect for:
• Trying new features without breaking main code
• Experimenting with different approaches
• Working on multiple features simultaneously
"""),
        ("Understanding Branches", """
Think of branches like parallel universes of your project:

main branch:     A---B---C---D
                      \\
feature branch:        E---F---G

Each branch has its own history of saves. You can work on the feature
branch without affecting main, then merge when ready.
"""),
        ("Switching Between Accounts", """
You can also switch between different user accounts:

bit switch work-account    # Switch to your work GitHub account
bit switch personal        # Switch to personal account

This automatically updates git configuration for the current repository.
""")
    ]
    
    for title, content in sections:
        print(f"\n📖 {title}")
        print("-" * 60)
        print(content.strip())
        if not confirm("\nContinue to next section?", default=True):
            break


def _tutorial_history():
    """Tutorial for viewing history and listings."""
    print_success("\n📋 History & Listing - Understand Your Project")
    print("="*80)
    
    sections = [
        ("The List Command", """
The 'bit list' command is your window into the project:

bit list              # Interactive menu to choose what to list
bit list saves        # Show recent commits/saves
bit list branches     # Show all branches
bit list history      # Show your recent actions
bit list accounts     # Show configured user accounts
"""),
        ("Understanding History", """
BetterGit tracks two types of history:

1. Git History: Your saves (commits) and their messages
2. Action History: Commands you've run (save, switch, push, etc.)

Both help you understand what happened and when.
"""),
        ("Reading Save History", """
When you run 'bit list saves', you see:

1. abc123: "Fix login bug" by John (2h ago)
2. def456: "Add user registration" by John (1d ago)

Each line shows:
• Commit hash (abc123) - unique identifier
• Message ("Fix login bug") - what changed
• Author (John) - who made the change
• Time (2h ago) - when it was made
"""),
        ("Action History", """
Action history shows what commands you've run:

bit list history         # Recent actions
bit list history -n 20   # Show 20 recent actions
bit list history -d      # Include detailed timestamps

This is helpful for:
• Remembering what you did
• Understanding how you got to current state
• Finding actions to undo
"""),
        ("Branch Overview", """
'bit list branches' shows:

✅ main (current)       # Current branch with checkmark
   feature-login        # Other local branches
   origin/develop       # Remote branches

The checkmark shows which branch you're currently on.
""")
    ]
    
    for title, content in sections:
        print(f"\n📖 {title}")
        print("-" * 60)
        print(content.strip())
        if not confirm("\nContinue to next section?", default=True):
            break


def _tutorial_remotes():
    """Tutorial for working with remote repositories."""
    print_success("\n🌐 Remote Repositories - Collaborate and Backup")
    print("="*80)
    
    sections = [
        ("What are Remotes?", """
Remotes are copies of your repository stored elsewhere:
• GitHub, GitLab, Bitbucket (online platforms)
• Another computer or server
• Cloud storage with git support

They enable:
• Collaboration with others
• Backup of your work
• Access from multiple devices
"""),
        ("Basic Remote Operations", """
Essential remote commands:

bit push              # Send your saves to remote
bit pull              # Get updates from remote
bit clone <url>       # Copy a remote repository
bit sync              # Push and pull in one command

Always pull before pushing to avoid conflicts!
"""),
        ("The Clone Command", """
BetterGit's clone is super smart:

bit clone                    # Interactive selection from your GitHub repos
bit clone <url>              # Clone specific repository
bit clone user/repo          # Clone GitHub repo by name

Features:
• Detects clipboard URLs automatically
• Lists your GitHub repositories
• Opens project in your editor after cloning
"""),
        ("Setting Up Remotes", """
When you create a new project:

bit init my-project    # Create local repository
# BetterGit asks if you want to create remote repository
# If yes, it creates GitHub repo and connects it automatically

For existing projects:
# You can manually add remotes through git commands
# or recreate with remote using bit init
"""),
        ("Collaboration Workflow", """
Typical collaboration flow:

1. bit clone <url>           # Get the project
2. bit switch new-feature -c # Create feature branch
3. # Make your changes
4. bit save "add feature"    # Save your work
5. bit push                  # Share with team
6. # Create pull request on GitHub
7. # After merge, switch back to main
8. bit pull                  # Get latest updates
""")
    ]
    
    for title, content in sections:
        print(f"\n📖 {title}")
        print("-" * 60)
        print(content.strip())
        if not confirm("\nContinue to next section?", default=True):
            break


def _tutorial_undo():
    """Tutorial for undoing changes and fixing mistakes."""
    print_success("\n↩️ Undoing Changes - Fix Mistakes Like a Pro")
    print("="*80)
    
    sections = [
        ("Why Undo Matters", """
Everyone makes mistakes! BetterGit makes fixing them easy:
• Undo the last action you took
• Undo specific commits from the past
• Delete unwanted branches
• Interactive selection of what to undo
• Safe operations with confirmation prompts
"""),
        ("Basic Undo", """
Simple undo operations:

bit undo              # Undo the last action
bit undo -i           # Interactive menu to choose what to undo
bit undo abc123       # Undo specific commit by hash
bit undo feature-branch # Delete specific branch

The most recent action is always the easiest to undo.
"""),
        ("Interactive Undo", """
'bit undo -i' shows you recent actions:

1. SAVE: "Fix login bug" (2h ago)
2. SWITCH: main → feature-login (3h ago)
3. PUSH: to main (1d ago)

Select any action to undo. BetterGit will undo that action
and all actions after it (like rewinding a tape).
"""),
        ("Targeted Undo", """
Undo specific things:

bit undo abc123         # Undo specific commit
• If it's the latest commit: moves changes to staging
• If it's older: offers revert commit or interactive rebase

bit undo feature-branch # Delete specific branch
• Confirms before deletion
• Asks about remote branch too
• Protects main/master branches
"""),
        ("Undo Safety Features", """
BetterGit protects you from dangerous operations:

⚠️  Confirms destructive actions
⚠️  Shows what will be affected
⚠️  Prevents deleting current branch
⚠️  Warns about protected branches (main, master)
⚠️  Explains consequences of actions

Always read the prompts carefully!
"""),
        ("What Can't Be Undone", """
Some things are permanent:
❌ Forced pushes to remote (affects others)
❌ Deleted files not tracked by git
❌ Actions outside of BetterGit
❌ Manual git commands (not logged in history)

That's why BetterGit encourages using its commands - they're trackable!
""")
    ]
    
    for title, content in sections:
        print(f"\n📖 {title}")
        print("-" * 60)
        print(content.strip())
        if not confirm("\nContinue to next section?", default=True):
            break


def _tutorial_advanced():
    """Tutorial for advanced features and workflows."""
    print_success("\n⚡ Advanced Features - Power User Tips")
    print("="*80)
    
    sections = [
        ("Stashing Changes", """
Stash lets you temporarily save uncommitted changes:

bit stash "work in progress"  # Save current changes temporarily
bit stash                     # Quick stash without message

Useful when you need to:
• Switch branches but aren't ready to commit
• Pull updates without committing current work
• Try a different approach while preserving current work
"""),
        ("Multiple Accounts", """
Manage different identities:

# Set up accounts in config
work-account:
  name: "John Smith"
  email: "john@company.com"

personal:
  name: "John"
  email: "john@personal.com"

# Switch between them
bit switch work-account    # Use work identity
bit switch personal        # Use personal identity
"""),
        ("Force Operations", """
Sometimes you need more power:

bit push -f               # Force push (dangerous!)
bit undo branch-name      # Force delete branch

These operations bypass safety checks. Use with extreme caution!
"""),
        ("Pull Request Workflow", """
Advanced GitHub integration:

bit pr create -t "Fix bug" -b "Fixes login issue"
bit pr list              # See all pull requests
bit pr checkout 42       # Check out PR #42 locally

Streamlines code review process.
"""),
        ("Repository Maintenance", """
Keep your repository healthy:

bit cleanup              # Clean up old branches and refs
bit sync                 # Synchronize with remote
bit graph                # Visualize commit history

Regular maintenance prevents issues.
"""),
        ("Configuration Tips", """
Customize BetterGit behavior:

# Set default editor
default_editor: "code"

# Set default branch name
main_branch_name: "main"

# Set default repository visibility
repo_visibility: "private"

Edit config with: bit config edit
"""),
        ("Debugging Issues", """
When things go wrong:

bit status               # Always start here
bit list history         # See what you did recently
bit --verbose <command>  # Get detailed output
bit tutorial -t undo     # Learn how to fix mistakes

Most issues can be resolved with undo operations!
""")
    ]
    
    for title, content in sections:
        print(f"\n📖 {title}")
        print("-" * 60)
        print(content.strip())
        if not confirm("\nContinue to next section?", default=True):
            break


if __name__ == '__main__':
    main()
