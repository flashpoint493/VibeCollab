"""
LLMContext Extension - 扩展机制处理器

扩展 = 流程钩子 + 上下文注入 + 引用文档
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class Context:
    """上下文定义"""
    id: str
    type: str  # reference | template | computed | file_list
    source: Optional[str] = None       # type=reference
    section: Optional[str] = None      # type=reference
    inline_if_short: bool = True       # type=reference
    content: Optional[str] = None      # type=template
    from_path: Optional[str] = None    # type=computed
    transform: Optional[str] = None    # type=computed
    pattern: Optional[str] = None      # type=file_list
    description: Optional[str] = None


@dataclass
class Hook:
    """钩子定义"""
    trigger: str      # 触发点
    action: str       # 动作类型
    context_id: Optional[str] = None
    condition: Optional[str] = None
    priority: int = 0


@dataclass
class Extension:
    """扩展定义"""
    domain: str
    hooks: List[Hook] = field(default_factory=list)
    contexts: Dict[str, Context] = field(default_factory=dict)
    additional_files: List[Dict] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    roles_override: List[Dict] = field(default_factory=list)


class ExtensionProcessor:
    """扩展处理器"""

    # 支持的触发点
    TRIGGERS = {
        "dialogue.start",
        "dialogue.end",
        "qa.list_test_cases",
        "qa.acceptance",
        "dev.feature_complete",
        "dev.before_implement",
        "build.pre",
        "build.post",
        "milestone.review",
        "milestone.planning",
    }

    # 支持的动作
    ACTIONS = {
        "inject_context",
        "append_checklist",
        "require_file_read",
        "update_file",
    }

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.extensions: Dict[str, Extension] = {}
        self._project_config: Dict[str, Any] = {}

    def load_extension(self, ext_data: Dict[str, Any], domain: str) -> Extension:
        """加载扩展定义"""
        ext = Extension(domain=domain)
        
        # 加载钩子
        for hook_data in ext_data.get("hooks", []):
            hook = Hook(
                trigger=hook_data.get("trigger", ""),
                action=hook_data.get("action", ""),
                context_id=hook_data.get("context_id"),
                condition=hook_data.get("condition"),
                priority=hook_data.get("priority", 0),
            )
            ext.hooks.append(hook)
        
        # 加载上下文
        for ctx_id, ctx_data in ext_data.get("contexts", {}).items():
            ctx = Context(
                id=ctx_id,
                type=ctx_data.get("type", "template"),
                source=ctx_data.get("source"),
                section=ctx_data.get("section"),
                inline_if_short=ctx_data.get("inline_if_short", True),
                content=ctx_data.get("content"),
                from_path=ctx_data.get("from"),
                transform=ctx_data.get("transform"),
                pattern=ctx_data.get("pattern"),
                description=ctx_data.get("description"),
            )
            ext.contexts[ctx_id] = ctx
        
        # 加载额外文件
        ext.additional_files = ext_data.get("additional_files", [])
        
        # 加载配置
        ext.config = ext_data.get("config", {})
        
        self.extensions[domain] = ext
        return ext

    def load_from_config(self, config: Dict[str, Any]) -> None:
        """从项目配置中加载所有扩展"""
        self._project_config = config
        
        # 加载 roles_override (顶级)
        roles_override = config.get("roles_override", [])
        
        # 加载 domain_extensions
        domain_exts = config.get("domain_extensions", {}) or {}
        for domain, ext_data in domain_exts.items():
            if ext_data:  # 确保 ext_data 不为 None
                ext = self.load_extension(ext_data, domain)
                ext.roles_override = roles_override

    def get_hooks_for_trigger(self, trigger: str) -> List[Hook]:
        """获取指定触发点的所有钩子，按优先级排序"""
        hooks = []
        for ext in self.extensions.values():
            for hook in ext.hooks:
                if hook.trigger == trigger:
                    hooks.append(hook)
        
        # 按优先级降序排列
        return sorted(hooks, key=lambda h: h.priority, reverse=True)

    def evaluate_condition(self, condition: Optional[str], runtime_ctx: Dict[str, Any]) -> bool:
        """评估条件表达式"""
        if not condition:
            return True
        
        # 简单条件解析器
        # 支持: files.exists('path'), project.has_feature('x'), project.domain == 'x'
        
        # files.exists('path')
        match = re.match(r"files\.exists\(['\"](.+)['\"]\)", condition)
        if match:
            file_path = self.project_root / match.group(1)
            return file_path.exists()
        
        # project.has_feature('x')
        match = re.match(r"project\.has_feature\(['\"](.+)['\"]\)", condition)
        if match:
            feature = match.group(1)
            features = self._project_config.get("project", {}).get("features", [])
            return feature in features
        
        # project.domain == 'x'
        match = re.match(r"project\.domain\s*==\s*['\"](.+)['\"]", condition)
        if match:
            target_domain = match.group(1)
            current_domain = self._project_config.get("project", {}).get("domain", "")
            return current_domain == target_domain
        
        # topic.relates_to('x') - 需要运行时上下文
        match = re.match(r"topic\.relates_to\(['\"](.+)['\"]\)", condition)
        if match:
            topic = match.group(1)
            current_topic = runtime_ctx.get("topic", "")
            return topic.lower() in current_topic.lower()
        
        # 默认返回 True（未知条件不阻止执行）
        return True

    def resolve_context(self, ctx: Context, variables: Dict[str, Any]) -> str:
        """解析上下文内容"""
        if ctx.type == "reference":
            return self._resolve_reference(ctx)
        elif ctx.type == "template":
            return self._resolve_template(ctx, variables)
        elif ctx.type == "file_list":
            return self._resolve_file_list(ctx)
        elif ctx.type == "computed":
            return self._resolve_computed(ctx, variables)
        return ""

    def _resolve_reference(self, ctx: Context) -> str:
        """解析引用类型上下文"""
        if not ctx.source:
            return ""
        
        file_path = self.project_root / ctx.source
        if not file_path.exists():
            return f"<!-- 引用文件不存在: {ctx.source} -->"
        
        content = file_path.read_text(encoding="utf-8")
        
        # 如果指定了章节，提取该章节
        if ctx.section:
            content = self._extract_section(content, ctx.section)
        
        # 如果内容较短且配置了内联，返回完整内容
        if ctx.inline_if_short and len(content) < 500:
            return content
        
        # 否则返回引用提示
        return f"📄 见 `{ctx.source}`" + (f" → {ctx.section}" if ctx.section else "")

    def _resolve_template(self, ctx: Context, variables: Dict[str, Any]) -> str:
        """解析模板类型上下文"""
        if not ctx.content:
            return ""
        
        content = ctx.content
        
        # 替换变量 {variable_name}
        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", str(value))
        
        return content

    def _resolve_file_list(self, ctx: Context) -> str:
        """解析文件列表类型上下文"""
        if not ctx.pattern:
            return ""
        
        files = list(self.project_root.glob(ctx.pattern))
        if not files:
            return f"<!-- 未找到匹配 {ctx.pattern} 的文件 -->"
        
        result = f"**{ctx.description or '相关文件'}**:\n"
        for f in files:
            result += f"- `{f.relative_to(self.project_root)}`\n"
        return result

    def _resolve_computed(self, ctx: Context, variables: Dict[str, Any]) -> str:
        """解析计算类型上下文"""
        if not ctx.from_path:
            return ""
        
        # 从配置中获取数据
        data = self._get_nested_value(self._project_config, ctx.from_path)
        if data is None:
            return ""
        
        # 简单转换
        if isinstance(data, list):
            return "\n".join(f"- {item}" for item in data)
        return str(data)

    def _extract_section(self, content: str, section_header: str) -> str:
        """从 Markdown 中提取指定章节"""
        lines = content.split("\n")
        result = []
        in_section = False
        section_level = 0
        
        for line in lines:
            if line.strip().startswith("#"):
                # 检查是否是目标章节
                if section_header in line:
                    in_section = True
                    section_level = len(line) - len(line.lstrip("#"))
                    result.append(line)
                    continue
                # 检查是否离开了目标章节
                elif in_section:
                    current_level = len(line) - len(line.lstrip("#"))
                    if current_level <= section_level:
                        break
            if in_section:
                result.append(line)
        
        return "\n".join(result)

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """获取嵌套字典的值，支持点号路径"""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def process_trigger(
        self, 
        trigger: str, 
        runtime_ctx: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        处理触发点，返回需要执行的动作列表
        
        Args:
            trigger: 触发点标识
            runtime_ctx: 运行时上下文（如当前话题）
            variables: 模板变量
        
        Returns:
            动作列表，每个动作包含:
            - action: 动作类型
            - content: 要注入的内容（如果有）
            - context_id: 上下文ID
            - source: 来源扩展
        """
        runtime_ctx = runtime_ctx or {}
        variables = variables or {}
        
        results = []
        hooks = self.get_hooks_for_trigger(trigger)
        
        for hook in hooks:
            # 评估条件
            if not self.evaluate_condition(hook.condition, runtime_ctx):
                continue
            
            result = {
                "action": hook.action,
                "context_id": hook.context_id,
            }
            
            # 如果需要注入上下文，解析内容
            if hook.action == "inject_context" and hook.context_id:
                for ext in self.extensions.values():
                    if hook.context_id in ext.contexts:
                        ctx = ext.contexts[hook.context_id]
                        # 合并扩展配置到变量
                        merged_vars = {**ext.config, **variables}
                        result["content"] = self.resolve_context(ctx, merged_vars)
                        result["source"] = ext.domain
                        break
            
            results.append(result)
        
        return results

    def generate_extension_section(self, domain: str) -> str:
        """为指定领域生成扩展章节内容"""
        if domain not in self.extensions:
            return ""
        
        ext = self.extensions[domain]
        content = f"""# 领域扩展: {domain.upper()}

## 扩展钩子

以下钩子在特定流程节点自动触发：

| 触发点 | 动作 | 条件 | 上下文 |
|-------|------|------|--------|
"""
        for hook in ext.hooks:
            condition = hook.condition or "-"
            ctx_id = hook.context_id or "-"
            content += f"| `{hook.trigger}` | {hook.action} | {condition} | {ctx_id} |\n"
        
        content += """
## 可用上下文

"""
        for ctx_id, ctx in ext.contexts.items():
            desc = ctx.description or ""
            content += f"### {ctx_id}\n\n"
            content += f"- **类型**: {ctx.type}\n"
            if ctx.source:
                content += f"- **来源**: `{ctx.source}`\n"
            if desc:
                content += f"- **说明**: {desc}\n"
            content += "\n"
        
        return content


def load_extension_from_file(path: Path, project_root: Optional[Path] = None) -> ExtensionProcessor:
    """从 YAML 文件加载扩展"""
    import yaml
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    processor = ExtensionProcessor(project_root)
    processor.load_from_config(data)
    return processor
