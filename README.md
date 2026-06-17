# Knowledge Base

这是一个本地「第二大脑」能力提供方：调用方 Agent 负责读取外部内容和 LLM 推理，本项目只提供确定性的 Skill + CLI 原语。

## 定位

- 不内置 LLM。
- 不抓网页、不解析公众号、不接飞书/微信。
- 只处理调用方传入的纯文本。
- 真相源是 Markdown + Git，SQLite FTS5 索引和静态站点都是可重建派生数据。

## 快速开始

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

```text
.kb/                 # 配置与派生索引
raw/                 # 原料层，immutable，只追加与回填元数据
wiki/                # 编译层，实体/主题/摘要/索引/日志
schema/              # 规则层，供 Agent 编译时读取
dist/                # 静态 Wiki 渲染产物
kb-skill/            # 交付给外部 Agent 的工作流说明书
```

## 核心链路

1. 外部 Agent 把文章、飞书、微信等来源清洗为纯文本。
2. `kb ingest` 写入原料层并建立索引。
3. `kb plan` 聚合原文、schema 和候选相关页面。
4. Agent 用 LLM 生成摘要、识别实体、判断关联。
5. Agent 调 `kb summary`、`kb entity upsert`、`kb topic upsert`、`kb link` 写入编译层。
6. `kb compiled` 回填原料状态并提交 Git 版本。
