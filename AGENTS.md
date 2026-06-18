# Agent 项目上下文

本文件给后续接手本仓库的 AI Agent 使用。目标是在开始编码前快速建立项目上下文，减少重新理解成本。

## 协作规则

- 始终使用中文回复。
- 开始处理代码前，先在项目中查找并阅读 `AGENTS.md`、`AGENT.md`、`CLAUDE.md`。若多个文件同时存在，遵循用户当前指令和更靠近修改目录的规则。
- 主干分支按项目协作规则记为 `rc/develop`；但本仓库的安装和更新文档面向 GitHub `master` 发布分支，修改发布链路前先确认用户目标。
- 新增文件后必须执行 `git add` 加入暂存区。
- 不需要为需求额外新增测试代码；但应运行与改动风险匹配的现有验证命令。
- 所有结论必须基于代码事实。修 bug 时先定位根因，避免只修表象。
- 修改前先分析现有链路，优先复用现有模块和风格，避免扩大范围。
- 编码完成后必须审查本地 diff，检查是否符合需求、是否有重复代码、是否可以收敛。
- 如果移除了某个方法的调用，且该方法不再被调用，应删除该方法。
- 构建规则：编码结束后，除非用户明确要求运行，否则先询问是否执行打包。唯一允许的打包命令是 `/bin/bash /Users/bytedance/project_space_a/cc/remotex build`；看到“安装完成”视为成功。

## 项目定位

本仓库是一个本地“第二大脑”知识库系统，提供 `knowledge-base` Codex skill 和 `kb` CLI。调用方 Agent 负责读取外部内容和 LLM 推理；本项目只负责确定性的本地文件、索引、渲染、Git 和 lint 操作。

明确边界：

- 不内置 LLM。
- 不抓网页、不解析公众号、不直接接微信或飞书消息。
- 只处理调用方 Agent 传入的纯文本。
- URL、本地文档、飞书文档等外部内容必须先由 Agent 读取成完整正文，再传给 `kb ingest`。
- 原料层保存完整原始文本，写入后 raw 文件只读，不回填正文或 frontmatter。
- Markdown + Git 是真相源；SQLite FTS5 索引和 `dist/` 静态站点是可重建派生产物。

## 仓库结构

- `README.md`：用户视角说明、安装、更新、核心链路。
- `pyproject.toml`：Python 包配置，要求 Python `>=3.11`，console script 为 `kb = "kb_cli.cli:app"`。
- `kb_cli/cli.py`：CLI 入口。Typer 可用时暴露 Typer app，否则保留 argparse fallback；两套入口共用 `_handle_*` 处理函数。
- `kb_core/project.py`：知识库根目录解析、初始化目录、默认 schema、`.gitignore` 合并。
- `kb_core/services.py`：面向 CLI 的业务编排层，包含 ingest、plan、summary、upsert、link、compiled。
- `kb_core/raw_store.py`：原料层读写、去重、编译状态读取。`mark_compiled` 写 `.kb/raw-status/<raw_id>.yaml`，不改 raw 文件。
- `kb_core/wiki_store.py`：编译层页面 upsert、双向 related、backlink、`wiki/index.md`、`wiki/log.md`。
- `kb_core/index_engine.py`：SQLite FTS5 索引，优先使用 `jieba` 分词，缺失时走内置正则分词。
- `kb_core/renderer.py`：把 Wiki 和 raw 渲染到 `dist/` 静态 HTML。
- `kb_core/maintainer.py`：lint 检查；`--fix` 当前只自动修复 `missing_backlink`。
- `kb_core/git_repo.py`：知识库实例内的 Git 初始化、add、commit、log。
- `kb-skill/SKILL.md`：Codex skill 主说明，告诉 Agent 何时使用知识库以及如何处理 URL、本地文档和普通文本。
- `kb-skill/workflows/`：新增文章、想法、查询、维护工作流。
- `kb-skill/references/cli-reference.md`：CLI 命令和 JSON 契约。
- `scripts/install`：从当前 checkout 安装/刷新本机 skill、`.venv` 和 `~/.local/bin/kb` wrapper。
- `scripts/update`：默认从 `origin/master` fast-forward 后重新执行 install；开发态可用 `--skip-pull`。
- `scripts/kb`：仓库内 CLI wrapper，自动使用 `.venv/bin/python`。

## 运行时知识库位置

源码仓库不应该包含知识库实例内容。不要在仓库根目录创建或提交这些目录：

