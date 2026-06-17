from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path
from typing import Any

from kb_core.errors import KbError
from kb_core.index_engine import IndexEngine
from kb_core.maintainer import Maintainer
from kb_core.project import Project
from kb_core.raw_store import RawStore
from kb_core.renderer import Renderer
from kb_core.services import (
    build_plan,
    init_project,
    ingest,
    link_pages,
    mark_compiled,
    raw_record_to_dict,
    upsert_page,
    wiki_page_to_dict,
    write_summary,
)
from kb_core.wiki_store import WikiStore

try:
    import typer  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal local envs
    typer = None


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        raise SystemExit(2)
    try:
        data, human = args.handler(args)
        _emit(data, bool(getattr(args, "json", False)), human)
    except KbError as exc:
        _emit_error(exc, bool(getattr(args, "json", False)))
    except BrokenPipeError:
        raise
    except Exception as exc:  # pragma: no cover - final CLI guard
        _emit_error(KbError(str(exc), code="unexpected_error"), bool(getattr(args, "json", False)))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kb")
    sub = parser.add_subparsers(dest="command")

    init_p = sub.add_parser("init", help="初始化知识库")
    init_p.add_argument("name")
    init_p.add_argument("--root")
    init_p.add_argument("--force", action="store_true")
    init_p.add_argument("--json", action="store_true")
    init_p.set_defaults(handler=_handle_init)

    ingest_p = sub.add_parser("ingest", help="写入纯文本到原料层")
    ingest_p.add_argument("--type", default="thought", choices=["article", "thought", "note"])
    ingest_p.add_argument("--text")
    ingest_p.add_argument("--text-file")
    ingest_p.add_argument("--title")
    ingest_p.add_argument("--source-url")
    ingest_p.add_argument("--source-path")
    ingest_p.add_argument("--author")
    ingest_p.add_argument("--context")
    ingest_p.add_argument("--json", action="store_true")
    ingest_p.set_defaults(handler=_handle_ingest)

    plan_p = sub.add_parser("plan", help="输出编译上下文")
    plan_p.add_argument("raw_id")
    plan_p.add_argument("--limit", type=int, default=8)
    plan_p.add_argument("--json", action="store_true")
    plan_p.set_defaults(handler=_handle_plan)

    summary_p = sub.add_parser("summary", help="写摘要页")
    summary_p.add_argument("raw_id")
    summary_p.add_argument("--text")
    summary_p.add_argument("--text-file")
    summary_p.add_argument("--json", action="store_true")
    summary_p.set_defaults(handler=_handle_summary)

    entity_p = sub.add_parser("entity", help="实体页操作")
    entity_sub = entity_p.add_subparsers(dest="entity_command")
    entity_upsert = entity_sub.add_parser("upsert")
    _add_page_args(entity_upsert)
    entity_upsert.set_defaults(handler=lambda args: _handle_page_upsert(args, "entity"))

    topic_p = sub.add_parser("topic", help="主题页操作")
    topic_sub = topic_p.add_subparsers(dest="topic_command")
    topic_upsert = topic_sub.add_parser("upsert")
    _add_page_args(topic_upsert)
    topic_upsert.set_defaults(handler=lambda args: _handle_page_upsert(args, "topic"))

    link_p = sub.add_parser("link", help="建立双向关联")
    link_p.add_argument("a")
    link_p.add_argument("b")
    link_p.add_argument("--json", action="store_true")
    link_p.set_defaults(handler=_handle_link)

    compiled_p = sub.add_parser("compiled", help="记录原料编译状态")
    compiled_p.add_argument("raw_id")
    compiled_p.add_argument("--tag", action="append", default=[])
    compiled_p.add_argument("--json", action="store_true")
    compiled_p.set_defaults(handler=_handle_compiled)

    search_p = sub.add_parser("search", help="全文检索")
    search_p.add_argument("query")
    search_p.add_argument("--layer", choices=["raw", "wiki"])
    search_p.add_argument("--type")
    search_p.add_argument("--limit", type=int, default=10)
    search_p.add_argument("--json", action="store_true")
    search_p.set_defaults(handler=_handle_search)

    get_p = sub.add_parser("get", help="读取编译层页面")
    get_p.add_argument("page_id")
    get_p.add_argument("--json", action="store_true")
    get_p.set_defaults(handler=_handle_get)

    get_raw_p = sub.add_parser("get-raw", help="读取原料层记录")
    get_raw_p.add_argument("raw_id")
    get_raw_p.add_argument("--json", action="store_true")
    get_raw_p.set_defaults(handler=_handle_get_raw)

    index_p = sub.add_parser("index", help="输出 wiki/index.md")
    index_p.add_argument("--json", action="store_true")
    index_p.set_defaults(handler=_handle_index)

    render_p = sub.add_parser("render", help="渲染静态 Wiki")
    render_p.add_argument("--open", action="store_true")
    render_p.add_argument("--json", action="store_true")
    render_p.set_defaults(handler=_handle_render)

    lint_p = sub.add_parser("lint", help="维护扫描")
    lint_p.add_argument("--check", action="append", default=[])
    lint_p.add_argument("--fix", action="store_true")
    lint_p.add_argument("--json", action="store_true")
    lint_p.set_defaults(handler=_handle_lint)

    log_p = sub.add_parser("log", help="查看 Git 历史")
    log_p.add_argument("-n", "--limit", type=int, default=20)
    log_p.add_argument("--json", action="store_true")
    log_p.set_defaults(handler=_handle_log)

    return parser


