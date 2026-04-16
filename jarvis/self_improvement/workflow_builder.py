"""
Advanced workflow builder for complex automation pipelines.

Enables chaining multiple operations together with conditional logic.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, List, Optional, Dict

from jarvis.core.logging import get_logger


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepCondition(Enum):
    """Conditions for step execution."""
    ALWAYS = "always"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    CUSTOM = "custom"


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    name: str
    action: Callable
    description: str = ""
    condition: StepCondition = StepCondition.ON_SUCCESS
    condition_func: Optional[Callable] = None
    retry_count: int = 0
    timeout_seconds: Optional[int] = None
    required: bool = True
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Any = None
    error: Optional[str] = None

    async def execute(self, context: Dict[str, Any]) -> bool:
        """Execute this step.
        
        Args:
            context: Shared context dict with previous results
            
        Returns:
            True if successful
        """
        self.status = WorkflowStatus.RUNNING
        
        try:
            # Call action (may be sync or async)
            if asyncio.iscoroutinefunction(self.action):
                self.result = await self.action(context)
            else:
                self.result = self.action(context)
            
            self.status = WorkflowStatus.SUCCEEDED
            return True
        
        except Exception as e:
            self.error = str(e)
            self.status = WorkflowStatus.FAILED
            return False


@dataclass
class Workflow:
    """A workflow is a sequence of steps with conditional execution."""
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    logger: Any = field(default_factory=lambda: get_logger(__name__))
    execution_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_step(
        self,
        name: str,
        action: Callable,
        description: str = "",
        condition: StepCondition = StepCondition.ON_SUCCESS,
        condition_func: Optional[Callable] = None,
        retry_count: int = 0,
        timeout_seconds: Optional[int] = None,
        required: bool = True
    ) -> "Workflow":
        """Add a step to the workflow.
        
        Returns:
            Self for chaining
        """
        step = WorkflowStep(
            name=name,
            action=action,
            description=description,
            condition=condition,
            condition_func=condition_func,
            retry_count=retry_count,
            timeout_seconds=timeout_seconds,
            required=required
        )
        self.steps.append(step)
        return self

    async def execute(self) -> bool:
        """Execute the workflow.
        
        Returns:
            True if all required steps succeeded
        """
        self.status = WorkflowStatus.RUNNING
        self.context = {}
        
        for step in self.steps:
            # Check conditions
            should_run = self._should_run_step(step)
            
            if not should_run:
                step.status = WorkflowStatus.SKIPPED
                self.logger.debug(f"Skipped: {step.name}")
                continue
            
            # Execute with retries
            success = False
            for attempt in range(step.retry_count + 1):
                try:
                    if step.timeout_seconds:
                        result = await asyncio.wait_for(
                            step.execute(self.context),
                            timeout=step.timeout_seconds
                        )
                        success = result
                    else:
                        success = await step.execute(self.context)
                    
                    if success:
                        break
                except asyncio.TimeoutError:
                    step.error = f"Timeout after {step.timeout_seconds}s"
                    if attempt < step.retry_count:
                        self.logger.warning(f"Retry {attempt+1}/{step.retry_count}: {step.name}")
                
                # Store result in context
                if step.result is not None:
                    self.context[step.name] = step.result
            
            # Log result
            if success:
                self.logger.info(f"✓ {step.name}")
            else:
                self.logger.error(f"✗ {step.name}: {step.error}")
                if step.required:
                    self.status = WorkflowStatus.FAILED
                    return False
        
        self.status = WorkflowStatus.SUCCEEDED
        return True

    def _should_run_step(self, step: WorkflowStep) -> bool:
        """Determine if a step should run."""
        if step.condition == StepCondition.ALWAYS:
            return True
        
        if step.condition == StepCondition.ON_SUCCESS:
            # Check if previous steps succeeded
            prev_success = all(
                s.status == WorkflowStatus.SUCCEEDED 
                for s in self.steps[:self.steps.index(step)]
                if s.status != WorkflowStatus.SKIPPED
            )
            return prev_success
        
        if step.condition == StepCondition.ON_FAILURE:
            # Check if any previous required step failed
            prev_failed = any(
                s.status == WorkflowStatus.FAILED 
                for s in self.steps[:self.steps.index(step)]
                if s.required
            )
            return prev_failed
        
        if step.condition == StepCondition.CUSTOM:
            if step.condition_func:
                return step.condition_func(self.context)
            return True
        
        return True

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of workflow execution."""
        succeeded = sum(1 for s in self.steps if s.status == WorkflowStatus.SUCCEEDED)
        failed = sum(1 for s in self.steps if s.status == WorkflowStatus.FAILED)
        skipped = sum(1 for s in self.steps if s.status == WorkflowStatus.SKIPPED)
        
        return {
            'name': self.name,
            'status': self.status.value,
            'total_steps': len(self.steps),
            'succeeded': succeeded,
            'failed': failed,
            'skipped': skipped,
            'results': {
                step.name: {
                    'status': step.status.value,
                    'result': step.result,
                    'error': step.error
                }
                for step in self.steps
            }
        }

    def get_results(self) -> Dict[str, Any]:
        """Get results from all steps."""
        return {
            step.name: step.result
            for step in self.steps
            if step.result is not None
        }


class WorkflowBuilder:
    """Fluent builder for creating workflows."""

    def __init__(self, name: str, description: str = ""):
        """Initialize workflow builder."""
        self.workflow = Workflow(name=name, description=description)

    def add(
        self,
        name: str,
        action: Callable,
        description: str = "",
        **kwargs
    ) -> "WorkflowBuilder":
        """Add a step to the workflow."""
        self.workflow.add_step(name, action, description, **kwargs)
        return self

    def build(self) -> Workflow:
        """Build and return the workflow."""
        return self.workflow

    async def execute(self) -> bool:
        """Build and execute the workflow."""
        return await self.workflow.execute()


class WorkflowComposer:
    """Compose multiple workflows together."""

    def __init__(self):
        """Initialize composer."""
        self.workflows: Dict[str, Workflow] = {}
        self.logger = get_logger(__name__)

    def add_workflow(self, name: str, workflow: Workflow) -> "WorkflowComposer":
        """Add a workflow to compose."""
        self.workflows[name] = workflow
        return self

    async def execute_sequential(self) -> bool:
        """Execute workflows sequentially.
        
        Returns:
            True if all workflows succeeded
        """
        for name, workflow in self.workflows.items():
            self.logger.info(f"Executing workflow: {name}")
            success = await workflow.execute()
            if not success:
                self.logger.error(f"Workflow {name} failed")
                return False
        
        return True

    async def execute_parallel(self, max_concurrent: int = 3) -> Dict[str, bool]:
        """Execute workflows in parallel.
        
        Args:
            max_concurrent: Maximum workflows to run concurrently
            
        Returns:
            Dict mapping workflow names to success status
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_limit(name: str, workflow: Workflow) -> tuple:
            async with semaphore:
                success = await workflow.execute()
                return name, success
        
        tasks = [
            run_with_limit(name, workflow)
            for name, workflow in self.workflows.items()
        ]
        
        results = await asyncio.gather(*tasks)
        return {name: success for name, success in results}

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all workflows."""
        return {
            name: workflow.get_summary()
            for name, workflow in self.workflows.items()
        }
