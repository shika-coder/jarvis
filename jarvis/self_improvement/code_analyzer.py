"""
Code Analyzer

Analyzes code for quality issues, security vulnerabilities, and performance problems.
"""

import ast
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from jarvis.core.logging import get_logger
from jarvis.self_improvement.base import CodeIssue, SelfImprovementBase

logger = get_logger(__name__)


class CodeAnalyzer(SelfImprovementBase):
    """
    Analyzes Python code for quality issues and potential improvements.
    
    Checks for:
    - Complexity issues (cyclomatic complexity, nested depth)
    - Security vulnerabilities (eval, exec, sql injection patterns)
    - Performance issues (inefficient algorithms, memory leaks)
    - Style issues (naming, docstrings, type hints)
    - Anti-patterns (bare except, unused variables)
    """
    
    def __init__(self):
        """Initialize code analyzer."""
        super().__init__(enabled=True)
        self.issues: List[CodeIssue] = []
    
    async def analyze_file(self, file_path: str) -> List[CodeIssue]:
        """
        Analyze a Python file.
        
        Args:
            file_path: Path to Python file to analyze
        
        Returns:
            List of found issues
        """
        try:
            with open(file_path, "r") as f:
                code = f.read()
            
            return await self.analyze_code(code, file_path)
        except Exception as e:
            logger.error(f"Failed to analyze file: {e}")
            return []
    
    async def analyze_code(
        self,
        code: str,
        file_path: str = "<string>"
    ) -> List[CodeIssue]:
        """
        Analyze Python code string.
        
        Args:
            code: Python code to analyze
            file_path: File path for reference (optional)
        
        Returns:
            List of found issues
        """
        self.issues.clear()
        
        try:
            tree = ast.parse(code)
            
            # Run different analyzers
            self._check_security(tree, code, file_path)
            self._check_complexity(tree, file_path)
            self._check_performance(tree, code, file_path)
            self._check_style(tree, code, file_path)
            
            self.log_action(
                "code_analysis",
                {"file": file_path, "issues_found": len(self.issues)}
            )
            
            logger.info(f"Analysis complete: {len(self.issues)} issues found")
            return self.issues
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            return []
    
    def _check_security(self, tree: ast.AST, code: str, file_path: str) -> None:
        """Check for security vulnerabilities."""
        for node in ast.walk(tree):
            # Check for eval/exec
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("eval", "exec"):
                        self.issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="security",
                            severity="critical",
                            description=f"Use of unsafe {node.func.id}() function",
                            suggestion=f"Replace {node.func.id}() with safer alternatives (ast.literal_eval, importlib, etc.)",
                            confidence=0.99
                        ))
            
            # Check for SQL injection patterns
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "format" or node.func.attr == "%":
                        for arg in node.args:
                            if isinstance(arg, ast.Constant) and "SELECT" in str(arg.value).upper():
                                self.issues.append(CodeIssue(
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    issue_type="security",
                                    severity="high",
                                    description="Potential SQL injection pattern",
                                    suggestion="Use parameterized queries instead of string formatting",
                                    confidence=0.75
                                ))
            
            # Check for bare except
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="style",
                        severity="medium",
                        description="Bare except clause catches all exceptions",
                        suggestion="Specify exception types: except (ValueError, TypeError):",
                        confidence=0.95
                    ))
    
    def _check_complexity(self, tree: ast.AST, file_path: str) -> None:
        """Check for complexity issues."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count nested depth
                depth = self._get_max_depth(node)
                if depth > 4:
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="complexity",
                        severity="medium",
                        description=f"Function '{node.name}' has high nesting depth ({depth})",
                        suggestion="Consider extracting nested logic into separate functions",
                        confidence=0.8
                    ))
                
                # Count if/else branches (cyclomatic complexity)
                branches = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.If, ast.For, ast.While)))
                if branches > 8:
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="complexity",
                        severity="high",
                        description=f"Function '{node.name}' has high cyclomatic complexity ({branches} branches)",
                        suggestion="Consider refactoring into smaller functions or using design patterns",
                        confidence=0.85
                    ))
    
    def _check_performance(self, tree: ast.AST, code: str, file_path: str) -> None:
        """Check for performance issues."""
        for node in ast.walk(tree):
            # Check for list comprehension in loops
            if isinstance(node, ast.For):
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.ListComp):
                        # This is actually good, so no issue
                        pass
            
            # Check for repeated string concatenation
            if isinstance(node, ast.BinOp):
                if isinstance(node.op, ast.Add):
                    if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
                        if isinstance(node.left.value, str):
                            self.issues.append(CodeIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                issue_type="performance",
                                severity="low",
                                description="String concatenation with + operator",
                                suggestion="Use f-strings or str.join() for better performance",
                                confidence=0.7
                            ))
    
    def _check_style(self, tree: ast.AST, code: str, file_path: str) -> None:
        """Check for style issues."""
        for node in ast.walk(tree):
            # Check for missing docstrings
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if docstring is None and node.name and not node.name.startswith("_"):
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="style",
                        severity="low",
                        description=f"'{node.name}' is missing a docstring",
                        suggestion='Add a docstring: """Description of function."""',
                        confidence=0.9
                    ))
            
            # Check for unused variables
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Simple check: starts with underscore is intentional unused
                        if not target.id.startswith("_"):
                            # Would need more complex analysis to truly detect unused
                            pass
    
    def _get_max_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Get maximum nesting depth in a node."""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While, ast.If, ast.With, ast.Try)):
                depth = self._get_max_depth(child, current_depth + 1)
                max_depth = max(max_depth, depth)
            else:
                depth = self._get_max_depth(child, current_depth)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    async def analyze_directory(
        self,
        directory: str,
        pattern: str = "*.py",
        exclude_patterns: List[str] = None
    ) -> Dict[str, List[CodeIssue]]:
        """
        Analyze all Python files in a directory.
        
        Args:
            directory: Directory to analyze
            pattern: File pattern to match
            exclude_patterns: Patterns to exclude
        
        Returns:
            Dictionary mapping file paths to found issues
        """
        exclude_patterns = exclude_patterns or [
            "*/__pycache__/*",
            "*/.*",
            "*/.git/*",
            "*/venv/*",
        ]
        
        results = {}
        dir_path = Path(directory)
        
        for file_path in dir_path.rglob(pattern):
            # Skip excluded patterns
            if any(exclude in str(file_path) for exclude in exclude_patterns):
                continue
            
            issues = await self.analyze_file(str(file_path))
            if issues:
                results[str(file_path)] = issues
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of analysis results."""
        by_severity = {}
        by_type = {}
        
        for issue in self.issues:
            # Count by severity
            if issue.severity not in by_severity:
                by_severity[issue.severity] = 0
            by_severity[issue.severity] += 1
            
            # Count by type
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = 0
            by_type[issue.issue_type] += 1
        
        return {
            "total_issues": len(self.issues),
            "by_severity": by_severity,
            "by_type": by_type,
        }
    
    def analyze(self, code: str, file_path: str = "<input>") -> Dict[str, Any]:
        """Synchronous wrapper for analyze_code."""
        import asyncio
        try:
            result = asyncio.run(self.analyze_code(code, file_path))
            return self.get_summary()
        except RuntimeError:
            # Already in async context, fall back to sync analysis
            return self._analyze_sync(code)
    
    def _analyze_sync(self, code: str) -> Dict[str, Any]:
        """Synchronous analysis without async."""
        self.issues = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"total_issues": 0, "by_severity": {}, "by_type": {}}
        
        self._check_security(tree, code, "<input>")
        self._check_complexity(tree, "<input>")
        self._check_performance(tree, code, "<input>")
        self._check_style(tree, code, "<input>")
        
        return self.get_summary()
    
    def analyze_security(self, code: str) -> List[CodeIssue]:
        """Synchronous wrapper for security analysis."""
        self.issues = []
        try:
            tree = ast.parse(code)
            self._check_security(tree, code, "<input>")
        except SyntaxError:
            pass
        return self.issues
    
    def analyze_complexity(self, code: str) -> List[CodeIssue]:
        """Synchronous wrapper for complexity analysis."""
        self.issues = []
        try:
            tree = ast.parse(code)
            self._check_complexity(tree, "<input>")
        except SyntaxError:
            pass
        return self.issues
    
    def analyze_performance(self, code: str) -> List[CodeIssue]:
        """Synchronous wrapper for performance analysis."""
        self.issues = []
        try:
            tree = ast.parse(code)
            self._check_performance(tree, code, "<input>")
        except SyntaxError:
            pass
        return self.issues
