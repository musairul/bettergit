"""Action history management for the undo functionality."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging


logger = logging.getLogger(__name__)


class HistoryError(Exception):
    """Raised when there's an error with action history."""
    pass


class ActionHistory:
    """Manages the history of state-changing actions for undo functionality."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "bettergit"
        self.history_file = self.config_dir / "history.json"
        self._ensure_history_exists()
    
    def _ensure_history_exists(self):
        """Ensure the history file exists."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            if not self.history_file.exists():
                self._save_history([])
        except Exception as e:
            raise HistoryError(f"Failed to create history file: {e}")
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load action history from file."""
        try:
            if not self.history_file.exists():
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in history file, resetting: {e}")
            return []
        except Exception as e:
            raise HistoryError(f"Failed to load history: {e}")
    
    def _save_history(self, history: List[Dict[str, Any]]):
        """Save action history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            raise HistoryError(f"Failed to save history: {e}")
    
    def log_action(self, action_type: str, details: Dict[str, Any], 
                   undo_command: Optional[str] = None, 
                   undo_details: Optional[Dict[str, Any]] = None):
        """
        Log a state-changing action.
        
        Args:
            action_type: Type of action (e.g., 'save', 'merge', 'push')
            details: Details about the action performed
            undo_command: Command needed to undo this action
            undo_details: Additional details needed for undo
        """
        try:
            history = self._load_history()
            
            action = {
                "id": len(history) + 1,
                "timestamp": datetime.now().isoformat(),
                "action_type": action_type,
                "details": details,
                "undo_command": undo_command,
                "undo_details": undo_details or {}
            }
            
            history.append(action)
            
            # Keep only the last 50 actions to prevent file bloat
            if len(history) > 50:
                history = history[-50:]
                # Renumber the actions
                for i, action in enumerate(history):
                    action["id"] = i + 1
            
            self._save_history(history)
            logger.info(f"Logged action: {action_type}")
            
        except Exception as e:
            # Don't fail the main operation if history logging fails
            logger.error(f"Failed to log action: {e}")
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get the action history, optionally limited to recent actions."""
        history = self._load_history()
        if limit:
            return history[-limit:]
        return history
    
    def get_last_action(self) -> Optional[Dict[str, Any]]:
        """Get the most recent action."""
        history = self._load_history()
        return history[-1] if history else None
    
    def remove_last_action(self) -> Optional[Dict[str, Any]]:
        """Remove and return the most recent action."""
        try:
            history = self._load_history()
            if not history:
                return None
            
            last_action = history.pop()
            self._save_history(history)
            return last_action
            
        except Exception as e:
            raise HistoryError(f"Failed to remove last action: {e}")
    
    def clear_history(self):
        """Clear all action history."""
        try:
            self._save_history([])
            logger.info("Cleared action history")
        except Exception as e:
            raise HistoryError(f"Failed to clear history: {e}")
    
    def get_undoable_actions(self) -> List[str]:
        """Get list of action types that can be undone."""
        return [
            "save",      # git reset --soft HEAD~1
            "merge",     # git reset --hard ORIG_HEAD
            "push",      # git push --force (dangerous)
            "pull",      # git reset --hard HEAD@{1}
            "stash",     # git stash pop
            "switch"     # git switch to previous branch
        ]


# Global history manager instance
history_manager = ActionHistory()
