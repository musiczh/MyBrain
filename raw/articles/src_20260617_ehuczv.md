---
id: src_20260617_ehuczv
type: article
title: Effective harnesses for long-running agents
created_at: "2026-06-17T21:39:02+08:00"
ingested_at: "2026-06-17T21:39:02+08:00"
content_hash: "sha256:174a27c4ca8a7c51a6acbe1cc2464eb564a00be1b2d83b68f630f202a02a0885"
status: compiled
compiled_at: "2026-06-17T21:41:11+08:00"
tags: [Agent, 长任务工程化, 跨会话交接, 端到端验证]
source_url: "https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents"
author: Justin Young / Anthropic
---

标题：Effective harnesses for long-running agents
来源：Anthropic Engineering
作者：Justin Young
发布日期：2025-11-26
URL：https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

这篇文章讨论长时间运行的 AI 编码 Agent 如何跨多个上下文窗口持续推进复杂任务。Anthropic 的核心判断是：单纯依赖上下文压缩不够，因为每个新会话都像没有记忆的新工程师接班；如果没有外部、可读、可执行的交接物，Agent 会反复猜测项目状态，或者在半成品基础上继续扩大问题。

文章观察到两个主要失败模式。第一，Agent 往往试图一次性完成过多内容，导致上下文耗尽时留下半实现、未记录的代码。第二，项目已有部分进展后，新的 Agent 会误判任务已经完成。另一个常见问题是，Agent 只做单元测试或 curl 级别验证，就把功能标记为完成，但真实端到端流程并不可用。

Anthropic 的解决方案是把 harness 分成初始化 Agent 和编码 Agent。初始化 Agent 只在第一次会话运行，负责建立未来会话需要的环境：init.sh、进度文件、初始 git 提交，以及一份结构化 feature list。feature list 将用户的高层目标拆成大量端到端功能验收项，初始都标记为 failing。文章倾向使用 JSON 而不是 Markdown，因为模型更不容易随意改写结构；后续编码 Agent 只能改变 passes 字段，不能删除或重写测试要求。

后续编码 Agent 每个会话都按固定启动流程接班：确认工作目录，阅读进度文件和 git 日志，阅读功能清单，启动开发环境，先跑基础端到端冒烟测试，确认应用没有被前序工作破坏，再选择一个最高优先级且未完成的功能。每次只做一个功能，完成后必须让环境回到干净状态：代码有序、没有明显缺陷、记录清楚、可以从主干角度合并。

文章强调端到端测试工具的重要性。对 Web App 来说，显式要求 Agent 像真实用户一样使用浏览器自动化验证，效果明显好于只读代码、跑单测或用 curl 请求。浏览器验证能帮助 Agent 发现代码层面不明显的问题，但仍存在工具和视觉能力限制，例如某些浏览器原生弹窗无法被 Puppeteer MCP 直接观察。

失败模式和对应治理方式可以概括为：过早宣布完成 -> 初始化阶段建立完整功能清单，编码阶段每次只选一个未完成项；留下有 bug 或无文档状态 -> 初始建立 git 和进度日志，每个会话开始读日志并跑基础测试，结束写提交和进度；过早标记功能通过 -> 只有严谨自测后才能更新 passes；浪费时间摸索如何启动项目 -> 初始化阶段提供 init.sh，编码阶段先读并运行它。

这套方法的本质不是让模型“记住”更多，而是把长期任务拆成可接班的工程系统：稳定的任务账本、可复现的启动脚本、可回滚的版本历史、明确的进度日志，以及面向用户行为的验收测试。它适用于 Codex/Claude Code 这类长任务代理：应该把 AGENTS/进度文件/功能清单/验证脚本作为跨会话协议，而不是只依赖聊天上下文。

未来方向包括：是否用单一通用编码 Agent 还是多 Agent 架构更好；测试、QA、代码清理等专用 Agent 是否能进一步提升软件生命周期内的子任务质量；以及这套经验如何从全栈 Web App 泛化到科研、金融建模等其他长期 agentic 任务。
