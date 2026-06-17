---
name: knowledge-base
description: Use when the user wants to remember, organize, compile, query, or maintain knowledge in the local second-brain knowledge base.
---

# Knowledge Base Skill

本 skill 让 Agent 把任意**已经读取为纯文本**的内容编译进本地个人知识库。知识库系统本身不具备 LLM 能力；你作为调用方 Agent 负责阅读、摘要、实体判断和综合回答，`kb` CLI 只负责确定性文件、索引、渲染、Git 与 lint 操作。

## 何时使用

- 用户说“记一下”“收藏这段”“整理进知识库”“做成第二大脑”。
- 用户询问“我之前记的某个主题/实体是什么”。
- 用户要求生成或浏览本地 Wiki。
- 用户要求检查知识库健康度、断链、孤立页或重复概念。

## 前置约束

- CLI 入口是 `kb`。如果当前环境找不到 `kb`，在本机可使用 `/Users/bytedance/MyProject/MyBrain/scripts/kb`，或把该 wrapper 复制到 `~/.local/bin/kb`。
- 不要让本系统抓网页、读公众号、读飞书或接微信。你需要先自行把外部内容读取并清洗为纯文本。
- 写入前先用 `kb search` 或 `kb index` 了解已有知识，避免重复建页。
- 原料层 immutable：不要改写 `raw/*` 正文，只能用 `kb compiled` 回填状态和标签。
- 编译层由你用 LLM 维护，但每次写入都必须通过 CLI。
- 查询时优先读编译层；只有细节不足时才回溯原料层。

## 决策路由

- 新增文章或较长资料：读 `workflows/ingest-article.md`。
- 新增想法、灵感、短笔记：读 `workflows/ingest-thought.md`。
- 查询已有知识：读 `workflows/query.md`。
- 维护知识库：读 `workflows/maintain.md`。
- 需要命令字段与 JSON 契约：读 `references/cli-reference.md`。

## 常用命令

```bash
kb init "My Brain"
kb ingest --type article --text-file article.txt --json
kb plan <raw_id> --json
kb summary <raw_id> --text "摘要正文" --json
kb entity upsert "RAG" --body-file entity.md --source <raw_id> --json
kb topic upsert "知识管理" --body-file topic.md --source <raw_id> --json
kb link entity_rag topic_知识管理 --json
kb compiled <raw_id> --tag RAG --tag 知识管理 --json
kb search "RAG 噪音" --json
kb render --json
kb lint --json
```
