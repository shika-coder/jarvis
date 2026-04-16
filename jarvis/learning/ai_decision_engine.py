"""
AI Decision Engine: Autonomous improvement selection with confidence scoring.

Makes decisions about which improvements to apply based on:
- ML confidence scores
- Knowledge base support
- Expected impact
- Risk assessment
- Audit trails for explainability
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum

from jarvis.learning.predictive_analyzer import PredictiveAnalyzer, PredictionResult
from jarvis.learning.knowledge_base import KnowledgeBase


logger = logging.getLogger(__name__)


class DecisionRisk(Enum):
    """Risk levels for decisions."""
    MINIMAL = 0.1
    LOW = 0.3
    MODERATE = 0.5
    HIGH = 0.7
    CRITICAL = 0.9


class DecisionStatus(Enum):
    """Status of a decision."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass
class DecisionScoring:
    """Scoring breakdown for a decision."""
    confidence_score: float  # ML model confidence (0-1)
    knowledge_support: float  # Knowledge base support (0-1)
    impact_score: float  # Expected impact (0-1)
    risk_score: float  # Risk assessment (0-1)
    final_score: float  # Weighted final score (0-1)

    def to_dict(self) -> Dict[str, float]:
        return {
            "confidence": self.confidence_score,
            "knowledge_support": self.knowledge_support,
            "impact": self.impact_score,
            "risk": self.risk_score,
            "final": self.final_score,
        }


@dataclass
class ImprovedDecision:
    """A decision about whether to apply an improvement."""
    id: str
    prediction: PredictionResult
    scoring: DecisionScoring
    decision: bool  # True = approve, False = reject
    reasoning: str
    status: DecisionStatus = DecisionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None

    def approve(self) -> None:
        """Approve this decision."""
        self.decision = True
        self.status = DecisionStatus.APPROVED
        logger.info(f"Decision {self.id} approved")

    def reject(self) -> None:
        """Reject this decision."""
        self.decision = False
        self.status = DecisionStatus.REJECTED
        logger.info(f"Decision {self.id} rejected")

    def mark_executed(self, result: Dict[str, Any], success: bool) -> None:
        """Mark decision as executed."""
        self.executed_at = datetime.now()
        self.execution_result = result
        self.status = (
            DecisionStatus.EXECUTED if success else DecisionStatus.FAILED
        )
        logger.info(
            f"Decision {self.id} executed: success={success}"
        )


