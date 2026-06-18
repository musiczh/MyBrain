---
name: knowledge-base
description: Use to reference, query, organize, compile, or maintain the user's local second-brain knowledge base. Trigger when the user mentions 知识库, 第二大脑, 我之前记过什么, 根据我的知识库回答, 参考已有积累, 个人经验, 回答问题需要个人上下文, remembering/collecting content, or when a conversation contains valuable thoughts, insights, preferences, decisions, or reusable lessons that should be offered for capture.
---

# Knowledge Base Skill

本 skill 让 Agent 在回答问题时参考用户本地个人知识积累，并把值得长期保存的内容编译进本地知识库。知识库是用户已有积累的参考层，不是唯一数据来源；你需要结合当前对话、通用知识、必要的外部信息和知识库命中内容回答。知识库系统本身不具备 LLM 能力；你作为调用方 Agent 负责阅读、摘要、实体判断和综合回答，`kb` CLI 只负责确定性文件、索引、渲染、Git 与 lint 操作。

## 何时使用

- 用户明确说“知识库”“第二大脑”“根据我的知识库回答”“查一下我之前记过什么”。
- 用户提出可能受个人积累、偏好、经验、历史决策影响的问题，适合轻量参考知识库后再回答。
- 用户说“记一下”“收藏这段”“整理进知识库”“做成第二大脑”。
- 用户在聊天中表达了长期偏好、方法论、感悟、明确决策、复用经验或反复出现的想法，适合主动建议入库。
- 用户询问“我之前记的某个主题/实体是什么”。
- 用户要求生成或浏览本地 Wiki。
- 用户要求检查知识库健康度、断链、孤立页或重复概念。

## 使用原则

- 知识库是参考，不是唯一依据。回答问题时不要只从知识库已有内容作答；命中知识库时，把它作为用户个人上下文融入答案。
- 知识库未命中时，正常基于当前对话和可用知识回答，不要声称“知识库中有相关结论”。
- 明确区分知识库已有结论、当前对话信息、外部资料和你的推断。
- 普通聊天中的主动入库必须先询问用户确认；用户同意后再调用 `kb ingest` 和后续编译命令。
- 不要把敏感信息、临时情绪、未明确的私密内容或低价值闲聊自动入库。

## 前置约束

- CLI 入口是 `kb`。标准安装方式：`git clone -b master https://github.com/musiczh/MyBrain.git && cd MyBrain && scripts/install`；后续更新本地 skill/CLI：在该仓库 `master` 分支运行 `scripts/update`。
- 如果当前环境找不到 `kb`，先确认 `~/.local/bin` 在 PATH 中；也可以在仓库内直接使用 `scripts/kb`。
- 默认知识库实例固定在 `~/.local/share/mybrain/default`；首次使用 `kb ingest/search/plan/...` 且该目录尚未初始化时，系统会自动初始化。
- 不要在当前代码仓库根目录创建 `.kb/`、`raw/`、`wiki/`、`schema/` 或 `dist/` 作为知识库实例内容。
- 不要让本系统抓网页、读公众号、读飞书或接微信。你需要先自行把外部内容读取并清洗为纯文本。
- 如果用户传入 URL，先由你读取该链接对应的完整正文，再用 `kb ingest --type article --text-file ... --source-url "<原链接>"` 把完整原文写入 raw；raw 页面必须保留原链接。
- 如果用户传入本地文档，先由你读取该文件的完整正文，再用 `kb ingest --type article --text-file ... --source-path "<本地路径>"` 把完整原文写入 raw。
- 如果用户传入普通文本，直接把用户原文完整传给 `kb ingest --type thought|note --text ...` 或 `--text-file`。
- 写入前先用 `kb search` 或 `kb index` 了解已有知识，避免重复建页。
- 原料层 immutable：`raw/*` 创建后只读，不改正文也不回填 metadata；`kb compiled` 只写独立状态文件。
- 编译层由你用 LLM 维护，但每次写入都必须通过 CLI。
- 查询时优先读编译层；只有细节不足时才回溯原料层。

## 决策路由

- 显式知识库查询、根据已有积累回答、普通问题需要个人上下文：读 `workflows/query.md`。
- 聊天中发现可长期沉淀的想法、偏好、决策、经验：读 `workflows/opportunistic-capture.md`。
- 新增文章或较长资料：读 `workflows/ingest-article.md`。
- 新增想法、灵感、短笔记：读 `workflows/ingest-thought.md`。
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
