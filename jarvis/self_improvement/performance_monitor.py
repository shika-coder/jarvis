"""
Performance Monitor

Tracks and analyzes agent performance metrics over time.
"""

import time
import psutil
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from jarvis.core.logging import get_logger
from jarvis.self_improvement.base import PerformanceMetric, SelfImprovementBase

logger = get_logger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not installed. Install with: pip install psutil")


@dataclass
class ExecutionProfile:
    """Profile of an execution."""
    name: str
    start_time: float
    end_time: float
    memory_start: int
    memory_end: int
    success: bool
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Execution duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def memory_used(self) -> int:
        """Memory used in bytes."""
        return self.memory_end - self.memory_start


class PerformanceMonitor(SelfImprovementBase):
    """
    Monitors and analyzes agent performance metrics.
    
    Tracks:
    - Execution times
    - Memory usage
    - Success/failure rates
    - Error patterns
    - Performance trends
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        super().__init__(enabled=PSUTIL_AVAILABLE)
        self.executions: List[ExecutionProfile] = []
        self.metrics: List[PerformanceMetric] = []
        self.current_execution: Optional[ExecutionProfile] = None
    
    def start_profiling(self, name: str) -> None:
        """
        Start profiling an operation.
        
        Args:
            name: Name of the operation
        """
        if not self.enabled:
            logger.warning("Performance monitoring disabled")
            return
        
        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            self.current_execution = ExecutionProfile(
                name=name,
                start_time=time.time(),
                end_time=0,
                memory_start=mem_info.rss,
                memory_end=0,
                success=False
            )
            
            logger.debug(f"Started profiling: {name}")
        except Exception as e:
            logger.error(f"Failed to start profiling: {e}")
    
    def stop_profiling(self, success: bool = True, error: Optional[str] = None) -> Optional[ExecutionProfile]:
        """
        Stop profiling and record execution profile.
        
        Args:
            success: Whether the operation succeeded
            error: Error message if failed
        
        Returns:
            ExecutionProfile if profiling active, None otherwise
        """
        if not self.enabled or self.current_execution is None:
            return None
        
        try:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            
            self.current_execution.end_time = time.time()
            self.current_execution.memory_end = mem_info.rss
            self.current_execution.success = success
            self.current_execution.error = error
            
            self.executions.append(self.current_execution)
            
            # Create metrics
            duration_metric = PerformanceMetric(
                metric_name=f"{self.current_execution.name}_duration",
                value=self.current_execution.duration,
                unit="ms",
                threshold=5.0  # 5ms threshold
            )
            duration_metric.exceeded = duration_metric.value > duration_metric.threshold
            self.metrics.append(duration_metric)
            
            memory_metric = PerformanceMetric(
                metric_name=f"{self.current_execution.name}_memory",
                value=self.current_execution.memory_used / (1024 * 1024),  # Convert to MB
                unit="MB",
                threshold=100.0  # 100MB threshold
            )
            memory_metric.exceeded = memory_metric.value > memory_metric.threshold
            self.metrics.append(memory_metric)
            
            # Log result
            status = "✓" if success else "✗"
            logger.info(
                f"{status} {self.current_execution.name}: "
                f"{self.current_execution.duration:.3f}s, "
                f"{self.current_execution.memory_used / 1024:.1f}KB"
            )
            
            profile = self.current_execution
            self.current_execution = None
            return profile
        except Exception as e:
            logger.error(f"Failed to stop profiling: {e}")
            return None
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions."""
        if not self.executions:
            return {"executions": 0}
        
        successful = sum(1 for e in self.executions if e.success)
        failed = len(self.executions) - successful
        
        durations = [e.duration for e in self.executions]
        memory_used = [e.memory_used / (1024 * 1024) for e in self.executions]
        
        return {
            "total_executions": len(self.executions),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(self.executions) if self.executions else 0,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "avg_memory": sum(memory_used) / len(memory_used) if memory_used else 0,
            "max_memory": max(memory_used) if memory_used else 0,
        }
    
    def get_operation_metrics(self, operation_name: str) -> Dict[str, Any]:
        """Get metrics for a specific operation."""
        operations = [e for e in self.executions if e.name == operation_name]
        
        if not operations:
            return {"found": False}
        
        durations = [e.duration for e in operations]
        memory_used = [e.memory_used / (1024 * 1024) for e in operations]
        successful = sum(1 for e in operations if e.success)
        
        return {
            "found": True,
            "count": len(operations),
            "successful": successful,
            "failed": len(operations) - successful,
            "success_rate": successful / len(operations),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "avg_memory": sum(memory_used) / len(memory_used),
            "max_memory": max(memory_used),
        }
    
    def get_slowest_operations(self, top_n: int = 10) -> List[ExecutionProfile]:
        """Get slowest operations."""
        sorted_executions = sorted(self.executions, key=lambda e: e.duration, reverse=True)
        return sorted_executions[:top_n]
    
    def get_memory_intensive_operations(self, top_n: int = 10) -> List[ExecutionProfile]:
        """Get most memory-intensive operations."""
        sorted_executions = sorted(self.executions, key=lambda e: e.memory_used, reverse=True)
        return sorted_executions[:top_n]
    
    def get_high_failure_operations(self, threshold: float = 0.2) -> List[str]:
        """Get operations with high failure rates."""
        operation_stats = {}
        
        for execution in self.executions:
            if execution.name not in operation_stats:
                operation_stats[execution.name] = {"total": 0, "failed": 0}
            
            operation_stats[execution.name]["total"] += 1
            if not execution.success:
                operation_stats[execution.name]["failed"] += 1
        
        problematic = []
        for op, stats in operation_stats.items():
            failure_rate = stats["failed"] / stats["total"]
            if failure_rate >= threshold:
                problematic.append(op)
        
        return problematic
    
    def get_anomalies(self) -> List[Dict[str, Any]]:
        """Detect performance anomalies."""
        anomalies = []
        
        # Check for excessive duration
        summary = self.get_execution_summary()
        avg_duration = summary.get("avg_duration", 0)
        
        for execution in self.executions[-10:]:  # Check last 10
            if execution.duration > avg_duration * 2:
                anomalies.append({
                    "type": "slow_execution",
                    "operation": execution.name,
                    "duration": execution.duration,
                    "avg_duration": avg_duration,
                    "multiplier": execution.duration / avg_duration if avg_duration > 0 else 0,
                })
        
        # Check for memory spikes
        avg_memory = summary.get("avg_memory", 0)
        
        for execution in self.executions[-10:]:
            if execution.memory_used / (1024 * 1024) > avg_memory * 3:
                anomalies.append({
                    "type": "memory_spike",
                    "operation": execution.name,
                    "memory": execution.memory_used / (1024 * 1024),
                    "avg_memory": avg_memory,
                    "multiplier": (execution.memory_used / (1024 * 1024)) / avg_memory if avg_memory > 0 else 0,
                })
        
        return anomalies
    
    def export_metrics(self) -> List[Dict[str, Any]]:
        """Export all recorded metrics."""
        return [
            {
                "timestamp": m.timestamp,
                "metric_name": m.metric_name,
                "value": m.value,
                "unit": m.unit,
                "threshold": m.threshold,
                "exceeded": m.exceeded,
            }
            for m in self.metrics
        ]
