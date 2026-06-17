---
id: entity_coding-agent
type: entity
title: Coding Agent
slug: coding-agent
aliases: [编码 Agent]
created_at: "2026-06-17T21:40:08+08:00"
updated_at: "2026-06-17T21:40:39+08:00"
sources: [src_20260617_ehuczv]
related: [summary_src_20260617_ehuczv, entity_long-running-agents, entity_initializer-agent, entity_feature-list, topic_agent-长任务工程化, topic_跨会话交接协议]
---

# Coding Agent

Coding Agent 是初始化完成后反复接力的执行角色。`src_20260617_ehuczv` 中的推荐流程是：每个新会话先确认目录、阅读进度文件和 git 日志、阅读 feature list、运行开发环境和基础端到端测试，再选择一个最高优先级的未完成功能推进。

它的关键约束是一次只做一个功能，并在结束时留下干净状态：代码可合并、验证过、进度记录清楚，便于下一个会话接班。

<!-- kb:related:start -->
## 关联
- [[Summary for src_20260617_ehuczv]]
- [[Long-running agents]]
- [[Initializer Agent]]
- [[Feature list]]
- [[Agent 长任务工程化]]
- [[跨会话交接协议]]
<!-- kb:related:end -->