def _add_page_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("title")
    parser.add_argument("--body")
    parser.add_argument("--body-file")
    parser.add_argument("--alias", action="append", default=[])
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--related", action="append", default=[])
    parser.add_argument("--json", action="store_true")


def _handle_init(args) -> tuple[dict[str, Any], str]:
    root = Path(args.root) if args.root else Project.default_root()
    data = init_project(root, args.name, force=args.force)
    return data, f"初始化完成：{data['root']}"


def _handle_ingest(args) -> tuple[dict[str, Any], str]:
    project = Project.resolve()
    text = _read_text(args.text, args.text_file, label="text")
    data = ingest(
        project,
        raw_type=args.type,
        text=text,
        title=args.title,
        source_url=args.source_url,
        source_path=args.source_path,
        author=args.author,
        context=args.context,
    )
    record = data["record"]
    if data["duplicated"]:
        human = f"已存在：{record['id']} {record.get('title') or ''}".strip()
    else:
        human = f"已写入：{record['id']} {record.get('title') or ''}".strip()
    return data, human


def _handle_plan(args) -> tuple[dict[str, Any], str]:
    data = build_plan(Project.resolve(), args.raw_id, limit=args.limit)
    return data, json.dumps(data, ensure_ascii=False, indent=2, default=str)


def _handle_summary(args) -> tuple[dict[str, Any], str]:
    text = _read_text(args.text, args.text_file, label="summary text")
    data = write_summary(Project.resolve(), args.raw_id, text)
    return data, f"摘要页已写入：{data['page']['id']}"


def _handle_page_upsert(args, page_type: str) -> tuple[dict[str, Any], str]:
    body = _read_text(args.body, args.body_file, label="body")
    data = upsert_page(
        Project.resolve(),
        page_type,
        args.title,
        body,
        aliases=args.alias,
        sources=args.source,
        related=args.related,
    )
    return data, f"{page_type} 已写入：{data['page']['id']}"


def _handle_link(args) -> tuple[dict[str, Any], str]:
    data = link_pages(Project.resolve(), args.a, args.b)
    return data, f"已关联：{args.a} <-> {args.b}"


def _handle_compiled(args) -> tuple[dict[str, Any], str]:
    data = mark_compiled(Project.resolve(), args.raw_id, args.tag)
    return data, f"已记录 compiled：{args.raw_id}"


def _handle_search(args) -> tuple[dict[str, Any], str]:
    project = Project.resolve()
    engine = IndexEngine(project)
    if args.layer:
        hits = engine.search(args.query, layer=args.layer, type=args.type, limit=args.limit)
    else:
        hits = engine.search(args.query, layer="wiki", type=args.type, limit=args.limit)
        if len(hits) < args.limit:
            hits.extend(engine.search(args.query, layer="raw", type=args.type, limit=args.limit - len(hits)))
    data = {"hits": [hit.__dict__ for hit in hits]}
    human = "\n".join(f"- [{hit.layer}/{hit.type}] {hit.id} {hit.title}\n  {hit.snippet}" for hit in hits) or "无匹配结果"
    return data, human


