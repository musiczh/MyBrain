# CLI Reference

所有命令支持人类可读输出；加 `--json` 后返回：

```json
{"ok": true, "data": {}}
```

错误统一返回：

```json
{"ok": false, "error": {"code": "...", "message": "...", "detail": {}}}
```

## 安装与更新

```bash
git clone -b master https://github.com/musiczh/MyBrain.git
cd MyBrain
scripts/install
scripts/update
```

- `scripts/install` 会把 `kb-skill/` 同步到 `${CODEX_HOME:-~/.codex}/skills/knowledge-base`，把 Python 包安装到本仓库 `.venv`，并写入 `~/.local/bin/kb`。
- `scripts/update` 会用 `--ff-only` 拉取 `origin/master` 后重新运行 `scripts/install`；只想从当前代码刷新本地 skill/CLI 时，使用 `scripts/update --skip-pull`。

## 初始化

```bash
kb init "<name>" [--root <path>] [--force] [--json]
```

不传 `--root` 时创建固定本地知识库 `~/.local/share/mybrain/default`。其他命令首次运行时如果该目录尚未初始化，也会自动创建默认知识库。

初始化会创建 `.kb/`、`raw/`、`wiki/`、`schema/`、`dist/`，写默认 schema，构建空索引并提交初始 Git 版本。知识库实例内容不应放在系统源码仓库中。

## 原料层

```bash
kb ingest --type article|thought|note --text "<文本>" [--title "..."] [--source-url "..."] [--source-path "..."] [--author "..."] [--context "..."] [--json]
kb ingest --type article --text-file article.txt [--source-url "..."] [--source-path "..."] --json
kb ingest --type article --text - --json
kb get-raw <raw_id> [--json]
kb compiled <raw_id> --tag "<标签>" [--tag "..."] [--json]
```

`ingest` 返回 `record.id`、`duplicated` 和 `commit`。传入 URL 时，调用方 Agent 必须先读取完整正文，再用 `--source-url` 保留原链接；传入本地文档时，调用方 Agent 必须先读取完整正文，再用 `--source-path` 保留本地路径。原料正文和 frontmatter 创建后不可修改，`compiled` 只写 `.kb/raw-status/<raw_id>.yaml`。

## 编译计划

```bash
kb plan <raw_id> [--limit 8] [--json]
```

返回原料正文、schema 全文和候选相关页面。

## 编译层

```bash
kb summary <raw_id> --text "<摘要>" [--json]
kb summary <raw_id> --text-file summary.md [--json]
kb entity upsert "<title>" --body-file entity.md [--alias "..."] [--source <raw_id>] [--related <page_id>] [--json]
kb topic upsert "<title>" --body-file topic.md [--source <raw_id>] [--related <page_id>] [--json]
kb link <page_id_a> <page_id_b> [--json]
kb get <page_id> [--json]
kb index [--json]
```

`entity/topic upsert` 会维护 frontmatter、正文关联区块、双向 related、`wiki/index.md`、`wiki/log.md` 和 FTS 索引。

## 检索

```bash
kb search "<query>" [--layer wiki|raw] [--type entity|topic|summary|article|thought|note] [--limit 10] [--json]
```

不指定 `--layer` 时先查 wiki，结果不足再补 raw。

## 渲染与维护

```bash
kb render [--open] [--json]
kb lint [--check orphan] [--check broken_link] [--fix] [--json]
kb log [-n 20] [--json]
```

`kb lint --fix` 目前只自动修复 `missing_backlink`。其他问题需要 Agent 读页后判断。
