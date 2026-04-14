"""
JARVIS Memory System

Handles short-term and long-term memory storage.
Stores user preferences, past projects, and learned improvements.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from jarvis.core.logging import get_logger

logger = get_logger(__name__)


class Memory:
    """Simple JSON-based memory system for JARVIS."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize memory system.
        
        Args:
            storage_dir: Directory for memory files (default: ./memory)
        """
        self.storage_dir = storage_dir or Path(__file__).parent.parent.parent / "memory_storage"
        self.storage_dir.mkdir(exist_ok=True)
        
        # Initialize memory files
        self.short_term_file = self.storage_dir / "short_term.json"
        self.long_term_file = self.storage_dir / "long_term.json"
        self.preferences_file = self.storage_dir / "preferences.json"
        self.projects_file = self.storage_dir / "projects.json"
        
        # Initialize files if they don't exist
        self._initialize_files()
        
        logger.info(f"Memory system initialized at: {self.storage_dir}")

    def _initialize_files(self):
        """Initialize memory storage files if they don't exist."""
        for file_path in [
            self.short_term_file,
            self.long_term_file,
            self.preferences_file,
            self.projects_file
        ]:
            if not file_path.exists():
                file_path.write_text(json.dumps({}))

    def store_short_term(self, key: str, value: Any):
        """
        Store information in short-term memory (conversation context).
        
        Args:
            key: Memory key
            value: Value to store
        """
        data = self._load_json(self.short_term_file)
        data[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save_json(self.short_term_file, data)
        logger.debug(f"Short-term memory stored: {key}")

    def retrieve_short_term(self, key: str) -> Optional[Any]:
        """
        Retrieve information from short-term memory.
        
        Args:
            key: Memory key
            
        Returns:
            Stored value or None
        """
        data = self._load_json(self.short_term_file)
        if key in data:
            return data[key].get("value")
        return None

    def store_long_term(self, key: str, value: Any):
        """
        Store information in long-term memory.
        
        Args:
            key: Memory key
            value: Value to store
        """
        data = self._load_json(self.long_term_file)
        data[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save_json(self.long_term_file, data)
        logger.debug(f"Long-term memory stored: {key}")

    def retrieve_long_term(self, key: str) -> Optional[Any]:
        """
        Retrieve information from long-term memory.
        
        Args:
            key: Memory key
            
        Returns:
            Stored value or None
        """
        data = self._load_json(self.long_term_file)
        if key in data:
            return data[key].get("value")
        return None

    def store_preference(self, key: str, value: Any):
        """
        Store user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        data = self._load_json(self.preferences_file)
        data[key] = value
        self._save_json(self.preferences_file, data)
        logger.debug(f"Preference stored: {key}")

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get user preference.
        
        Args:
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        data = self._load_json(self.preferences_file)
        return data.get(key, default)

    def record_project(self, project_data: Dict[str, Any]):
        """
        Record a completed project.
        
        Args:
            project_data: Project information (name, type, files, status, etc.)
        """
        projects = self._load_json(self.projects_file)
        project_id = project_data.get("name", "unnamed")
        
        projects[project_id] = {
            **project_data,
            "timestamp": datetime.now().isoformat()
        }
        self._save_json(self.projects_file, projects)
        logger.debug(f"Project recorded: {project_id}")

    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get list of past projects.
        
        Returns:
            List of project records
        """
        projects = self._load_json(self.projects_file)
        return list(projects.values())

    def clear_short_term(self):
        """Clear all short-term memory."""
        self._save_json(self.short_term_file, {})
        logger.info("Short-term memory cleared")

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file safely."""
        try:
            content = file_path.read_text()
            return json.loads(content) if content else {}
        except Exception as e:
            logger.warning(f"Error loading {file_path}: {e}")
            return {}

    def _save_json(self, file_path: Path, data: Dict[str, Any]):
        """Save JSON file safely."""
        try:
            file_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error("json_save_error", f"Error saving {file_path}: {e}")
