"""Configuration management for BetterGit."""

import os
import yaml
import keyring
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging


logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when there's an error with configuration."""
    pass


class ConfigManager:
    """Manages BetterGit configuration and secure credential storage."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "bettergit"
        self.config_file = self.config_dir / "config.yml"
        self.keyring_service = "bettergit"
        self._config = None
        self._ensure_config_exists()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration structure."""
        return {
            "accounts": {
                "personal": {
                    "name": "Your Name",
                    "email": "personal@example.com",
                    "ssh_key": "~/.ssh/id_rsa_personal"
                }
            },
            "current_account": "personal",
            "defaults": {
                "remote_service": "github",
                "repo_visibility": "private",
                "main_branch_name": "main"
            },
            "issue_tracker": {
                "platform": "github",
                "api_url": "https://api.github.com",
                "project_key": "PROJ"
            }
        }
    
    def _ensure_config_exists(self):
        """Ensure the configuration directory and file exist."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            if not self.config_file.exists():
                logger.info(f"Creating default config at {self.config_file}")
                default_config = self._get_default_config()
                self._save_config(default_config)
                print(f"Created default configuration at {self.config_file}")
                print("Please edit this file to configure your accounts and preferences.")
                
        except Exception as e:
            raise ConfigError(f"Failed to create config directory: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_file}")
            return self._get_default_config()
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}")
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}")
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the current configuration, loading if necessary."""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def reload_config(self):
        """Reload configuration from file."""
        self._config = None
    
    def get_current_account(self) -> str:
        """Get the currently active account alias."""
        return self.config.get("current_account", "personal")
    
    def set_current_account(self, alias: str):
        """Set the currently active account."""
        if alias not in self.get_accounts():
            raise ConfigError(f"Account '{alias}' not found in configuration")
        
        config = self.config.copy()
        config["current_account"] = alias
        self._save_config(config)
        self._config = config
        logger.info(f"Set current account to: {alias}")
    
    def get_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured accounts."""
        return self.config.get("accounts", {})
    
    def get_account(self, alias: str) -> Optional[Dict[str, Any]]:
        """Get a specific account configuration."""
        return self.get_accounts().get(alias)
    
    def get_current_account_config(self) -> Dict[str, Any]:
        """Get the configuration for the currently active account."""
        current = self.get_current_account()
        account = self.get_account(current)
        if not account:
            raise ConfigError(f"Current account '{current}' not found in configuration")
        return account
    
    def get_default(self, key: str) -> Any:
        """Get a default setting value."""
        return self.config.get("defaults", {}).get(key)
    
    def get_issue_tracker_config(self) -> Dict[str, Any]:
        """Get issue tracker configuration."""
        return self.config.get("issue_tracker", {})
    
    def store_credential(self, account_alias: str, token: str):
        """Securely store a credential for an account."""
        try:
            keyring.set_password(self.keyring_service, account_alias, token)
            logger.info(f"Stored credential for account: {account_alias}")
        except Exception as e:
            raise ConfigError(f"Failed to store credential: {e}")
    
    def get_credential(self, account_alias: str) -> Optional[str]:
        """Retrieve a stored credential for an account."""
        try:
            return keyring.get_password(self.keyring_service, account_alias)
        except Exception as e:
            logger.warning(f"Failed to retrieve credential for {account_alias}: {e}")
            return None
    
    def delete_credential(self, account_alias: str):
        """Delete a stored credential for an account."""
        try:
            keyring.delete_password(self.keyring_service, account_alias)
            logger.info(f"Deleted credential for account: {account_alias}")
        except Exception as e:
            logger.warning(f"Failed to delete credential for {account_alias}: {e}")
    
    def list_stored_credentials(self) -> List[str]:
        """List account aliases that have stored credentials."""
        stored = []
        for alias in self.get_accounts().keys():
            if self.get_credential(alias):
                stored.append(alias)
        return stored


# Global config manager instance
config_manager = ConfigManager()
