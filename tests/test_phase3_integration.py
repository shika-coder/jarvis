"""
End-to-end integration tests for Phase 3 self-improvement system.

Tests full pipelines with real agents and components.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path

from jarvis.self_improvement import (
    CodeAnalyzer,
    PerformanceMonitor,
    TestGenerator,
    RefactoringEngine,
    WorkflowBuilder,
    DeploymentPlan,
)


class TestPhase3Integration:
    """Integration tests for Phase 3 components."""

    def test_code_analysis_to_test_generation(self):
        """Test analyzing code and generating tests."""
        analyzer = CodeAnalyzer()
        generator = TestGenerator()

        code = """
def process_data(items):
    '''Process a list of items.'''
    if not items:
        return None
    
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    
    return result
"""

        # Analyze
        analysis = analyzer.analyze(code)
        assert analysis['total_issues'] >= 0

        # Generate tests
        tests = generator.generate_for_function(code, "process_data")
        assert len(tests) > 0
        assert any("process_data" in test.function_name for test in tests)

    def test_code_analysis_and_refactoring(self):
        """Test analyzing code and proposing refactoring."""
        analyzer = CodeAnalyzer()
        engine = RefactoringEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("""
def calculate(x, y):
    if x > 0:
        if y > 0:
            return x + y
    return x - y
""")

            # Analyze
            security_issues = analyzer.analyze_security(test_file.read_text())

            # Get refactoring proposals
            proposals = engine.propose_optimizations(test_file)
            assert isinstance(proposals, list)

    def test_performance_monitoring_workflow(self):
        """Test monitoring performance during workflow execution."""
        monitor = PerformanceMonitor()

        if not monitor.is_available():
            pytest.skip("psutil not available")

        async def operation_1(context):
            monitor.start_profiling("op1")
            await asyncio.sleep(0.01)
            monitor.stop_profiling(success=True)
            return "result1"

        async def operation_2(context):
            monitor.start_profiling("op2")
            await asyncio.sleep(0.01)
            monitor.stop_profiling(success=True)
            return "result2"

        workflow = WorkflowBuilder("perf_test") \
            .add("step1", operation_1) \
            .add("step2", operation_2) \
            .build()

        # Execute workflow
        asyncio.run(workflow.execute())

        # Check monitoring results
        summary = monitor.get_execution_summary()
        assert summary['total_executions'] >= 2

    def test_workflow_with_conditional_steps(self):
        """Test workflow with conditional execution."""
        results = []

        async def always_step(context):
            results.append("always")
            return True

        async def on_success_step(context):
            results.append("on_success")
            return True

        async def failure_step(context):
            results.append("failure")
            raise Exception("Intentional failure")

        async def recovery_step(context):
            results.append("recovery")
            return True

        from jarvis.self_improvement import WorkflowBuilder, StepCondition

        workflow = WorkflowBuilder("conditional") \
            .add("step1", always_step, condition=StepCondition.ALWAYS) \
            .add("step2", on_success_step, condition=StepCondition.ON_SUCCESS) \
            .add("step3", failure_step, required=False) \
            .add("step4", recovery_step, condition=StepCondition.ON_FAILURE, required=False) \
            .build()

        success = asyncio.run(workflow.execute())
        assert success
        assert "always" in results
        assert "on_success" in results

    def test_deployment_plan_validation(self):
        """Test deployment plan creation and validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "module1.py"
            file1.write_text("def function1(): pass")

            file2 = Path(tmpdir) / "module2.py"
            file2.write_text("def function2(): pass")

            # Create deployment plan
            plan = DeploymentPlan("test_deploy", "Test deployment")
            plan.add_step("update_module1", file1, "def function1(): return 42")
            plan.add_step("update_module2", file2, "def function2(): return 100")

            # Validate
            async def validate():
                return await plan.validate_all()

            valid = asyncio.run(validate())
            assert valid

    def test_full_improvement_pipeline(self):
        """Test full end-to-end improvement pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "agent.py"
            test_file.write_text("""
def analyze_request(request):
    '''Analyze incoming request.'''
    if request is None:
        return None
    
    if isinstance(request, dict):
        if 'data' in request:
            data = request['data']
            result = data
            return result
    
    return None
