# 新增文章工作流

目标：把一篇外部 Agent 已清洗好的文章纯文本写入原料层，并由 Agent 编译为摘要、实体、主题和关联。

## 步骤

1. 先查已有知识：

   ```bash
   kb search "<文章标题或核心关键词>" --layer wiki --json
   ```

2. 写入原料层：

   ```bash
   kb ingest --type article --text-file article.txt --source-url "<可选来源>" --json
   ```

   如果返回 `duplicated: true`，告知用户该内容已存在，停止本流程。

3. 获取编译上下文：

   ```bash
   kb plan <raw_id> --json
   ```

   读取返回的 `text`、`schema` 和 `related_pages`。

4. 你用 LLM 生成编译结果：

   - 300 字以内结构化摘要。
   - 不超过 10 个关键实体。
   - 0-3 个最相关主题。
   - 强相关页面列表，避免弱相关泛链。

5. 写摘要页：

   ```bash
   kb summary <raw_id> --text-file summary.md --json
   ```

6. 对每个实体先判断是否已有页面。已有则更新或追加新观点；没有则新建：

   ```bash
   kb entity upsert "<实体标题>" --body-file entity.md --source <raw_id> --related <page_id> --json
   ```

7. 对主题页做跨源综合：

   ```bash
   kb topic upsert "<主题标题>" --body-file topic.md --source <raw_id> --related <page_id> --json
   ```

8. 对强相关页面建立双向关系：

   ```bash
   kb link <page_id_a> <page_id_b> --json
   ```

9. 回填原料状态和标签：

   ```bash
   kb compiled <raw_id> --tag "<标签1>" --tag "<标签2>" --json
   ```

10. 向用户汇报本次新建/更新的摘要、实体、主题和主要关联。

## 判断标准

- 不要为只出现一次且无复用价值的名词创建实体页。
- 同一概念存在别名时，优先更新已有实体页并补 `--alias`。
- 主题页应做跨源综合，不要复制摘要页内容。
- 每个正文观点应保留来源 id，便于后续回溯。
