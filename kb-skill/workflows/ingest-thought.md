# 新增想法工作流

目标：把用户的短想法、灵感、工作感悟或零散笔记完整写入原料层，再整理进已有知识体系。

## 步骤

1. 提炼关键词并搜索已有编译层：

   ```bash
   kb search "<关键词>" --layer wiki --json
   ```

2. 写入原料层：

   ```bash
   kb ingest --type thought --text "<用户原文>" --context "<可选上下文>" --json
   ```

   必须传入用户原始完整文本，不要只存整理后的观点。

3. 获取编译上下文：

   ```bash
   kb plan <raw_id> --json
   ```

4. 你用 LLM 提炼：

   - 1-3 句核心观点。
   - 相关实体或主题。
   - 这条想法对已有页面是补充、反例、问题还是新主题。

5. 优先追加到已有实体/主题；确实没有承载页时再新建：

   ```bash
   kb entity upsert "<实体标题>" --body-file entity.md --source <raw_id> --json
   kb topic upsert "<主题标题>" --body-file topic.md --source <raw_id> --json
   ```

6. 建立少量强关联：

   ```bash
   kb link <page_id_a> <page_id_b> --json
   ```

7. 记录编译状态：

   ```bash
   kb compiled <raw_id> --tag "<标签>" --json
   ```

## 判断标准

- 想法不需要总是生成摘要页；只有信息量足够或用户明确要求时再写 `kb summary`。
- 对尚未成熟的观点，可归入主题页的“未决问题/观察”小节。
- 避免把每条短想法都膨胀成独立实体。
- 原料页必须能通过 `kb get-raw <raw_id>` 读回用户原始完整文本；不要修改 `raw/*` 文件。
