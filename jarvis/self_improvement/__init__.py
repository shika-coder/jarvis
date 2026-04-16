"""
JARVIS Self-Improvement Module (Phase 3)

Analyzes agent outputs, detects inefficiencies, and proposes code improvements.
"""

from jarvis.self_improvement.base import (
    SelfImprovementBase,
    CodeIssue,
    PerformanceMetric,
    RefactoringProposal,
    BackupManager,
    ChangeValidator,
    ImprovementTracker,
)
from jarvis.self_improvement.code_analyzer import CodeAnalyzer
from jarvis.self_improvement.performance_monitor import PerformanceMonitor, ExecutionProfile
from jarvis.self_improvement.test_generator import TestGenerator, TestCase
from jarvis.self_improvement.refactor_engine import RefactoringEngine, RefactoringStep
from jarvis.self_improvement.workflow_builder import (
    Workflow,
    WorkflowBuilder,
    WorkflowComposer,
    WorkflowStep,
    WorkflowStatus,
    StepCondition,
)
from jarvis.self_improvement.deployment_planner import (
    DeploymentPlan,
    DeploymentStrategy,
    DeploymentStatus,
    DeploymentStep,
)

__all__ = [
    "SelfImprovementBase",
    "CodeIssue",
    "PerformanceMetric",
    "RefactoringProposal",
    "BackupManager",
    "ChangeValidator",
    "ImprovementTracker",
    "CodeAnalyzer",
    "PerformanceMonitor",
    "ExecutionProfile",
    "TestGenerator",
    "TestCase",
    "RefactoringEngine",
    "RefactoringStep",
    "Workflow",
    "WorkflowBuilder",
    "WorkflowComposer",
    "WorkflowStep",
    "WorkflowStatus",
    "StepCondition",
    "DeploymentPlan",
    "DeploymentStrategy",
    "DeploymentStatus",
    "DeploymentStep",
]
