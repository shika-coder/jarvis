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

__all__ = [
    "SelfImprovementBase",
    "CodeIssue",
    "PerformanceMetric",
    "RefactoringProposal",
    "BackupManager",
    "ChangeValidator",
    "ImprovementTracker",
    "CodeAnalyzer",
]
