"""
多开发者支持模块

提供开发者身份识别、上下文管理、协作文档生成等功能。
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class DeveloperManager:
    """开发者管理器，负责身份识别和目录管理"""
    
    def __init__(self, project_root: Path, config: dict):
        """
        初始化开发者管理器
        
        Args:
            project_root: 项目根目录
            config: 项目配置（project.yaml）
        """
        self.project_root = project_root
        self.config = config
        self.multi_dev_config = config.get('multi_developer', {})
        self.enabled = self.multi_dev_config.get('enabled', False)
        
        # 开发者目录
        self.developers_dir = project_root / self.multi_dev_config.get('context', {}).get(
            'per_developer_dir', 'docs/developers'
        )
    
    def get_current_developer(self) -> str:
        """
        获取当前开发者身份
        
        Returns:
            开发者标识符（标准化后的字符串）
        """
        identity_config = self.multi_dev_config.get('identity', {})
        primary = identity_config.get('primary', 'git_username')
        fallback = identity_config.get('fallback', 'system_user')
        normalize = identity_config.get('normalize', True)
        
        developer = None
        
        # 尝试主策略
        if primary == 'git_username':
            developer = self._get_git_username()
        elif primary == 'system_user':
            developer = self._get_system_user()
        elif primary == 'manual':
            # 手动模式：从环境变量或配置文件读取
            developer = os.environ.get('VIBECOLLAB_DEVELOPER')
        
        # 降级到备用策略
        if not developer:
            if fallback == 'git_username':
                developer = self._get_git_username()
            elif fallback == 'system_user':
                developer = self._get_system_user()
        
        # 最终降级：使用默认值
        if not developer:
            developer = 'unknown_developer'
        
        # 标准化
        if normalize:
            developer = self._normalize_developer_name(developer)
        
        return developer
    
    def _get_git_username(self) -> Optional[str]:
        """从 Git 配置获取用户名"""
        try:
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _get_system_user(self) -> Optional[str]:
        """获取系统用户名"""
        return os.environ.get('USER') or os.environ.get('USERNAME')
    
    def _normalize_developer_name(self, name: str) -> str:
        """
        标准化开发者名称
        
        规则：
        - 转为小写
        - 替换空格为下划线
        - 移除特殊字符，只保留字母、数字、下划线
        
        Args:
            name: 原始名称
        
        Returns:
            标准化后的名称
        """
        # 转小写
        name = name.lower()
        # 替换空格为下划线
        name = name.replace(' ', '_')
        # 移除特殊字符
        name = re.sub(r'[^a-z0-9_]', '', name)
        return name
    
    def get_developer_dir(self, developer: Optional[str] = None) -> Path:
        """
        获取开发者的工作目录
        
        Args:
            developer: 开发者标识符，None 则使用当前开发者
        
        Returns:
            开发者工作目录路径
        """
        if developer is None:
            developer = self.get_current_developer()
        return self.developers_dir / developer
    
    def get_developer_context_file(self, developer: Optional[str] = None) -> Path:
        """
        获取开发者的 CONTEXT.md 文件路径
        
        Args:
            developer: 开发者标识符，None 则使用当前开发者
        
        Returns:
            CONTEXT.md 文件路径
        """
        return self.get_developer_dir(developer) / "CONTEXT.md"
    
    def get_developer_metadata_file(self, developer: Optional[str] = None) -> Path:
        """
        获取开发者的元数据文件路径
        
        Args:
            developer: 开发者标识符，None 则使用当前开发者
        
        Returns:
            元数据文件路径
        """
        metadata_filename = self.multi_dev_config.get('context', {}).get(
            'metadata_file', '.metadata.yaml'
        )
        return self.get_developer_dir(developer) / metadata_filename
    
    def list_developers(self) -> List[str]:
        """
        列出所有开发者
        
        Returns:
            开发者标识符列表
        """
        if not self.developers_dir.exists():
            return []
        
        developers = []
        for item in self.developers_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                developers.append(item.name)
        
        return sorted(developers)
    
    def ensure_developer_dir(self, developer: Optional[str] = None) -> Path:
        """
        确保开发者目录存在，不存在则创建
        
        Args:
            developer: 开发者标识符，None 则使用当前开发者
        
        Returns:
            开发者工作目录路径
        """
        dev_dir = self.get_developer_dir(developer)
        dev_dir.mkdir(parents=True, exist_ok=True)
        return dev_dir
    
    def init_developer_context(self, developer: Optional[str] = None, force: bool = False):
        """
        初始化开发者的上下文文件
        
        Args:
            developer: 开发者标识符，None 则使用当前开发者
            force: 是否强制重新初始化（覆盖已有文件）
        """
        if developer is None:
            developer = self.get_current_developer()
        
        dev_dir = self.ensure_developer_dir(developer)
        context_file = self.get_developer_context_file(developer)
        metadata_file = self.get_developer_metadata_file(developer)
        
        # 初始化 CONTEXT.md
        if not context_file.exists() or force:
            project_name = self.config.get('project', {}).get('name', 'MyProject')
            project_version = self.config.get('project', {}).get('version', 'v1.0')
            
            context_content = f"""# {project_name} - {developer} 的工作上下文

