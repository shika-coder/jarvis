"""
JARVIS System Monitor: Real-time status and metrics display.

Provides terminal-based monitoring of JARVIS system health and activity.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class SystemMonitor:
    """Terminal-based monitoring for JARVIS system."""

    def __init__(self, log_file: Optional[Path] = None):
        """Initialize monitor.

        Args:
            log_file: Optional file to log metrics
        """
        self.log_file = log_file or Path("logs/jarvis_metrics.json")
        self.log_file.parent.mkdir(exist_ok=True)
        self.metrics_history = []

    def display_status(self, status: Dict[str, Any]) -> str:
        """Display formatted system status.

        Args:
            status: System status from Phase4System.get_system_status()

        Returns:
            Formatted status string
        """
        output = []
        output.append("\n" + "=" * 80)
        output.append("JARVIS SYSTEM STATUS")
        output.append("=" * 80)

        # Learning System
        learning = status.get("learning_system", {})
        output.append("\n📚 LEARNING SYSTEM")
        output.append(f"  Outcomes Recorded: {learning.get('outcomes_recorded', 0)}")
        output.append(
            f"  Model Available: {'✅ YES' if learning.get('model_path_exists') else '❌ NO'}"
        )

        # Knowledge Base
        knowledge = status.get("knowledge_base", {})
        output.append("\n📖 KNOWLEDGE BASE")
        output.append(f"  Stored Entries: {knowledge.get('entries', 0)}")
        output.append(f"  Categories: {knowledge.get('categories', 0)}")

        # Decision Engine
        decisions = status.get("decision_engine", {})
        output.append("\n🤖 DECISION ENGINE")
        output.append(f"  Total Decisions: {decisions.get('total_decisions', 0)}")
        output.append(f"  Approved: {decisions.get('approved', 0)}")
        output.append(f"  Rejected: {decisions.get('rejected', 0)}")
        approval_rate = decisions.get("approval_rate", 0)
        output.append(f"  Approval Rate: {approval_rate:.1f}%")
        exec_success = decisions.get("execution_success_rate", 0)
        output.append(f"  Execution Success: {exec_success:.1f}%")

        # Background Optimizer
        bg_opt = status.get("background_optimizer", {})
        output.append("\n⚡ BACKGROUND OPTIMIZER")
        output.append(f"  Pending Tasks: {bg_opt.get('pending_tasks', 0)}")
        output.append(f"  Running Tasks: {bg_opt.get('running_tasks', 0)}")

        stats = bg_opt.get("stats", {})
        output.append(f"  Total Tasks: {stats.get('total', 0)}")
        output.append(f"  Completed: {stats.get('completed', 0)}")
        output.append(f"  Successful: {stats.get('successful', 0)}")
        success_rate = stats.get("success_rate", 0)
        output.append(f"  Success Rate: {success_rate:.1f}%")

        # Multi-Agent Coordinator
        agents = status.get("multi_agent_coordinator", {})
        output.append("\n👥 MULTI-AGENT COORDINATOR")
        output.append(f"  Active Agents: {agents.get('agents', 0)}")
        output.append(f"  Pending Tasks: {agents.get('pending_tasks', 0)}")

        output.append("\n" + "=" * 80)
        output.append(f"Timestamp: {datetime.now().isoformat()}")
        output.append("=" * 80 + "\n")

        result = "\n".join(output)
        return result

    def display_decisions(self, decisions: list) -> str:
        """Display recent decisions.

        Args:
            decisions: List of decisions from audit trail

        Returns:
            Formatted decisions string
        """
        if not decisions:
            return "No decisions recorded yet.\n"

        output = []
        output.append("\n" + "=" * 80)
        output.append("RECENT DECISIONS")
        output.append("=" * 80)

        for i, decision in enumerate(decisions[-10:], 1):  # Last 10
            status = "✅ APPROVED" if decision.get("decision") == "approved" else "❌ REJECTED"
            output.append(f"\n[{i}] {decision.get('improvement', 'unknown')}")
            output.append(f"    Status: {status}")
            output.append(f"    Confidence: {decision.get('confidence', 0):.1%}")
            output.append(f"    Score: {decision.get('final_score', 0):.2f}")
            output.append(f"    Time: {decision.get('created_at', 'unknown')}")

        output.append("\n" + "=" * 80 + "\n")
        return "\n".join(output)

    def display_outcomes(self, outcomes: list) -> str:
        """Display learning outcomes.

        Args:
            outcomes: List of outcomes from audit trail

        Returns:
            Formatted outcomes string
        """
        if not outcomes:
            return "No outcomes recorded yet.\n"

        output = []
        output.append("\n" + "=" * 80)
        output.append("LEARNING OUTCOMES")
        output.append("=" * 80)

        # Stats
        total = len(outcomes)
        successful = sum(1 for o in outcomes if o.get("success"))
        success_rate = (successful / total * 100) if total > 0 else 0

        output.append(f"\nTotal Outcomes: {total}")
        output.append(f"Successful: {successful}")
        output.append(f"Failed: {total - successful}")
        output.append(f"Success Rate: {success_rate:.1f}%")

        # Recent outcomes
        output.append("\nRecent Outcomes (last 10):")
        for i, outcome in enumerate(outcomes[-10:], 1):
            status = "✅" if outcome.get("success") else "❌"
            output.append(
                f"  [{i}] {status} {outcome.get('type', 'unknown')} "
                f"@ {outcome.get('timestamp', 'unknown')}"
            )

        output.append("\n" + "=" * 80 + "\n")
        return "\n".join(output)

    def log_metrics(self, status: Dict[str, Any]) -> None:
        """Log metrics to file.

        Args:
            status: System status to log
        """
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "status": status,
            }
            self.metrics_history.append(metrics)

            # Write to file
            with open(self.log_file, "w") as f:
                json.dump(self.metrics_history[-100:], f, indent=2)  # Keep last 100
        except Exception as e:
            print(f"⚠️  Failed to log metrics: {e}")

    def get_health_summary(self, status: Dict[str, Any]) -> str:
        """Get one-line health summary.

        Args:
            status: System status

        Returns:
            Health summary string
        """
        decisions = status.get("decision_engine", {})
        bg_opt = status.get("background_optimizer", {})
        stats = bg_opt.get("stats", {})

        success_rate = stats.get("success_rate", 0)
        health = "🟢 HEALTHY" if success_rate >= 70 else "🟡 WARNING" if success_rate >= 50 else "🔴 CRITICAL"

        return (
            f"{health} | Decisions: {decisions.get('total_decisions', 0)} | "
            f"Success Rate: {success_rate:.0f}% | "
            f"Pending: {bg_opt.get('pending_tasks', 0)}"
        )


def print_welcome():
    """Print welcome message."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                     JARVIS SYSTEM MONITOR                                 ║
