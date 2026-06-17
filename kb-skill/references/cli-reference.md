# CLI Reference

所有命令支持人类可读输出；加 `--json` 后返回：

```json
{"ok": true, "data": {}}
```

错误统一返回：

```json
{"ok": false, "error": {"code": "...", "message": "...", "detail": {}}}
```

## 初始化

```bash
kb init "<name>" [--root .] [--force] [--json]
```

创建 `.kb/`、`raw/`、`wiki/`、`schema/`、`dist/`，写默认 schema，构建空索引并提交初始 Git 版本。

## 原料层

```bash
kb ingest --type article|thought|note --text "<文本>" [--title "..."] [--source-url "..."] [--author "..."] [--context "..."] [--json]
kb ingest --type article --text-file article.txt --json
kb ingest --type article --text - --json
kb get-raw <raw_id> [--json]
kb compiled <raw_id> --tag "<标签>" [--tag "..."] [--json]
```

`ingest` 返回 `record.id`、`duplicated` 和 `commit`。原料正文不可修改，`compiled` 只回填 metadata。

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
