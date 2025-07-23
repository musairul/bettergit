"""Tests for BetterGit configuration management."""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from bettergit.config import ConfigManager, ConfigError


class TestConfigManager:
    """Test the configuration management system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / ".config" / "bettergit"
        self.config_file = self.config_dir / "config.yml"
    
    def test_default_config_creation(self):
        """Test creation of default configuration."""
        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            config_manager = ConfigManager()
            
            assert self.config_file.exists()
            
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            assert 'accounts' in config
            assert 'current_account' in config
            assert 'defaults' in config
    
    def test_get_current_account(self):
        """Test getting current account."""
        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            config_manager = ConfigManager()
            current = config_manager.get_current_account()
            
            assert current == 'personal'
    
    def test_set_current_account(self):
        """Test setting current account."""
        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            config_manager = ConfigManager()
            
            # This should work since 'personal' exists in default config
            config_manager.set_current_account('personal')
            assert config_manager.get_current_account() == 'personal'
    
    def test_set_invalid_account(self):
        """Test setting invalid account."""
        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            config_manager = ConfigManager()
            
            with pytest.raises(ConfigError):
                config_manager.set_current_account('nonexistent')
    
    def test_get_accounts(self):
        """Test getting all accounts."""
        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            config_manager = ConfigManager()
            accounts = config_manager.get_accounts()
            
            assert isinstance(accounts, dict)
            assert 'personal' in accounts
    
    def test_credential_storage_mock(self):
        """Test credential storage (mocked)."""
        with patch('pathlib.Path.home', return_value=Path(self.temp_dir)):
            with patch('keyring.set_password') as mock_set:
                with patch('keyring.get_password', return_value='test_token') as mock_get:
                    config_manager = ConfigManager()
                    
                    # Store credential
                    config_manager.store_credential('test_account', 'test_token')
                    mock_set.assert_called_once_with('bettergit', 'test_account', 'test_token')
                    
                    # Retrieve credential
                    token = config_manager.get_credential('test_account')
                    assert token == 'test_token'
                    mock_get.assert_called_once_with('bettergit', 'test_account')
