"""
Phase 4 Integration Tests: Background optimizer, decision engine, and system.
"""

import pytest
from datetime import datetime, timedelta

from jarvis.learning.background_optimizer import (
    BackgroundOptimizer,
    OptimizationPriority,
)
from jarvis.learning.ai_decision_engine import (
    AIDecisionEngine,
    DecisionStatus,
)
from jarvis.learning.predictive_analyzer import PredictiveAnalyzer, PredictionResult
from jarvis.learning.learning_system import LearningSystem, ImprovementOutcome
from jarvis.learning.knowledge_base import KnowledgeBase
from jarvis.learning.phase4_integration import Phase4System


# ==================== Background Optimizer Tests ====================

class TestBackgroundOptimizer:
    """Test BackgroundOptimizer functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analyzer = PredictiveAnalyzer(LearningSystem(), KnowledgeBase())
        self.optimizer = BackgroundOptimizer(self.analyzer, max_concurrent=2)

    def test_add_task(self):
        """Test adding optimization tasks."""
        prediction = PredictionResult(
            improvement_type="add_docstring",
            confidence=0.85,
            expected_impact=0.6,
            rationale="Missing docstrings",
            historical_data={"success_rate": 0.8}
        )
        task_id = self.optimizer.add_task("test.py", prediction)
        assert task_id is not None
        assert task_id in self.optimizer.tasks
        assert self.optimizer.get_pending_count() == 1

    def test_task_priority_ordering(self):
        """Test tasks sorted by priority."""
        pred = PredictionResult(
            improvement_type="test",
            confidence=0.8,
            expected_impact=0.5,
            rationale="test",
            historical_data={}
        )

        low = self.optimizer.add_task(
            "a.py", pred, priority=OptimizationPriority.LOW
        )
        high = self.optimizer.add_task(
            "b.py", pred, priority=OptimizationPriority.HIGH
        )
        normal = self.optimizer.add_task(
            "c.py", pred, priority=OptimizationPriority.NORMAL
        )

        pending = [t for t in self.optimizer.tasks.values() if t.is_pending()]
        pending.sort(key=lambda t: t.priority.value, reverse=True)

        assert pending[0].id == high
        assert pending[1].id == normal
        assert pending[2].id == low

    def test_pause_resume(self):
        """Test pause/resume functionality."""
        assert not self.optimizer.is_paused
        self.optimizer.pause()
        assert self.optimizer.is_paused
        self.optimizer.resume()
        assert not self.optimizer.is_paused

    def test_get_task_status(self):
        """Test task status retrieval."""
        pred = PredictionResult(
            improvement_type="test",
            confidence=0.8,
            expected_impact=0.5,
            rationale="test",
            historical_data={}
        )
        task_id = self.optimizer.add_task("test.py", pred)
        status = self.optimizer.get_task_status(task_id)

        assert status["id"] == task_id
        assert status["status"] == "pending"
        assert status["success"] is False
        assert "file_path" in status
        assert "created_at" in status

    def test_clear_completed_tasks(self):
        """Test clearing completed tasks."""
        pred = PredictionResult(
            improvement_type="test",
            confidence=0.8,
            expected_impact=0.5,
            rationale="test",
            historical_data={}
        )

        task_id = self.optimizer.add_task("test.py", pred)
        task = self.optimizer.tasks[task_id]

        task.started_at = datetime.now()
        task.completed_at = datetime.now() - timedelta(hours=2)
        task.success = True

        cleared = self.optimizer.clear_completed()
        assert cleared == 1
        assert task_id not in self.optimizer.tasks

    def test_stats_tracking(self):
        """Test statistics tracking."""
        pred = PredictionResult(
            improvement_type="test",
            confidence=0.8,
            expected_impact=0.5,
            rationale="test",
            historical_data={}
        )

        self.optimizer.add_task("a.py", pred)
        self.optimizer.add_task("b.py", pred)

        assert self.optimizer.stats.total_tasks == 2
        assert self.optimizer.stats.completed_tasks == 0


# ==================== AI Decision Engine Tests ====================

class TestAIDecisionEngine:
    """Test AIDecisionEngine functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        learning = LearningSystem()
        knowledge = KnowledgeBase()
        analyzer = PredictiveAnalyzer(learning, knowledge)
        self.engine = AIDecisionEngine(analyzer, knowledge)

    def test_decision_thresholds(self):
        """Test decision threshold enforcement."""
        self.engine.update_thresholds(
            confidence_threshold=0.7,
            impact_threshold=0.5,
            max_risk_score=0.4,
        )

        assert self.engine.confidence_threshold == 0.7
        assert self.engine.impact_threshold == 0.5
        assert self.engine.max_risk_score == 0.4

    def test_approve_decision(self):
        """Test approving a decision."""
        pred = PredictionResult(
            improvement_type="add_type_hints",
            confidence=0.9,
            expected_impact=0.8,
            rationale="Missing type hints",
            historical_data={"success": 0.95}
        )

        decisions = self.engine.make_decision("test.py", [pred])
        assert len(decisions) > 0
        assert decisions[0].status == DecisionStatus.APPROVED

    def test_reject_low_confidence(self):
        """Test rejecting low confidence prediction."""
        self.engine.update_thresholds(confidence_threshold=0.9)

        pred = PredictionResult(
            improvement_type="refactor",
            confidence=0.3,
            expected_impact=0.2,
            rationale="Low confidence refactoring",
            historical_data={}
        )

        decisions = self.engine.make_decision("test.py", [pred])
        assert len(decisions) > 0
        # Status is PENDING but decision field is False
        assert decisions[0].decision is False

    def test_decision_scoring(self):
        """Test decision scoring breakdown."""
        pred = PredictionResult(
            improvement_type="add_docstring",
            confidence=0.8,
            expected_impact=0.7,
            rationale="Missing docs",
            historical_data={"known": True}
        )

        decisions = self.engine.make_decision("test.py", [pred])
        decision = decisions[0]

        scoring = decision.scoring
        assert 0.0 <= scoring.confidence_score <= 1.0
        assert 0.0 <= scoring.knowledge_support <= 1.0
        assert 0.0 <= scoring.impact_score <= 1.0
        assert 0.0 <= scoring.risk_score <= 1.0
        assert 0.0 <= scoring.final_score <= 1.0

    def test_get_approved_decisions(self):
        """Test retrieving approved decisions."""
        pred_good = PredictionResult(
            improvement_type="high_confidence",
            confidence=0.95,
            expected_impact=0.9,
            rationale="High confidence",
            historical_data={"success": 1.0}
        )

        pred_bad = PredictionResult(
            improvement_type="low_confidence",
            confidence=0.2,
            expected_impact=0.1,
            rationale="Low confidence",
            historical_data={}
        )

        self.engine.update_thresholds(confidence_threshold=0.7)
        self.engine.make_decision("test.py", [pred_good, pred_bad])

        approved = self.engine.get_approved_decisions()
        assert len(approved) >= 1

    def test_decision_audit_trail(self):
        """Test audit trail recording."""
        pred = PredictionResult(
            improvement_type="test",
            confidence=0.85,
            expected_impact=0.6,
            rationale="test",
            historical_data={}
        )

        self.engine.make_decision("file1.py", [pred])
        self.engine.make_decision("file2.py", [pred])

        history = self.engine.get_decision_history()
        assert len(history) >= 2
        assert all("improvement" in h for h in history)
        assert all("decision" in h for h in history)
        assert all("created_at" in h for h in history)

    def test_decision_stats(self):
        """Test statistics tracking."""
        pred = PredictionResult(
            improvement_type="test",
            confidence=0.8,
            expected_impact=0.6,
            rationale="test",
            historical_data={}
        )

        self.engine.make_decision("test.py", [pred])

        stats = self.engine.get_stats()
        assert stats["total_decisions"] >= 1
        assert "approval_rate" in stats


