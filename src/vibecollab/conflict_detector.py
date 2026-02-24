"""
跨开发者冲突检测模块

提供多开发者协作中的冲突检测功能。
"""

import platform
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml


# Windows GBK 编码兼容
def is_windows_gbk():
    """检测是否为 Windows 且使用 GBK 编码"""
    if platform.system() != "Windows":
        return False
    try:
        "✅⚠️❌🔴🟡🟢".encode(sys.stdout.encoding or "utf-8")
        return False
    except (UnicodeEncodeError, LookupError):
        return True


USE_EMOJI = not is_windows_gbk()

EMOJI_MAP = {
    "success": "OK" if not USE_EMOJI else "✅",
    "warning": "!" if not USE_EMOJI else "⚠️",
    "error": "X" if not USE_EMOJI else "❌",
    "high": "[!]" if not USE_EMOJI else "🔴",
    "medium": "[~]" if not USE_EMOJI else "🟡",
    "low": "[*]" if not USE_EMOJI else "🟢",
    "idea": "[?]" if not USE_EMOJI else "💡",
}



class ConflictType:
    """冲突类型枚举"""
    FILE = "file"              # 文件冲突
    TASK = "task"              # 任务冲突
    DEPENDENCY = "dependency"  # 依赖冲突
    NAMING = "naming"          # 命名冲突


class Conflict:
    """冲突对象"""

    def __init__(self, conflict_type: str, severity: str,
                 developers: List[str], description: str,
                 details: Optional[Dict] = None):
        """
        初始化冲突对象

        Args:
            conflict_type: 冲突类型（file/task/dependency/naming）
            severity: 严重程度（high/medium/low）
            developers: 涉及的开发者列表
            description: 冲突描述
            details: 详细信息（可选）
        """
        self.type = conflict_type
        self.severity = severity
        self.developers = developers
        self.description = description
        self.details = details or {}
        self.detected_at = datetime.now()

    def to_dict(self) -> Dict:
        """转为字典格式"""
        return {
            'type': self.type,
            'severity': self.severity,
            'developers': self.developers,
            'description': self.description,
            'details': self.details,
            'detected_at': self.detected_at.isoformat()
        }

    def __str__(self) -> str:
        """字符串表示"""
        devs = ', '.join(self.developers)
        return f"[{self.severity.upper()}] {self.type}: {self.description} (涉及: {devs})"


