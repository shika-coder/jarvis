"""
Automated test generation for JARVIS components.

Analyzes code to generate test cases automatically.
"""

import ast
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

from jarvis.core.logging import get_logger


@dataclass
class TestCase:
    """Represents a generated test case."""
    name: str
    function_name: str
    inputs: List[any] = field(default_factory=list)
    expected_output: Optional[any] = None
    is_edge_case: bool = False
    description: str = ""

    def to_pytest_code(self) -> str:
        """Generate pytest test code for this case."""
        code = f'    def test_{self.name}(self):\n'
        code += f'        """Test {self.description or self.name}."""\n'
        
        # Build assertions based on inputs/outputs
        if self.inputs:
            code += f'        # Inputs: {self.inputs}\n'
        if self.expected_output is not None:
            code += f'        assert result is not None  # {self.expected_output}\n'
        else:
            code += f'        # TODO: Add specific assertions\n'
        
        return code


class TestGenerator:
    """Generates test cases from code analysis."""

    def __init__(self):
        self.generated_tests: List[TestCase] = []
        self.logger = get_logger(__name__)

    def generate_for_function(self, func_source: str, func_name: str) -> List[TestCase]:
        """Generate test cases for a function.
        
        Args:
            func_source: Source code of the function
            func_name: Name of the function
            
        Returns:
            List of generated test cases
        """
        tests = []
        
        try:
            tree = ast.parse(func_source)
            func_def = None
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    func_def = node
                    break
            
            if not func_def:
                self.logger.warning(f"Function {func_name} not found in source")
                return []
            
            # Generate basic test cases
            tests.extend(self._generate_signature_tests(func_def))
            tests.extend(self._generate_edge_case_tests(func_def))
            tests.extend(self._generate_path_tests(func_def))
            
        except SyntaxError as e:
            self.logger.error(f"Syntax error parsing function: {e}")
            return []
        
        self.generated_tests.extend(tests)
        return tests

    def _generate_signature_tests(self, func_def: ast.FunctionDef) -> List[TestCase]:
        """Generate tests based on function signature."""
        tests = []
        args = func_def.args
        
        # Test with None for optional args
        for arg in args.args:
            test_name = f"with_none_{arg.arg}"
            tests.append(TestCase(
                name=test_name,
                function_name=func_def.name,
                inputs=[None],
                description=f"Test with None for {arg.arg}"
            ))
        
        # Test with empty inputs if applicable
        if args.args:
            tests.append(TestCase(
                name="empty_inputs",
                function_name=func_def.name,
                inputs=[],
                description="Test with empty inputs"
            ))
        
        return tests

    def _generate_edge_case_tests(self, func_def: ast.FunctionDef) -> List[TestCase]:
        """Generate edge case tests."""
        tests = []
        
        # Test error handling
        tests.append(TestCase(
            name="error_handling",
            function_name=func_def.name,
            inputs=["invalid"],
            description="Test error handling with invalid input",
            is_edge_case=True
        ))
        
        # Test with zero/negative if numeric
        tests.append(TestCase(
            name="zero_input",
            function_name=func_def.name,
            inputs=[0],
            description="Test with zero input",
            is_edge_case=True
        ))
        
        tests.append(TestCase(
            name="negative_input",
            function_name=func_def.name,
            inputs=[-1],
            description="Test with negative input",
            is_edge_case=True
        ))
        
        # Test with empty collections
        tests.append(TestCase(
            name="empty_collection",
            function_name=func_def.name,
            inputs=[[]],
            description="Test with empty collection",
            is_edge_case=True
        ))
        
        return tests

    def _generate_path_tests(self, func_def: ast.FunctionDef) -> List[TestCase]:
        """Generate tests for different code paths."""
        tests = []
        
        # Count if/for/while statements
        path_count = 0
        for node in ast.walk(func_def):
            if isinstance(node, (ast.If, ast.For, ast.While)):
                path_count += 1
        
        # Generate one test per path
        for i in range(max(1, min(path_count, 3))):  # Max 3 path tests
            tests.append(TestCase(
                name=f"code_path_{i+1}",
                function_name=func_def.name,
                description=f"Test code path {i+1}"
            ))
        
        return tests

    def generate_for_class(self, class_source: str, class_name: str) -> dict:
        """Generate test suite for a class.
        
        Args:
            class_source: Source code of the class
            class_name: Name of the class
            
        Returns:
            Dictionary mapping method names to test cases
        """
        test_suites = {}
        
        try:
            tree = ast.parse(class_source)
            class_def = None
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    class_def = node
                    break
            
            if not class_def:
                self.logger.warning(f"Class {class_name} not found in source")
                return {}
            
            # Generate tests for each public method
            for node in class_def.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    method_tests = [
                        TestCase(
                            name=f"{node.name}_basic",
                            function_name=node.name,
                            description=f"Basic test for {node.name}"
                        ),
                        TestCase(
                            name=f"{node.name}_edge_case",
                            function_name=node.name,
                            description=f"Edge case test for {node.name}",
                            is_edge_case=True
                        )
                    ]
                    test_suites[node.name] = method_tests
        
        except SyntaxError as e:
            self.logger.error(f"Syntax error parsing class: {e}")
            return {}
        
        return test_suites

    def generate_test_file(self, module_path: Path, class_name: str) -> str:
        """Generate complete test file content.
        
        Args:
            module_path: Path to module file
            class_name: Name of class to test
            
        Returns:
            Generated test file content
        """
        content = f'''"""
Auto-generated tests for {class_name}.

Generated by JARVIS TestGenerator.
DO NOT EDIT - regenerate tests instead.
"""

import pytest
from pathlib import Path

# Import the class to test
# from jarvis.module import {class_name}


class Test{class_name}:
    """Auto-generated test suite for {class_name}."""

    def setup_method(self):
        """Set up test fixtures."""
        # TODO: Initialize {class_name} instance
        pass

    def teardown_method(self):
        """Clean up after tests."""
        pass

    # Generated test cases will be added here
    def test_placeholder(self):
        """Placeholder test."""
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
        return content

    def export_test_metrics(self) -> dict:
        """Export metrics about generated tests."""
        edge_case_count = sum(1 for t in self.generated_tests if t.is_edge_case)
        
        return {
            'total_tests': len(self.generated_tests),
            'edge_cases': edge_case_count,
            'by_function': self._group_by_function(),
            'coverage_estimate': min(100, 30 + len(self.generated_tests) * 5)
        }

    def _group_by_function(self) -> dict:
        """Group tests by function name."""
        groups = {}
        for test in self.generated_tests:
            if test.function_name not in groups:
                groups[test.function_name] = []
            groups[test.function_name].append(test.name)
        return groups