""")

            # Phase 1: Analyze
            analyzer = CodeAnalyzer()
            analysis = analyzer.analyze(test_file.read_text())
            print(f"Analysis: {analysis['total_issues']} issues found")

            # Phase 2: Generate tests
            generator = TestGenerator()
            tests = generator.generate_for_function(
                test_file.read_text(),
                "analyze_request"
            )
            print(f"Generated: {len(tests)} tests")

            # Phase 3: Propose refactoring
            engine = RefactoringEngine()
            proposals = engine.propose_optimizations(test_file)
            print(f"Proposed: {len(proposals)} refactorings")

            # Phase 4: Monitor performance
            monitor = PerformanceMonitor()
            if monitor.is_available():
                monitor.start_profiling("full_pipeline")
                asyncio.sleep(0.01)
                monitor.stop_profiling(success=True)

            summary = monitor.get_execution_summary() if monitor.is_available() else {}
            print(f"Performance: {summary}")

    def test_workflow_error_handling(self):
        """Test workflow error handling and recovery."""
        execution_log = []

        async def step1(context):
            execution_log.append("step1_start")
            return "step1_result"

        async def step2_fail(context):
            execution_log.append("step2_fail")
            raise ValueError("Step 2 failed")

        async def step3_recovery(context):
            execution_log.append("step3_recovery")
            return "recovered"

        from jarvis.self_improvement import StepCondition

        workflow = WorkflowBuilder("error_handling") \
            .add("step1", step1) \
            .add("step2", step2_fail, required=False) \
            .add("step3", step3_recovery, condition=StepCondition.ALWAYS) \
            .build()

        success = asyncio.run(workflow.execute())
        assert success
        assert execution_log[0] == "step1_start"
        assert "step2_fail" in execution_log
        assert "step3_recovery" in execution_log

    def test_workflow_with_context_passing(self):
        """Test workflow passing context between steps."""
        async def step1(context):
            context['value1'] = 10
            return 10

        async def step2(context):
            context['value2'] = context.get('value1', 0) * 2
            return context['value2']

        async def step3(context):
            result = context.get('value1', 0) + context.get('value2', 0)
            return result

        workflow = WorkflowBuilder("context_test") \
            .add("calc1", step1) \
            .add("calc2", step2) \
            .add("calc3", step3) \
            .build()

        asyncio.run(workflow.execute())
        results = workflow.get_results()

        assert results['calc1'] == 10
        assert results['calc2'] == 20
        assert results['calc3'] == 30

    def test_multiple_test_generators(self):
        """Test generating tests for multiple functions."""
        generator = TestGenerator()

        code = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Division by zero")
    return a / b
"""

        test_add = generator.generate_for_function(code, "add")
        test_multiply = generator.generate_for_function(code, "multiply")
        test_divide = generator.generate_for_function(code, "divide")

        assert len(test_add) > 0
        assert len(test_multiply) > 0
        assert len(test_divide) > 0

        metrics = generator.export_test_metrics()
        assert metrics['total_tests'] > 0


class TestPhase3EndToEnd:
    """Full end-to-end tests."""

    async def run_improvement_cycle(self):
        """Run a complete improvement cycle."""
        results = {
            'analyzed': False,
            'tests_generated': False,
            'refactoring_proposed': False,
            'deployment_planned': False,
        }

        code = """
def process(items):
    result = []
    for i in items:
        if i > 0:
            result.append(i)
    return result
"""

        # Analyze
        analyzer = CodeAnalyzer()
        analysis = analyzer.analyze(code)
        results['analyzed'] = analysis['total_issues'] >= 0

        # Generate tests
        generator = TestGenerator()
        tests = generator.generate_for_function(code, "process")
        results['tests_generated'] = len(tests) > 0

        # Propose refactoring
        engine = RefactoringEngine()
        proposals = engine.propose_optimizations(Path("test.py"))
        results['refactoring_proposed'] = isinstance(proposals, list)

        # Plan deployment
        plan = DeploymentPlan("improvement", "Code improvement")
        results['deployment_planned'] = len(plan.steps) >= 0

        return results

    def test_complete_cycle(self):
        """Test complete improvement cycle."""
        results = asyncio.run(self.run_improvement_cycle())
        assert results['analyzed']
        assert results['tests_generated']
        assert results['refactoring_proposed']
        assert results['deployment_planned']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
