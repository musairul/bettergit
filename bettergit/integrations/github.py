"""GitHub API integration."""

from .base import IntegrationClient, IntegrationError
from typing import Dict, Any, List, Optional
import re
import logging


logger = logging.getLogger(__name__)


class GitHubClient(IntegrationClient):
    """GitHub API client for repository and pull request management."""
    
    def __init__(self, token: Optional[str] = None):
        super().__init__("https://api.github.com", token)
    
    def _set_auth_headers(self):
        """Set GitHub authentication headers."""
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "BetterGit/1.0.0"
        })
    
    def get_authenticated_user(self) -> Dict[str, Any]:
        """Get the authenticated user's information."""
        return self._make_request("GET", "/user")
    
    def create_repository(self, name: str, description: str = "", 
                         private: bool = True) -> Dict[str, Any]:
        """Create a new GitHub repository."""
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": False
        }
        return self._make_request("POST", "/user/repos", data=data)
    
    def create_pull_request(self, repo_owner: str, repo_name: str,
                           title: str, body: str, head: str, 
                           base: str = "main") -> Dict[str, Any]:
        """Create a new pull request."""
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        endpoint = f"/repos/{repo_owner}/{repo_name}/pulls"
        return self._make_request("POST", endpoint, data=data)
    
    def list_pull_requests(self, repo_owner: str, repo_name: str,
                          state: str = "open") -> List[Dict[str, Any]]:
        """List pull requests for a repository."""
        endpoint = f"/repos/{repo_owner}/{repo_name}/pulls"
        params = {"state": state}
        return self._make_request("GET", endpoint, params=params)
    
    def get_pull_request(self, repo_owner: str, repo_name: str,
                        pr_number: int) -> Dict[str, Any]:
        """Get a specific pull request."""
        endpoint = f"/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        return self._make_request("GET", endpoint)
    
    def get_issue(self, repo_owner: str, repo_name: str,
                 issue_number: int) -> Dict[str, Any]:
        """Get a specific issue."""
        endpoint = f"/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
        return self._make_request("GET", endpoint)
    
    def list_issues(self, repo_owner: str, repo_name: str,
                   state: str = "open", labels: Optional[str] = None) -> List[Dict[str, Any]]:
        """List issues for a repository."""
        endpoint = f"/repos/{repo_owner}/{repo_name}/issues"
        params = {"state": state}
        if labels:
            params["labels"] = labels
        return self._make_request("GET", endpoint, params=params)
    
    def get_repository(self, repo_owner: str, repo_name: str) -> Dict[str, Any]:
        """Get repository information."""
        endpoint = f"/repos/{repo_owner}/{repo_name}"
        return self._make_request("GET", endpoint)
    
    @staticmethod
    def parse_repo_url(url: str) -> Optional[tuple]:
        """
        Parse a GitHub repository URL to extract owner and repo name.
        
        Returns:
            Tuple of (owner, repo_name) or None if not a valid GitHub URL
        """
        # Handle various GitHub URL formats
        patterns = [
            r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$',
            r'github\.com/([^/]+)/([^/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                owner, repo = match.groups()
                # Remove .git suffix if present
                if repo.endswith('.git'):
                    repo = repo[:-4]
                return owner, repo
        
        return None
    
    def create_branch_from_issue(self, repo_owner: str, repo_name: str,
                                issue_number: int) -> str:
        """
        Create a branch name from an issue.
        
        Returns:
            Formatted branch name suitable for the issue
        """
        try:
            issue = self.get_issue(repo_owner, repo_name, issue_number)
            title = issue.get('title', f'issue-{issue_number}')
            
            # Clean up the title to create a valid branch name
            # Remove non-alphanumeric characters and replace with hyphens
            clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
            clean_title = re.sub(r'\s+', '-', clean_title.strip())
            clean_title = clean_title.lower()[:50]  # Limit length
            
            # Determine branch prefix based on issue labels
            labels = [label['name'].lower() for label in issue.get('labels', [])]
            
            if 'bug' in labels:
                prefix = 'fix'
            elif 'enhancement' in labels or 'feature' in labels:
                prefix = 'feature'
            elif 'documentation' in labels:
                prefix = 'docs'
            else:
                prefix = 'feature'
            
            return f"{prefix}/{issue_number}-{clean_title}"
            
        except IntegrationError:
            # Fallback if we can't fetch the issue
            return f"feature/{issue_number}-work-on-issue"
