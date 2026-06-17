# 查询工作流

目标：从编译层优先查询知识，必要时回溯原料层，并由 Agent 生成回答。

## 步骤

1. 先读索引或搜索编译层：

   ```bash
   kb index
   kb search "<用户问题关键词>" --layer wiki --json
   ```

2. 根据命中读取相关 Wiki 页：

   ```bash
   kb get <page_id> --json
   ```

3. 如果 Wiki 页的结构化知识不足，再回溯原料：

   ```bash
   kb get-raw <raw_id> --json
   ```

4. 你用 LLM 综合回答用户，并明确区分：

   - 已编译结论。
   - 原料中的细节。
   - 你的推断。

5. 如果回答本身有长期价值，询问用户是否归档；用户同意后用 `kb topic upsert` 回流为主题页。

## 原则

- 默认不直接全量扫描 `raw/`。
- 搜索结果不足时换关键词，不要立刻读取所有原料。
- 回答需要可追溯时引用 page id 或 raw id。
