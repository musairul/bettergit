"""Base classes for third-party integrations."""

import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging


logger = logging.getLogger(__name__)


class IntegrationError(Exception):
    """Raised when there's an error with third-party integrations."""
    pass


class IntegrationClient(ABC):
    """Base class for third-party service integrations."""
    
    def __init__(self, api_url: str, token: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        if token:
            self._set_auth_headers()
    
    @abstractmethod
    def _set_auth_headers(self):
        """Set authentication headers for the session."""
        pass
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make an authenticated API request."""
        try:
            url = f"{self.api_url}/{endpoint.lstrip('/')}"
            
            response = self.session.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                timeout=30
            )
            
            if response.status_code == 401:
                raise IntegrationError("Authentication failed. Please check your token.")
            elif response.status_code == 403:
                raise IntegrationError("Access forbidden. Check your permissions.")
            elif response.status_code == 404:
                raise IntegrationError("Resource not found.")
            elif not response.ok:
                raise IntegrationError(f"API request failed: {response.status_code} {response.text}")
            
            return response.json() if response.content else {}
            
        except requests.RequestException as e:
            raise IntegrationError(f"Network error: {e}")
        except ValueError as e:
            raise IntegrationError(f"Invalid JSON response: {e}")
    
    @abstractmethod
    def create_repository(self, name: str, description: str = "", 
                         private: bool = True) -> Dict[str, Any]:
        """Create a new repository."""
        pass
    
    @abstractmethod
    def create_pull_request(self, repo_owner: str, repo_name: str,
                           title: str, body: str, head: str, 
                           base: str = "main") -> Dict[str, Any]:
        """Create a new pull request."""
        pass
    
    @abstractmethod
    def list_pull_requests(self, repo_owner: str, repo_name: str,
                          state: str = "open") -> List[Dict[str, Any]]:
        """List pull requests for a repository."""
        pass
    
    @abstractmethod
    def get_pull_request(self, repo_owner: str, repo_name: str,
                        pr_number: int) -> Dict[str, Any]:
        """Get a specific pull request."""
        pass
    
    @abstractmethod
    def get_issue(self, repo_owner: str, repo_name: str,
                 issue_number: int) -> Dict[str, Any]:
        """Get a specific issue."""
        pass
