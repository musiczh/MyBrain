---
id: entity_initializer-agent
type: entity
title: Initializer Agent
slug: initializer-agent
aliases: [初始化 Agent]
created_at: "2026-06-17T21:40:01+08:00"
updated_at: "2026-06-17T21:40:16+08:00"
sources: [src_20260617_ehuczv]
related: [summary_src_20260617_ehuczv, entity_long-running-agents, entity_coding-agent, entity_feature-list]
---

# Initializer Agent

Initializer Agent 是长任务 harness 中只在第一次会话运行的专门角色。根据 `src_20260617_ehuczv`，它负责为后续 Agent 建立环境和接班材料，包括 `init.sh`、进度文件、初始 git 基线，以及结构化的 feature list。

它的价值是把用户的高层目标预先展开为可执行、可检查的任务账本，降低后续会话误判完成度或重新摸索项目状态的概率。

<!-- kb:related:start -->
## 关联
- [[Summary for src_20260617_ehuczv]]
- [[Long-running agents]]
- [[Coding Agent]]
- [[Feature list]]
<!-- kb:related:end -->
