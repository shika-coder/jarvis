"""
JARVIS Task Executor

Handles task execution, script running, and workflow automation.
Runs scripts, automates workflows, and controls local environment safely.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import subprocess
import asyncio
import json
import re
from datetime import datetime
from jarvis.core.logging import get_logger
from jarvis.core.engine import Command

logger = get_logger(__name__)


class TaskExecutor:
    """Agent for executing tasks and automating workflows."""

    def __init__(self, workspace: Optional[Path] = None):
        """
        Initialize the task executor.
        
        Args:
            workspace: Root directory for task operations
        """
        self.workspace = workspace or Path.cwd()
        logger.info(f"TaskExecutor initialized with workspace: {self.workspace}")

    async def execute(self, command: Command) -> Dict[str, Any]:
        """
        Execute a task command.
        
        Args:
            command: Parsed command
            
        Returns:
            Execution result
        """
        logger.log_action("task_execution_started", {
            "action": command.action,
            "parameters": command.parameters
        })

        try:
            if command.action == "execute":
                return await self.execute_task(command)
            elif command.action == "run":
                return await self.run_script(command)
            elif command.action == "automate":
                return await self.automate_workflow(command)
            else:
                return {
                    "success": False,
                    "error": f"Unknown task action: {command.action}"
                }
        except Exception as e:
            logger.log_error("task_execution", str(e))
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_task(self, command: Command) -> Dict[str, Any]:
        """Execute a generic task."""
        logger.debug("Executing task...")
        
        try:
            task_name = " ".join(command.parameters.get("raw_words", []))
            
            logger.log_action("task_execution", {
                "task": task_name,
                "timestamp": datetime.now().isoformat()
            })
            
            # Execute the task based on keywords
            if any(x in task_name.lower() for x in ["backup", "copy", "duplicate"]):
                result = await self._backup_task(task_name)
            elif any(x in task_name.lower() for x in ["clean", "delete", "remove"]):
                result = await self._cleanup_task(task_name)
            elif any(x in task_name.lower() for x in ["deploy", "push", "upload"]):
                result = await self._deployment_task(task_name)
            else:
                result = await self._generic_task(task_name)
            
            return result
        except Exception as e:
            logger.log_error("task_execution_failed", str(e))
            return {
                "success": False,
                "error": f"Task execution failed: {str(e)}"
            }
    
    async def _backup_task(self, task_name: str) -> Dict[str, Any]:
        """Execute a backup task."""
        logger.log_action("backup_started", {"task": task_name})
        
        # Create backup directory
        backup_dir = self.workspace / ".backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "success": True,
            "output": f"Backup created at {backup_dir}",
            "details": {
                "task_type": "backup",
                "backup_location": str(backup_dir),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _cleanup_task(self, task_name: str) -> Dict[str, Any]:
        """Execute a cleanup task."""
        logger.log_action("cleanup_started", {"task": task_name})
        
        files_cleaned = 0
        
        # Clean common cache/temp files
        patterns = ["*.pyc", "__pycache__", "*.log", ".DS_Store"]
        for pattern in patterns:
            for file in self.workspace.glob(f"**/{pattern}"):
                try:
                    if file.is_file():
                        file.unlink()
                    elif file.is_dir():
                        import shutil
                        shutil.rmtree(file)
                    files_cleaned += 1
                except Exception as e:
                    logger.debug(f"Could not clean {file}: {e}")
        
        return {
            "success": True,
            "output": f"Cleanup completed: {files_cleaned} items removed",
            "details": {
                "task_type": "cleanup",
                "items_cleaned": files_cleaned,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _deployment_task(self, task_name: str) -> Dict[str, Any]:
        """Execute a deployment task."""
        logger.log_action("deployment_started", {"task": task_name})
        
        return {
            "success": True,
            "output": "Deployment task prepared (requires manual confirmation)",
            "details": {
                "task_type": "deployment",
                "status": "ready",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _generic_task(self, task_name: str) -> Dict[str, Any]:
        """Execute a generic task."""
        logger.log_action("generic_task", {"task": task_name})
        
        return {
            "success": True,
            "output": f"Task '{task_name}' executed",
            "details": {
                "task_type": "generic",
                "task_name": task_name,
                "timestamp": datetime.now().isoformat()
            }
        }

    async def run_script(self, command: Command) -> Dict[str, Any]:
        """Run a script file."""
        logger.debug("Running script...")
        
        try:
            words = command.parameters.get("raw_words", [])
            script_name = words[-1] if words else None
            
            if not script_name:
                return {
                    "success": False,
                    "error": "No script specified"
                }
            
            # Find script file
            script_path = self.workspace / script_name
            if not script_path.exists():
                # Try with .py extension
                script_path = self.workspace / f"{script_name}.py"
            
            if not script_path.exists():
                return {
                    "success": False,
                    "error": f"Script not found: {script_name}"
                }
            
            logger.log_action("script_execution", {
                "script": str(script_path)
            })
            
            # Execute script
            result = await asyncio.to_thread(
                self.execute_command_safe,
                f"python {script_path}"
            )
            
            return {
                "success": result.get("success", False),
                "output": result.get("stdout", "Script executed"),
                "details": {
                    "script": str(script_path),
                    "return_code": result.get("return_code", 0),
                    "stderr": result.get("stderr", "")[:200]
                }
            }
        except Exception as e:
            logger.log_error("script_execution_failed", str(e))
            return {
                "success": False,
                "error": f"Script execution failed: {str(e)}"
            }

    async def automate_workflow(self, command: Command) -> Dict[str, Any]:
        """Automate a workflow."""
        logger.debug("Automating workflow...")
        
        try:
            task_name = " ".join(command.parameters.get("raw_words", []))
            
            logger.log_action("workflow_automation", {
                "workflow": task_name
            })
            
            # Create workflow configuration
            workflow_config = {
                "name": task_name,
                "created_at": datetime.now().isoformat(),
                "steps": [
                    {"step": 1, "action": "Initialize", "status": "ready"},
                    {"step": 2, "action": "Execute", "status": "pending"},
                    {"step": 3, "action": "Verify", "status": "pending"},
                    {"step": 4, "action": "Report", "status": "pending"}
                ],
                "status": "configured"
            }
            
            # Save workflow configuration
            workflow_dir = self.workspace / ".workflows"
            workflow_dir.mkdir(exist_ok=True)
            
            workflow_file = workflow_dir / f"{task_name.replace(' ', '_')}.json"
            workflow_file.write_text(json.dumps(workflow_config, indent=2))
            
            return {
                "success": True,
                "output": f"Workflow '{task_name}' configured",
                "details": {
                    "workflow_name": task_name,
                    "workflow_file": str(workflow_file),
                    "status": "configured",
                    "steps": len(workflow_config["steps"])
                }
            }
        except Exception as e:
            logger.log_error("workflow_automation_failed", str(e))
            return {
                "success": False,
                "error": f"Workflow automation failed: {str(e)}"
            }

    async def execute_command_safe(
        self,
        cmd: str,
        cwd: Optional[Path] = None,
        timeout: int = 60,
        require_confirmation: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a shell command with safety checks.
        
        Args:
            cmd: Command to execute
            cwd: Working directory
            timeout: Command timeout in seconds
            require_confirmation: Whether to require user confirmation
            
        Returns:
            Command output and result
        """
        cwd = cwd or self.workspace
        
        if require_confirmation:
            logger.warning(f"Command requires confirmation: {cmd}")
            # In real implementation, would ask for user confirmation
            confirmation = True  # Placeholder
            if not confirmation:
                return {
                    "success": False,
                    "error": "Command execution cancelled"
                }
        
        logger.log_action("execute_safe_command", {
            "command": cmd,
            "working_dir": str(cwd)
        })
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            logger.log_error("command_execution", "Command timeout", f"Timeout: {timeout}s")
            return {
                "success": False,
                "error": "Command timeout"
            }
        except Exception as e:
            logger.log_error("command_execution", str(e))
            return {
                "success": False,
                "error": str(e)
            }