# ==================== Phase 4 Integration Tests ====================

class TestPhase4Integration:
    """Test Phase4System integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.system = Phase4System()

    def test_system_initialization(self):
        """Test system initializes all components."""
        assert self.system.learning_system is not None
        assert self.system.knowledge_base is not None
        assert self.system.code_analyzer is not None
        assert self.system.multi_agent_coordinator is not None
        assert self.system.predictive_analyzer is not None
        assert self.system.decision_engine is not None
        assert self.system.background_optimizer is not None

    def test_get_system_status(self):
        """Test retrieving system status."""
        status = self.system.get_system_status()

        assert "initialized" in status
        assert "learning_system" in status
        assert "knowledge_base" in status
        assert "decision_engine" in status
        assert "background_optimizer" in status
        assert "multi_agent_coordinator" in status

        assert status["initialized"] is True

    def test_export_system_state(self):
        """Test exporting system state."""
        state = self.system.export_system_state()

        assert "learning_system" in state
        assert "knowledge_base" in state
        assert "decision_stats" in state
        assert "optimization_stats" in state

    def test_get_audit_trail(self):
        """Test retrieving audit trail."""
        trail = self.system.get_audit_trail()

        assert "decision_history" in trail
        assert "learning_outcomes" in trail
        assert "background_tasks" in trail

        assert isinstance(trail["decision_history"], list)
        assert isinstance(trail["learning_outcomes"], list)
        assert isinstance(trail["background_tasks"], list)


# ==================== Integration Flow Tests ====================

class TestIntegrationFlow:
    """Test complete end-to-end flows."""

    def setup_method(self):
        """Setup test fixtures."""
        self.system = Phase4System()

    def test_background_optimization_integration(self):
        """Test background optimizer integrates with prediction."""
        pred = PredictionResult(
            improvement_type="test",
            confidence=0.8,
            expected_impact=0.5,
            rationale="test",
            historical_data={}
        )

        task_id = self.system.background_optimizer.add_task(
            "test.py",
            pred,
        )

        assert task_id is not None
        assert self.system.background_optimizer.get_pending_count() == 1

    def test_decision_engine_integration(self):
        """Test decision engine integrates with analyzer."""
        pred = PredictionResult(
            improvement_type="test",
            confidence=0.8,
            expected_impact=0.7,
            rationale="test",
            historical_data={}
        )

        decisions = self.system.decision_engine.make_decision(
            "test.py",
            [pred],
        )

        assert len(decisions) >= 1
        assert decisions[0].decision is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
