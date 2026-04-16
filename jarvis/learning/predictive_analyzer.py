"""
Predictive analyzer for code improvements using ML models.

Predicts which code improvements will be most beneficial.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from jarvis.core.logging import get_logger
from jarvis.learning.learning_system import LearningSystem
from jarvis.learning.knowledge_base import KnowledgeBase, KnowledgeEntry


@dataclass
class PredictionResult:
    """Result of an improvement prediction."""
    improvement_type: str
    confidence: float  # 0-1 confidence from ML model
    expected_impact: float  # Estimated performance improvement
    rationale: str  # Explanation for the prediction
    historical_data: Dict[str, Any]  # Historical success info


class PredictiveAnalyzer:
    """Predicts optimal code improvements using ML and knowledge base."""

    def __init__(self, learning_system: LearningSystem = None,
                 knowledge_base: KnowledgeBase = None):
        """Initialize predictive analyzer.
        
        Args:
            learning_system: Optional LearningSystem instance
            knowledge_base: Optional KnowledgeBase instance
        """
        self.learning_system = learning_system or LearningSystem()
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.logger = get_logger(__name__)

    def analyze(self, code_metrics: Dict[str, Any]) -> List[PredictionResult]:
        """Analyze code and predict best improvements.
        
        Args:
            code_metrics: Code metrics dictionary
            
        Returns:
            List of predictions, sorted by expected benefit
        """
        results = []

        # Get recommendations from learning system
        recommendations = self.learning_system.recommend_improvements(code_metrics)

        for rec in recommendations:
            imp_type = rec['type']

            # Look up in knowledge base
            kb_entries = self.knowledge_base.query(category=imp_type)

            # Build rationale
            rationale = f"Historical success rate: {rec['historical_success_rate']:.0%}, "
            rationale += f"Average impact: {rec['avg_impact']:+.1%}"

            if kb_entries:
                kb_entry = kb_entries[0]
                rationale += f", KB confidence: {kb_entry.confidence:.0%}"

            result = PredictionResult(
                improvement_type=imp_type,
                confidence=float(rec['confidence']),
                expected_impact=float(rec['avg_impact']),
                rationale=rationale,
                historical_data={
                    'success_rate': rec['historical_success_rate'],
                    'sample_size': rec['sample_size'],
                    'avg_impact': rec['avg_impact'],
                }
            )
            results.append(result)

        # Sort by expected impact
        results.sort(key=lambda r: r.expected_impact, reverse=True)

        self.logger.info(f"Predicted {len(results)} improvements")
        return results

    def get_top_predictions(self, code_metrics: Dict[str, Any],
                           top_n: int = 3) -> List[PredictionResult]:
        """Get top N improvement predictions.
        
        Args:
            code_metrics: Code metrics dictionary
            top_n: Number of predictions to return
            
        Returns:
            List of top predictions
        """
        all_predictions = self.analyze(code_metrics)
        return all_predictions[:top_n]

    def get_detailed_plan(self, code_metrics: Dict[str, Any],
                         max_improvements: int = 5) -> Dict[str, Any]:
        """Get detailed improvement plan.
        
        Args:
            code_metrics: Code metrics dictionary
            max_improvements: Maximum improvements to include
            
        Returns:
            Detailed plan with steps and priorities
        """
        predictions = self.analyze(code_metrics)[:max_improvements]

        plan = {
            'total_predicted_impact': sum(p.expected_impact for p in predictions),
            'improvements': [],
            'confidence_average': sum(p.confidence for p in predictions) / len(predictions) if predictions else 0,
        }

        for i, pred in enumerate(predictions, 1):
            plan['improvements'].append({
                'priority': i,
                'type': pred.improvement_type,
                'confidence': pred.confidence,
                'expected_impact': pred.expected_impact,
                'rationale': pred.rationale,
            })

        return plan

    def validate_prediction(self, improvement_type: str, success: bool,
                          actual_impact: float) -> None:
        """Record actual outcome of a prediction.
        
        Args:
            improvement_type: Type of improvement
            success: Whether it was successful
            actual_impact: Actual performance impact
        """
        # Update knowledge base
        kb_entries = self.knowledge_base.query(category=improvement_type)
        if kb_entries:
            self.knowledge_base.update_success(kb_entries[0].key, success)

        self.logger.info(f"Validated: {improvement_type} - "
                        f"{'✓' if success else '✗'} ({actual_impact:+.1%})")

    def get_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics for the predictor.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            'learning_system': {
                'total_outcomes': len(self.learning_system.outcomes),
                'model_trained': self.learning_system.model is not None,
                'patterns': self.learning_system.get_pattern_analysis(),
            },
            'knowledge_base': self.knowledge_base.get_stats(),
        }

    def get_recommendations_for_issue(self, issue_type: str) -> List[Dict[str, Any]]:
        """Get recommendations for a specific issue type.
        
        Args:
            issue_type: Type of code issue (e.g., 'performance', 'security')
            
        Returns:
            List of recommended improvements for this issue
        """
        # Query knowledge base for this category
        entries = self.knowledge_base.query(category=issue_type, min_confidence=0.5)

        recommendations = []
        for entry in entries:
            recommendations.append({
                'key': entry.key,
                'title': entry.title,
                'description': entry.description,
                'confidence': entry.confidence,
                'success_rate': entry.success_rate(),
                'times_used': entry.times_used,
            })

        return recommendations
