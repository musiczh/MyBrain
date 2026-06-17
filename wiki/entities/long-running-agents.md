---
id: entity_long-running-agents
type: entity
title: Long-running agents
slug: long-running-agents
aliases: [长时间运行 Agent, 长任务 Agent]
created_at: "2026-06-17T21:39:52+08:00"
updated_at: "2026-06-17T21:40:31+08:00"
sources: [src_20260617_ehuczv]
related: [summary_src_20260617_ehuczv, entity_initializer-agent, entity_coding-agent, entity_claude-agent-sdk, topic_agent-长任务工程化]
---

# Long-running agents

Long-running agents 指需要跨多个上下文窗口或多次会话持续推进复杂目标的 AI Agent。`src_20260617_ehuczv` 的关键判断是：这类任务的主要瓶颈不是单次上下文压缩，而是新会话缺少可靠外部记忆和接班协议。

有效治理方向是把任务状态外化为可读、可验证、可回滚的工程制品：功能清单、启动脚本、进度日志、git 历史和端到端验收。

<!-- kb:related:start -->
## 关联
- [[Summary for src_20260617_ehuczv]]
- [[Initializer Agent]]
- [[Coding Agent]]
- [[Claude Agent SDK]]
- [[Agent 长任务工程化]]
<!-- kb:related:end -->
