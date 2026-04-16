"""
Machine Learning-based improvement pattern learning system.

Learns from historical improvements to predict effective optimizations.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pickle

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from jarvis.core.logging import get_logger


@dataclass
class ImprovementOutcome:
    """Records the outcome of an improvement."""
    improvement_type: str
    code_metrics_before: Dict[str, Any]
    code_metrics_after: Dict[str, Any]
    performance_impact: float  # % improvement
    success: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class LearningSystem:
    """Learns from improvement outcomes to predict effective optimizations."""

    def __init__(self, storage_dir: Path = None):
        """Initialize learning system.
        
        Args:
            storage_dir: Directory to store patterns and models
        """
        self.storage_dir = storage_dir or Path("learning_data")
        self.storage_dir.mkdir(exist_ok=True)
        
        self.logger = get_logger(__name__)
        self.outcomes: List[ImprovementOutcome] = []
        self.patterns: Dict[str, Any] = {}
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        
        self._load_outcomes()
        self._load_model()

    def record_outcome(self, outcome: ImprovementOutcome) -> None:
        """Record the outcome of an improvement.
        
        Args:
            outcome: The improvement outcome to record
        """
        self.outcomes.append(outcome)
        self._save_outcomes()
        self.logger.info(f"Recorded: {outcome.improvement_type} - "
                        f"{'✓' if outcome.success else '✗'} "
                        f"({outcome.performance_impact:+.1%})")

    def extract_features(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Extract ML features from code metrics.
        
        Args:
            metrics: Code metrics dictionary
            
        Returns:
            Dictionary of numeric features
        """
        features = {
            'complexity_score': float(metrics.get('complexity', 1)),
            'lines_of_code': float(metrics.get('lines', 0)),
            'function_count': float(metrics.get('functions', 0)),
            'security_issues': float(metrics.get('security_issues', 0)),
            'performance_warnings': float(metrics.get('perf_warnings', 0)),
            'style_violations': float(metrics.get('style_violations', 0)),
        }
        return features

    def train(self) -> bool:
        """Train ML model on recorded outcomes.
        
        Returns:
            True if training successful
        """
        if len(self.outcomes) < 10:
            self.logger.warning(f"Need at least 10 outcomes for training, have {len(self.outcomes)}")
            return False

        try:
            # Prepare data
            X_list = []
            y_list = []

            for outcome in self.outcomes:
                before_feat = self.extract_features(outcome.code_metrics_before)
                after_feat = self.extract_features(outcome.code_metrics_after)

                # Combine features: before metrics + improvement type
                features = list(before_feat.values())
                # Add improvement type as one-hot
                imp_types = list(set(o.improvement_type for o in self.outcomes))
                for imp_type in imp_types:
                    features.append(1.0 if imp_type == outcome.improvement_type else 0.0)

                X_list.append(features)
                y_list.append(1 if outcome.success else 0)

            if not X_list:
                return False

            X = np.array(X_list)
            y = np.array(y_list)

            # Store feature names for later
            self.feature_names = list(self.extract_features({}).keys())

            # Normalize features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)

            # Split and train
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )

            self.model = RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42
            )
            self.model.fit(X_train, y_train)

            # Evaluate
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)

            self.logger.info(f"Model trained: train={train_score:.2%}, test={test_score:.2%}")
            self._save_model()
            return True

        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            return False

    def predict(self, code_metrics: Dict[str, Any], 
                improvement_types: List[str]) -> List[Tuple[str, float]]:
        """Predict which improvements will be successful.
        
        Args:
            code_metrics: Current code metrics
            improvement_types: List of improvement types to evaluate
            
        Returns:
            List of (improvement_type, confidence) tuples, sorted by confidence
        """
        if not self.model:
            self.logger.warning("Model not trained yet")
            return [(itype, 0.5) for itype in improvement_types]

        try:
            features = list(self.extract_features(code_metrics).values())

            # Add improvement type one-hot encoding and get predictions
            imp_types = list(set(o.improvement_type for o in self.outcomes))
            predictions = []

            for target_type in improvement_types:
                test_features = features.copy()
                for imp_type in imp_types:
                    test_features.append(1.0 if imp_type == target_type else 0.0)

                X = np.array([test_features])
                if self.scaler:
                    X = self.scaler.transform(X)

                # Get prediction probability
                proba = self.model.predict_proba(X)[0]
                confidence = float(proba[1])  # Probability of success
                predictions.append((target_type, confidence))

            # Sort by confidence descending
            predictions.sort(key=lambda x: x[1], reverse=True)
            return predictions

        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            return [(itype, 0.5) for itype in improvement_types]

    def get_pattern_analysis(self) -> Dict[str, Any]:
        """Analyze patterns in improvement outcomes.
        
        Returns:
            Dictionary with pattern statistics
        """
        if not self.outcomes:
            return {'total_outcomes': 0}

        df = pd.DataFrame([o.to_dict() for o in self.outcomes])

        success_by_type = df.groupby('improvement_type').agg({
            'success': ['sum', 'count', 'mean'],
            'performance_impact': ['mean', 'min', 'max']
        })

        avg_impact = df[df['success']]['performance_impact'].mean()
        success_rate = df['success'].mean()

        return {
            'total_outcomes': len(self.outcomes),
            'success_rate': float(success_rate),
            'avg_impact': float(avg_impact),
            'by_type': success_by_type.to_dict(),
            'most_successful': df[df['success']]['improvement_type'].value_counts().to_dict(),
            'model_trained': self.model is not None,
        }

    def recommend_improvements(self, code_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recommend improvements based on patterns and predictions.
        
        Args:
            code_metrics: Current code metrics
            
        Returns:
            List of recommendations with confidence scores
        """
        # Get all improvement types we know about
        all_types = list(set(o.improvement_type for o in self.outcomes))
        if not all_types:
            return []

        # Get predictions
        predictions = self.predict(code_metrics, all_types)

        # Convert to recommendations
        recommendations = []
        for itype, confidence in predictions:
            # Find historical outcomes for this type
            outcomes = [o for o in self.outcomes if o.improvement_type == itype]
            if outcomes:
                success_count = sum(1 for o in outcomes if o.success)
                success_rate = success_count / len(outcomes)
                avg_impact = sum(o.performance_impact for o in outcomes) / len(outcomes)

                recommendations.append({
                    'type': itype,
                    'confidence': float(confidence),
                    'historical_success_rate': float(success_rate),
                    'avg_impact': float(avg_impact),
                    'sample_size': len(outcomes),
                })

        return recommendations

    def _save_outcomes(self) -> None:
        """Save outcomes to disk."""
        try:
            path = self.storage_dir / "outcomes.json"
            data = [o.to_dict() for o in self.outcomes]
            path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save outcomes: {e}")

    def _load_outcomes(self) -> None:
        """Load outcomes from disk."""
        try:
            path = self.storage_dir / "outcomes.json"
            if path.exists():
                data = json.loads(path.read_text())
                self.outcomes = [
                    ImprovementOutcome(**o) for o in data
                ]
                self.logger.info(f"Loaded {len(self.outcomes)} outcomes")
        except Exception as e:
            self.logger.error(f"Failed to load outcomes: {e}")

    def _save_model(self) -> None:
        """Save trained model to disk."""
        try:
            path = self.storage_dir / "model.pkl"
            with open(path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'feature_names': self.feature_names,
                }, f)
            self.logger.info("Model saved")
        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")

    def _load_model(self) -> bool:
        """Load trained model from disk."""
        try:
            path = self.storage_dir / "model.pkl"
            if path.exists():
                with open(path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data.get('model')
                    self.scaler = data.get('scaler')
                    self.feature_names = data.get('feature_names', [])
                self.logger.info("Model loaded")
                return True
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
        return False

    def export_summary(self) -> Dict[str, Any]:
        """Export learning system summary.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            'total_outcomes': len(self.outcomes),
            'patterns': self.get_pattern_analysis(),
            'model_available': self.model is not None,
            'storage_location': str(self.storage_dir),
        }