║                  Autonomous AI Code Improvement Agent                     ║
║                                                                            ║
║  Analyzing Code → ML Predictions → Autonomous Decisions → Safe Execution  ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 Real-time monitoring of JARVIS Phase 4 system:
   • Learning System: ML models and outcome tracking
   • Knowledge Base: Pattern storage with confidence scores
   • Decision Engine: Autonomous improvement selection
   • Background Optimizer: Non-blocking task execution
   • Multi-Agent Coordinator: Task delegation

For detailed documentation, see PHASE4_COMPLETION.md
""")


def print_quick_start():
    """Print quick start guide."""
    print("""
🚀 QUICK START
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from jarvis.learning.phase4_integration import Phase4System
from jarvis.monitoring.system_monitor import SystemMonitor

system = Phase4System()
monitor = SystemMonitor()

# Run full autonomous workflow
result = await system.analyze_and_improve(
    file_path="mycode.py",
    auto_execute=True,
    run_background=True
)

# Display real-time status
print(monitor.display_status(system.get_system_status()))

# View decisions and outcomes
trail = system.get_audit_trail()
print(monitor.display_decisions(trail['decision_history']))
print(monitor.display_outcomes(trail['learning_outcomes']))

# Log metrics for monitoring
monitor.log_metrics(system.get_system_status())

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
