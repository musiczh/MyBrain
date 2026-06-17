---
id: entity_feature-list
type: entity
title: Feature list
slug: feature-list
aliases: [功能清单, feature_list.json]
created_at: "2026-06-17T21:40:16+08:00"
updated_at: "2026-06-17T21:40:16+08:00"
sources: [src_20260617_ehuczv]
related: [summary_src_20260617_ehuczv, entity_initializer-agent, entity_coding-agent]
---

# Feature list

Feature list 是长任务 Agent harness 的结构化任务账本。`src_20260617_ehuczv` 描述的做法是：初始化阶段把用户目标展开为大量端到端功能验收项，初始状态都标记为 failing；后续编码 Agent 只允许在验证后更新 `passes` 状态。

文章倾向使用 JSON 承载 feature list，因为结构化格式更能约束模型，降低随意删除、改写或弱化验收项的风险。

<!-- kb:related:start -->
## 关联
- [[Summary for src_20260617_ehuczv]]
- [[Initializer Agent]]
- [[Coding Agent]]
<!-- kb:related:end -->
