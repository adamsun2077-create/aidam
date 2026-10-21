---
name: aidam-core
description: Aidam 工作区规则、上下文导航、会话协作与工具入口。
---

# Aidam Core

执行规则唯一源为 `system/AIDAM.md`，不重复维护角色和流程。

直接根据目标、交付物和风险选择必要专用技能。工具导航：

- 本地检查：`python3 system/tools/aidam.py doctor .`
- 近期摘要：`python3 system/tools/aidam.py context recent .`
- 项目定位：`python3 system/tools/aidam.py context assemble . --task "关键词"`
- 路径声明与独立日志：`python3 system/tools/aidam.py session start/finish .`，参数见帮助。

摘要和关键词结果只作导航，相关原文仍需回读。工具不可用或未做验证时如实说明。
