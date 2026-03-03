"""
Project lifecycle management - Lifecycle stage management
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Default stage definitions
DEFAULT_STAGES = {
    "demo": {
        "name": "Prototype Validation",
        "description": "Quickly validate core concepts and feasibility",
        "focus": ["Rapid iteration", "Concept validation", "Core features"],
        "principles": [
            "Fail fast, adjust fast",
            "Prioritize core features, defer optimization",
            "Technical debt is acceptable, but must be documented",
            "Detailed Git development iteration records",
            "Record important decisions in DECISIONS.md",
            "Set up CI/CD"
        ],
        "milestones": []
    },
    "production": {
        "name": "Production",
        "description": "Productization development, preparing for scale",
        "focus": ["Stability", "Performance optimization", "Maintainability"],
        "principles": [
            "Code quality first",
            "Prepare for release and announcements, define and refine target platform support",
            "Full code review before launch, build more stable and robust code structure",
            "Complete QA product test coverage",
            "Define performance standards",
            "Unit tests, coding standards checks",
            "Complete release platform standards"
        ],
        "milestones": []
    },
    "commercial": {
        "name": "Commercialization",
        "description": "Market-facing, pursuing growth",
        "focus": ["User experience", "Market adaptation", "Scalability", "Plugin-based incremental development", "Data hot-update"],
        "principles": [
            "User feedback driven",
            "Data-driven decisions",
            "Fast market response"
        ],
        "milestones": []
    },
    "stable": {
        "name": "Stable Operations",
        "description": "Mature product, stable maintenance",
        "focus": ["Stability", "Maintenance cost", "Long-term planning"],
        "principles": [
            "Changes require caution",
            "Backward compatibility first",
            "Complete documentation"
        ],
        "milestones": []
    }
}

# Stage order
STAGE_ORDER = ["demo", "production", "commercial", "stable"]


class LifecycleManager:
    """Project lifecycle manager"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize lifecycle manager

        Args:
            config: Project configuration dictionary
        """
        self.config = config
        self.lifecycle_config = config.get("lifecycle", {})

        # If no stages in config, use defaults
        if "stages" not in self.lifecycle_config:
            self.lifecycle_config["stages"] = DEFAULT_STAGES.copy()

    @classmethod
    def create_default(cls, current_stage: str = "demo") -> "LifecycleManager":
        """Create default lifecycle configuration

        Args:
            current_stage: Initial stage, defaults to demo
        """
        config = {
            "lifecycle": {
                "current_stage": current_stage,
                "stage_history": [
                    {
                        "stage": current_stage,
                        "started_at": datetime.now().strftime("%Y-%m-%d"),
                        "milestones_completed": []
                    }
                ],
                "stages": DEFAULT_STAGES.copy()
            }
        }
        return cls(config)

    def get_current_stage(self) -> str:
        """Get current stage

        Returns:
            str: Current stage code
        """
        return self.lifecycle_config.get("current_stage", "demo")

    def get_stage_info(self, stage: Optional[str] = None) -> Dict[str, Any]:
        """Get stage information

        Args:
            stage: Stage code, returns current stage if None

        Returns:
            Dict: Stage information
        """
        if stage is None:
            stage = self.get_current_stage()

        stages = self.lifecycle_config.get("stages", DEFAULT_STAGES)
        return stages.get(stage, DEFAULT_STAGES.get(stage, {}))

    def get_stage_history(self) -> List[Dict[str, Any]]:
        """Get stage history

        Returns:
            List[Dict]: Stage history records
        """
        return self.lifecycle_config.get("stage_history", [])

    def can_upgrade(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check if upgrade to next stage is possible

        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (can upgrade, next stage code, reason)
        """
        current_stage = self.get_current_stage()

        # Get current stage position in order
        try:
            current_index = STAGE_ORDER.index(current_stage)
        except ValueError:
            return False, None, f"Unknown current stage: {current_stage}"

        # Check if already at the last stage
        if current_index >= len(STAGE_ORDER) - 1:
            return False, None, "Already at the last stage, cannot upgrade further"

        # Get next stage
        next_stage = STAGE_ORDER[current_index + 1]

        # Check if current stage milestones are completed
        stage_info = self.get_stage_info(current_stage)
        milestones = stage_info.get("milestones", [])

        if milestones:
            # Check milestone completion
            completed = [m for m in milestones if m.get("completed", False)]
            if len(completed) < len(milestones):
                return False, next_stage, f"Current stage still has {len(milestones) - len(completed)} milestones incomplete"

        return True, next_stage, None

    def upgrade_to_stage(self, target_stage: str) -> Tuple[bool, Optional[str]]:
        """Upgrade to specified stage

        Args:
            target_stage: Target stage code

        Returns:
            Tuple[bool, Optional[str]]: (success, error message)
        """
        current_stage = self.get_current_stage()

        # Validate target stage
        if target_stage not in STAGE_ORDER:
            return False, f"Invalid stage code: {target_stage}"

        # Check if upgrade is possible
        can_upgrade, next_stage, reason = self.can_upgrade()
        if not can_upgrade and target_stage != current_stage:
            if reason:
                return False, reason
            return False, "Cannot upgrade to that stage"

        # If target is not the next stage, check order
        try:
            current_index = STAGE_ORDER.index(current_stage)
            target_index = STAGE_ORDER.index(target_stage)

            if target_index <= current_index:
                return False, f"Target stage {target_stage} cannot be earlier than or equal to current stage {current_stage}"

            # Check if intermediate stages are skipped
            if target_index > current_index + 1:
                return False, f"Cannot skip intermediate stages, please upgrade to {STAGE_ORDER[current_index + 1]} first"
        except ValueError:
            return False, "Stage validation failed"

        # Execute upgrade
        # Update current stage
        if "lifecycle" not in self.config:
            self.config["lifecycle"] = {}

        self.config["lifecycle"]["current_stage"] = target_stage

        # Record stage history
        if "stage_history" not in self.config["lifecycle"]:
            self.config["lifecycle"]["stage_history"] = []

        # Update current stage's end time
        history = self.config["lifecycle"]["stage_history"]
        if history and history[-1].get("stage") == current_stage:
            history[-1]["ended_at"] = datetime.now().strftime("%Y-%m-%d")

        # Add new stage record
        history.append({
            "stage": target_stage,
            "started_at": datetime.now().strftime("%Y-%m-%d"),
            "milestones_completed": []
        })

        return True, None

    def check_milestone_completion(self) -> Dict[str, Any]:
        """Check milestone completion status

        Returns:
            Dict: Milestone completion statistics
        """
        current_stage = self.get_current_stage()
        stage_info = self.get_stage_info(current_stage)
        milestones = stage_info.get("milestones", [])

        if not milestones:
            return {
                "total": 0,
                "completed": 0,
                "pending": 0,
                "completion_rate": 1.0,
                "ready_for_upgrade": True
            }

        completed = [m for m in milestones if m.get("completed", False)]
        pending = [m for m in milestones if not m.get("completed", False)]

        return {
            "total": len(milestones),
            "completed": len(completed),
            "pending": len(pending),
            "completion_rate": len(completed) / len(milestones) if milestones else 1.0,
            "ready_for_upgrade": len(completed) == len(milestones),
            "milestones": milestones
        }

    def get_upgrade_suggestions(self, target_stage: Optional[str] = None) -> List[str]:
        """Get upgrade suggestions

        Args:
            target_stage: Target stage, uses next stage if None

        Returns:
            List[str]: Upgrade suggestions list
        """
        if target_stage is None:
            can_upgrade, next_stage, _ = self.can_upgrade()
            if not can_upgrade:
                return []
            target_stage = next_stage

        current_stage = self.get_current_stage()
        current_info = self.get_stage_info(current_stage)
        target_info = self.get_stage_info(target_stage)

        suggestions = []

        # Compare principles, find noteworthy changes
        current_principles = set(current_info.get("principles", []))
        target_principles = set(target_info.get("principles", []))

        new_principles = target_principles - current_principles
        if new_principles:
            suggestions.append(f"New principles: {', '.join(new_principles)}")

        # Compare focus areas
        current_focus = set(current_info.get("focus", []))
        target_focus = set(target_info.get("focus", []))

        new_focus = target_focus - current_focus
        if new_focus:
            suggestions.append(f"New focus areas: {', '.join(new_focus)}")

        return suggestions

    def to_config_dict(self) -> Dict[str, Any]:
        """Convert to configuration dictionary

        Returns:
            Dict: Configuration dictionary
        """
        return {
            "lifecycle": self.lifecycle_config
        }
