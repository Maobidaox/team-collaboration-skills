---
name: java-engineering-playbook
display_name: Java 工程实践手册
display_name_en: Java Engineering Playbook
description: 面向 Java/Spring 项目的需求实现、代码审查、测试、架构设计、性能优化与故障诊断；在用户提到 Java、Spring、JVM、Maven、Gradle 或后端工程任务时使用
description_zh: 为 Java 与 Spring 工程任务提供仓库感知、风险驱动和可验证的实施方法
description_en: Repository-aware, risk-driven, and verifiable guidance for Java and Spring engineering tasks
category: coding
version: 1.0.0
author: Replace With Your Name
disable-model-invocation: false
user-invocable: true
---

# Java Engineering Playbook

为真实 Java 代码库提供可复用的工程决策框架。先以项目中的版本、约束和既有模式为准，再选择最小可行方案。不要把本技能当成强制重构清单。

## 使用边界

适用于：

- Java/Spring 功能开发、缺陷修复和代码重构
- API、数据库、消息、缓存、批处理与微服务设计
- 代码审查、测试策略、安全检查和依赖风险处理
- JVM、并发、性能、生产故障与可观测性分析

不自动授权：

- 发布生产、修改云资源、执行数据库破坏性迁移
- 升级主要框架/JDK 大版本或替换技术栈
- 访问未由用户提供或授权的生产数据与密钥

## 路由

只读取当前任务需要的参考资料：

- **进入陌生仓库、确认版本、选择构建命令**：`@references/project-discovery.md`
- **设计或实现 API、事务、数据、缓存、消息、并发逻辑**：`@references/architecture-and-implementation.md`
- **编写测试、审查变更、做安全或依赖检查**：`@references/testing-quality-security.md`
- **诊断线上故障、慢请求、GC、线程池、数据库性能**：`@references/troubleshooting-performance.md`
- **需要检索或核验技术事实**：`@references/official-sources.md`

可按需复制模板：

- 技术方案：`@templates/technical-design-template.md`
- 代码审查：`@templates/code-review-template.md`
- 故障诊断：`@templates/incident-diagnosis-template.md`

## 通用执行框架

1. **定义任务**：复述目标、非目标、验收条件和风险边界。
2. **读取事实**：检查项目指令、工作树、构建文件、版本、相邻实现和测试。
3. **制定最小方案**：说明关键业务不变量、失败模式、兼容性与验证方法。
4. **实施或分析**：保持改动聚焦；每个重要结论指向代码、配置、日志或测量证据。
5. **验证**：先局部后整体；测试、静态检查、构建或运行结果必须来自真实执行。
6. **交付**：给出结果、改动、验证、剩余风险和必要的下一步。

## 决策规则

- 项目约定与当前支持版本优先于外部通用示例。
- 对外行为或数据语义不清且不同选择会产生明显后果时，先询问；其余信息可做保守假设并明确说明。
- 用户只要求诊断/审查时保持只读；用户要求实现/修复时才修改文件。
- 对版本敏感或近期可能变化的事实，查官方文档并记录适用版本；不要从记忆给出“最新版本”。
- 对无法在当前环境验证的生产假设，给出验证步骤和预期证据，不把假设写成结论。
