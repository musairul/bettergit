"""Integration modules for third-party services."""

from .github import GitHubClient
from .base import IntegrationClient, IntegrationError

__all__ = ["GitHubClient", "IntegrationClient", "IntegrationError"]
