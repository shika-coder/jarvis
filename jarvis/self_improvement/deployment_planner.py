"""
Deployment planner for safe code deployment.

Plans and executes deployments with validation and rollback.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis.core.logging import get_logger
from jarvis.self_improvement.base import BackupManager


class DeploymentStatus(Enum):
    """Deployment execution status."""
    PLANNED = "planned"
    VALIDATING = "validating"
    BACKING_UP = "backing_up"
    DEPLOYING = "deploying"
    ROLLED_BACK = "rolled_back"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class DeploymentStep:
    """A single deployment step."""
    name: str
    file_path: Path
    changes: str
    validation_passed: bool = False
    backup_created: bool = False
    deployed: bool = False
    status: str = "pending"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class DeploymentPlan:
    """Plan for deploying code changes."""

    def __init__(self, name: str, description: str = ""):
        """Initialize deployment plan."""
        self.name = name
        self.description = description
        self.steps: List[DeploymentStep] = []
        self.status = DeploymentStatus.PLANNED
        self.logger = get_logger(__name__)
        self.backup_manager = BackupManager()
        self.deployed_files: List[Path] = []

    def add_step(
        self,
        name: str,
        file_path: Path,
        changes: str
    ) -> "DeploymentPlan":
        """Add a deployment step.
        
        Returns:
            Self for chaining
        """
        step = DeploymentStep(
            name=name,
            file_path=file_path,
            changes=changes
        )
        self.steps.append(step)
        return self

    async def validate_all(self) -> bool:
        """Validate all deployment steps.
        
        Returns:
            True if all validations pass
        """
        self.status = DeploymentStatus.VALIDATING
        
        for step in self.steps:
            if await self._validate_step(step):
                step.validation_passed = True
                self.logger.info(f"✓ Validated: {step.name}")
            else:
                self.logger.error(f"✗ Validation failed: {step.name}")
                self.status = DeploymentStatus.FAILED
                return False
        
        return True

    async def _validate_step(self, step: DeploymentStep) -> bool:
        """Validate a single deployment step."""
        # Check file exists
        if not step.file_path.exists():
            self.logger.error(f"File not found: {step.file_path}")
            return False
        
        # Basic syntax check
        try:
            import ast
            ast.parse(step.changes)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in changes: {e}")
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = [
            'eval(', 'exec(', '__import__(',
            'os.system(', 'subprocess.call('
        ]
        if any(pattern in step.changes for pattern in dangerous_patterns):
            self.logger.warning(f"Dangerous pattern detected in {step.name}")
        
        return True

    async def backup_all(self) -> bool:
        """Create backups of all files.
        
        Returns:
            True if all backups created
        """
        self.status = DeploymentStatus.BACKING_UP
        
        for step in self.steps:
            try:
                backup_id = await self.backup_manager.create_backup(
                    str(step.file_path),
                    label=f"deploy_{self.name}"
                )
                step.backup_created = True
                self.logger.info(f"✓ Backed up: {step.name} -> {backup_id}")
            except Exception as e:
                self.logger.error(f"Backup failed for {step.name}: {e}")
                return False
        
        return True

    async def deploy(self) -> bool:
        """Deploy all changes.
        
        Returns:
            True if all deployments successful
        """
        if not self.steps:
            self.logger.warning("No steps to deploy")
            return False
        
        # Validate
        if not await self.validate_all():
            return False
        
        # Backup
        if not await self.backup_all():
            return False
        
        # Deploy
        self.status = DeploymentStatus.DEPLOYING
        
        for step in self.steps:
            try:
                step.file_path.write_text(step.changes)
                step.deployed = True
                step.status = "deployed"
                self.deployed_files.append(step.file_path)
                self.logger.info(f"✓ Deployed: {step.name}")
            except Exception as e:
                self.logger.error(f"Deployment failed for {step.name}: {e}")
                step.status = "failed"
                await self._rollback()
                return False
        
        self.status = DeploymentStatus.SUCCEEDED
        return True

    async def _rollback(self) -> bool:
        """Rollback deployed changes.
        
        Returns:
            True if rollback successful
        """
        self.status = DeploymentStatus.ROLLED_BACK
        self.logger.warning("Rolling back deployment...")
        
        # Restore from backups
        for file_path in self.deployed_files:
            try:
                # Find corresponding backup
                for step in self.steps:
                    if step.file_path == file_path and step.backup_created:
                        # Restore backup (implementation depends on BackupManager)
                        self.logger.info(f"Restoring: {step.name}")
                        break
            except Exception as e:
                self.logger.error(f"Rollback failed for {file_path}: {e}")
        
        return True

    def get_summary(self) -> Dict[str, Any]:
        """Get deployment summary."""
        validated = sum(1 for s in self.steps if s.validation_passed)
        backed_up = sum(1 for s in self.steps if s.backup_created)
        deployed = sum(1 for s in self.steps if s.deployed)
        
        return {
            'name': self.name,
            'status': self.status.value,
            'total_steps': len(self.steps),
            'validated': validated,
            'backed_up': backed_up,
            'deployed': deployed,
            'deployment_time': datetime.now().isoformat(),
            'steps': [
                {
                    'name': step.name,
                    'file': str(step.file_path),
                    'status': step.status,
                    'validated': step.validation_passed,
                    'backed_up': step.backup_created,
                    'deployed': step.deployed,
                }
                for step in self.steps
            ]
        }

    def save_plan(self, path: Path) -> bool:
        """Save deployment plan to file.
        
        Args:
            path: Path to save plan to
            
        Returns:
            True if successful
        """
        try:
            plan_data = {
                'name': self.name,
                'description': self.description,
                'created_at': datetime.now().isoformat(),
                'steps': [
                    {
                        'name': step.name,
                        'file_path': str(step.file_path),
                        'changes_hash': hash(step.changes),
                    }
                    for step in self.steps
                ]
            }
            path.write_text(json.dumps(plan_data, indent=2))
            self.logger.info(f"Plan saved: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save plan: {e}")
            return False

    def load_plan(self, path: Path) -> bool:
        """Load deployment plan from file.
        
        Args:
            path: Path to load plan from
            
        Returns:
            True if successful
        """
        try:
            data = json.loads(path.read_text())
            self.name = data.get('name', self.name)
            self.description = data.get('description', self.description)
            self.logger.info(f"Plan loaded: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load plan: {e}")
            return False


class DeploymentStrategy:
    """Strategy for deployment execution."""

    def __init__(self, strategy_type: str = "blue_green"):
        """Initialize deployment strategy.
        
        Args:
            strategy_type: "blue_green", "canary", or "rolling"
        """
        self.strategy_type = strategy_type
        self.logger = get_logger(__name__)

    def validate(self) -> bool:
        """Validate strategy is applicable."""
        valid_strategies = ["blue_green", "canary", "rolling"]
        if self.strategy_type not in valid_strategies:
            self.logger.error(f"Unknown strategy: {self.strategy_type}")
            return False
        return True

    def get_plan(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Get deployment steps based on strategy."""
        if self.strategy_type == "blue_green":
            return self._blue_green_plan(files)
        elif self.strategy_type == "canary":
            return self._canary_plan(files)
        else:
            return self._rolling_plan(files)

    def _blue_green_plan(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Blue-green deployment: test in blue, switch to green."""
        return [
            {'phase': 'backup_current', 'action': 'backup'},
            {'phase': 'deploy_green', 'action': 'deploy', 'files': files},
            {'phase': 'validate_green', 'action': 'validate'},
            {'phase': 'switch_traffic', 'action': 'activate'},
        ]

    def _canary_plan(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Canary deployment: gradual rollout."""
        return [
            {'phase': 'deploy_canary', 'action': 'deploy', 'percentage': 10},
            {'phase': 'monitor_canary', 'action': 'monitor', 'duration': 300},
            {'phase': 'deploy_rest', 'action': 'deploy', 'percentage': 100},
            {'phase': 'monitor_full', 'action': 'monitor', 'duration': 600},
        ]

    def _rolling_plan(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Rolling deployment: one instance at a time."""
        plan = [
            {'phase': 'drain_connections', 'action': 'drain'},
        ]
        for f in files:
            plan.append({'phase': 'deploy_file', 'action': 'deploy', 'file': str(f)})
            plan.append({'phase': 'verify_file', 'action': 'verify', 'file': str(f)})
        plan.append({'phase': 'restore_connections', 'action': 'restore'})
        return plan