class AIDecisionEngine:
    """Autonomous AI decision engine for improvement selection."""

    def __init__(
        self,
        analyzer: PredictiveAnalyzer,
        knowledge_base: KnowledgeBase,
        confidence_threshold: float = 0.6,
        impact_threshold: float = 0.3,
        max_risk_score: float = 0.7,
    ):
        """Initialize decision engine.

        Args:
            analyzer: PredictiveAnalyzer for predictions
            knowledge_base: KnowledgeBase for pattern support
            confidence_threshold: Min confidence to consider (0-1)
            impact_threshold: Min expected impact (0-1)
            max_risk_score: Max acceptable risk (0-1)
        """
        self.analyzer = analyzer
        self.knowledge_base = knowledge_base
        self.confidence_threshold = confidence_threshold
        self.impact_threshold = impact_threshold
        self.max_risk_score = max_risk_score

        self.decisions: Dict[str, ImprovedDecision] = {}
        self._decision_count = 0

    def make_decision(
        self,
        file_path: str,
        predictions: Optional[List[PredictionResult]] = None,
    ) -> List[ImprovedDecision]:
        """Make decisions about which improvements to apply.

        Args:
            file_path: File being analyzed
            predictions: List of predictions (if None, will analyze)

        Returns:
            List of approved decisions
        """
        logger.info(f"Making decisions for {file_path}")

        # Get predictions if not provided
        if predictions is None:
            predictions = self.analyzer.analyze(file_path)

        decisions = []

        for prediction in predictions:
            decision = self._evaluate_prediction(file_path, prediction)
            self.decisions[decision.id] = decision
            decisions.append(decision)

            if decision.decision:
                logger.info(
                    f"✓ APPROVED: {prediction.improvement_type} "
                    f"(score={decision.scoring.final_score:.2f})"
                )
            else:
                logger.info(
                    f"✗ REJECTED: {prediction.improvement_type} "
                    f"(reason: {decision.reasoning})"
                )

        return decisions

    def _evaluate_prediction(
        self,
        file_path: str,
        prediction: PredictionResult,
    ) -> ImprovedDecision:
        """Evaluate single prediction and make decision."""
        decision_id = f"dec-{self._decision_count}"
        self._decision_count += 1

        # Score components
        confidence = prediction.confidence

        # Knowledge support: check if pattern is well-known
        knowledge_entries = self.knowledge_base.query(
            category=prediction.improvement_type,
            min_confidence=0.3,
        )
        knowledge_support = (
            min(1.0, len(knowledge_entries) * 0.2)
            if knowledge_entries
            else 0.0
        )

        # Impact score (from prediction or estimate)
        impact = getattr(prediction, "expected_impact", 0.5)

        # Risk assessment
        risk = self._assess_risk(prediction)

        # Final weighted score
        # Higher confidence, knowledge support, and impact = higher score
        # Higher risk = lower score
        final_score = (
            confidence * 0.4 +
            knowledge_support * 0.2 +
            impact * 0.3 +
            (1.0 - risk) * 0.1
        )

        scoring = DecisionScoring(
            confidence_score=confidence,
            knowledge_support=knowledge_support,
            impact_score=impact,
            risk_score=risk,
            final_score=final_score,
        )

        # Make decision based on thresholds
        passed_confidence = confidence >= self.confidence_threshold
        passed_impact = impact >= self.impact_threshold
        passed_risk = risk <= self.max_risk_score

        decision = (
            passed_confidence and
            passed_impact and
            passed_risk
        )

        # Build reasoning
        reasoning = self._build_reasoning(
            prediction,
            scoring,
            decision,
            passed_confidence,
            passed_impact,
            passed_risk,
        )

        improved_decision = ImprovedDecision(
            id=decision_id,
            prediction=prediction,
            scoring=scoring,
            decision=decision,
            reasoning=reasoning,
        )

        if decision:
            improved_decision.approve()

        return improved_decision

    def _assess_risk(self, prediction: PredictionResult) -> float:
        """Assess risk of applying improvement."""
        risk = 0.0

        # Risk based on improvement type
        high_risk_types = {
            "refactor_architecture": 0.6,
            "modify_api": 0.5,
            "change_algorithm": 0.4,
        }

        for risk_type, risk_val in high_risk_types.items():
            if risk_type in prediction.improvement_type:
                risk = max(risk, risk_val)

        # Reduce risk if high knowledge support
        knowledge_entries = self.knowledge_base.query(
            category=prediction.improvement_type
        )
        if knowledge_entries:
            avg_confidence = sum(
                e.confidence for e in knowledge_entries
            ) / len(knowledge_entries)
            risk *= max(0.1, 1.0 - avg_confidence * 0.5)

        return min(1.0, risk)

    def _build_reasoning(
        self,
        prediction: PredictionResult,
        scoring: DecisionScoring,
        decision: bool,
        passed_confidence: bool,
        passed_impact: bool,
        passed_risk: bool,
    ) -> str:
        """Build human-readable reasoning for decision."""
        parts = []

        if decision:
            parts.append("APPROVED because:")
        else:
            parts.append("REJECTED because:")

        if passed_confidence:
            parts.append(
                f"✓ Confidence {scoring.confidence_score:.1%} >= "
                f"{self.confidence_threshold:.1%}"
            )
        else:
            parts.append(
                f"✗ Confidence {scoring.confidence_score:.1%} < "
                f"{self.confidence_threshold:.1%}"
            )

        if passed_impact:
            parts.append(
                f"✓ Impact {scoring.impact_score:.1%} >= "
                f"{self.impact_threshold:.1%}"
            )
        else:
            parts.append(
                f"✗ Impact {scoring.impact_score:.1%} < "
                f"{self.impact_threshold:.1%}"
            )

        if passed_risk:
            parts.append(
                f"✓ Risk {scoring.risk_score:.1%} <= "
                f"{self.max_risk_score:.1%}"
            )
        else:
            parts.append(
                f"✗ Risk {scoring.risk_score:.1%} > "
                f"{self.max_risk_score:.1%}"
            )

        parts.append(f"Knowledge support: {scoring.knowledge_support:.1%}")
        parts.append(f"Rationale: {prediction.rationale}")

        return " | ".join(parts)

    def get_approved_decisions(self) -> List[ImprovedDecision]:
        """Get all approved decisions."""
        return [d for d in self.decisions.values() if d.decision]

    def get_rejected_decisions(self) -> List[ImprovedDecision]:
        """Get all rejected decisions."""
        return [d for d in self.decisions.values() if not d.decision]

    def get_decision_by_id(self, decision_id: str) -> Optional[ImprovedDecision]:
        """Get decision by ID."""
        return self.decisions.get(decision_id)

    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Get audit trail of all decisions."""
        history = []
        for decision in self.decisions.values():
            history.append({
                "id": decision.id,
                "improvement": decision.prediction.improvement_type,
                "decision": "approved" if decision.decision else "rejected",
                "status": decision.status.value,
                "confidence": decision.scoring.confidence_score,
                "final_score": decision.scoring.final_score,
                "reasoning": decision.reasoning,
                "created_at": decision.created_at.isoformat(),
                "executed_at": (
                    decision.executed_at.isoformat()
                    if decision.executed_at else None
                ),
            })
        return history

    def get_stats(self) -> Dict[str, Any]:
        """Get decision statistics."""
        approved = self.get_approved_decisions()
        rejected = self.get_rejected_decisions()
        executed = [d for d in self.decisions.values() if d.status == DecisionStatus.EXECUTED]
        failed = [d for d in self.decisions.values() if d.status == DecisionStatus.FAILED]

        return {
            "total_decisions": len(self.decisions),
            "approved": len(approved),
            "rejected": len(rejected),
            "executed": len(executed),
            "failed": len(failed),
            "approval_rate": (
                len(approved) / len(self.decisions) * 100
                if self.decisions
                else 0.0
            ),
            "execution_success_rate": (
                len(executed) / (len(executed) + len(failed)) * 100
                if (len(executed) + len(failed)) > 0
                else 0.0
            ),
        }

    def update_thresholds(
        self,
        confidence_threshold: Optional[float] = None,
        impact_threshold: Optional[float] = None,
        max_risk_score: Optional[float] = None,
    ) -> None:
        """Update decision thresholds."""
        if confidence_threshold is not None:
            self.confidence_threshold = max(0.0, min(1.0, confidence_threshold))
        if impact_threshold is not None:
            self.impact_threshold = max(0.0, min(1.0, impact_threshold))
        if max_risk_score is not None:
            self.max_risk_score = max(0.0, min(1.0, max_risk_score))

        logger.info(
            f"Updated thresholds: "
            f"confidence={self.confidence_threshold}, "
            f"impact={self.impact_threshold}, "
            f"risk={self.max_risk_score}"
        )