```text
.kb/
raw/
wiki/
schema/
dist/
```

默认运行时知识库固定在：

```text
~/.local/share/mybrain/default
```

`Project.resolve()` 不再从当前工作目录向上查找知识库；它只使用 `KB_ROOT` 显式覆盖，或使用上述默认目录。首次运行需要知识库的命令时，如果默认目录未初始化，会自动执行默认初始化。

## 数据模型

Raw 类型定义在 `kb_core/models.py`：

- `article` -> `raw/articles/`，id 前缀 `src_`。
- `thought` -> `raw/thoughts/`，id 前缀 `thought_`。
- `note` -> `raw/notes/`，id 前缀 `note_`。

Wiki 类型定义在 `kb_core/models.py`：

- `summary` -> `wiki/summaries/<raw_id>.md`，id 为 `summary_<raw_id>`。
- `entity` -> `wiki/entities/<slug>.md`，id 为 `entity_<slug>`。
- `topic` -> `wiki/topics/<slug>.md`，id 为 `topic_<slug>`。

Schema 位于运行时知识库的 `schema/`：

- `categories.md`
- `workflows.md`
- `conventions.md`

派生产物：

- `.kb/index.sqlite`：SQLite FTS5 索引，可通过 `IndexEngine.build()` 重建。
- `.kb/raw-status/<raw_id>.yaml`：原料编译状态。
- `dist/`：静态站点，可通过 `kb render` 重建。
- Git 历史：每次 ingest/compile/link/render 相关写操作按服务层逻辑提交。

## 核心链路

新增原料：

1. Agent 读取 URL 或本地文档的完整正文；普通文本则保持用户原文。
2. Agent 调 `kb ingest --type article|thought|note`，必要时带 `--source-url` 或 `--source-path`。
3. `Normalizer.build()` 只校验类型和非空，并保留输入文本原样。
4. `RawStore.add()` 计算 `content_hash`，用索引和文件扫描去重，写 raw Markdown 并更新 FTS。
5. `GitRepo.commit()` 提交 ingest 变更。

编译原料：

1. Agent 调 `kb plan <raw_id>`。
2. `build_plan()` 返回 raw 完整正文、schema 全文和候选相关 Wiki 页。
3. Agent 用 LLM 生成摘要、实体、主题、关联判断。
4. Agent 通过 `kb summary`、`kb entity upsert`、`kb topic upsert`、`kb link` 写入编译层。
5. `WikiStore.upsert()` 维护 frontmatter、related 区块、双向 backlink、`wiki/index.md`、`wiki/log.md` 和 FTS。
6. Agent 调 `kb compiled <raw_id>`；该命令只写 `.kb/raw-status`，不会修改 raw 文件。

查询知识：

1. Agent 优先使用 `kb index` 或 `kb search --layer wiki`。
2. 根据命中调用 `kb get <page_id>` 读取编译层页面。
3. Wiki 信息不足或需要核验原文时，再调用 `kb get-raw <raw_id>`。
4. Agent 输出时应区分已编译结论、原料细节和自己的推断。
5. 若回答有长期价值，先征得用户同意，再用 `kb topic upsert` 或 `kb entity upsert` 回流。

## CLI 接口速览

- `kb init "<name>" [--root <path>] [--force] [--json]`：初始化知识库。无 `--root` 时使用固定默认目录。
- `kb ingest`：写入完整纯文本到原料层。支持 `--text`、`--text-file`、`--text -`、`--source-url`、`--source-path`。
- `kb plan <raw_id>`：返回 raw、schema、候选相关页面，供 Agent 编译。
- `kb summary <raw_id>`：写摘要页。
- `kb entity upsert "<title>"`：写实体页，合并 aliases/sources/related。
- `kb topic upsert "<title>"`：写主题页，合并 sources/related。
- `kb link <page_id_a> <page_id_b>`：建立双向 related。
- `kb compiled <raw_id>`：记录编译状态到 `.kb/raw-status`。
- `kb search "<query>"`：FTS 检索；未指定 layer 时先查 wiki，结果不足再补 raw。
- `kb get <page_id>`：读取编译层页面。
- `kb get-raw <raw_id>`：读取原料层完整正文。
- `kb index`：输出 `wiki/index.md`。
- `kb render [--open]`：渲染静态 Wiki。
- `kb lint [--check ...] [--fix]`：健康检查；`--fix` 仅修复 missing backlink。
- `kb log [-n 20]`：读取知识库实例的 Git 历史。

