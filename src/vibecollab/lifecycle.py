"""
项目生涯管理 - 生命周期阶段管理
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
import yaml


# 默认阶段定义
DEFAULT_STAGES = {
    "demo": {
        "name": "原型验证",
        "description": "快速验证核心概念和可行性",
        "focus": ["快速迭代", "概念验证", "核心功能"],
        "principles": [
            "快速试错，快速调整",
            "优先核心功能，暂缓优化",
            "技术债务可接受，但需记录",
            "详细的Git开发迭代记录",
            "记录重要决定DECISIONS.md",
            "建立 CI/CD"
        ],
        "milestones": []
    },
    "production": {
        "name": "量产",
        "description": "产品化开发，准备规模化",
        "focus": ["稳定性", "性能优化", "可维护性"],
        "principles": [
            "代码质量优先",
            "建立发布和宣发预备, 指定和完善目标平台支持",
            "启动前review全量代码，建立更稳定稳健的代码结构",
            "完善QA产品测试覆盖",
            "定义性能标准",
            "Unitest单元测试、检查规范",
            "完善发布平台标准"
        ],
        "milestones": []
    },
    "commercial": {
        "name": "商业化",
        "description": "面向市场，追求增长",
        "focus": ["用户体验", "市场适配", "扩展性", "插件化增量开发", "数据热更"],
        "principles": [
            "用户反馈驱动",
            "数据驱动决策",
            "快速响应市场"
        ],
        "milestones": []
    },
    "stable": {
        "name": "稳定运营",
        "description": "成熟产品，稳定维护",
        "focus": ["稳定性", "维护成本", "长期规划"],
        "principles": [
            "变更需谨慎",
            "向后兼容优先",
            "文档完善"
        ],
        "milestones": []
    }
}

# 阶段顺序
STAGE_ORDER = ["demo", "production", "commercial", "stable"]


class LifecycleManager:
    """项目生涯管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化生涯管理器
        
        Args:
            config: 项目配置字典
        """
        self.config = config
        self.lifecycle_config = config.get("lifecycle", {})
        
        # 如果配置中没有 stages，使用默认值
        if "stages" not in self.lifecycle_config:
            self.lifecycle_config["stages"] = DEFAULT_STAGES.copy()
        
    @classmethod
    def create_default(cls, current_stage: str = "demo") -> "LifecycleManager":
        """创建默认生涯配置
        
        Args:
            current_stage: 初始阶段，默认为 demo
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
        """获取当前阶段
        
        Returns:
            str: 当前阶段代码
        """
        return self.lifecycle_config.get("current_stage", "demo")
    
    def get_stage_info(self, stage: Optional[str] = None) -> Dict[str, Any]:
        """获取阶段信息
        
        Args:
            stage: 阶段代码，如果为 None 则返回当前阶段
            
        Returns:
            Dict: 阶段信息
        """
        if stage is None:
            stage = self.get_current_stage()
        
        stages = self.lifecycle_config.get("stages", DEFAULT_STAGES)
        return stages.get(stage, DEFAULT_STAGES.get(stage, {}))
    
    def get_stage_history(self) -> List[Dict[str, Any]]:
        """获取阶段历史
        
        Returns:
            List[Dict]: 阶段历史记录
        """
        return self.lifecycle_config.get("stage_history", [])
    
    def can_upgrade(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """检查是否可以升级到下一阶段
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (是否可以升级, 下一阶段代码, 原因)
        """
        current_stage = self.get_current_stage()
        
        # 获取当前阶段在顺序中的位置
        try:
            current_index = STAGE_ORDER.index(current_stage)
        except ValueError:
            return False, None, f"未知的当前阶段: {current_stage}"
        
        # 检查是否已经是最后阶段
        if current_index >= len(STAGE_ORDER) - 1:
            return False, None, "已经是最后阶段，无法继续升级"
        
        # 获取下一阶段
        next_stage = STAGE_ORDER[current_index + 1]
        
        # 检查当前阶段的里程碑是否完成
        stage_info = self.get_stage_info(current_stage)
        milestones = stage_info.get("milestones", [])
        
        if milestones:
            # 检查里程碑完成情况
            completed = [m for m in milestones if m.get("completed", False)]
            if len(completed) < len(milestones):
                return False, next_stage, f"当前阶段还有 {len(milestones) - len(completed)} 个里程碑未完成"
        
        return True, next_stage, None
    
    def upgrade_to_stage(self, target_stage: str) -> Tuple[bool, Optional[str]]:
        """升级到指定阶段
        
        Args:
            target_stage: 目标阶段代码
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息)
        """
        current_stage = self.get_current_stage()
        
        # 验证目标阶段
        if target_stage not in STAGE_ORDER:
            return False, f"无效的阶段代码: {target_stage}"
        
        # 检查是否可以升级
        can_upgrade, next_stage, reason = self.can_upgrade()
        if not can_upgrade and target_stage != current_stage:
            if reason:
                return False, reason
            return False, "无法升级到该阶段"
        
        # 如果目标阶段不是下一阶段，需要检查顺序
        try:
            current_index = STAGE_ORDER.index(current_stage)
            target_index = STAGE_ORDER.index(target_stage)
            
            if target_index <= current_index:
                return False, f"目标阶段 {target_stage} 不能早于或等于当前阶段 {current_stage}"
            
            # 检查是否跳过了中间阶段
            if target_index > current_index + 1:
                return False, f"不能跳过中间阶段，请先升级到 {STAGE_ORDER[current_index + 1]}"
        except ValueError:
            return False, "阶段验证失败"
        
        # 执行升级
        # 更新当前阶段
        if "lifecycle" not in self.config:
            self.config["lifecycle"] = {}
        
        self.config["lifecycle"]["current_stage"] = target_stage
        
        # 记录阶段历史
        if "stage_history" not in self.config["lifecycle"]:
            self.config["lifecycle"]["stage_history"] = []
        
        # 更新当前阶段的结束时间
        history = self.config["lifecycle"]["stage_history"]
        if history and history[-1].get("stage") == current_stage:
            history[-1]["ended_at"] = datetime.now().strftime("%Y-%m-%d")
        
        # 添加新阶段记录
        history.append({
            "stage": target_stage,
            "started_at": datetime.now().strftime("%Y-%m-%d"),
            "milestones_completed": []
        })
        
        return True, None
    
    def check_milestone_completion(self) -> Dict[str, Any]:
        """检查里程碑完成情况
        
        Returns:
            Dict: 里程碑完成情况统计
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
        """获取升级建议
        
        Args:
            target_stage: 目标阶段，如果为 None 则使用下一阶段
            
        Returns:
            List[str]: 升级建议列表
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
        
        # 对比原则，找出需要关注的变化
        current_principles = set(current_info.get("principles", []))
        target_principles = set(target_info.get("principles", []))
        
        new_principles = target_principles - current_principles
        if new_principles:
            suggestions.append(f"新增原则: {', '.join(new_principles)}")
        
        # 对比重点
        current_focus = set(current_info.get("focus", []))
        target_focus = set(target_info.get("focus", []))
        
        new_focus = target_focus - current_focus
        if new_focus:
            suggestions.append(f"新增关注点: {', '.join(new_focus)}")
        
        return suggestions
    
    def to_config_dict(self) -> Dict[str, Any]:
        """转换为配置字典
        
        Returns:
            Dict: 配置字典
        """
        return {
            "lifecycle": self.lifecycle_config
        }
