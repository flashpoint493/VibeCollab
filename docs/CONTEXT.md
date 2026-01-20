# LLMTXTGenerator 当前上下文

## 当前状态
- **阶段**: Phase 1 - 核心框架完成
- **进度**: 扩展机制设计完成，文档同步
- **下一步**: 实现扩展钩子的代码支持

## 最近对话 (2026-01-20)

### 对话4: 文档同步
- 更新 README 同步最新扩展机制设计
- 补充扩展机制章节：钩子触发点、上下文类型
- 完善配置示例

### 对话3: 扩展机制重设计
- 扩展 = 流程钩子 + 上下文注入 + 引用文档
- 新增 extension.schema.yaml
- 重构 game/web/data 三个领域扩展

### 对话2: Python 包重构
- 重构为标准包结构
- 添加 CLI (Click + Rich)
- 准备 PyPI 发布

### 对话1: 项目初始化
- 从游戏 llm.txt 抽象核心协议
- 设计 YAML Schema

## 待完成事项
- [ ] 在 generator.py 中实现扩展钩子处理
- [ ] 生成 llm.txt 时渲染扩展内容
- [ ] 添加扩展机制单元测试
- [ ] 完善 mobile/infra 领域扩展

## 技术债务
- templates/ 和 src/llmtxt/templates/ 存在重复

---
*最后更新: 2026-01-20 对话4*
