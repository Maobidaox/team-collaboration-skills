# 搭台师 (Benchwright) — 工作台搭建专家

一位专注「工作台搭建」的 AI 专家：帮助个人与团队把零散的工具、流程和数据，整合为可用、可落地、可持续演进的个性化工作台。

## 类型
Agent 型（单个 AI 专家）

## 核心能力
- 需求调研与场景拆解
- 信息架构与模块规划
- 工具与系统集成设计
- 流程自动化编排
- 可视化与交互设计
- 选型与落地路线（MVP → 迭代）

## 内置技能
- `workbench-blueprint`：工作台搭建方法论 + 《工作台蓝图》模板 + 模块库参考，交付结构化、可评审的搭建方案。

## 使用示例（试试这样问我）
- 帮我设计一个销售团队的工作台，需要包含哪些核心模块？
- 如何把我的日常重复性工作自动化成一个工作台？
- 帮我规划一个项目管理可视化工作台的信息架构与布局

## 头像
头像位于 `avatars/expert.png`（512×512，PNG，≤500KB）。如需替换，要求：PNG/JPG、512×512、单张 ≤500KB。

## 安装
专家已置于专家目录：
```
/Users/jacky.chen/.workbuddy/plugins/marketplaces/my-experts/plugins/workbench-builder/
```
如需重新注册使其可见：
```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享
```bash
python3 scripts/package_expert.py <expert-dir> <output-dir>
```
注意：`<output-dir>` 必须放在专家目录**外部**，否则 zip 会把自身递归打进去导致体积爆炸。
