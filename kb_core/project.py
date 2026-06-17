from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .errors import KbNotFoundError, ValidationError
from .models import dump_yaml, load_yaml


DEFAULT_CATEGORIES = """# 分类规则

- 技术概念：编程语言、框架、工具、架构模式。
- 工作方法：研发流程、协作经验、效率实践。
- 个人洞察：灵感、观点、反思。

Agent 可以按用户偏好持续补充本文件，但应保持规则可读、可执行。
"""

DEFAULT_WORKFLOWS = """# 编译工作流

## 新文章入库
1. 读取原料和候选相关页面。
2. 生成 300 字以内结构化摘要。
3. 提取不超过 10 个关键实体。
4. 已有实体页则增量补充，不存在则新建。
5. 判断归入已有或新建主题页。
6. 建立强相关双链并回填原料状态。

## 新想法入库
1. 提炼 1-3 句核心观点。
2. 搜索已有实体和主题。
3. 追加到最相关页面或新建主题。
4. 建立关联并记录编译日志。
"""

DEFAULT_CONVENTIONS = """# 命名约定

- 实体页标题使用常见中文名或英文原名。
- alias 记录同义词、缩写和中英文别名。
- 正文引用原料时使用脚注或明确 source id。
- 避免为一次性细节创建实体页，优先归入主题页。
"""


class Project:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self._config: dict[str, Any] | None = None

    @classmethod
    def resolve(cls, start: Path | None = None) -> "Project":
        env_root = os.environ.get("KB_ROOT")
        if env_root:
            root = Path(env_root).expanduser().resolve()
            if (root / ".kb").is_dir():
                return cls(root)
            raise KbNotFoundError("KB_ROOT does not point to an initialized knowledge base", root=str(root))
        current = (start or Path.cwd()).resolve()
        if current.is_file():
            current = current.parent
        for candidate in [current, *current.parents]:
            if (candidate / ".kb").is_dir():
                return cls(candidate)
        raise KbNotFoundError("knowledge base is not initialized; run `kb init <name>` first", start=str(current))

    @classmethod
    def init(cls, root: Path, name: str, force: bool = False) -> "Project":
        root = root.expanduser().resolve()
        kb_dir = root / ".kb"
        if kb_dir.exists() and not force:
            raise ValidationError("knowledge base already initialized", root=str(root))
        root.mkdir(parents=True, exist_ok=True)
        for path in [
            kb_dir,
            root / "raw" / "articles",
            root / "raw" / "thoughts",
            root / "raw" / "notes",
            root / "wiki" / "entities",
            root / "wiki" / "topics",
            root / "wiki" / "summaries",
            root / "wiki" / ".archive",
            root / "schema",
            root / "dist",
        ]:
            path.mkdir(parents=True, exist_ok=True)
        config = {
            "schema_version": 1,
            "name": name,
            "render": {"title": name, "theme": "system"},
        }
        (kb_dir / "config.yaml").write_text(dump_yaml(config), encoding="utf-8")
        cls._write_if_missing(root / "schema" / "categories.md", DEFAULT_CATEGORIES)
        cls._write_if_missing(root / "schema" / "workflows.md", DEFAULT_WORKFLOWS)
        cls._write_if_missing(root / "schema" / "conventions.md", DEFAULT_CONVENTIONS)
        cls._write_if_missing(root / "wiki" / "index.md", "# 知识库索引\n\n暂无编译页。\n")
        cls._write_if_missing(root / "wiki" / "log.md", "# 编译日志\n\n")
        cls._merge_gitignore(root)
        project = cls(root)
        from .index_engine import IndexEngine
        from .git_repo import GitRepo

        IndexEngine(project).build()
        GitRepo(root).commit(f"chore: 初始化知识库 {name}")
        return project

    @property
    def config(self) -> dict[str, Any]:
        if self._config is None:
            config_path = self.root / ".kb" / "config.yaml"
            if not config_path.exists():
                raise KbNotFoundError(root=str(self.root))
            self._config = load_yaml(config_path.read_text(encoding="utf-8"))
        return self._config

    def path(self, *parts: str | os.PathLike[str]) -> Path:
        target = self.root.joinpath(*map(Path, parts)).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise ValidationError("path escapes knowledge base root", path=str(target)) from exc
        return target

    @staticmethod
    def _write_if_missing(path: Path, content: str) -> None:
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    @staticmethod
    def _merge_gitignore(root: Path) -> None:
        gitignore = root / ".gitignore"
        required = [".kb/index.sqlite", ".kb/.lock", "dist/", "__pycache__/", ".pytest_cache/"]
        existing = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
        merged = existing[:]
        for item in required:
            if item not in merged:
                merged.append(item)
        gitignore.write_text("\n".join(merged).rstrip() + "\n", encoding="utf-8")
