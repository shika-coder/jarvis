#!/usr/bin/env python3
"""
JARVIS System Monitor - Quick Status Display

Shows real-time system status and metrics.
"""

import asyncio
from jarvis.learning.phase4_integration import Phase4System
from jarvis.monitoring.system_monitor import SystemMonitor, print_welcome, print_quick_start


async def main():
    """Run system monitor."""
    print_welcome()

    # Initialize system
    print("🚀 Initializing JARVIS Phase 4 System...")
    system = Phase4System()
    monitor = SystemMonitor()

    # Display current status
    status = system.get_system_status()
    print(monitor.display_status(status))

    # Get audit trail
    trail = system.get_audit_trail()

    # Display decisions
    if trail.get("decision_history"):
        print(monitor.display_decisions(trail["decision_history"]))
    else:
        print("📋 No decisions recorded yet. Run analyze_and_improve() to start.\n")

    # Display outcomes
    if trail.get("learning_outcomes"):
        print(monitor.display_outcomes(trail["learning_outcomes"]))
    else:
        print("📊 No learning outcomes recorded yet.\n")

    # Health summary
    print("=" * 80)
    print("SYSTEM HEALTH")
    print("=" * 80)
    print(monitor.get_health_summary(status))
    print()

    # Quick start
    print_quick_start()


if __name__ == "__main__":
    asyncio.run(main())
