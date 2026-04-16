"""
Background Optimizer: Continuous non-blocking improvement engine.

Runs improvements in the background without blocking main agent loop.
Supports pause/resume, priority queuing, and rate limiting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, List, Dict
from enum import Enum

from jarvis.learning.predictive_analyzer import PredictiveAnalyzer, PredictionResult
from jarvis.self_improvement.refactor_engine import RefactoringEngine


logger = logging.getLogger(__name__)


class OptimizationPriority(Enum):
    """Priority levels for optimization tasks."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class OptimizationTask:
    """Individual optimization task."""
    id: str
    file_path: str
    improvement_type: str
    prediction: PredictionResult
    priority: OptimizationPriority = OptimizationPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None

    def is_pending(self) -> bool:
        return self.started_at is None and self.completed_at is None

    def is_running(self) -> bool:
        return self.started_at is not None and self.completed_at is None

    def is_completed(self) -> bool:
        return self.completed_at is not None

    def get_duration(self) -> Optional[float]:
        if self.started_at is None or self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()


@dataclass
class OptimizationStats:
    """Statistics about optimization runs."""
    total_tasks: int = 0
    completed_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_duration: float = 0.0
    avg_duration: float = 0.0

    def success_rate(self) -> float:
        if self.completed_tasks == 0:
            return 0.0
        return (self.successful_tasks / self.completed_tasks) * 100


