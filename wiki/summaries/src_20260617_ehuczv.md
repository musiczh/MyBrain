---
id: summary_src_20260617_ehuczv
type: summary
title: Summary for src_20260617_ehuczv
slug: src_20260617_ehuczv
aliases: []
created_at: "2026-06-17T21:39:25+08:00"
updated_at: "2026-06-17T21:40:16+08:00"
sources: [src_20260617_ehuczv]
related: [entity_long-running-agents, entity_initializer-agent, entity_coding-agent, entity_feature-list]
---

# Summary for src_20260617_ehuczv

Anthropic 认为长时间运行的编码 Agent 不能只靠上下文压缩续航，必须依赖外部 harness：初始化 Agent 先建立 feature list、init.sh、进度日志和 git 基线；后续编码 Agent 每次接班先读日志和功能清单、跑基础端到端验证，再只推进一个未完成功能。核心启发是把长期任务变成可接班、可验证、可回滚的工程系统，而不是依赖聊天记忆。来源：src_20260617_ehuczv。

<!-- kb:related:start -->
## 关联
- [[Long-running agents]]
- [[Initializer Agent]]
- [[Coding Agent]]
- [[Feature list]]
<!-- kb:related:end -->