## 当前状态
- **版本**: {project_version}
- **开发者**: {developer}
- **上次更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 当前任务
(暂无任务)

## 最近完成
(暂无记录)

## 待解决问题
(暂无问题)

## 技术债务
(暂无债务)

---
*此文件由 {developer} 维护*
"""
            context_file.write_text(context_content, encoding='utf-8')
        
        # 初始化元数据
        if not metadata_file.exists() or force:
            metadata = {
                'developer': developer,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_updates': 0
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                yaml.dump(metadata, f, allow_unicode=True, sort_keys=False)
    
    def update_metadata(self, developer: Optional[str] = None):
        """
        更新开发者的元数据
        
        Args:
            developer: 开发者标识符，None 则使用当前开发者
        """
        if developer is None:
            developer = self.get_current_developer()
        
        metadata_file = self.get_developer_metadata_file(developer)
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f) or {}
        else:
            metadata = {
                'developer': developer,
                'created_at': datetime.now().isoformat(),
                'total_updates': 0
            }
        
        metadata['last_updated'] = datetime.now().isoformat()
        metadata['total_updates'] = metadata.get('total_updates', 0) + 1
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, allow_unicode=True, sort_keys=False)
    
    def get_developer_status(self, developer: str) -> Dict:
        """
        获取开发者的状态信息
        
        Args:
            developer: 开发者标识符
        
        Returns:
            包含状态信息的字典
        """
        context_file = self.get_developer_context_file(developer)
        metadata_file = self.get_developer_metadata_file(developer)
        
        status = {
            'developer': developer,
            'exists': context_file.exists(),
            'context_file': str(context_file),
            'last_updated': None,
            'total_updates': 0
        }
        
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = yaml.safe_load(f) or {}
                status['last_updated'] = metadata.get('last_updated')
                status['total_updates'] = metadata.get('total_updates', 0)
        
        return status


class ContextAggregator:
    """上下文聚合器，负责生成全局 CONTEXT.md"""
    
    def __init__(self, project_root: Path, config: dict):
        """
        初始化上下文聚合器
        
        Args:
            project_root: 项目根目录
            config: 项目配置（project.yaml）
        """
        self.project_root = project_root
        self.config = config
        self.multi_dev_config = config.get('multi_developer', {})
        self.developer_manager = DeveloperManager(project_root, config)
    
    def aggregate(self) -> str:
        """
        聚合所有开发者的上下文，生成全局 CONTEXT.md
        
        Returns:
            聚合后的全局 CONTEXT 内容
        """
        project_name = self.config.get('project', {}).get('name', 'MyProject')
        project_version = self.config.get('project', {}).get('version', 'v1.0')
        
        developers = self.developer_manager.list_developers()
        
        # 构建全局 CONTEXT
        sections = []
        
        # 标题和警告
        sections.append(f"# {project_name} 全局上下文")
        sections.append("")
        sections.append("> ⚠️ **此文件自动生成，请勿手动编辑**")
        sections.append(f"> 上次更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"> 聚合自: {', '.join(developers) if developers else '(无开发者)'}")
        sections.append("")
        
        # 项目整体状态
        sections.append("## 项目整体状态")
        sections.append(f"- **版本**: {project_version}")
        sections.append(f"- **活跃开发者**: {len(developers)} ({', '.join(developers)})")
        sections.append("")
        
        # 各开发者工作状态
        if developers:
            sections.append("## 各开发者工作状态")
            sections.append("")
            
            for dev in developers:
                dev_status = self._extract_developer_summary(dev)
                sections.append(f"### {dev}")
                sections.append(f"- **上次更新**: {dev_status['last_updated']}")
                sections.append(f"- **当前任务**: {dev_status['current_task']}")
                sections.append(f"- **进度**: {dev_status['progress']}")
                sections.append(f"- **待解决问题**: {dev_status['issues']}")
                sections.append(f"- **下一步**: {dev_status['next_steps']}")
                sections.append("")
        else:
            sections.append("## 开发者状态")
            sections.append("(暂无开发者)")
            sections.append("")
        
        # 跨开发者依赖（从 COLLABORATION.md 提取）
        collaboration_info = self._extract_collaboration_info()
        if collaboration_info:
            sections.append("## 跨开发者协作")
            sections.append(collaboration_info)
            sections.append("")
        
        # 全局技术债务（合并所有开发者）
        global_debts = self._merge_technical_debts(developers)
        if global_debts:
            sections.append("## 全局技术债务")
            for debt in global_debts:
                sections.append(f"- {debt}")
            sections.append("")
        
        sections.append("---")
        sections.append("*此文件由多开发者上下文自动聚合生成*")
        
        return "\n".join(sections)
    
    def _extract_developer_summary(self, developer: str) -> Dict:
        """
        从开发者的 CONTEXT.md 提取摘要信息
        
        Args:
            developer: 开发者标识符
        
        Returns:
            摘要信息字典
        """
        context_file = self.developer_manager.get_developer_context_file(developer)
        
        summary = {
            'last_updated': '未知',
            'current_task': '(暂无任务)',
            'progress': '(无)',
            'issues': '(无)',
            'next_steps': '(无)'
        }
        
        if not context_file.exists():
            return summary
        
        try:
            content = context_file.read_text(encoding='utf-8')
            
            # 提取上次更新时间
            if '上次更新' in content:
                match = re.search(r'上次更新.*?(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
                if match:
                    summary['last_updated'] = match.group(1)
            
            # 提取当前任务（简单提取第一行非空内容）
            if '## 当前任务' in content:
                task_section = re.search(r'## 当前任务\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
                if task_section:
                    lines = [l.strip() for l in task_section.group(1).split('\n') if l.strip() and not l.strip().startswith('(')]
                    if lines:
                        summary['current_task'] = lines[0][:100]  # 限制长度
            
            # 提取其他信息（简化版）
            # 可以根据需要进一步细化提取逻辑
            
        except Exception:
            pass
        
        return summary
    
    def _extract_collaboration_info(self) -> Optional[str]:
        """
        从 COLLABORATION.md 提取协作信息
        
        Returns:
            协作信息字符串，无则返回 None
        """
        collab_config = self.multi_dev_config.get('collaboration', {})
        collab_file_path = self.project_root / collab_config.get('file', 'docs/developers/COLLABORATION.md')
        
        if not collab_file_path.exists():
            return None
        
        try:
            content = collab_file_path.read_text(encoding='utf-8')
            # 提取关键协作信息（简化版）
            # 实际可以解析任务依赖矩阵等
            return "(详见 docs/developers/COLLABORATION.md)"
        except Exception:
            return None
    
    def _merge_technical_debts(self, developers: List[str]) -> List[str]:
        """
        合并所有开发者的技术债务
        
        Args:
            developers: 开发者列表
        
        Returns:
            技术债务列表
        """
        debts = []
        
        for dev in developers:
            context_file = self.developer_manager.get_developer_context_file(dev)
            if not context_file.exists():
                continue
            
            try:
                content = context_file.read_text(encoding='utf-8')
                if '## 技术债务' in content:
                    debt_section = re.search(r'## 技术债务\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
                    if debt_section:
                        lines = [l.strip() for l in debt_section.group(1).split('\n') if l.strip() and l.strip().startswith('-')]
                        for line in lines:
                            debts.append(f"[{dev}] {line}")
            except Exception:
                pass
        
        return debts
    
    def generate_and_save(self) -> Path:
        """
        生成并保存全局 CONTEXT.md
        
        Returns:
            保存的文件路径
        """
        context_config = self.multi_dev_config.get('context', {})
        output_file = self.project_root / context_config.get('aggregation_file', 'docs/CONTEXT.md')
        
        content = self.aggregate()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding='utf-8')
        
        return output_file


def migrate_to_multi_developer(project_root: Path, config: dict, developer_name: Optional[str] = None):
    """
    将单开发者项目迁移到多开发者模式
    
    Args:
        project_root: 项目根目录
        config: 项目配置
        developer_name: 初始开发者名称，None 则自动识别
    """
    dm = DeveloperManager(project_root, config)
    
    if developer_name is None:
        developer_name = dm.get_current_developer()
    
    # 1. 创建开发者目录
    dev_dir = dm.ensure_developer_dir(developer_name)
    
    # 2. 移动现有的 CONTEXT.md
    old_context = project_root / "docs" / "CONTEXT.md"
    new_context = dm.get_developer_context_file(developer_name)
    
    if old_context.exists() and not new_context.exists():
        # 移动文件
        new_context.write_text(old_context.read_text(encoding='utf-8'), encoding='utf-8')
        
        # 备份原文件
        backup = project_root / "docs" / "CONTEXT.md.backup"
        old_context.rename(backup)
    
    # 3. 初始化元数据
    dm.init_developer_context(developer_name)
    
    # 4. 生成 COLLABORATION.md
    collab_config = config.get('multi_developer', {}).get('collaboration', {})
    collab_file = project_root / collab_config.get('file', 'docs/developers/COLLABORATION.md')
    
    if not collab_file.exists():
        collab_content = f"""# 开发者协作记录

## 当前协作关系

(暂无协作记录)

## 任务分配矩阵

| 任务 | 负责人 | 协作者 | 状态 | 依赖 |
|------|--------|--------|------|------|
| - | {developer_name} | - | - | - |

## 交接记录

(暂无交接记录)

---
*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        collab_file.parent.mkdir(parents=True, exist_ok=True)
        collab_file.write_text(collab_content, encoding='utf-8')
    
    # 5. 生成新的全局聚合 CONTEXT.md
    aggregator = ContextAggregator(project_root, config)
    aggregator.generate_and_save()
    
    print(f"✅ 成功迁移到多开发者模式")
    print(f"   开发者: {developer_name}")
    print(f"   上下文目录: {dev_dir}")
