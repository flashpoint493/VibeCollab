"""Tests for LifecycleManager."""

from vibecollab.lifecycle import (
    LifecycleManager,
)


class TestInit:
    def test_default_stages_loaded(self):
        mgr = LifecycleManager({"lifecycle": {"current_stage": "demo"}})
        assert "stages" in mgr.lifecycle_config

    def test_custom_stages_preserved(self):
        custom = {"lifecycle": {"stages": {"demo": {"name": "Custom"}}}}
        mgr = LifecycleManager(custom)
        assert mgr.lifecycle_config["stages"]["demo"]["name"] == "Custom"

    def test_empty_config(self):
        mgr = LifecycleManager({})
        assert mgr.get_current_stage() == "demo"


class TestCreateDefault:
    def test_creates_demo(self):
        mgr = LifecycleManager.create_default()
        assert mgr.get_current_stage() == "demo"
        assert len(mgr.get_stage_history()) == 1

    def test_creates_production(self):
        mgr = LifecycleManager.create_default("production")
        assert mgr.get_current_stage() == "production"


class TestGetStageInfo:
    def test_current_stage(self):
        mgr = LifecycleManager.create_default()
        info = mgr.get_stage_info()
        assert info["name"] == "原型验证"

    def test_specific_stage(self):
        mgr = LifecycleManager.create_default()
        info = mgr.get_stage_info("production")
        assert info["name"] == "量产"

    def test_unknown_stage_returns_empty(self):
        mgr = LifecycleManager({"lifecycle": {"current_stage": "unknown"}})
        info = mgr.get_stage_info("nonexistent")
        assert info == {}


class TestCanUpgrade:
    def test_demo_can_upgrade(self):
        mgr = LifecycleManager.create_default("demo")
        can, next_stage, reason = mgr.can_upgrade()
        assert can is True
        assert next_stage == "production"
        assert reason is None

    def test_stable_cannot_upgrade(self):
        mgr = LifecycleManager({"lifecycle": {"current_stage": "stable"}})
        can, next_stage, reason = mgr.can_upgrade()
        assert can is False
        assert next_stage is None
        assert "最后阶段" in reason

    def test_unknown_stage(self):
        mgr = LifecycleManager({"lifecycle": {"current_stage": "alien"}})
        can, next_stage, reason = mgr.can_upgrade()
        assert can is False
        assert "未知" in reason

    def test_incomplete_milestones_block_upgrade(self):
        config = {
            "lifecycle": {
                "current_stage": "demo",
                "stages": {
                    "demo": {
                        "name": "原型验证",
                        "milestones": [
                            {"name": "M1", "completed": True},
                            {"name": "M2", "completed": False},
                        ],
                    }
                },
            }
        }
        mgr = LifecycleManager(config)
        can, next_stage, reason = mgr.can_upgrade()
        assert can is False
        assert "1 个里程碑未完成" in reason

    def test_all_milestones_complete(self):
        config = {
            "lifecycle": {
                "current_stage": "demo",
                "stages": {
                    "demo": {
                        "name": "原型验证",
                        "milestones": [
                            {"name": "M1", "completed": True},
                        ],
                    }
                },
            }
        }
        mgr = LifecycleManager(config)
        can, _, _ = mgr.can_upgrade()
        assert can is True


class TestUpgradeToStage:
    def test_upgrade_demo_to_production(self):
        mgr = LifecycleManager.create_default("demo")
        success, error = mgr.upgrade_to_stage("production")
        assert success is True
        assert error is None
        assert mgr.get_current_stage() == "production"

    def test_upgrade_invalid_stage(self):
        mgr = LifecycleManager.create_default("demo")
        success, error = mgr.upgrade_to_stage("alien")
        assert success is False
        assert "无效" in error

    def test_cannot_downgrade(self):
        mgr = LifecycleManager({"lifecycle": {"current_stage": "production"}})
        success, error = mgr.upgrade_to_stage("demo")
        assert success is False

    def test_cannot_skip_stages(self):
        mgr = LifecycleManager.create_default("demo")
        success, error = mgr.upgrade_to_stage("commercial")
        assert success is False
        assert "跳过" in error

    def test_upgrade_records_history(self):
        mgr = LifecycleManager.create_default("demo")
        mgr.upgrade_to_stage("production")
        history = mgr.get_stage_history()
        assert len(history) == 2
        assert history[-1]["stage"] == "production"
        assert "started_at" in history[-1]
        # Previous stage should have ended_at
        assert "ended_at" in history[0]

    def test_upgrade_same_stage_fails(self):
        mgr = LifecycleManager.create_default("demo")
        success, error = mgr.upgrade_to_stage("demo")
        assert success is False


class TestCheckMilestoneCompletion:
    def test_no_milestones(self):
        mgr = LifecycleManager.create_default()
        result = mgr.check_milestone_completion()
        assert result["total"] == 0
        assert result["completion_rate"] == 1.0
        assert result["ready_for_upgrade"] is True

    def test_partial_milestones(self):
        config = {
            "lifecycle": {
                "current_stage": "demo",
                "stages": {
                    "demo": {
                        "milestones": [
                            {"name": "M1", "completed": True},
                            {"name": "M2", "completed": False},
                            {"name": "M3", "completed": True},
                        ]
                    }
                },
            }
        }
        mgr = LifecycleManager(config)
        result = mgr.check_milestone_completion()
        assert result["total"] == 3
        assert result["completed"] == 2
        assert result["pending"] == 1
        assert result["ready_for_upgrade"] is False


class TestGetUpgradeSuggestions:
    def test_suggestions_from_demo_to_production(self):
        mgr = LifecycleManager.create_default("demo")
        suggestions = mgr.get_upgrade_suggestions("production")
        assert len(suggestions) > 0
        # Should mention new principles or focus areas
        combined = " ".join(suggestions)
        assert "新增" in combined

    def test_suggestions_no_target(self):
        mgr = LifecycleManager.create_default("demo")
        suggestions = mgr.get_upgrade_suggestions()
        assert isinstance(suggestions, list)

    def test_suggestions_when_cannot_upgrade(self):
        mgr = LifecycleManager({"lifecycle": {"current_stage": "stable"}})
        suggestions = mgr.get_upgrade_suggestions()
        assert suggestions == []


class TestToConfigDict:
    def test_returns_lifecycle_key(self):
        mgr = LifecycleManager.create_default()
        d = mgr.to_config_dict()
        assert "lifecycle" in d
        assert "current_stage" in d["lifecycle"]
