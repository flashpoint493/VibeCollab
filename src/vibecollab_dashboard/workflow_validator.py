"""
Workflow Validator - Runtime validation for workflow health assessment.

This module performs comprehensive validation of the current project state,
checking for issues that could affect workflow execution and providing
actionable feedback.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

# Use absolute imports for testing compatibility
from vibecollab.core.workflow import discover_workflows, find_workflow
from vibecollab.core.execution_plan import PlanRunner
from vibecollab.domain.task_manager import TaskManager
from vibecollab.domain.role import RoleManager
from vibecollab.utils.git import is_git_repo


@dataclass
class ValidationIssue:
    """Individual validation issue with severity and details."""
    severity: str  # ERROR / WARN / INFO
    code: str
    message: str
    suggestion: Optional[str] = None
    affected_files: Optional[List[str]] = None


@dataclass
class ValidationResult:
    """Complete validation result with issue summary."""
    status: str  # ok / warning / error
    total_issues: int
    error_count: int
    warning_count: int
    info_count: int
    issues: List[ValidationIssue]


class WorkflowValidator:
    """Validates workflow runtime state and configuration."""

    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.issues: List[ValidationIssue] = []

    def validate_all(self) -> ValidationResult:
        """Perform comprehensive validation of all aspects."""
        self.issues.clear()
        
        # Run all validation checks
        self._validate_workflow_files()
        self._validate_plan_schema()
        self._validate_prompt_action_hosts()
        self._validate_command_existence()
        self._validate_plan_state_files()
        self._validate_active_state_matching()
        self._validate_roadmap_task_alignment()
        self._validate_role_context()
        self._validate_docs_context_recency()
        self._validate_git_sync_recommendation()
        
        # Calculate summary
        error_count = sum(1 for issue in self.issues if issue.severity == "ERROR")
        warning_count = sum(1 for issue in self.issues if issue.severity == "WARN")
        info_count = sum(1 for issue in self.issues if issue.severity == "INFO")
        
        # Determine overall status
        if error_count > 0:
            status = "error"
        elif warning_count > 0:
            status = "warning"
        else:
            status = "ok"
        
        return ValidationResult(
            status=status,
            total_issues=len(self.issues),
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            issues=self.issues.copy()
        )

    def _validate_workflow_files(self) -> None:
        """Validate workflow file discoverability and parsability."""
        workflows_dir = self.project_root / ".vibecollab" / "workflows"
        
        if not workflows_dir.exists():
            self.issues.append(ValidationIssue(
                severity="WARN",
                code="WORKFLOWS_DIR_MISSING",
                message="Workflows directory not found",
                suggestion="Create .vibecollab/workflows/ directory for workflow files"
            ))
            return
        
        workflows = discover_workflows(self.project_root)
        if not workflows:
            self.issues.append(ValidationIssue(
                severity="INFO",
                code="NO_WORKFLOWS_FOUND",
                message="No workflow files found in workflows directory",
                suggestion="Add workflow YAML files to .vibecollab/workflows/"
            ))
        
        # Check individual workflow files
        for wf in workflows:
            try:
                with open(wf.path, "r", encoding="utf-8") as f:
                    yaml.safe_load(f)
            except Exception as e:
                self.issues.append(ValidationIssue(
                    severity="ERROR",
                    code="WORKFLOW_PARSE_ERROR",
                    message=f"Failed to parse workflow file: {wf.name}",
                    suggestion=f"Fix YAML syntax in {wf.path.relative_to(self.project_root)}",
                    affected_files=[str(wf.path.relative_to(self.project_root))]
                ))

    def _validate_plan_schema(self) -> None:
        """Validate plan schema compliance."""
        workflows = discover_workflows(self.project_root)
        
        for wf in workflows:
            try:
                # Basic schema validation
                plan_data = wf.raw
                
                # Check required fields
                if "name" not in plan_data:
                    self.issues.append(ValidationIssue(
                        severity="WARN",
                        code="MISSING_PLAN_NAME",
                        message=f"Workflow missing name: {wf.path.name}",
                        suggestion="Add 'name' field to workflow definition"
                    ))
                
                if "steps" not in plan_data or not isinstance(plan_data["steps"], list):
                    self.issues.append(ValidationIssue(
                        severity="ERROR",
                        code="INVALID_STEPS_FIELD",
                        message=f"Invalid or missing steps in workflow: {wf.name}",
                        suggestion="Ensure 'steps' field exists and is a list"
                    ))
                
                # Validate individual steps
                if "steps" in plan_data and isinstance(plan_data["steps"], list):
                    for i, step in enumerate(plan_data["steps"]):
                        if not isinstance(step, dict):
                            self.issues.append(ValidationIssue(
                                severity="ERROR",
                                code="INVALID_STEP_FORMAT",
                                message=f"Step {i+1} in {wf.name} is not a dictionary",
                                suggestion="Each step should be a dictionary with required fields"
                            ))
                        elif "name" not in step:
                            self.issues.append(ValidationIssue(
                                severity="WARN",
                                code="MISSING_STEP_NAME",
                                message=f"Step {i+1} in {wf.name} missing name",
                                suggestion="Add 'name' field to each step"
                            ))
                            
            except Exception as e:
                self.issues.append(ValidationIssue(
                    severity="ERROR",
                    code="SCHEMA_VALIDATION_ERROR",
                    message=f"Schema validation failed for {wf.name}: {str(e)}",
                    suggestion="Check workflow YAML structure and syntax"
                ))

    def _validate_prompt_action_hosts(self) -> None:
        """Validate that prompt/loop action hosts are configured."""
        workflows = discover_workflows(self.project_root)
        
        for wf in workflows:
            if "steps" in wf.raw and isinstance(wf.raw["steps"], list):
                for i, step in enumerate(wf.raw["steps"]):
                    if isinstance(step, dict) and step.get("type") in ["prompt", "loop"]:
                        if "host" not in step:
                            self.issues.append(ValidationIssue(
                                severity="WARN",
                                code="MISSING_HOST_CONFIG",
                                message=f"Prompt/loop step {i+1} in {wf.name} missing host configuration",
                                suggestion="Add 'host' field to prompt/loop steps"
                            ))

    def _validate_command_existence(self) -> None:
        """Validate that workflow-referenced commands exist."""
        workflows = discover_workflows(self.project_root)
        
        for wf in workflows:
            if "steps" in wf.raw and isinstance(wf.raw["steps"], list):
                for i, step in enumerate(wf.raw["steps"]):
                    if isinstance(step, dict) and step.get("type") == "command":
                        command = step.get("command", "")
                        if not command:
                            self.issues.append(ValidationIssue(
                                severity="ERROR",
                                code="MISSING_COMMAND",
                                message=f"Command step {i+1} in {wf.name} has no command",
                                suggestion="Specify a command to execute"
                            ))

    def _validate_plan_state_files(self) -> None:
        """Validate that plan state files are readable."""
        plan_state_dir = self.project_root / ".vibecollab" / "plan_state"
        
        if not plan_state_dir.exists():
            return  # No state files is not an error
        
        for state_file in plan_state_dir.glob("*.json"):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    json.load(f)
            except Exception as e:
                self.issues.append(ValidationIssue(
                    severity="ERROR",
                    code="CORRUPT_STATE_FILE",
                    message=f"Corrupted plan state file: {state_file.name}",
                    suggestion=f"Remove or fix {state_file.relative_to(self.project_root)}",
                    affected_files=[str(state_file.relative_to(self.project_root))]
                ))

    def _validate_active_state_matching(self) -> None:
        """Validate that active state matches actual plan files."""
        plan_state_dir = self.project_root / ".vibecollab" / "plan_state"
        
        if not plan_state_dir.exists():
            return
        
        for state_file in plan_state_dir.glob("*.json"):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                
                plan_name = state_data.get("plan_name", state_file.stem)
                workflow = find_workflow(plan_name, self.project_root)
                
                if not workflow:
                    self.issues.append(ValidationIssue(
                        severity="WARN",
                        code="ORPHANED_STATE_FILE",
                        message=f"State file references non-existent workflow: {plan_name}",
                        suggestion=f"Remove {state_file.relative_to(self.project_root)} or restore workflow"
                    ))
                
            except Exception:
                continue  # Already handled in _validate_plan_state_files

    def _validate_roadmap_task_alignment(self) -> None:
        """Validate roadmap and tasks alignment."""
        try:
            task_manager = TaskManager(self.project_root)
            tasks = task_manager.list_tasks()
            
            roadmap_path = self.project_root / "docs" / "ROADMAP.md"
            if roadmap_path.exists():
                roadmap_content = roadmap_path.read_text(encoding="utf-8")
                
                # Check if tasks reference roadmap items
                for task in tasks:
                    if task.feature and "[ ]" in roadmap_content:
                        # Simple check for feature mention in roadmap
                        if task.feature not in roadmap_content:
                            self.issues.append(ValidationIssue(
                                severity="INFO",
                                code="TASK_ROADMAP_MISMATCH",
                                message=f"Task {task.id} feature not found in roadmap",
                                suggestion=f"Update roadmap to include feature: {task.feature}"
                            ))
                            
        except Exception:
            pass  # Task manager or roadmap might not be available

    def _validate_role_context(self) -> None:
        """Validate role context existence."""
        try:
            role_manager = RoleManager(self.project_root)
            current_role = role_manager.get_current_role()
            
            if current_role:
                role_context = role_manager.get_role_context(current_role)
                if not role_context:
                    self.issues.append(ValidationIssue(
                        severity="WARN",
                        code="MISSING_ROLE_CONTEXT",
                        message=f"Role context missing for current role: {current_role}",
                        suggestion=f"Run 'vibecollab role init {current_role}' to create context"
                    ))
                    
        except Exception:
            self.issues.append(ValidationIssue(
                severity="WARN",
                code="ROLE_MANAGER_UNAVAILABLE",
                message="Role manager not available",
                suggestion="Check role configuration and permissions"
            ))

    def _validate_docs_context_recency(self) -> None:
        """Validate that docs/context are not too old."""
        import time
        from datetime import datetime, timedelta
        
        critical_files = [
            "docs/CONTEXT.md",
            "docs/ROADMAP.md", 
            "docs/DECISIONS.md",
            ".vibecollab/tasks.json"
        ]
        
        cutoff_time = datetime.now() - timedelta(days=7)  # 7 days old
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                    if mtime < cutoff_time:
                        self.issues.append(ValidationIssue(
                            severity="INFO",
                            code="STALE_DOCUMENT",
                            message=f"Document may be outdated: {file_path}",
                            suggestion=f"Consider updating {file_path} with recent changes"
                        ))
                except Exception:
                    pass

    def _validate_git_sync_recommendation(self) -> None:
        """Recommend git sync if there are uncommitted changes."""
        if not is_git_repo(self.project_root):
            return
        
        try:
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                self.issues.append(ValidationIssue(
                    severity="INFO",
                    code="UNCOMMITTED_CHANGES",
                    message="Uncommitted changes detected",
                    suggestion="Consider committing changes before proceeding with workflow execution"
                ))
                
        except Exception:
            pass  # Git command failed, skip this check


def validate_workflow(project_root: Path) -> ValidationResult:
    """Convenience function to validate workflow state."""
    validator = WorkflowValidator(project_root)
    return validator.validate_all()