## 安装与更新链路

用户安装：

```bash
git clone -b master https://github.com/musiczh/MyBrain.git
cd MyBrain
scripts/install
```

`scripts/install` 做三件事：

- 创建或更新本仓库 `.venv` 并 `pip install -e <repo>`。
- 把 `kb-skill/` 同步到 `${CODEX_HOME:-~/.codex}/skills/knowledge-base`。
- 写入 `${HOME}/.local/bin/kb` wrapper，指向当前仓库和当前 `.venv` Python。

用户更新：

```bash
cd MyBrain
scripts/update
```

`scripts/update` 默认要求当前 branch 等于 `master` 且工作区干净，然后执行 `git pull --ff-only origin master`，再调用 `scripts/install`。本地开发态只想刷新 skill/CLI 时用：

```bash
scripts/update --skip-pull
```

## 开发前检查

建议开始任何代码改动前执行：

```bash
git status --short --branch
rg --files -g 'AGENTS.md' -g 'AGENT.md' -g 'CLAUDE.md'
```

读代码优先入口：

```text
README.md
kb-skill/SKILL.md
kb-skill/references/cli-reference.md
kb_cli/cli.py
kb_core/services.py
kb_core/project.py
kb_core/raw_store.py
kb_core/wiki_store.py
kb_core/index_engine.py
```

如果改 skill 工作流，还要读对应文件：

```text
kb-skill/workflows/ingest-article.md
kb-skill/workflows/ingest-thought.md
kb-skill/workflows/opportunistic-capture.md
kb-skill/workflows/query.md
kb-skill/workflows/maintain.md
```

## 验证命令

按改动范围选择，不要无意义扩大验证：

```bash
bash -n scripts/install scripts/update scripts/kb
python3 -m compileall kb_core kb_cli
scripts/kb --help
scripts/kb ingest --help
scripts/kb search --help
```

如果改了 skill 内容，使用系统 skill 校验脚本：

```bash
/private/tmp/kb-skill-validate-venv/bin/python /Users/bytedance/.codex/skills/.system/skill-creator/scripts/quick_validate.py kb-skill
```

如果改了安装更新脚本，建议用临时目录验证，避免污染真实安装：

```bash
scripts/install --skip-deps --skill-dir /private/tmp/mybrain-install-check/skills/knowledge-base --bin-dir /private/tmp/mybrain-install-check/bin
/private/tmp/mybrain-install-check/bin/kb --help
scripts/update --skip-pull --skip-deps --skill-dir /private/tmp/mybrain-update-check/skills/knowledge-base --bin-dir /private/tmp/mybrain-update-check/bin
```

完成后检查：

```bash
git diff --check
git diff --cached --check
git status --short --branch
```

## 常见坑

- 不要把运行时知识库实例写入源码仓库。`.kb/`、`raw/`、`wiki/`、`schema/`、`dist/` 属于用户本地知识库目录。
- 不要让 CLI 直接抓 URL 或解析文档。读取外部内容是 Agent 的职责，CLI 只接收完整纯文本。
- 不要修改 raw 文件来记录编译状态。状态只能通过 `kb compiled` 写 `.kb/raw-status/<raw_id>.yaml`。
- 不要在查询时默认全量扫描 raw。优先 `wiki`，不足时再回溯原料。
- Typer 和 argparse 入口共存。新增 CLI 命令时要复用同一个 `_handle_*` 函数，并同时补齐 argparse 和 Typer wrapper。
- 写页面时通过 `WikiStore`，不要绕过它直接改 `wiki/`，否则会漏掉 FTS、index、log、backlink。
- 改安装脚本时注意它们通过自身路径解析仓库根目录，不应硬编码本机路径。
- 修改 `kb-skill/` 后，如果要让本机 Codex 立即生效，需要运行 `scripts/update --skip-pull` 或 `scripts/install` 同步到 `~/.codex/skills/knowledge-base`。

## 提交信息建议

需求完成后生成中文 Conventional Commits message，风格参考当前历史。提交正文说明本次改动的具体行为变化、涉及模块和验证结果。

示例：

```text
feat: 优化知识库 skill 的参考回答策略

更新 skill 触发描述和查询工作流，让 Agent 在回答问题时把本地知识库作为个人上下文参考，并在普通聊天中先确认再沉淀高价值信息。
```
