---
id: topic_agent-长任务工程化
type: topic
title: Agent 长任务工程化
slug: agent-长任务工程化
aliases: []
created_at: "2026-06-17T21:40:31+08:00"
updated_at: "2026-06-17T21:41:06+08:00"
sources: [src_20260617_ehuczv]
related: [summary_src_20260617_ehuczv, entity_long-running-agents, entity_initializer-agent, entity_coding-agent, entity_feature-list, topic_跨会话交接协议, topic_ai-编码-agent-验证, entity_claude-agent-sdk]
---

# Agent 长任务工程化

Agent 长任务工程化关注如何让 AI Agent 在多次会话、多个上下文窗口之间稳定推进复杂目标。`src_20260617_ehuczv` 提供的核心模式是：不要把长期能力押在模型记忆或上下文压缩上，而要把任务拆解、环境启动、进度记录、版本历史和验收测试固化为外部 harness。

可复用原则：

- 先由初始化流程建立完整任务账本和运行脚本。
- 后续执行者每次只推进一个明确功能。
- 开始新工作前先验证系统基础状态。
- 完成后留下可接班、可回滚、可审计的工作区。

这类工程化约束适合 Codex、Claude Code 等长任务编码代理，也可能泛化到科研、金融建模等长周期 agentic 工作。

<!-- kb:related:start -->
## 关联
- [[Summary for src_20260617_ehuczv]]
- [[Long-running agents]]
- [[Initializer Agent]]
- [[Coding Agent]]
- [[Feature list]]
- [[跨会话交接协议]]
- [[AI 编码 Agent 验证]]
- [[Claude Agent SDK]]
<!-- kb:related:end -->