def _handle_get(args) -> tuple[dict[str, Any], str]:
    page = WikiStore(Project.resolve()).get(args.page_id)
    data = {"page": wiki_page_to_dict(page), "body": page.body}
    return data, page.body


def _handle_get_raw(args) -> tuple[dict[str, Any], str]:
    record = RawStore(Project.resolve()).get(args.raw_id)
    data = {"record": raw_record_to_dict(record), "content": record.content}
    return data, record.content


def _handle_index(args) -> tuple[dict[str, Any], str]:
    project = Project.resolve()
    content = project.path("wiki", "index.md").read_text(encoding="utf-8")
    return {"content": content}, content


def _handle_render(args) -> tuple[dict[str, Any], str]:
    index_path = Renderer(Project.resolve()).render_site()
    if args.open:
        webbrowser.open(index_path.resolve().as_uri())
    return {"index": str(index_path)}, f"渲染完成：{index_path}"


def _handle_lint(args) -> tuple[dict[str, Any], str]:
    maintainer = Maintainer(Project.resolve())
    if args.fix:
        fixed = maintainer.fix_missing_backlinks()
        issues = maintainer.lint(args.check or None)
        data = {"fixed": [issue.__dict__ for issue in fixed], "issues": [issue.__dict__ for issue in issues]}
        human = f"已修复 missing_backlink：{len(fixed)}；剩余问题：{len(issues)}"
    else:
        issues = maintainer.lint(args.check or None)
        data = {"issues": [issue.__dict__ for issue in issues]}
        human = "\n".join(f"- [{issue.check}] {issue.page_id}: {issue.message}" for issue in issues) or "未发现问题"
    return data, human


def _handle_log(args) -> tuple[dict[str, Any], str]:
    from kb_core.git_repo import GitRepo

    entries = GitRepo(Project.resolve().root).log(args.limit)
    human = "\n".join(f"{item['commit'][:8]} {item['date']} {item['subject']}" for item in entries)
    return {"entries": entries}, human


def _read_text(value: str | None, file_value: str | None, *, label: str) -> str:
    if value == "-":
        return sys.stdin.read()
    if file_value:
        return Path(file_value).read_text(encoding="utf-8")
    if value is not None:
        return value
    raise KbError(f"{label} is required; use --{label.replace(' ', '-')} or --{label.replace(' ', '-')}-file", "missing_text")


def _emit(data: dict[str, Any], as_json: bool, human: str) -> None:
    if as_json:
        print(json.dumps({"ok": True, "data": data}, ensure_ascii=False, indent=2, default=str))
    else:
        print(human)


def _emit_error(error: KbError, as_json: bool) -> None:
    payload = {"ok": False, "error": error.to_dict()}
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str), file=sys.stderr)
    else:
        print(f"错误：{error.message}", file=sys.stderr)
    raise SystemExit(1)