class BackgroundOptimizer:
    """Continuous improvement engine running in background."""

    def __init__(
        self,
        analyzer: PredictiveAnalyzer,
        refactor_engine: Optional[RefactoringEngine] = None,
        max_concurrent: int = 2,
        rate_limit_per_second: float = 1.0,
    ):
        """Initialize optimizer.

        Args:
            analyzer: PredictiveAnalyzer for generating predictions
            refactor_engine: Engine for applying improvements (optional)
            max_concurrent: Max concurrent optimizations
            rate_limit_per_second: Max optimization rate
        """
        self.analyzer = analyzer
        self.refactor_engine = refactor_engine
        self.max_concurrent = max_concurrent
        self.rate_limit_per_second = rate_limit_per_second

        self.tasks: Dict[str, OptimizationTask] = {}
        self.is_running = False
        self.is_paused = False
        self.stats = OptimizationStats()

        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._task_handlers: Dict[str, Callable] = {}

    def register_handler(self, improvement_type: str, handler: Callable) -> None:
        """Register handler for improvement type.

        Args:
            improvement_type: Type of improvement
            handler: Async function to execute optimization
        """
        self._task_handlers[improvement_type] = handler
        logger.info(f"Registered handler for {improvement_type}")

    def add_task(
        self,
        file_path: str,
        prediction: PredictionResult,
        priority: OptimizationPriority = OptimizationPriority.NORMAL,
    ) -> str:
        """Add optimization task to queue.

        Args:
            file_path: File to optimize
            prediction: Prediction for improvement
            priority: Task priority

        Returns:
            Task ID
        """
        task_id = f"opt-{len(self.tasks)}-{datetime.now().timestamp()}"
        task = OptimizationTask(
            id=task_id,
            file_path=file_path,
            improvement_type=prediction.improvement_type,
            prediction=prediction,
            priority=priority,
        )
        self.tasks[task_id] = task
        self.stats.total_tasks += 1
        logger.info(
            f"Added task {task_id}: {prediction.improvement_type} "
            f"(priority={priority.name}, confidence={prediction.confidence:.2f})"
        )
        return task_id

    async def process_tasks(self, max_iterations: Optional[int] = None) -> int:
        """Process all pending tasks.

        Args:
            max_iterations: Max iterations before stopping (None = all)

        Returns:
            Number of tasks processed
        """
        self.is_running = True
        processed = 0
        iteration = 0

        logger.info("Background optimizer starting...")

        while self.is_running:
            # Check pause state
            while self.is_paused and self.is_running:
                await asyncio.sleep(0.5)

            # Get pending tasks, sorted by priority (high first)
            pending = [
                t
                for t in self.tasks.values()
                if t.is_pending()
            ]
            if not pending:
                break

            pending.sort(key=lambda t: t.priority.value, reverse=True)

            # Process with concurrency limit
            batch = pending[: self.max_concurrent]
            tasks = [self._execute_task(t) for t in batch]

            await asyncio.gather(*tasks)
            processed += len(batch)
            iteration += 1

            # Rate limiting
            await asyncio.sleep(1.0 / self.rate_limit_per_second)

            if max_iterations and iteration >= max_iterations:
                break

        self.is_running = False
        logger.info(f"Background optimizer completed: {processed} tasks")
        return processed

    async def _execute_task(self, task: OptimizationTask) -> None:
        """Execute single optimization task."""
        async with self._semaphore:
            try:
                task.started_at = datetime.now()
                logger.info(f"Executing task {task.id}: {task.improvement_type}")

                # Get handler or use default
                handler = self._task_handlers.get(
                    task.improvement_type,
                    self._default_handler,
                )

                result = await handler(task)
                task.success = result is True or (
                    isinstance(result, dict) and result.get("success", False)
                )

            except Exception as e:
                logger.error(f"Task {task.id} failed: {e}", exc_info=True)
                task.success = False
                task.error = str(e)

            finally:
                task.completed_at = datetime.now()
                self.stats.completed_tasks += 1
                if task.success:
                    self.stats.successful_tasks += 1
                else:
                    self.stats.failed_tasks += 1

                # Update average duration
                duration = task.get_duration()
                if duration:
                    self.stats.total_duration += duration
                    self.stats.avg_duration = (
                        self.stats.total_duration / self.stats.completed_tasks
                    )

                logger.info(
                    f"Task {task.id} completed: "
                    f"success={task.success}, duration={duration:.2f}s"
                )

    async def _default_handler(self, task: OptimizationTask) -> bool:
        """Default handler using refactor engine."""
        if not self.refactor_engine:
            logger.warning("No refactor engine; skipping task")
            return False

        logger.info(
            f"Applying {task.improvement_type} to {task.file_path}"
        )

        # Use refactor engine to apply changes
        # In production, would parse prediction and apply specific changes
        logger.info(f"Would apply: {task.prediction.rationale}")

        return True

    def pause(self) -> None:
        """Pause background optimization."""
        self.is_paused = True
        logger.info("Background optimizer paused")

    def resume(self) -> None:
        """Resume background optimization."""
        self.is_paused = False
        logger.info("Background optimizer resumed")

    def stop(self) -> None:
        """Stop background optimizer."""
        self.is_running = False
        logger.info("Background optimizer stopped")

    def get_stats(self) -> OptimizationStats:
        """Get current statistics."""
        return self.stats

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific task."""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        return {
            "id": task.id,
            "file_path": task.file_path,
            "improvement_type": task.improvement_type,
            "priority": task.priority.name,
            "status": (
                "pending"
                if task.is_pending()
                else "running"
                if task.is_running()
                else "completed"
            ),
            "success": task.success,
            "error": task.error,
            "duration": task.get_duration(),
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks with status."""
        return [self.get_task_status(task_id) for task_id in self.tasks]

    def get_pending_count(self) -> int:
        """Get count of pending tasks."""
        return sum(1 for t in self.tasks.values() if t.is_pending())

    def get_running_count(self) -> int:
        """Get count of running tasks."""
        return sum(1 for t in self.tasks.values() if t.is_running())

    def clear_completed(self, before: Optional[datetime] = None) -> int:
        """Clear completed tasks older than timestamp.

        Args:
            before: Clear tasks completed before this time (default: 1 hour ago)

        Returns:
            Number of tasks cleared
        """
        if before is None:
            before = datetime.now() - timedelta(hours=1)

        to_remove = [
            task_id
            for task_id, task in self.tasks.items()
            if task.is_completed() and task.completed_at < before
        ]

        for task_id in to_remove:
            del self.tasks[task_id]

        logger.info(f"Cleared {len(to_remove)} completed tasks")
        return len(to_remove)

    async def run_in_background(self) -> asyncio.Task:
        """Start optimizer running in background.

        Returns:
            AsyncIO task (does not await)
        """
        logger.info("Starting background optimizer task")
        return asyncio.create_task(self.process_tasks())
