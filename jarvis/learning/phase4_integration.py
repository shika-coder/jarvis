"""
Phase 4 Integration: Unified AI system coordinating all components.

Integrates:
- Learning System (ML predictions)
- Knowledge Base (pattern storage)
- Predictive Analyzer (ranked recommendations)
- AI Decision Engine (autonomous decisions)
- Multi-Agent Coordinator (task execution)
- Background Optimizer (continuous improvement)

Creates seamless workflow from analysis → prediction → decision → execution → learning feedback.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from jarvis.learning.learning_system import LearningSystem
from jarvis.learning.knowledge_base import KnowledgeBase
from jarvis.learning.predictive_analyzer import PredictiveAnalyzer
from jarvis.learning.ai_decision_engine import AIDecisionEngine
from jarvis.learning.background_optimizer import BackgroundOptimizer, OptimizationPriority
from jarvis.agents.multi_agent_coordinator import MultiAgentCoordinator, Task, AgentType
from jarvis.self_improvement.code_analyzer import CodeAnalyzer


logger = logging.getLogger(__name__)


class Phase4System:
    """Unified Phase 4 AI system integrating all learning and coordination components."""

    def __init__(
        self,
        learning_system: Optional[LearningSystem] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
        code_analyzer: Optional[CodeAnalyzer] = None,
        multi_agent_coordinator: Optional[MultiAgentCoordinator] = None,
    ):
        """Initialize Phase 4 system.

        Args:
            learning_system: ML learning engine (created if None)
            knowledge_base: Pattern storage (created if None)
            code_analyzer: Code analysis engine (created if None)
            multi_agent_coordinator: Agent coordination (created if None)
        """
        self.learning_system = learning_system or LearningSystem()
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.code_analyzer = code_analyzer or CodeAnalyzer()
        self.multi_agent_coordinator = multi_agent_coordinator or MultiAgentCoordinator()

        # Create dependent systems
        self.predictive_analyzer = PredictiveAnalyzer(
            self.learning_system,
            self.knowledge_base,
        )
        self.decision_engine = AIDecisionEngine(
            self.predictive_analyzer,
            self.knowledge_base,
        )
        self.background_optimizer = BackgroundOptimizer(
            self.predictive_analyzer,
            max_concurrent=2,
            rate_limit_per_second=1.0,
        )

        self._initialized = True
        logger.info("Phase 4 System initialized")

    async def analyze_and_improve(
        self,
        file_path: str,
        auto_execute: bool = False,
        run_background: bool = False,
    ) -> Dict[str, Any]:
        """Full improvement workflow: analyze → predict → decide → execute.

        Args:
            file_path: File to analyze and improve
            auto_execute: Auto-execute approved improvements
            run_background: Run improvements in background

        Returns:
            Workflow results with decisions and outcomes
        """
        logger.info(f"Starting full workflow for {file_path}")

        results = {
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "analysis": None,
            "predictions": [],
            "decisions": [],
            "executed_tasks": [],
            "background_tasks": [],
        }

        try:
            # Step 1: Analyze code
            logger.info("Step 1: Analyzing code...")
            analysis = await self.code_analyzer.analyze_async(file_path)
            results["analysis"] = {
                "issues": [
                    {
                        "type": issue.get("type"),
                        "severity": issue.get("severity"),
                        "message": issue.get("message"),
                    }
                    for issue in analysis.get("issues", [])
                    if isinstance(issue, dict)
                ],
                "metrics": analysis.get("metrics", {}),
            }

            # Step 2: Generate predictions
            logger.info("Step 2: Generating predictions...")
            predictions = self.predictive_analyzer.analyze(analysis.get("metrics", {}))
            results["predictions"] = [
                {
                    "type": p.improvement_type,
                    "confidence": p.confidence,
                    "impact": p.expected_impact,
                    "rationale": p.rationale,
                }
                for p in predictions
            ]

            # Step 3: Make decisions
            logger.info("Step 3: Making autonomous decisions...")
            decisions = self.decision_engine.make_decision(file_path, predictions)
            results["decisions"] = [
                {
                    "id": d.id,
                    "improvement": d.prediction.improvement_type,
                    "approved": d.decision,
                    "score": d.scoring.final_score,
                    "reasoning": d.reasoning,
                }
                for d in decisions
            ]

            # Step 4: Execute or queue improvements
            approved = self.decision_engine.get_approved_decisions()

            if auto_execute:
                if run_background:
                    logger.info("Step 4: Queueing improvements for background execution...")
                    for decision in approved:
                        task_id = self.background_optimizer.add_task(
                            file_path,
                            decision.prediction,
                            priority=OptimizationPriority.NORMAL,
                        )
                        results["background_tasks"].append(task_id)
                else:
                    logger.info("Step 4: Executing improvements...")
                    for decision in approved:
                        task = Task(
                            id=f"imp-{decision.id}",
                            task_type="apply_improvement",
                            data={
                                "file_path": file_path,
                                "improvement_type": decision.prediction.improvement_type,
                                "prediction": decision.prediction,
                            },
                            agent_type=AgentType.OPTIMIZER,
                        )
                        await self.multi_agent_coordinator.delegate_task(task)
                        results["executed_tasks"].append(task.id)

        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            results["error"] = str(e)

        logger.info(f"Workflow completed: {len(approved)} improvements approved")
        return results

    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status."""
        return {
            "initialized": self._initialized,
            "learning_system": {
                "outcomes_recorded": len(self.learning_system.outcomes),
                "model_path_exists": (
                    self.learning_system.model_path.exists()
                    if hasattr(self.learning_system, "model_path")
                    else False
                ),
            },
            "knowledge_base": {
                "entries": len(self.knowledge_base.entries),
                "categories": len(set(e.category for e in self.knowledge_base.entries.values())),
            },
            "decision_engine": self.decision_engine.get_stats(),
            "background_optimizer": {
                "pending_tasks": self.background_optimizer.get_pending_count(),
                "running_tasks": self.background_optimizer.get_running_count(),
                "stats": {
                    "total": self.background_optimizer.stats.total_tasks,
                    "completed": self.background_optimizer.stats.completed_tasks,
                    "successful": self.background_optimizer.stats.successful_tasks,
                    "success_rate": self.background_optimizer.stats.success_rate(),
                },
            },
            "multi_agent_coordinator": {
                "agents": len(self.multi_agent_coordinator.agents),
                "pending_tasks": len(self.multi_agent_coordinator.task_queue),
            },
        }

    async def record_outcome(
        self,
        improvement_type: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record improvement outcome for learning feedback.

        Args:
            improvement_type: Type of improvement applied
            success: Whether improvement was successful
            details: Additional outcome details
        """
        from jarvis.learning.learning_system import ImprovementOutcome

        outcome = ImprovementOutcome(
            improvement_type=improvement_type,
            success=success,
            details=details or {},
        )
        self.learning_system.record_outcome(outcome)

        # Update knowledge base if successful
        if success:
            self.knowledge_base.update_success(improvement_type)

        logger.info(
            f"Recorded outcome: {improvement_type} = "
            f"{'✓ SUCCESS' if success else '✗ FAILURE'}"
        )

    def export_system_state(self) -> Dict[str, Any]:
        """Export complete system state for serialization."""
        return {
            "learning_system": self.learning_system.export_summary(),
            "knowledge_base": self.knowledge_base.export(),
            "decision_stats": self.decision_engine.get_stats(),
            "optimization_stats": {
                "total_tasks": self.background_optimizer.stats.total_tasks,
                "successful": self.background_optimizer.stats.successful_tasks,
                "success_rate": self.background_optimizer.stats.success_rate(),
            },
        }

    async def import_system_state(self, state: Dict[str, Any]) -> None:
        """Import system state from serialization."""
        try:
            if "knowledge_base" in state:
                await self.knowledge_base.import_json(state["knowledge_base"])
            logger.info("System state imported successfully")
        except Exception as e:
            logger.error(f"Failed to import system state: {e}", exc_info=True)

    def get_audit_trail(self) -> Dict[str, Any]:
        """Get complete audit trail for all decisions and executions."""
        return {
            "decision_history": self.decision_engine.get_decision_history(),
            "learning_outcomes": [
                {
                    "type": o.improvement_type,
                    "success": o.success,
                    "timestamp": o.timestamp.isoformat(),
                }
                for o in self.learning_system.outcomes
            ],
            "background_tasks": self.background_optimizer.get_all_tasks(),
        }

    async def reset(self, keep_knowledge: bool = True) -> None:
        """Reset system state.

        Args:
            keep_knowledge: Keep knowledge base entries
        """
        logger.warning("Resetting Phase 4 system...")
        self.learning_system = LearningSystem()
        if not keep_knowledge:
            self.knowledge_base = KnowledgeBase()
        self.decision_engine = AIDecisionEngine(
            self.predictive_analyzer,
            self.knowledge_base,
        )
        self.background_optimizer = BackgroundOptimizer(
            self.predictive_analyzer,
        )
        logger.info("System reset complete")