class ConflictDetector:
    """跨开发者冲突检测器"""

    def __init__(self, project_root: Path, config: dict):
        """
        初始化冲突检测器

        Args:
            project_root: 项目根目录
            config: 项目配置
        """
        self.project_root = project_root
        self.config = config
        self.multi_dev_config = config.get('multi_developer', {})

        # 开发者目录
        self.developers_dir = project_root / self.multi_dev_config.get('context', {}).get(
            'per_developer_dir', 'docs/developers'
        )

        # 缓存
        self._developer_contexts = {}
        self._collaboration_data = None
        self._git_changed_files = {}

    def detect_all_conflicts(self, target_developer: Optional[str] = None,
                            between_developers: Optional[Tuple[str, str]] = None) -> List[Conflict]:
        """
        检测所有类型的冲突

        Args:
            target_developer: 目标开发者（None 则检测当前开发者）
            between_developers: 检测两个特定开发者之间的冲突

        Returns:
            冲突列表
        """
        conflicts = []

        # 加载数据
        self._load_developer_contexts()
        self._load_collaboration_data()
        self._load_git_changes()

        # 确定要检查的开发者范围
        if between_developers:
            dev1, dev2 = between_developers
            if dev1 not in self._developer_contexts or dev2 not in self._developer_contexts:
                return conflicts
            check_pairs = [(dev1, dev2)]
        elif target_developer:
            if target_developer not in self._developer_contexts:
                return conflicts
            other_devs = [d for d in self._developer_contexts.keys() if d != target_developer]
            check_pairs = [(target_developer, other) for other in other_devs]
        else:
            # 检测所有开发者之间的冲突
            devs = list(self._developer_contexts.keys())
            check_pairs = [(devs[i], devs[j]) for i in range(len(devs)) for j in range(i+1, len(devs))]

        # 执行各类冲突检测
        for dev1, dev2 in check_pairs:
            conflicts.extend(self._detect_file_conflicts(dev1, dev2))
            conflicts.extend(self._detect_task_conflicts(dev1, dev2))
            conflicts.extend(self._detect_naming_conflicts(dev1, dev2))

        # 检测依赖冲突（全局检测，不限于两两对比）
        conflicts.extend(self._detect_dependency_conflicts())

        return conflicts

    def _load_developer_contexts(self):
        """加载所有开发者的上下文"""
        if not self.developers_dir.exists():
            return

        for dev_dir in self.developers_dir.iterdir():
            if not dev_dir.is_dir() or dev_dir.name.startswith('.'):
                continue

            developer = dev_dir.name
            context_file = dev_dir / "CONTEXT.md"
            metadata_file = dev_dir / ".metadata.yaml"

            if context_file.exists():
                context_content = context_file.read_text(encoding='utf-8')

                # 提取关键信息
                current_tasks = self._extract_current_tasks(context_content)
                recent_work = self._extract_section_content(context_content, "最近完成")
                issues = self._extract_section_content(context_content, "待解决问题")

                metadata = {}
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = yaml.safe_load(f) or {}

                self._developer_contexts[developer] = {
                    'tasks': current_tasks,
                    'recent_work': recent_work,
                    'issues': issues,
                    'metadata': metadata,
                    'raw_content': context_content
                }

    def _load_collaboration_data(self):
        """加载协作文档数据"""
        collab_config = self.multi_dev_config.get('collaboration', {})
        collab_file = self.project_root / collab_config.get('file', 'docs/developers/COLLABORATION.md')

        if not collab_file.exists():
            self._collaboration_data = {'tasks': {}, 'dependencies': {}}
            return

        content = collab_file.read_text(encoding='utf-8')

        # 解析任务分配矩阵
        tasks = {}
        task_pattern = r'\| (TASK-[A-Z]+-\d+)[:\s]([^\|]+) \| ([^\|]+) \| ([^\|]*) \| ([^\|]+) \| ([^\|]+) \|'
        for match in re.finditer(task_pattern, content):
            task_id = match.group(1).strip()
            task_name = match.group(2).strip()
            owner = match.group(3).strip()
            collaborators = match.group(4).strip()
            status = match.group(5).strip()
            dependencies = match.group(6).strip()

            tasks[task_id] = {
                'name': task_name,
                'owner': owner,
                'collaborators': [c.strip() for c in collaborators.split(',') if c.strip() and c.strip() != '-'],
                'status': status,
                'dependencies': [d.strip() for d in dependencies.split(',') if d.strip() and d.strip() != '-']
            }

        self._collaboration_data = {'tasks': tasks}

    def _load_git_changes(self):
        """加载 Git 变更文件（从各开发者的 CONTEXT 推断）"""
        # 简化版：从 CONTEXT.md 的"最近完成"章节提取文件路径
        for developer, ctx_data in self._developer_contexts.items():
            recent = ctx_data.get('recent_work', '')

            # 提取可能的文件路径（简单正则）
            file_patterns = re.findall(r'`([^\`]+\.[a-z]{2,4})`', recent)
            self._git_changed_files[developer] = set(file_patterns)

    def _detect_file_conflicts(self, dev1: str, dev2: str) -> List[Conflict]:
        """检测文件冲突"""
        conflicts = []

        files1 = self._git_changed_files.get(dev1, set())
        files2 = self._git_changed_files.get(dev2, set())

        common_files = files1 & files2

        if common_files:
            conflicts.append(Conflict(
                conflict_type=ConflictType.FILE,
                severity="medium",
                developers=[dev1, dev2],
                description="同时修改了相同的文件",
                details={'files': list(common_files)}
            ))

        return conflicts

    def _detect_task_conflicts(self, dev1: str, dev2: str) -> List[Conflict]:
        """检测任务冲突"""
        conflicts = []

        tasks1 = self._developer_contexts.get(dev1, {}).get('tasks', [])
        tasks2 = self._developer_contexts.get(dev2, {}).get('tasks', [])

        # 检测相似任务描述（简单字符串匹配）
        for task1 in tasks1:
            for task2 in tasks2:
                similarity = self._calculate_similarity(task1, task2)
                if similarity > 0.6:  # 60% 相似度阈值
                    conflicts.append(Conflict(
                        conflict_type=ConflictType.TASK,
                        severity="high",
                        developers=[dev1, dev2],
                        description="可能存在重复或重叠的任务",
                        details={
                            f'{dev1}_task': task1,
                            f'{dev2}_task': task2,
                            'similarity': similarity
                        }
                    ))

        return conflicts

    def _detect_dependency_conflicts(self) -> List[Conflict]:
        """检测依赖冲突（循环依赖、不一致依赖）"""
        conflicts = []

        tasks = self._collaboration_data.get('tasks', {})

        # 构建依赖图
        dep_graph = defaultdict(set)
        for task_id, task_data in tasks.items():
            for dep in task_data.get('dependencies', []):
                dep_graph[task_id].add(dep)

        # 检测循环依赖（深度优先搜索）
        visited = set()
        rec_stack = set()

        def has_cycle(node, path):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path + [neighbor]):
                        return True
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle = path[path.index(neighbor):] + [neighbor]
                    conflicts.append(Conflict(
                        conflict_type=ConflictType.DEPENDENCY,
                        severity="high",
                        developers=self._get_developers_for_tasks(cycle),
                        description="检测到循环依赖",
                        details={'cycle': ' → '.join(cycle)}
                    ))
                    return True

            rec_stack.remove(node)
            return False

        for task_id in dep_graph.keys():
            if task_id not in visited:
                has_cycle(task_id, [task_id])

        return conflicts

    def _detect_naming_conflicts(self, dev1: str, dev2: str) -> List[Conflict]:
        """检测命名冲突（函数名、类名等）"""
        conflicts = []

        # 从 CONTEXT 中提取可能的命名（简化版）
        ctx1 = self._developer_contexts.get(dev1, {}).get('raw_content', '')
        ctx2 = self._developer_contexts.get(dev2, {}).get('raw_content', '')

        # 提取代码块中的类名/函数名
        names1 = self._extract_code_names(ctx1)
        names2 = self._extract_code_names(ctx2)

        common_names = names1 & names2

        if common_names:
            conflicts.append(Conflict(
                conflict_type=ConflictType.NAMING,
                severity="low",
                developers=[dev1, dev2],
                description="使用了相同的命名",
                details={'names': list(common_names)}
            ))

        return conflicts

    def _extract_current_tasks(self, content: str) -> List[str]:
        """从 CONTEXT 中提取当前任务"""
        tasks = []

        # 提取"当前任务"章节
        section = self._extract_section_content(content, "当前任务")

        # 提取列表项
        lines = section.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('*'):
                task = line.lstrip('-*').strip()
                if task and not task.startswith('('):
                    tasks.append(task)

        return tasks

    def _extract_section_content(self, content: str, section_header: str) -> str:
        """从 Markdown 中提取指定章节的内容"""
        pattern = rf'##\s+{re.escape(section_header)}\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()
        return ""

    def _extract_code_names(self, content: str) -> Set[str]:
        """从内容中提取代码命名（类名、函数名等）"""
        names = set()

        # 提取代码块
        code_blocks = re.findall(r'```[a-z]*\n(.*?)\n```', content, re.DOTALL)

        for code in code_blocks:
            # 提取类名（class ClassName）
            class_names = re.findall(r'class\s+([A-Z][a-zA-Z0-9_]*)', code)
            names.update(class_names)

            # 提取函数名（def function_name 或 function functionName）
            func_names = re.findall(r'(?:def|function)\s+([a-z_][a-zA-Z0-9_]*)', code)
            names.update(func_names)

        return names

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度（简单版Jaccard相似度）"""
        if not str1 or not str2:
            return 0.0

        # 转小写并分词
        words1 = set(re.findall(r'\w+', str1.lower()))
        words2 = set(re.findall(r'\w+', str2.lower()))

        if not words1 or not words2:
            return 0.0

        # Jaccard 相似度
        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _get_developers_for_tasks(self, task_ids: List[str]) -> List[str]:
        """获取任务对应的开发者"""
        tasks = self._collaboration_data.get('tasks', {})
        developers = set()

        for task_id in task_ids:
            task = tasks.get(task_id, {})
            owner = task.get('owner', '')
            if owner:
                developers.add(owner)

        return list(developers)

    def generate_conflict_report(self, conflicts: List[Conflict], verbose: bool = False) -> str:
        """
        生成冲突报告

        Args:
            conflicts: 冲突列表
            verbose: 是否包含详细信息

        Returns:
            报告文本
        """
        if not conflicts:
            return f"{EMOJI_MAP['success']} 未检测到冲突"

        lines = []
        lines.append(f"{EMOJI_MAP['warning']} 检测到 {len(conflicts)} 个潜在冲突\n")

        # 按严重程度分组
        by_severity = defaultdict(list)
        for conflict in conflicts:
            by_severity[conflict.severity].append(conflict)

        severity_order = ['high', 'medium', 'low']
        severity_icons = {
            'high': EMOJI_MAP['high'],
            'medium': EMOJI_MAP['medium'],
            'low': EMOJI_MAP['low']
        }

        for severity in severity_order:
            items = by_severity.get(severity, [])
            if not items:
                continue

            lines.append(f"\n{severity_icons[severity]} {severity.upper()} 优先级 ({len(items)} 个):")
            lines.append("-" * 60)

            for i, conflict in enumerate(items, 1):
                devs = ', '.join(conflict.developers)
                lines.append(f"{i}. [{conflict.type.upper()}] {conflict.description}")
                lines.append(f"   涉及开发者: {devs}")

                if verbose and conflict.details:
                    lines.append("   详细信息:")
                    for key, value in conflict.details.items():
                        lines.append(f"     - {key}: {value}")

                lines.append("")

        lines.append("\n" + "=" * 60)
        lines.append(f"{EMOJI_MAP['idea']} 建议:")
        lines.append("  1. 与相关开发者沟通，明确分工边界")
        lines.append("  2. 更新 COLLABORATION.md 记录协作决策")
        lines.append("  3. 考虑任务重新分配或合并")

        return '\n'.join(lines)
