# Knowledge Base

这是一个本地「第二大脑」能力提供方：调用方 Agent 负责读取外部内容和 LLM 推理，本项目只提供确定性的 Skill + CLI 原语。

## 定位

- 不内置 LLM。
- 不抓网页、不解析公众号、不接飞书/微信。
- 只处理调用方传入的纯文本。
- 原料层保存调用方传入的完整原始文本；写入后 raw 文件只读，不再修改。
- 真相源是 Markdown + Git，SQLite FTS5 索引和静态站点都是可重建派生数据。

## 快速开始

知识库实例默认固定在 `~/.local/share/mybrain/default`。首次运行任意需要知识库的命令时，如果该目录尚未初始化，系统会自动创建。

```bash
kb init "My Brain"
kb ingest --type thought --text "Karpathy 的 LLM Wiki 思路适合做第二大脑。" --json
kb search "LLM Wiki" --json
```

Codex 本地接入时，如果没有通过 pip 安装入口，可以把项目 wrapper 放到 PATH 中：

```bash
cp scripts/kb ~/.local/bin/kb
```

长文本可以通过 stdin 或文件传入：

```bash
kb ingest --type article --text-file article.txt
cat article.txt | kb ingest --type article --text -
```

## 目录结构

下面是知识库实例目录结构，不应放在本系统源码仓库中：

```text
.kb/                 # 配置、索引和原料编译状态
raw/                 # 原料层，immutable，保存完整原始文本
wiki/                # 编译层，实体/主题/摘要/索引/日志
schema/              # 规则层，供 Agent 编译时读取
dist/                # 静态 Wiki 渲染产物
```

本系统仓库只保留 `kb_core/`、`kb_cli/`、`kb-skill/`、`scripts/` 等系统源码与 Skill 交付物。

## 核心链路

1. 外部 Agent 把文章、飞书、微信等来源清洗为纯文本。
2. `kb ingest` 写入原料层并建立索引。
3. `kb plan` 聚合原文、schema 和候选相关页面。
4. Agent 用 LLM 生成摘要、识别实体、判断关联。
5. Agent 调 `kb summary`、`kb entity upsert`、`kb topic upsert`、`kb link` 写入编译层。
6. `kb compiled` 在独立状态文件中记录编译状态，原料文件保持只读。
