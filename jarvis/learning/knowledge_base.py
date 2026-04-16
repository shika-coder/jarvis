"""
Knowledge base for storing and retrieving improvement patterns.

Maintains a persistent store of what works and what doesn't.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from jarvis.core.logging import get_logger


@dataclass
class KnowledgeEntry:
    """A single knowledge entry."""
    key: str  # Unique identifier
    category: str  # Type of knowledge (pattern, heuristic, rule, etc.)
    title: str
    description: str
    data: Dict[str, Any]
    confidence: float = 0.5  # 0-1 confidence score
    times_used: int = 0
    times_successful: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.times_used == 0:
            return 0.0
        return self.times_successful / self.times_used

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class KnowledgeBase:
    """Stores and retrieves knowledge about improvements."""

    def __init__(self, storage_path: Path = None):
        """Initialize knowledge base.
        
        Args:
            storage_path: Path to store knowledge entries
        """
        self.storage_path = storage_path or Path("knowledge_base.json")
        self.logger = get_logger(__name__)
        self.entries: Dict[str, KnowledgeEntry] = {}
        
        self._load()

    def add(self, entry: KnowledgeEntry) -> bool:
        """Add a knowledge entry.
        
        Args:
            entry: Knowledge entry to add
            
        Returns:
            True if successful
        """
        try:
            self.entries[entry.key] = entry
            self._save()
            self.logger.info(f"Added knowledge: {entry.key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add knowledge: {e}")
            return False

    def get(self, key: str) -> Optional[KnowledgeEntry]:
        """Retrieve a knowledge entry.
        
        Args:
            key: Entry identifier
            
        Returns:
            Knowledge entry or None
        """
        return self.entries.get(key)

    def query(self, category: str = None, min_confidence: float = 0.0) -> List[KnowledgeEntry]:
        """Query knowledge entries.
        
        Args:
            category: Filter by category
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of matching entries, sorted by confidence
        """
        results = [
            entry for entry in self.entries.values()
            if (category is None or entry.category == category)
            and entry.confidence >= min_confidence
        ]
        # Sort by confidence (descending) then by success rate
        results.sort(key=lambda e: (e.confidence, e.success_rate()), reverse=True)
        return results

    def update_success(self, key: str, success: bool) -> bool:
        """Update success count for an entry.
        
        Args:
            key: Entry identifier
            success: Whether the usage was successful
            
        Returns:
            True if successful
        """
        entry = self.entries.get(key)
        if not entry:
            return False

        try:
            entry.times_used += 1
            if success:
                entry.times_successful += 1
            entry.updated_at = datetime.now().isoformat()

            # Update confidence based on success rate
            entry.confidence = min(1.0, entry.success_rate() * 1.1)

            self._save()
            return True
        except Exception as e:
            self.logger.error(f"Failed to update success: {e}")
            return False

    def remove(self, key: str) -> bool:
        """Remove a knowledge entry.
        
        Args:
            key: Entry identifier
            
        Returns:
            True if successful
        """
        if key in self.entries:
            del self.entries[key]
            self._save()
            self.logger.info(f"Removed knowledge: {key}")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base.
        
        Returns:
            Dictionary with statistics
        """
        if not self.entries:
            return {'total_entries': 0}

        categories = {}
        total_uses = 0
        total_successes = 0

        for entry in self.entries.values():
            if entry.category not in categories:
                categories[entry.category] = {
                    'count': 0,
                    'avg_confidence': 0.0,
                    'total_uses': 0,
                    'total_successes': 0,
                }

            cat_stats = categories[entry.category]
            cat_stats['count'] += 1
            cat_stats['total_uses'] += entry.times_used
            cat_stats['total_successes'] += entry.times_successful

            total_uses += entry.times_used
            total_successes += entry.times_successful

        # Calculate averages
        for cat_stats in categories.values():
            if cat_stats['count'] > 0:
                cat_stats['avg_confidence'] = 0.5  # Would need to recalculate

        return {
            'total_entries': len(self.entries),
            'total_uses': total_uses,
            'total_successes': total_successes,
            'overall_success_rate': total_successes / total_uses if total_uses > 0 else 0.0,
            'by_category': categories,
        }

    def export(self) -> Dict[str, Any]:
        """Export all knowledge.
        
        Returns:
            Dictionary of all entries
        """
        return {
            'entries': {k: v.to_dict() for k, v in self.entries.items()},
            'stats': self.get_stats(),
            'exported_at': datetime.now().isoformat(),
        }

    def import_entries(self, data: Dict[str, Any]) -> bool:
        """Import knowledge entries.
        
        Args:
            data: Dictionary of entries to import
            
        Returns:
            True if successful
        """
        try:
            for key, entry_dict in data.items():
                entry = KnowledgeEntry(**entry_dict)
                self.entries[key] = entry

            self._save()
            self.logger.info(f"Imported {len(data)} entries")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import entries: {e}")
            return False

    def _save(self) -> None:
        """Save knowledge base to disk."""
        try:
            data = {
                key: entry.to_dict()
                for key, entry in self.entries.items()
            }
            self.storage_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save knowledge base: {e}")

    def _load(self) -> None:
        """Load knowledge base from disk."""
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text())
                for key, entry_dict in data.items():
                    self.entries[key] = KnowledgeEntry(**entry_dict)

                self.logger.info(f"Loaded {len(self.entries)} knowledge entries")
        except Exception as e:
            self.logger.error(f"Failed to load knowledge base: {e}")

    def clear_low_confidence(self, threshold: float = 0.3) -> int:
        """Remove low confidence entries.
        
        Args:
            threshold: Confidence threshold
            
        Returns:
            Number of entries removed
        """
        to_remove = [
            key for key, entry in self.entries.items()
            if entry.confidence < threshold
        ]

        for key in to_remove:
            del self.entries[key]

        if to_remove:
            self._save()
            self.logger.info(f"Removed {len(to_remove)} low-confidence entries")

        return len(to_remove)
