# VibeCollab 重要决策记录

## DECISION-001: 创建 AI Agent 开发者

- **等级**: B
- **角色**: [ARCH]
- **日期**: 2026-02-25
- **开发者**: jarvis01
- **问题**: 需要推进 VibeCollab 开发，使用 Agent 自主模式
- **决策**: 创建新的 AI Agent 开发者 jarvis01，使用 GLM-4.7 API
- **理由**:
  - GLM-4.7 提供强大的代码能力
  - Agent 自主模式可以提高开发效率
  - 符合 VibeCollab 的核心理念（AI 作为协作伙伴）
- **影响**:
  - 新开发者上下文: docs/developers/jarvis01/
  - 需要更新多开发者配置
- **状态**: CONFIRMED
- **相关文件**:
  - .vibecollab.local.yaml
  - project.yaml (llm_client 配置)

## DECISION-002: v0.8.0 开发计划

- **等级**: A
- **角色**: [ARCH][DESIGN]
- **日期**: 2026-02-25
- **开发者**: jarvis01
- **问题**: 确定下一个版本的开发重点
- **决策**: v0.8.0 专注于以下核心功能：
  1. P0: 多开发者协同增强
  2. P1: Insight 系统优化
  3. P1: Agent 模式完善
  4. P2: 项目健康信号
  5. P2: 文档一致性检查
- **理由**:
  - 多开发者协同是核心需求
  - Insight 系统是差异化功能
  - Agent 模式符合项目愿景
  - 健康信号和文档检查是质量保障
- **影响**:
  - 需要重构部分模块
  - 新增健康检查系统
  - 增强文档同步机制
- **状态**: CONFIRMED
- **相关文件**:
  - ROADMAP.md
  - docs/CHANGELOG.md

## DECISION-003: 不将 Developer 作为包，采用 Profile 模式

- **等级**: A
- **角色**: [ARCH][DESIGN]
- **日期**: 2026-02-25
- **开发者**: jarvis01
- **问题**: 是否应该将 Developer 单元也做成包，以便未来组装形成带经验的团队 Agent？
- **决策**: 暂不将 Developer 作为包，采用 Developer Profile + Insight Collection 模式
- **理由**:
  - LLM + 上下文系统已足够表达"经验"
  - Insight 作为知识包已符合设计理念
  - 避免过度设计（遵循 YAGNI 原则）
  - Developer 有状态（CONTEXT.md），打包复杂度高
  - 保留未来扩展能力
- **替代方案**:
  - **Developer Profile**: 定义角色的技能、倾向、常用模式（可打包）
  - **Insight Collection**: 将一组相关 Insight 打包为"技能包"（可移植）
  - **模板系统**: 提供预设的 Developer 模板
- **影响**:
  - 不增加 Developer 包化复杂度
  - 专注于优化 Insight 系统
  - 保持系统简洁性
- **相关 Insight**:
  - INS-011: 避免过度设计 - 依靠 LLM 推理而非静态配置
- **状态**: PENDING_CONFIRMATION
- **相关文件**:
  - docs/DECISION_ANALYSIS.md
  - .vibecollab/insights/INS-011.yaml

## DECISION-004: v0.8+ 实施 ProjectAdapter 优化框架

- **等级**: A
- **角色**: [ARCH][DESIGN]
- **日期**: 2026-02-25
- **开发者**: jarvis01
- **问题**: 如何支持用户自定义 project.yaml 字段，同时保持向后兼容性？
- **决策**: 实施 ProjectAdapter 配置适配器模式
- **理由**:
  - 提高配置灵活性和兼容性
  - 支持用户自定义字段
  - 向后兼容现有配置
  - 提供验证和迁移工具
- **实现计划**:
  - **P0 (核心适配器)**:
    - 实现 ProjectAdapter 类
    - 提供字段获取的容错机制
    - 内置默认角色定义
  - **P1 (模板改进)**:
    - 所有模板改用适配器访问字段
    - 支持自定义字段渲染
    - 向后兼容现有配置
  - **P2 (工具支持)**:
    - 新增 `vibecollab validate config` 命令
    - 配置校验和提示
    - 配置迁移工具
- **字段分类**:
  - **Protocol Required**: project.name, project.version, project.domain
  - **Core Strongly Recommended**: roles, philosophy, lifecycle
  - **Fully Customizable**: custom.*, extension.*
- **相关 Insight**:
  - INS-012: 配置适配器模式 - 向后兼容的扩展机制
- **状态**: PENDING_CONFIRMATION
- **相关文件**:
  - docs/DECISION_ANALYSIS.md
  - .vibecollab/insights/INS-012.yaml

---
*此文件由 VibeCollab 自动维护*
