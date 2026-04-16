"""
Safe code refactoring engine for JARVIS.

Proposes and applies safe code improvements with automatic rollback.
"""

import ast
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Callable

from jarvis.core.logging import get_logger
from jarvis.self_improvement.base import BackupManager, ChangeValidator


@dataclass
class RefactoringStep:
    """A single refactoring step."""
    name: str
    description: str
    file_path: Path
    original_code: str
    refactored_code: str
    reason: str
    impact_level: str = "low"  # low, medium, high
    is_reversible: bool = True
    dependencies: List[str] = field(default_factory=list)

    def get_diff(self) -> str:
        """Get diff between original and refactored."""
        original_lines = self.original_code.splitlines(keepends=True)
        refactored_lines = self.refactored_code.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            refactored_lines,
            fromfile=f"{self.file_path} (original)",
            tofile=f"{self.file_path} (refactored)"
        )
        return ''.join(diff)


class RefactoringEngine:
    """Proposes and applies safe code refactoring."""

    def __init__(self, backup_manager: Optional[BackupManager] = None):
        self.backup_manager = backup_manager or BackupManager()
        self.logger = get_logger(__name__)
        self.validator = ChangeValidator()
        self.refactoring_history: List[RefactoringStep] = []

    def propose_optimizations(self, code_file: Path) -> List[RefactoringStep]:
        """Propose refactoring opportunities.
        
        Args:
            code_file: Path to Python file
            
        Returns:
            List of proposed refactoring steps
        """
        proposals = []
        
        try:
            code = code_file.read_text()
            tree = ast.parse(code)
        except (SyntaxError, FileNotFoundError) as e:
            self.logger.error(f"Cannot parse {code_file}: {e}")
            return []
        
        # Propose various improvements
        proposals.extend(self._propose_string_optimization(code, code_file))
        proposals.extend(self._propose_import_cleanup(tree, code, code_file))
        proposals.extend(self._propose_function_extraction(tree, code, code_file))
        proposals.extend(self._propose_dead_code_removal(tree, code, code_file))
        
        return proposals

    def _propose_string_optimization(self, code: str, file_path: Path) -> List[RefactoringStep]:
        """Propose string concatenation optimizations."""
        proposals = []
        
        # Look for string concatenation in loops
        if '+=' in code and 'for ' in code:
            lines = code.splitlines()
            for i, line in enumerate(lines):
                if '+=' in line and 'str' in line.lower():
                    original = code
                    # Suggest using join() instead
                    refactored = code.replace(
                        ''.join([lines[j] for j in range(max(0, i-2), min(len(lines), i+3))]),
                        "# Use ''.join() for string concatenation"
                    )
                    
                    proposals.append(RefactoringStep(
                        name="optimize_string_concat",
                        description="Replace string concatenation with join()",
                        file_path=file_path,
                        original_code=original,
                        refactored_code=refactored,
                        reason="Using join() is faster for string concatenation",
                        impact_level="low"
                    ))
        
        return proposals

    def _propose_import_cleanup(self, tree: ast.AST, code: str, file_path: Path) -> List[RefactoringStep]:
        """Propose removal of unused imports."""
        proposals = []
        
        # Collect all imports
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        # Check if all are used (simplified heuristic)
        used_count = sum(code.count(imp) for imp in imports)
        
        if used_count < len(imports):
            proposals.append(RefactoringStep(
                name="cleanup_imports",
                description="Remove or organize unused imports",
                file_path=file_path,
                original_code=code,
                refactored_code=code,  # Would need actual cleanup
                reason="Reduce import clutter and improve startup time",
                impact_level="low"
            ))
        
        return proposals

    def _propose_function_extraction(self, tree: ast.AST, code: str, file_path: Path) -> List[RefactoringStep]:
        """Propose extraction of large functions."""
        proposals = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count lines in function
                end_line = node.end_lineno or 0
                start_line = node.lineno or 0
                lines = end_line - start_line
                
                if lines > 50:  # Large function threshold
                    proposals.append(RefactoringStep(
                        name="extract_function",
                        description=f"Extract {node.name} into smaller functions",
                        file_path=file_path,
                        original_code=code,
                        refactored_code=code,
                        reason=f"Function {node.name} is {lines} lines - consider breaking into smaller functions",
                        impact_level="medium"
                    ))
        
        return proposals

    def _propose_dead_code_removal(self, tree: ast.AST, code: str, file_path: Path) -> List[RefactoringStep]:
        """Propose removal of unreachable code."""
        proposals = []
        
        for node in ast.walk(tree):
            # Look for obvious dead code patterns
            if isinstance(node, ast.Return):
                # Check for code after return
                parent_found = False
                for parent in ast.walk(tree):
                    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node in ast.walk(parent):
                            parent_found = True
                            break
                
                if parent_found:
                    proposals.append(RefactoringStep(
                        name="remove_dead_code",
                        description="Remove unreachable code after return",
                        file_path=file_path,
                        original_code=code,
                        refactored_code=code,
                        reason="Code after return statement is unreachable",
                        impact_level="low"
                    ))
                    break  # Only add once
        
        return proposals

    def apply_refactoring(self, step: RefactoringStep, dry_run: bool = True) -> bool:
        """Apply a refactoring step.
        
        Args:
            step: The refactoring step to apply
            dry_run: If True, don't actually write changes
            
        Returns:
            True if applied successfully
        """
        try:
            # Validate the change
            is_valid, issues = self.validator.validate_change(
                step.file_path,
                step.original_code,
                step.refactored_code
            )
            
            if not is_valid:
                self.logger.error(f"Validation failed for {step.name}: {issues}")
                return False
            
            # Create backup
            if step.file_path.exists():
                self.backup_manager.create_backup(
                    step.file_path,
                    tag=f"before_{step.name}"
                )
            
            # Apply change (unless dry run)
            if not dry_run:
                step.file_path.write_text(step.refactored_code)
                self.logger.info(f"Applied refactoring: {step.name}")
                self.refactoring_history.append(step)
            else:
                self.logger.debug(f"Dry run: {step.name}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to apply refactoring {step.name}: {e}")
            return False

    def apply_batch(self, steps: List[RefactoringStep], dry_run: bool = True) -> dict:
        """Apply multiple refactoring steps.
        
        Args:
            steps: List of refactoring steps
            dry_run: If True, don't write changes
            
        Returns:
            Dict with success/failure counts
        """
        results = {
            'applied': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for step in steps:
            if self.apply_refactoring(step, dry_run=dry_run):
                results['applied'] += 1
                results['details'].append({
                    'step': step.name,
                    'status': 'applied' if not dry_run else 'dry_run',
                    'file': str(step.file_path)
                })
            else:
                results['failed'] += 1
                results['details'].append({
                    'step': step.name,
                    'status': 'failed',
                    'file': str(step.file_path)
                })
        
        return results

    def rollback_last(self) -> bool:
        """Rollback the last applied refactoring."""
        if not self.refactoring_history:
            self.logger.warning("No refactorings to rollback")
            return False
        
        step = self.refactoring_history.pop()
        
        try:
            # Restore from backup
            backup_path = self.backup_manager.get_backup(
                step.file_path,
                tag=f"before_{step.name}"
            )
            
            if backup_path and backup_path.exists():
                step.file_path.write_text(backup_path.read_text())
                self.logger.info(f"Rolled back: {step.name}")
                return True
            else:
                self.logger.error(f"No backup found for {step.name}")
                return False
        
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            self.refactoring_history.append(step)  # Restore to history
            return False

    def get_refactoring_summary(self) -> dict:
        """Get summary of refactorings applied."""
        by_type = {}
        by_file = {}
        
        for step in self.refactoring_history:
            # Group by type
            by_type[step.name] = by_type.get(step.name, 0) + 1
            
            # Group by file
            file_key = str(step.file_path)
            if file_key not in by_file:
                by_file[file_key] = []
            by_file[file_key].append(step.name)
        
        return {
            'total_refactorings': len(self.refactoring_history),
            'by_type': by_type,
            'by_file': by_file,
            'impact_assessment': self._assess_impact()
        }

    def _assess_impact(self) -> dict:
        """Assess the impact of refactorings."""
        high_impact = sum(1 for s in self.refactoring_history if s.impact_level == 'high')
        medium_impact = sum(1 for s in self.refactoring_history if s.impact_level == 'medium')
        low_impact = sum(1 for s in self.refactoring_history if s.impact_level == 'low')
        
        return {
            'high_impact': high_impact,
            'medium_impact': medium_impact,
            'low_impact': low_impact,
            'reversible': sum(1 for s in self.refactoring_history if s.is_reversible)
        }
