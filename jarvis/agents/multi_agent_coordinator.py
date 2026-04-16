"""
Multi-agent coordination system for JARVIS.

Coordinates multiple specialized agents to work together.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from jarvis.core.logging import get_logger


class AgentType(Enum):
    """Types of agents."""
    CODING = "coding"
    RESEARCH = "research"
    TASK_EXECUTOR = "task_executor"
    OPTIMIZER = "optimizer"
    MONITOR = "monitor"


@dataclass
class Task:
    """A task for an agent."""
    id: str
    task_type: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    assigned_agent: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    status: str = "pending"


class Agent:
    """Base agent class."""

    def __init__(self, agent_id: str, agent_type: AgentType, handler: Callable = None):
        """Initialize agent.
        
        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent
            handler: Async handler function for tasks
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.handler = handler
        self.logger = get_logger(__name__)
        self.tasks_completed = 0
        self.tasks_failed = 0

    async def execute(self, task: Task) -> bool:
        """Execute a task.
        
        Args:
            task: Task to execute
            
        Returns:
            True if successful
        """
        try:
            task.status = "running"
            task.assigned_agent = self.agent_id

            if self.handler:
                result = self.handler(task)
                if asyncio.iscoroutine(result):
                    task.result = await result
                else:
                    task.result = result
            else:
                task.result = f"Executed by {self.agent_id}"

            task.status = "completed"
            self.tasks_completed += 1
            return True

        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            self.tasks_failed += 1
            return False


class MultiAgentCoordinator:
    """Coordinates multiple agents."""

    def __init__(self):
        """Initialize coordinator."""
        self.logger = get_logger(__name__)
        self.agents: Dict[str, Agent] = {}
        self.task_queue: List[Task] = []
        self.completed_tasks: List[Task] = []

    def register_agent(self, agent: Agent) -> None:
        """Register an agent.
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id} ({agent.agent_type.value})")

    def add_task(self, task: Task) -> None:
        """Add a task to the queue.
        
        Args:
            task: Task to add
        """
        self.task_queue.append(task)
        self.logger.debug(f"Added task: {task.id} ({task.task_type})")

    def get_suitable_agent(self, task: Task) -> Optional[Agent]:
        """Find suitable agent for a task.
        
        Args:
            task: Task to find agent for
            
        Returns:
            Suitable agent or None
        """
        # Simple routing: match task type to agent type
        for agent in self.agents.values():
            if agent.agent_type.value == task.task_type or task.task_type == "any":
                return agent

        # Return any available agent
        if self.agents:
            return list(self.agents.values())[0]

        return None

    async def process_tasks(self, max_concurrent: int = 3) -> Dict[str, Any]:
        """Process all tasks in queue.
        
        Args:
            max_concurrent: Maximum concurrent task executions
            
        Returns:
            Dictionary with results
        """
        if not self.task_queue:
            self.logger.info("No tasks to process")
            return {'processed': 0, 'succeeded': 0, 'failed': 0}

        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_task(task: Task) -> Task:
            async with semaphore:
                agent = self.get_suitable_agent(task)
                if agent:
                    await agent.execute(task)
                else:
                    task.error = "No suitable agent found"
                    task.status = "failed"

                self.completed_tasks.append(task)
                return task

        # Create and run tasks
        tasks = [run_task(task) for task in self.task_queue]
        results = await asyncio.gather(*tasks)

        # Count results
        succeeded = sum(1 for t in results if t.status == "completed")
        failed = sum(1 for t in results if t.status == "failed")

        self.task_queue = []  # Clear queue

        self.logger.info(f"Processed {len(results)} tasks: "
                        f"{succeeded} succeeded, {failed} failed")

        return {
            'processed': len(results),
            'succeeded': succeeded,
            'failed': failed,
            'results': [
                {
                    'task_id': t.id,
                    'status': t.status,
                    'agent': t.assigned_agent,
                    'result': t.result,
                    'error': t.error,
                }
                for t in results
            ]
        }

    def delegate_task(self, task: Task) -> Optional[str]:
        """Delegate a task to best agent immediately.
        
        Args:
            task: Task to delegate
            
        Returns:
            Agent ID if delegated, None otherwise
        """
        agent = self.get_suitable_agent(task)
        if agent:
            task.assigned_agent = agent.agent_id
            self.logger.info(f"Delegated {task.id} to {agent.agent_id}")
            return agent.agent_id

        return None

    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status.
        
        Returns:
            Status dictionary
        """
        return {
            'agents': len(self.agents),
            'pending_tasks': len(self.task_queue),
            'completed_tasks': len(self.completed_tasks),
            'agents_status': {
                agent_id: {
                    'type': agent.agent_type.value,
                    'tasks_completed': agent.tasks_completed,
                    'tasks_failed': agent.tasks_failed,
                }
                for agent_id, agent in self.agents.items()
            }
        }

    def get_agent_summary(self) -> Dict[str, Any]:
        """Get summary of all agents.
        
        Returns:
            Agent summary
        """
        total_completed = sum(a.tasks_completed for a in self.agents.values())
        total_failed = sum(a.tasks_failed for a in self.agents.values())

        return {
            'total_agents': len(self.agents),
            'total_tasks_completed': total_completed,
            'total_tasks_failed': total_failed,
            'success_rate': total_completed / (total_completed + total_failed)
            if (total_completed + total_failed) > 0 else 0,
            'agents': [
                {
                    'id': agent.agent_id,
                    'type': agent.agent_type.value,
                    'completed': agent.tasks_completed,
                    'failed': agent.tasks_failed,
                }
                for agent in self.agents.values()
            ]
        }
