---
id: topic_ai-编码-agent-验证
type: topic
title: AI 编码 Agent 验证
slug: ai-编码-agent-验证
aliases: []
created_at: "2026-06-17T21:40:47+08:00"
updated_at: "2026-06-17T21:40:47+08:00"
sources: [src_20260617_ehuczv]
related: [summary_src_20260617_ehuczv, entity_coding-agent, entity_feature-list]
---

# AI 编码 Agent 验证

AI 编码 Agent 验证关注 Agent 如何证明功能真的可用，而不只是代码看起来合理。`src_20260617_ehuczv` 的经验是，缺少显式要求时，Agent 容易用单元测试或 curl 请求替代真实用户路径，并过早把功能标记为完成。

更可靠的策略是把端到端验证放进 harness：编码 Agent 在开始新功能前先跑基础冒烟测试，完成后用浏览器自动化按用户行为验证对应 feature list 项，只有验证通过后才能更新 passes 状态。

这个主题后续可继续沉淀 Playwright、Puppeteer MCP、视觉检查和人类验收路径相关经验。

<!-- kb:related:start -->
## 关联
- [[Summary for src_20260617_ehuczv]]
- [[Coding Agent]]
- [[Feature list]]
<!-- kb:related:end -->