if typer is not None:
    app = typer.Typer(add_completion=False, help="Local second-brain knowledge base")
    entity_app = typer.Typer(add_completion=False)
    topic_app = typer.Typer(add_completion=False)

    @app.command("init")
    def typer_init(name: str, root: str | None = None, force: bool = False, json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_init(argparse.Namespace(name=name, root=root, force=force, json=json_output)), json_output)

    @app.command("ingest")
    def typer_ingest(
        type: str = typer.Option("thought", "--type"),
        text: str | None = None,
        text_file: str | None = typer.Option(None, "--text-file"),
        title: str | None = None,
        source_url: str | None = typer.Option(None, "--source-url"),
        source_path: str | None = typer.Option(None, "--source-path"),
        author: str | None = None,
        context: str | None = None,
        json_output: bool = typer.Option(False, "--json"),
    ):
        _typer_run(
            lambda: _handle_ingest(
                argparse.Namespace(
                    type=type,
                    text=text,
                    text_file=text_file,
                    title=title,
                    source_url=source_url,
                    source_path=source_path,
                    author=author,
                    context=context,
                    json=json_output,
                )
            ),
            json_output,
        )

    @app.command("plan")
    def typer_plan(raw_id: str, limit: int = 8, json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_plan(argparse.Namespace(raw_id=raw_id, limit=limit, json=json_output)), json_output)

    @app.command("summary")
    def typer_summary(
        raw_id: str,
        text: str | None = None,
        text_file: str | None = typer.Option(None, "--text-file"),
        json_output: bool = typer.Option(False, "--json"),
    ):
        _typer_run(lambda: _handle_summary(argparse.Namespace(raw_id=raw_id, text=text, text_file=text_file, json=json_output)), json_output)

    @entity_app.command("upsert")
    def typer_entity_upsert(
        title: str,
        body: str | None = None,
        body_file: str | None = typer.Option(None, "--body-file"),
        alias: list[str] = typer.Option([], "--alias"),
        source: list[str] = typer.Option([], "--source"),
        related: list[str] = typer.Option([], "--related"),
        json_output: bool = typer.Option(False, "--json"),
    ):
        args = argparse.Namespace(title=title, body=body, body_file=body_file, alias=alias, source=source, related=related, json=json_output)
        _typer_run(lambda: _handle_page_upsert(args, "entity"), json_output)

    @topic_app.command("upsert")
    def typer_topic_upsert(
        title: str,
        body: str | None = None,
        body_file: str | None = typer.Option(None, "--body-file"),
        alias: list[str] = typer.Option([], "--alias"),
        source: list[str] = typer.Option([], "--source"),
        related: list[str] = typer.Option([], "--related"),
        json_output: bool = typer.Option(False, "--json"),
    ):
        args = argparse.Namespace(title=title, body=body, body_file=body_file, alias=alias, source=source, related=related, json=json_output)
        _typer_run(lambda: _handle_page_upsert(args, "topic"), json_output)

    @app.command("link")
    def typer_link(a: str, b: str, json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_link(argparse.Namespace(a=a, b=b, json=json_output)), json_output)

    @app.command("compiled")
    def typer_compiled(raw_id: str, tag: list[str] = typer.Option([], "--tag"), json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_compiled(argparse.Namespace(raw_id=raw_id, tag=tag, json=json_output)), json_output)

    @app.command("search")
    def typer_search(
        query: str,
        layer: str | None = None,
        type: str | None = None,
        limit: int = 10,
        json_output: bool = typer.Option(False, "--json"),
    ):
        _typer_run(lambda: _handle_search(argparse.Namespace(query=query, layer=layer, type=type, limit=limit, json=json_output)), json_output)

    @app.command("get")
    def typer_get(page_id: str, json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_get(argparse.Namespace(page_id=page_id, json=json_output)), json_output)

    @app.command("get-raw")
    def typer_get_raw(raw_id: str, json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_get_raw(argparse.Namespace(raw_id=raw_id, json=json_output)), json_output)

    @app.command("index")
    def typer_index(json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_index(argparse.Namespace(json=json_output)), json_output)

    @app.command("render")
    def typer_render(open: bool = False, json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_render(argparse.Namespace(open=open, json=json_output)), json_output)

    @app.command("lint")
    def typer_lint(check: list[str] = typer.Option([], "--check"), fix: bool = False, json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_lint(argparse.Namespace(check=check, fix=fix, json=json_output)), json_output)

    @app.command("log")
    def typer_log(limit: int = typer.Option(20, "-n", "--limit"), json_output: bool = typer.Option(False, "--json")):
        _typer_run(lambda: _handle_log(argparse.Namespace(limit=limit, json=json_output)), json_output)

    app.add_typer(entity_app, name="entity")
    app.add_typer(topic_app, name="topic")

    def _typer_run(handler, json_output: bool) -> None:
        try:
            data, human = handler()
            _emit(data, json_output, human)
        except KbError as exc:
            _emit_error(exc, json_output)
else:
    app = main


if __name__ == "__main__":
    if typer is not None:
        app()
    else:
        main()
