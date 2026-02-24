"""
PatternEngine 单元测试
"""

import pytest
from pathlib import Path
from vibecollab.pattern_engine import (
    PatternEngine,
    PATTERNS_DIR,
    _filter_join_list,
    _filter_quote_list,
    _filter_format_review,
)
from vibecollab.generator import LLMContextGenerator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_config():
    """最小可渲染配置"""
    return {
        "project": {"name": "TestProject", "version": "v1.0"},
        "philosophy": {
            "vibe_development": {"enabled": True, "principles": ["测试原则"]},
            "decision_quality": {"target_rate": 0.9, "critical_tolerance": 0},
        },
        "roles": [
            {
                "code": "DEV",
                "name": "开发",
                "focus": ["实现"],
                "triggers": ["开发"],
                "is_gatekeeper": False,
            }
        ],
        "decision_levels": [
            {
                "level": "S",
                "name": "战略决策",
                "scope": "整体方向",
                "review": {"required": True, "mode": "sync"},
            }
        ],
        "documentation": {"key_files": []},
    }


@pytest.fixture
def full_config():
    """完整配置（加载 project.yaml）"""
    import yaml

    project_yaml = Path(__file__).parent.parent / "project.yaml"
    if not project_yaml.exists():
        pytest.skip("project.yaml not found")
    with open(project_yaml, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# PatternEngine 初始化
# ---------------------------------------------------------------------------

class TestPatternEngineInit:
    def test_init_default_patterns_dir(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine.patterns_dir == PATTERNS_DIR
        assert engine.manifest is not None
        assert "sections" in engine.manifest

    def test_init_custom_patterns_dir(self, minimal_config):
        engine = PatternEngine(minimal_config, patterns_dir=PATTERNS_DIR)
        assert engine.patterns_dir == PATTERNS_DIR

    def test_manifest_has_sections(self, minimal_config):
        engine = PatternEngine(minimal_config)
        sections = engine.manifest["sections"]
        assert len(sections) >= 20
        assert sections[0]["id"] == "header"
        assert sections[-1]["id"] == "footer"

    def test_list_patterns(self, minimal_config):
        engine = PatternEngine(minimal_config)
        patterns = engine.list_patterns()
        assert len(patterns) >= 20
        ids = [p["id"] for p in patterns]
        assert "header" in ids
        assert "philosophy" in ids
        assert "footer" in ids


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------

class TestPatternEngineRender:
    def test_render_produces_content(self, minimal_config):
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert len(output) > 1000
        assert "# TestProject AI 协作开发规则" in output
        assert "# 一、核心理念" in output

    def test_render_contains_all_mandatory_sections(self, minimal_config):
        engine = PatternEngine(minimal_config)
        output = engine.render()
        mandatory = [
            "# 一、核心理念",
            "# 二、职能角色定义",
            "# 三、决策分级制度",
            "# 四、开发流程协议",
            "# 五、测试体系",
            "# 六、里程碑定义",
            "# 七、迭代管理",
            "# 八、阶段化协作规则",
            "# 九、上下文管理",
        ]
        for section in mandatory:
            assert section in output, f"Missing section: {section}"

    def test_render_conditional_sections_excluded(self, minimal_config):
        """multi_developer 未启用时不应渲染 §10"""
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "# 十、多开发者/Agent 协作协议" not in output

    def test_render_conditional_sections_included(self, minimal_config):
        """multi_developer 启用时应渲染 §10"""
        minimal_config["multi_developer"] = {
            "enabled": True,
            "identity": {"primary": "git_username", "fallback": "system_user", "normalize": True},
        }
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "# 十、多开发者/Agent 协作协议" in output

    def test_render_default_true_conditions(self, minimal_config):
        """protocol_check 未在 config 中但默认启用"""
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "# 十二、协议自检机制" in output

    def test_render_full_config(self, full_config):
        """使用完整 project.yaml 渲染"""
        engine = PatternEngine(full_config, project_root=Path(__file__).parent.parent)
        output = engine.render()
        assert "# LLMContextGenerator AI 协作开发规则" in output
        assert "# 十、多开发者/Agent 协作协议" in output
        assert len(output) > 15000

    def test_render_footer_has_timestamp(self, minimal_config):
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "*本文档是活文档" in output
        assert "*生成时间:" in output


# ---------------------------------------------------------------------------
# 条件评估
# ---------------------------------------------------------------------------

class TestConditionEvaluation:
    def test_simple_bool_true(self, minimal_config):
        minimal_config["multi_developer"] = {"enabled": True}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.multi_developer.enabled") is True

    def test_simple_bool_false(self, minimal_config):
        minimal_config["multi_developer"] = {"enabled": False}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.multi_developer.enabled") is False

    def test_missing_key_returns_false(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.nonexistent.enabled") is False

    def test_missing_key_with_default_true(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.nonexistent.enabled|true") is True

    def test_missing_key_with_default_false(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.nonexistent.enabled|false") is False

    def test_deep_path(self, minimal_config):
        minimal_config["testing"] = {"product_qa": {"enabled": True}}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.testing.product_qa.enabled") is True

    def test_dict_non_empty(self, minimal_config):
        minimal_config["symbology"] = {"test": [{"symbol": "X", "meaning": "Y"}]}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.symbology") is True

    def test_dict_empty(self, minimal_config):
        minimal_config["symbology"] = {}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.symbology") is False

    def test_has_extensions_false(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("has_extensions") is False

    def test_unknown_condition_returns_true(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("something_else") is True


# ---------------------------------------------------------------------------
# 自定义 Jinja2 Filters
# ---------------------------------------------------------------------------

class TestFilters:
    def test_join_list_default(self):
        assert _filter_join_list(["a", "b", "c"]) == "a、b、c"

    def test_join_list_custom_sep(self):
        assert _filter_join_list(["a", "b"], ", ") == "a, b"

    def test_join_list_non_list(self):
        assert _filter_join_list("hello") == "hello"

    def test_quote_list(self):
        assert _filter_quote_list(["设计", "协议"]) == '"设计"、"协议"'

    def test_quote_list_custom_sep(self):
        assert _filter_quote_list(["a", "b"], ", ") == '"a", "b"'

    def test_format_review_sync(self):
        r = {"required": True, "mode": "sync"}
        assert _filter_format_review(r) == "必须人工确认，记录决策理由"

    def test_format_review_async(self):
        r = {"required": True, "mode": "async"}
        assert _filter_format_review(r) == "人工Review，可异步确认"

    def test_format_review_auto(self):
        r = {"required": False, "mode": "auto"}
        assert _filter_format_review(r) == "AI 提出建议，人工可快速确认或默认通过"

    def test_format_review_none(self):
        r = {"required": False, "mode": "none"}
        assert _filter_format_review(r) == "AI 自主决策，事后可调整"

    def test_format_review_required_fallback(self):
        r = {"required": True}
        assert _filter_format_review(r) == "需要 Review"


# ---------------------------------------------------------------------------
# 与 LLMContextGenerator 的集成
# ---------------------------------------------------------------------------

class TestGeneratorIntegration:
    def test_generate_uses_patterns(self, minimal_config):
        gen = LLMContextGenerator(minimal_config)
        output = gen.generate()
        assert "# TestProject AI 协作开发规则" in output

    def test_generate_full_config(self, full_config):
        """使用完整 project.yaml 通过 Generator 生成"""
        project_root = Path(__file__).parent.parent
        gen = LLMContextGenerator(full_config, project_root)
        output = gen.generate()
        assert "# LLMContextGenerator AI 协作开发规则" in output
        assert len(output) > 15000


# ---------------------------------------------------------------------------
# Template Overlay 机制
# ---------------------------------------------------------------------------

class TestTemplateOverlay:
    """测试用户本地模板覆盖/扩展功能"""

    @pytest.fixture
    def overlay_project(self, tmp_path, minimal_config):
        """创建带本地 overlay 的临时项目"""
        import yaml

        # 创建项目目录结构
        patterns_dir = tmp_path / ".vibecollab" / "patterns"
        patterns_dir.mkdir(parents=True)

        return {
            "root": tmp_path,
            "patterns_dir": patterns_dir,
            "config": minimal_config,
        }

    def test_no_overlay_dir(self, minimal_config, tmp_path):
        """没有本地 patterns 目录时正常运行"""
        engine = PatternEngine(minimal_config, project_root=tmp_path)
        assert engine.local_patterns_dir is None
        assert not engine.has_local_overlay
        output = engine.render()
        assert len(output) > 1000

    def test_overlay_detected(self, overlay_project):
        """检测到本地 patterns 目录"""
        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        assert engine.local_patterns_dir is not None
        assert engine.has_local_overlay

    def test_overlay_template_override(self, overlay_project):
        """本地模板覆盖内置模板"""
        # 创建本地 footer 模板
        local_footer = overlay_project["patterns_dir"] / "26_footer.md.j2"
        local_footer.write_text(
            "*Custom footer by {{ project.name }}*\n",
            encoding="utf-8",
        )

        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        output = engine.render()
        assert "*Custom footer by TestProject*" in output
        # 原始 footer 不应出现
        assert "*最珍贵的不是结果" not in output

    def test_overlay_manifest_add_section(self, overlay_project):
        """本地 manifest 新增章节"""
        import yaml

        # 创建自定义模板
        custom_tmpl = overlay_project["patterns_dir"] / "custom_section.md.j2"
        custom_tmpl.write_text(
            "# 自定义章节\n\n本项目特有的协作规则。\n",
            encoding="utf-8",
        )

        # 创建本地 manifest，在 footer 之前插入
        local_manifest = {
            "sections": [
                {
                    "id": "custom_rules",
                    "template": "custom_section.md.j2",
                    "description": "项目自定义规则",
                    "after": "changelog",
                }
            ]
        }
        manifest_path = overlay_project["patterns_dir"] / "manifest.yaml"
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(local_manifest, f, allow_unicode=True)

        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        output = engine.render()
        assert "# 自定义章节" in output
        assert "本项目特有的协作规则" in output

    def test_overlay_manifest_exclude_section(self, overlay_project):
        """本地 manifest 排除章节"""
        import yaml

        local_manifest = {
            "exclude": ["prompt_engineering", "prd_management"],
        }
        manifest_path = overlay_project["patterns_dir"] / "manifest.yaml"
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(local_manifest, f, allow_unicode=True)

        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        patterns = engine.list_patterns()
        ids = [p["id"] for p in patterns]
        assert "prompt_engineering" not in ids
        assert "prd_management" not in ids
        # 其他章节仍在
        assert "header" in ids
        assert "footer" in ids

    def test_overlay_manifest_replace_condition(self, overlay_project):
        """本地 manifest 替换章节条件"""
        import yaml

        # 强制启用 multi_developer（即使 config 中没有）
        local_manifest = {
            "sections": [
                {
                    "id": "multi_developer",
                    "template": "16_multi_developer.md.j2",
                    "description": "多开发者协作（强制启用）",
                    # 没有 condition → 无条件渲染
                }
            ]
        }
        manifest_path = overlay_project["patterns_dir"] / "manifest.yaml"
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(local_manifest, f, allow_unicode=True)

        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        # 检查 manifest 中 multi_developer 没有 condition
        for entry in engine.manifest["sections"]:
            if entry["id"] == "multi_developer":
                assert entry.get("condition") is None
                break

    def test_overlay_list_patterns_source(self, overlay_project):
        """list_patterns 正确标注模板来源"""
        # 创建本地 footer 模板
        local_footer = overlay_project["patterns_dir"] / "26_footer.md.j2"
        local_footer.write_text("*Custom*\n", encoding="utf-8")

        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        patterns = engine.list_patterns()
        sources = {p["id"]: p["source"] for p in patterns}
        assert sources["footer"] == "local"
        assert sources["header"] == "builtin"

    def test_merge_manifests_static(self):
        """静态测试 _merge_manifests 合并逻辑"""
        builtin = {
            "sections": [
                {"id": "a", "template": "a.j2", "description": "A"},
                {"id": "b", "template": "b.j2", "description": "B"},
                {"id": "c", "template": "c.j2", "description": "C"},
            ]
        }
        local = {
            "exclude": ["b"],
            "sections": [
                {"id": "a", "template": "a_custom.j2", "description": "A Custom"},
                {"id": "d", "template": "d.j2", "description": "D", "after": "a"},
            ],
        }
        result = PatternEngine._merge_manifests(builtin, local)
        ids = [s["id"] for s in result["sections"]]

        # b 被排除
        assert "b" not in ids
        # a 被覆盖
        a_entry = next(s for s in result["sections"] if s["id"] == "a")
        assert a_entry["template"] == "a_custom.j2"
        # d 插入在 a 之后
        assert ids.index("d") == ids.index("a") + 1
        # c 仍在
        assert "c" in ids
