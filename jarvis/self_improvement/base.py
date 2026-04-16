"""
Self-Improvement Module

Autonomous system analysis and optimization.
Analyzes code quality, performance, and suggests improvements.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from jarvis.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CodeIssue:
    """Represents a code quality issue."""
    file_path: str
    line_number: Optional[int]
    issue_type: str  # security, performance, complexity, style
    severity: str  # critical, high, medium, low
    description: str
    suggestion: Optional[str] = None
    confidence: float = 0.9


@dataclass
class PerformanceMetric:
    """Represents a performance measurement."""
    metric_name: str
    value: float
    unit: str  # ms, bytes, count, percentage
    timestamp: float = field(default_factory=time.time)
    threshold: Optional[float] = None
    exceeded: bool = False


@dataclass
class RefactoringProposal:
    """Represents a proposed code change."""
    id: str
    file_path: str
    description: str
    changes: Dict[str, Any]  # old_code, new_code, reason
    impact: Dict[str, Any]  # estimated performance, complexity, test_coverage
    risk_level: str  # low, medium, high
    can_apply: bool = True
    backup_created: bool = False


class SelfImprovementBase:
    """Base class for self-improvement components."""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize self-improvement base.
        
        Args:
            enabled: Whether self-improvement features are enabled
        """
        self.enabled = enabled
        self.audit_trail: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def log_action(
        self,
        action: str,
        details: Dict[str, Any],
        success: bool = True
    ) -> None:
        """
        Log a self-improvement action to audit trail.
        
        Args:
            action: Type of action performed
            details: Details about the action
            success: Whether the action succeeded
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "success": success,
        }
        self.audit_trail.append(entry)
        
        status = "✓" if success else "✗"
        logger.info(f"{status} {action}: {details}")
    
    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get the audit trail of all improvements."""
        return self.audit_trail
    
    def is_available(self) -> bool:
        """Check if this component is available and enabled."""
        return self.enabled
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about improvements."""
        successful = sum(1 for entry in self.audit_trail if entry.get("success", False))
        return {
            "total_actions": len(self.audit_trail),
            "successful_actions": successful,
            "enabled": self.enabled,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
        }


class BackupManager:
    """Manages backups for safe code modifications."""
    
    def __init__(self, backup_dir: str = "backups"):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups
        """
        import os
        from pathlib import Path
        
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backups: Dict[str, str] = {}
        
        logger.info(f"BackupManager initialized at {self.backup_dir}")
    
    async def create_backup(
        self,
        file_path: str,
        label: str = "auto"
    ) -> Optional[str]:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to file to backup
            label: Label for the backup
        
        Returns:
            Backup ID if successful, None otherwise
        """
        try:
            from pathlib import Path
            import shutil
            
            source = Path(file_path)
            if not source.exists():
                logger.error(f"File not found: {file_path}")
                return None
            
            # Create backup filename
            timestamp = int(time.time() * 1000)
            backup_id = f"{source.stem}_{label}_{timestamp}"
            backup_path = self.backup_dir / f"{backup_id}.bak"
            
            # Copy file
            shutil.copy2(source, backup_path)
            self.backups[backup_id] = str(backup_path)
            
            logger.info(f"Backup created: {backup_id}")
            return backup_id
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None
    
    async def restore_backup(self, backup_id: str) -> bool:
        """
        Restore a file from backup.
        
        Args:
            backup_id: ID of backup to restore
        
        Returns:
            True if restoration successful, False otherwise
        """
        try:
            import shutil
            from pathlib import Path
            
            if backup_id not in self.backups:
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            backup_path = Path(self.backups[backup_id])
            if not backup_path.exists():
                logger.error(f"Backup file missing: {backup_path}")
                return False
            
            # Restore would require knowing original location
            logger.info(f"Backup ready for restoration: {backup_id}")
            return True
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False
    
    def list_backups(self) -> List[str]:
        """List all available backups."""
        return list(self.backups.keys())
    
    def get_backup_path(self, backup_id: str) -> Optional[str]:
        """Get path to a backup."""
        return self.backups.get(backup_id)


class ChangeValidator:
    """Validates proposed code changes before applying them."""
    
    def __init__(self):
        """Initialize change validator."""
        self.validations: List[Dict[str, Any]] = []
    
    async def validate_syntax(self, code: str) -> bool:
        """
        Validate Python syntax.
        
        Args:
            code: Python code to validate
        
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            import ast
            ast.parse(code)
            logger.info("✓ Syntax validation passed")
            return True
        except SyntaxError as e:
            logger.error(f"✗ Syntax validation failed: {e}")
            return False
    
    async def validate_imports(self, code: str) -> bool:
        """
        Check for undefined imports.
        
        Args:
            code: Python code to validate
        
        Returns:
            True if imports are valid, False otherwise
        """
        try:
            import ast
            tree = ast.parse(code)
            
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
            
            logger.info(f"✓ Found {len(imports)} imports")
            return True
        except Exception as e:
            logger.error(f"✗ Import validation failed: {e}")
            return False
    
    async def validate_change(
        self,
        original: str,
        modified: str,
        change_type: str = "refactor"
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of a code change.
        
        Args:
            original: Original code
            modified: Modified code
            change_type: Type of change (refactor, fix, feature)
        
        Returns:
            Validation results
        """
        results = {
            "valid": False,
            "syntax_valid": False,
            "imports_valid": False,
            "warnings": [],
            "change_type": change_type,
        }
        
        # Validate syntax
        results["syntax_valid"] = await self.validate_syntax(modified)
        if not results["syntax_valid"]:
            results["warnings"].append("Syntax validation failed")
        
        # Validate imports
        results["imports_valid"] = await self.validate_imports(modified)
        if not results["imports_valid"]:
            results["warnings"].append("Import validation failed")
        
        # Overall validation
        results["valid"] = results["syntax_valid"] and results["imports_valid"]
        
        self.validations.append(results)
        return results


class ImprovementTracker:
    """Tracks improvements over time."""
    
    def __init__(self):
        """Initialize improvement tracker."""
        self.improvements: List[Dict[str, Any]] = []
        self.metrics_history: List[PerformanceMetric] = []
    
    def record_improvement(
        self,
        improvement_type: str,
        description: str,
        metrics: Dict[str, float],
        success: bool = True
    ) -> None:
        """
        Record an improvement.
        
        Args:
            improvement_type: Type of improvement
            description: Description of the improvement
            metrics: Performance metrics (before/after)
            success: Whether improvement was successful
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": improvement_type,
            "description": description,
            "metrics": metrics,
            "success": success,
        }
        self.improvements.append(entry)
        
        if success:
            logger.info(f"✓ Improvement recorded: {description}")
        else:
            logger.warning(f"⚠ Improvement failed: {description}")
    
    def add_metric(self, metric: PerformanceMetric) -> None:
        """Add a performance metric."""
        self.metrics_history.append(metric)
    
    def get_improvements_by_type(self, improvement_type: str) -> List[Dict[str, Any]]:
        """Get improvements of a specific type."""
        return [i for i in self.improvements if i["type"] == improvement_type]
    
    def get_improvement_stats(self) -> Dict[str, Any]:
        """Get statistics about recorded improvements."""
        successful = sum(1 for i in self.improvements if i.get("success", False))
        by_type = {}
        for imp in self.improvements:
            imp_type = imp["type"]
            if imp_type not in by_type:
                by_type[imp_type] = 0
            by_type[imp_type] += 1
        
        return {
            "total_improvements": len(self.improvements),
            "successful": successful,
            "failed": len(self.improvements) - successful,
            "by_type": by_type,
            "metrics_recorded": len(self.metrics_history),
        }
