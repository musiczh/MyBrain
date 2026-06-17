# 维护工作流

目标：用确定性 lint 找出知识库结构问题，由 Agent 决策是否修复。

## 步骤

1. 扫描问题：

   ```bash
   kb lint --json
   ```

2. 对 `missing_backlink` 可直接自动修：

   ```bash
   kb lint --fix --json
   ```

3. 对其他问题先读相关页面：

   ```bash
   kb get <page_id> --json
   ```

4. 你判断修复策略：

   - `orphan`：补关联或归档。
   - `broken_link`：创建目标页、改链接或移除错误关联。
   - `duplicate_concept`：合并页面或把一个概念作为 alias。
   - `stale`：根据来源更新页面或标注旧结论。

5. 每次修复后重新运行：

   ```bash
   kb lint --json
   ```

## 原则

- 除 `missing_backlink` 外，不要自动替用户做语义合并。
- 归档前确认页面没有仍有价值的入口。
- 修复后向用户说明保留、合并、归档的原因。
