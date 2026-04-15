"""
Workflow Panel - Rich TUI panel for development cockpit visualization.

This module provides a real-time dashboard showing workflow context,
roadmap progress, active plans, role requests, and prompt suggestions.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns

# Use absolute imports for testing compatibility
from vibecollab_dashboard.workflow_snapshot import WorkflowSnapshotGenerator, save_snapshot
from vibecollab_dashboard.workflow_validator import validate_workflow


class WorkflowPanel:
    """Rich TUI panel for workflow visualization."""

    def __init__(self, project_root: Path, watch_mode: bool = False):
        self.project_root = project_root.resolve()
        self.watch_mode = watch_mode
        self.console = Console()
        self.snapshot_generator = WorkflowSnapshotGenerator(project_root)

    def render_panel(self) -> Layout:
        """Render the complete workflow panel layout."""
        # Generate current snapshot
        snapshot = self.snapshot_generator.generate_snapshot()
        validation_result = validate_workflow(self.project_root)
        
        # Create main layout
        layout = Layout()
        
        # Split into main content and footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Split main area into 3 columns
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="center"),
            Layout(name="right")
        )
        
        # Split left column into top and bottom
        layout["left"].split_column(
            Layout(name="project_status"),
            Layout(name="workflow_health")
        )
        
        # Split center column into top and bottom
        layout["center"].split_column(
            Layout(name="roadmap_tasks"),
            Layout(name="active_plans")
        )
        
        # Split right column into top and bottom
        layout["right"].split_column(
            Layout(name="role_requests"),
            Layout(name="prompt_suggestions")
        )
        
        # Render each section
        layout["header"].update(self._render_header(snapshot))
        layout["project_status"].update(self._render_project_status(snapshot))
        layout["workflow_health"].update(self._render_workflow_health(validation_result))
        layout["roadmap_tasks"].update(self._render_roadmap_tasks(snapshot))
        layout["active_plans"].update(self._render_active_plans(snapshot))
        layout["role_requests"].update(self._render_role_requests(snapshot))
        layout["prompt_suggestions"].update(self._render_prompt_suggestions(snapshot))
        layout["footer"].update(self._render_footer())
        
        return layout

    def _render_header(self, snapshot) -> Panel:
        """Render header panel with project info and timestamp."""
        project = snapshot.project
        title = Text(f"VibeCollab Development Cockpit", style="bold blue")
        
        if project:
            subtitle = Text(f"{project.name} v{project.version} - {project.milestone}", style="dim")
        else:
            subtitle = Text("Project information unavailable", style="dim red")
        
        timestamp = Text(f"Last updated: {datetime.now().strftime('%H:%M:%S')}", style="dim")
        
        header_content = f"{title}\n{subtitle}\n{timestamp}"
        
        return Panel(
            Align.center(header_content),
            title="Development Cockpit",
            border_style="blue"
        )

    def _render_project_status(self, snapshot) -> Panel:
        """Render project status panel."""
        project = snapshot.project
        if not project:
            return Panel("Project status unavailable", title="Project Status", border_style="red")
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()
        
        # Git status with emoji
        git_status = "🔴" if project.git_dirty else "🟢"
        git_info = f"{git_status} {project.git_changed_files} files changed"
        
        table.add_row("Version:", project.version)
        table.add_row("Milestone:", project.milestone)
        table.add_row("Git Status:", git_info)
        table.add_row("Recent Event:", project.recent_event_time or "None")
        table.add_row("Current Role:", project.current_role or "None")
        
        return Panel(table, title="Project Status", border_style="green")

    def _render_workflow_health(self, validation_result) -> Panel:
        """Render workflow health panel."""
        # Determine status color
        if validation_result.status == "error":
            status_style = "red"
            status_emoji = "🔴"
        elif validation_result.status == "warning":
            status_style = "yellow"
            status_emoji = "🟡"
        else:
            status_style = "green"
            status_emoji = "🟢"
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()
        
        table.add_row("Status:", f"{status_emoji} {validation_result.status.upper()}")
        table.add_row("Errors:", str(validation_result.error_count))
        table.add_row("Warnings:", str(validation_result.warning_count))
        table.add_row("Info:", str(validation_result.info_count))
        
        # Add critical issues if any
        critical_issues = [issue for issue in validation_result.issues 
                          if issue.severity in ["ERROR", "WARN"]]
        
        if critical_issues:
            issues_text = "\n".join([f"• {issue.message}" for issue in critical_issues[:3]])
            if len(critical_issues) > 3:
                issues_text += f"\n... and {len(critical_issues) - 3} more"
            table.add_row("Issues:", issues_text)
        
        return Panel(table, title="Workflow Health", border_style=status_style)

    def _render_roadmap_tasks(self, snapshot) -> Panel:
        """Render roadmap and tasks panel."""
        roadmap = snapshot.roadmap
        tasks = snapshot.tasks
        
        if not roadmap or not tasks:
            return Panel("Roadmap and tasks unavailable", title="Roadmap & Tasks", border_style="red")
        
        # Progress bar for tasks
        total_tasks = roadmap.todo_count + roadmap.in_progress_count + roadmap.review_count + roadmap.done_count
        if total_tasks > 0:
            progress = (roadmap.done_count / total_tasks) * 100
            progress_bar = f"[{roadmap.done_count}/{total_tasks}] {progress:.1f}%"
        else:
            progress_bar = "No tasks"
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()
        
        table.add_row("Milestone Pending:", str(roadmap.milestone_pending_count))
        table.add_row("Progress:", progress_bar)
        table.add_row("TODO:", str(roadmap.todo_count))
        table.add_row("IN_PROGRESS:", str(roadmap.in_progress_count))
        table.add_row("REVIEW:", str(roadmap.review_count))
        table.add_row("DONE:", str(roadmap.done_count))
        
        if roadmap.current_main_task:
            table.add_row("Current Task:", roadmap.current_main_task)
        
        return Panel(table, title="Roadmap & Tasks", border_style="cyan")

    def _render_active_plans(self, snapshot) -> Panel:
        """Render active plans panel."""
        plans = snapshot.plans
        
        if not plans or not plans.get("active"):
            return Panel("No active plans", title="Active Plans", border_style="yellow")
        
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Plan", style="bold")
        table.add_column("Status")
        table.add_column("Progress")
        table.add_column("Resumable")
        
        for plan_data in plans["active"][:3]:  # Show max 3 plans
            plan_name = plan_data.get("plan_name", "Unknown")
            status = plan_data.get("status", "unknown")
            current_step = plan_data.get("current_step_index", 0)
            total_steps = plan_data.get("total_steps", 0)
            resumable = "Yes" if plan_data.get("resumable", False) else "No"
            
            if total_steps > 0:
                progress = f"{current_step}/{total_steps}"
            else:
                progress = "-"
            
            table.add_row(plan_name, status, progress, resumable)
        
        if len(plans["active"]) > 3:
            table.add_row(f"... {len(plans['active']) - 3} more", "", "", "")
        
        return Panel(table, title="Active Plans", border_style="magenta")

    def _render_role_requests(self, snapshot) -> Panel:
        """Render role requests panel."""
        role_info = snapshot.role
        
        if not role_info:
            return Panel("Role information unavailable", title="Role Requests", border_style="red")
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()
        
        table.add_row("Current Role:", role_info.get("current", "Unknown"))
        table.add_row("Active Roles:", ", ".join(role_info.get("active_roles", [])))
        
        # Add common CLI command prompts
        table.add_row("Onboard:", "vibecollab onboard")
        table.add_row("Prompt:", "vibecollab prompt")
        table.add_row("Insights:", "vibecollab insights tags")
        table.add_row("Role Switch:", "vibecollab role switch <role>")
        table.add_row("Context:", "vibecollab context")
        
        # Add role-specific information if available
        if snapshot.roadmap and snapshot.roadmap.role_request_entry_hint:
            table.add_row("Hint:", snapshot.roadmap.role_request_entry_hint)
        
        return Panel(table, title="Role Requests", border_style="yellow")

    def _render_prompt_suggestions(self, snapshot) -> Panel:
        """Render prompt suggestions panel."""
        suggestions = snapshot.suggestions
        
        if not suggestions:
            return Panel("No suggestions available", title="Prompt Suggestions", border_style="blue")
        
        content = ""
        
        if suggestions.get("next_commands"):
            content += "[bold]Next Commands:[/bold]\n"
            for cmd in suggestions["next_commands"][:3]:
                content += f"• {cmd}\n"
            content += "\n"
        
        if suggestions.get("prompt_hints"):
            content += "[bold]Prompt Hints:[/bold]\n"
            for hint in suggestions["prompt_hints"][:3]:
                content += f"• {hint}\n"
        
        return Panel(content.strip(), title="Prompt Suggestions", border_style="blue")

    def _render_footer(self) -> Panel:
        """Render footer with commands and status."""
        if self.watch_mode:
            status = "[green]WATCH MODE[/green] - Auto-refresh every 2 seconds"
            commands = "Press [bold]q[/bold] to quit, [bold]r[/bold] to refresh, [bold]j[/bold] to export JSON"
        else:
            status = "[yellow]STATIC MODE[/yellow] - Single snapshot"
            commands = "Use [bold]--watch[/bold] for auto-refresh mode"
        
        footer_content = f"{status}\n{commands}"
        
        return Panel(
            Align.center(footer_content),
            border_style="dim"
        )

    def display(self) -> None:
        """Display the workflow panel."""
        if self.watch_mode:
            self._display_watch_mode()
        else:
            self._display_static_mode()

    def _display_static_mode(self) -> None:
        """Display a single static snapshot."""
        layout = self.render_panel()
        self.console.print(layout)
        
        # Save snapshot to file
        snapshot = self.snapshot_generator.generate_snapshot()
        snapshot_path = self.project_root / ".vibecollab" / "runtime" / "workflow_snapshot.json"
        save_snapshot(snapshot, snapshot_path)
        
        self.console.print(f"\n[dim]Snapshot saved to: {snapshot_path.relative_to(self.project_root)}[/dim]")

    def _display_watch_mode(self) -> None:
        """Display live updating panel with auto-refresh."""
        def refresh_layout():
            return self.render_panel()
        
        try:
            with Live(refresh_layout(), refresh_per_second=0.5, screen=True) as live:
                while True:
                    time.sleep(2)  # Refresh every 2 seconds
                    live.update(refresh_layout())
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Watch mode stopped.[/yellow]")


def display_workflow_panel(project_root: Path, watch: bool = False) -> None:
    """Convenience function to display workflow panel."""
    panel = WorkflowPanel(project_root, watch)
    panel.display()