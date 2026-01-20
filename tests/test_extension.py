"""
扩展机制单元测试
"""

import pytest
from pathlib import Path
import tempfile
import os

from llmtxt.extension import ExtensionProcessor, Extension, Hook, Context


class TestExtensionProcessor:
    """测试扩展处理器"""

    def test_load_extension(self):
        """测试加载扩展"""
        processor = ExtensionProcessor()
        
        ext_data = {
            "hooks": [
                {
                    "trigger": "qa.list_test_cases",
                    "action": "inject_context",
                    "context_id": "gm_commands",
                    "condition": "files.exists('docs/GM.md')",
                }
            ],
            "contexts": {
                "gm_commands": {
                    "type": "reference",
                    "source": "docs/GM.md",
                    "description": "GM 命令",
                }
            },
            "config": {
                "gm_trigger_key": "/",
            }
        }
        
        ext = processor.load_extension(ext_data, "game")
        
        assert ext.domain == "game"
        assert len(ext.hooks) == 1
        assert ext.hooks[0].trigger == "qa.list_test_cases"
        assert "gm_commands" in ext.contexts
        assert ext.config["gm_trigger_key"] == "/"

    def test_get_hooks_for_trigger(self):
        """测试获取触发点钩子"""
        processor = ExtensionProcessor()
        
        # 添加多个扩展
        processor.load_extension({
            "hooks": [
                {"trigger": "qa.list_test_cases", "action": "inject_context", "priority": 1},
                {"trigger": "build.pre", "action": "append_checklist"},
            ]
        }, "game")
        
        processor.load_extension({
            "hooks": [
                {"trigger": "qa.list_test_cases", "action": "inject_context", "priority": 10},
            ]
        }, "web")
        
        hooks = processor.get_hooks_for_trigger("qa.list_test_cases")
        
        assert len(hooks) == 2
        # 应按优先级降序排列
        assert hooks[0].priority == 10
        assert hooks[1].priority == 1

    def test_evaluate_condition_files_exists(self):
        """测试文件存在条件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = ExtensionProcessor(Path(tmpdir))
            
            # 文件不存在
            assert not processor.evaluate_condition(
                "files.exists('docs/GM.md')", {}
            )
            
            # 创建文件
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "GM.md").write_text("# GM")
            
            # 文件存在
            assert processor.evaluate_condition(
                "files.exists('docs/GM.md')", {}
            )

    def test_evaluate_condition_project_domain(self):
        """测试项目域条件"""
        processor = ExtensionProcessor()
        processor._project_config = {"project": {"domain": "game"}}
        
        assert processor.evaluate_condition("project.domain == 'game'", {})
        assert not processor.evaluate_condition("project.domain == 'web'", {})

    def test_evaluate_condition_has_feature(self):
        """测试功能特性条件"""
        processor = ExtensionProcessor()
        processor._project_config = {
            "project": {"features": ["gm_console", "debug_mode"]}
        }
        
        assert processor.evaluate_condition("project.has_feature('gm_console')", {})
        assert not processor.evaluate_condition("project.has_feature('multiplayer')", {})

    def test_resolve_template_context(self):
        """测试模板上下文解析"""
        processor = ExtensionProcessor()
        
        ctx = Context(
            id="test",
            type="template",
            content="测试 {name}，按 {key} 打开",
        )
        
        result = processor.resolve_context(ctx, {"name": "GM", "key": "/"})
        
        assert "测试 GM" in result
        assert "按 / 打开" in result

    def test_resolve_reference_context(self):
        """测试引用上下文解析"""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = ExtensionProcessor(Path(tmpdir))
            
            # 创建引用文件（短内容，应内联）
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "SHORT.md").write_text("This is short content", encoding="utf-8")
            
            ctx = Context(
                id="short",
                type="reference",
                source="docs/SHORT.md",
                inline_if_short=True,
            )
            
            result = processor.resolve_context(ctx, {})
            assert "short content" in result

    def test_resolve_file_list_context(self):
        """测试文件列表上下文解析"""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = ExtensionProcessor(Path(tmpdir))
            
            # 创建匹配文件
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "GDD_Core.md").write_text("# Core")
            (docs_dir / "GDD_UI.md").write_text("# UI")
            (docs_dir / "README.md").write_text("# README")  # 不匹配
            
            ctx = Context(
                id="gdd",
                type="file_list",
                pattern="docs/GDD_*.md",
                description="游戏设计文档",
            )
            
            result = processor.resolve_context(ctx, {})
            assert "GDD_Core.md" in result
            assert "GDD_UI.md" in result
            assert "README.md" not in result

    def test_process_trigger(self):
        """测试触发点处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = ExtensionProcessor(Path(tmpdir))
            
            # 创建引用文件
            docs_dir = Path(tmpdir) / "docs"
            docs_dir.mkdir()
            (docs_dir / "GM.md").write_text("# GM Commands")
            
            processor.load_extension({
                "hooks": [
                    {
                        "trigger": "qa.list_test_cases",
                        "action": "inject_context",
                        "context_id": "gm_commands",
                        "condition": "files.exists('docs/GM.md')",
                    }
                ],
                "contexts": {
                    "gm_commands": {
                        "type": "reference",
                        "source": "docs/GM.md",
                    }
                }
            }, "game")
            
            results = processor.process_trigger("qa.list_test_cases")
            
            assert len(results) == 1
            assert results[0]["action"] == "inject_context"
            assert "GM Commands" in results[0]["content"]

    def test_process_trigger_condition_not_met(self):
        """测试条件不满足时不触发"""
        processor = ExtensionProcessor()
        
        processor.load_extension({
            "hooks": [
                {
                    "trigger": "qa.list_test_cases",
                    "action": "inject_context",
                    "context_id": "gm_commands",
                    "condition": "files.exists('docs/NONEXISTENT.md')",
                }
            ],
            "contexts": {
                "gm_commands": {"type": "template", "content": "test"}
            }
        }, "game")
        
        results = processor.process_trigger("qa.list_test_cases")
        
        # 条件不满足，不应返回结果
        assert len(results) == 0


class TestExtension:
    """测试扩展数据类"""

    def test_extension_dataclass(self):
        """测试 Extension 数据类"""
        ext = Extension(domain="game")
        
        assert ext.domain == "game"
        assert ext.hooks == []
        assert ext.contexts == {}

    def test_hook_dataclass(self):
        """测试 Hook 数据类"""
        hook = Hook(
            trigger="qa.list_test_cases",
            action="inject_context",
            context_id="test",
        )
        
        assert hook.trigger == "qa.list_test_cases"
        assert hook.priority == 0  # 默认值

    def test_context_dataclass(self):
        """测试 Context 数据类"""
        ctx = Context(
            id="test",
            type="reference",
            source="docs/TEST.md",
        )
        
        assert ctx.id == "test"
        assert ctx.inline_if_short == True  # 默认值
