#!/usr/bin/env python3
"""Aidam Starter: offline workspace tools, Python standard library only."""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
import zipfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

VERSION = "0.2.0"
SOURCE = Path(__file__).resolve().parent
AREAS = ("projects", "data", "content", "clients", "skills")
# Exact release boundary. Adding files requires changing this list and the manifest.
RELEASE_FILES = (
    ".gitignore", "LICENSE", "README.md", "aidam.py",
    "CHANGELOG.md", "docs/architecture.md", "docs/connectors.md", "docs/privacy.md",
    "docs/quickstart.md", "docs/skills.md", "docs/walkthrough.md",
    "template/AGENTS.md", "template/CLAUDE.md", "template/START-HERE.md",
    "template/.gitignore", "template/system/AIDAM.md",
    "template/system/memory/MEMORY.md", "template/system/bridges/README.md",
    "template/system/skills/aidam-core/SKILL.md",
    "template/system/skills/verification-before-completion/SKILL.md",
    "template/operations/docs/templates/context.md",
    "template/operations/docs/templates/session.md",
    "template/operations/docs/templates/bridge.md",
    "template/operations/docs/templates/handoff.md",
    "tests/test_aidam.py",
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def inside(root, relative):
    raw = Path(relative)
    if raw.is_absolute() or ".." in raw.parts:
        raise ValueError("只接受工作区内的相对路径，禁止 .. 和绝对路径")
    target = (root / raw).resolve()
    if target != root and root not in target.parents:
        raise ValueError("路径或符号链接越出工作区")
    return target


def workspace(path):
    root = Path(path).expanduser().resolve()
    if not (root / "system/AIDAM.md").is_file():
        raise ValueError("目标不是有效的 Aidam 工作区，缺少 system/AIDAM.md")
    for relative in ("system", "system/runtime", "system/memory", "active"):
        inside(root, relative)
    return root


def today():
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def context_text(name):
    return ("---\nupdated: " + today() + "\n---\n\n# " + name +
            "\n\n| 事项 | 状态 | 下一步 |\n|---|---|---|\n| 待补充 | 未开始 | 确认目标与验收标准 |\n")


def initialize(args):
    raw = Path(args.path).expanduser()
    if raw.is_symlink():
        raise ValueError("初始化目标不能是符号链接")
    root = raw.resolve()
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("初始化目标必须不存在或为空目录；现有文件不会覆盖")
    template = SOURCE / "template"
    if not template.is_dir():
        raise ValueError("请从下载的 Starter 仓库运行 init")
    files = list(template.rglob("*"))
    if any(p.is_symlink() for p in files):
        raise ValueError("模板含符号链接，初始化已停止")
    root.mkdir(parents=True, exist_ok=True)
    for file in files:
        destination = root / file.relative_to(template)
        if file.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, destination)
    directories = ["system/runtime", "system/tools", "system/memory/sessions",
                   "operations/log", "operations/research", "operations/output",
                   "operations/product", "operations/tools", "archive", "tmp"]
    for area in AREAS:
        directories.append("active/" + area)
    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)
    for area in AREAS:
        (root / "active" / area / ".context.md").write_text(context_text(area), encoding="utf-8")
    shutil.copyfile(Path(__file__), root / "system/tools/aidam.py")
    write_json(root / "system/local.json", {"version": VERSION, "owner": "待填写", "bridges": {}})
    write_json(root / "system/runtime/sessions.json", {})
    print("已创建空白工作区：" + str(root))
    print("下一步：阅读 START-HERE.md，并运行 doctor。所有外部连接默认关闭。")


def doctor(args):
    root = Path(args.path).expanduser().resolve()
    errors = 0
    required = ("system/AIDAM.md", "AGENTS.md", "system/memory/MEMORY.md",
                "system/tools/aidam.py", "system/local.json")
    for name in required:
        try:
            path = inside(root, name)
            if not path.is_file():
                raise ValueError("缺少文件")
            if name.endswith(".json"):
                json.loads(path.read_text(encoding="utf-8"))
            print("OK " + name)
        except (ValueError, OSError):
            errors += 1
            print("ERROR " + name)
    for area in AREAS:
        try:
            if not inside(root, "active/" + area).is_dir():
                raise ValueError("目录缺失")
        except ValueError:
            errors += 1
            print("ERROR active/" + area)
    print("ERROR=" + str(errors) + "（仅检查本地骨架，不代表外部连接已授权）")
    return 1 if errors else 0


@contextmanager
def session_lock(root):
    runtime = inside(root, "system/runtime")
    runtime.mkdir(parents=True, exist_ok=True)
    lock = runtime / "session.lock"
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError("会话状态正在写入；稍后重试。异常退出的锁请先确认无进程使用再手动删除")
    try:
        yield inside(root, "system/runtime/sessions.json")
    finally:
        lock.rmdir()


def load_sessions(file):
    return json.loads(file.read_text(encoding="utf-8")) if file.exists() else {}


def overlap(first, second):
    return first == second or first in second.parents or second in first.parents


def session_start(args):
    root = workspace(args.path)
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,31}", args.entry):
        raise ValueError("entry 使用 1–32 位小写字母、数字或连字符")
    claims = [inside(root, path) for path in args.claim]
    with session_lock(root) as state:
        sessions = load_sessions(state)
        for record in sessions.values():
            for previous in record["claims"]:
                if any(overlap(path, inside(root, previous)) for path in claims):
                    raise ValueError("路径与进行中的会话重叠：" + record["id"])
        identifier = uuid.uuid4().hex[:12]
        record = {"id": identifier, "entry": args.entry,
                  "started": datetime.now().astimezone().isoformat(),
                  "claims": [path.relative_to(root).as_posix() for path in claims]}
        sessions[identifier] = record
        write_json(state, sessions)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def session_finish(args):
    root = workspace(args.path)
    with session_lock(root) as state:
        sessions = load_sessions(state)
        if args.id not in sessions:
            raise ValueError("找不到进行中的会话 ID")
        record = sessions[args.id]
        now = datetime.now().astimezone()
        folder = inside(root, "system/memory/sessions/" + now.strftime("%Y-%m-%d"))
        folder.mkdir(parents=True, exist_ok=True)
        log = folder / (now.strftime("%H%M%S") + "-" + record["entry"] + "-" + args.id + ".md")
        content = ("# [" + record["entry"] + "] " + now.strftime("%H:%M") + " 会话记录\n\n" +
                   args.summary + "\n\n- started: " + record["started"] + "\n- finished: " +
                   now.isoformat() + "\n\n## 声明路径\n\n" +
                   "\n".join("- " + p for p in record["claims"]) + "\n")
        # Exclusive create preserves history if a finish is repeated after a partial failure.
        with log.open("x", encoding="utf-8") as file:
            file.write(content)
        del sessions[args.id]
        write_json(state, sessions)
    print("已写入独立日志：" + str(log.relative_to(root)))


def project(args):
    root = workspace(args.path)
    if not args.name.strip() or args.name in (".", "..") or any(c in args.name for c in "/\\\n\r"):
        raise ValueError("项目名必须是单个目录名")
    destination = inside(root, "active/" + args.area + "/" + args.name)
    destination.mkdir(exist_ok=False)
    (destination / "README.md").write_text("# " + args.name + "\n\n## 目标\n\n待填写。\n\n## 验收标准\n\n待填写。\n", encoding="utf-8")
    (destination / ".context.md").write_text(context_text(args.name), encoding="utf-8")
    print("已创建项目：" + str(destination.relative_to(root)))
    print("请同步更新所属区域的 .context.md 状态表。")


def context(args):
    """Read only navigation; summaries never replace original evidence."""
    root = workspace(args.path)
    records = []
    if args.action == "recent":
        cutoff = datetime.now().astimezone().date() - timedelta(days=args.days - 1)
        folder = inside(root, "system/memory/sessions")
        for file in sorted(folder.glob("*/*.md"), reverse=True):
            try:
                day = datetime.strptime(file.parent.name, "%Y-%m-%d").date()
            except ValueError:
                continue
            if not cutoff <= day <= datetime.now().astimezone().date():
                continue
            safe = inside(root, file.relative_to(root))
            lines = safe.read_text(encoding="utf-8").splitlines()
            summary = " · ".join(line.lstrip("# ") for line in lines if line.strip())[:240]
            records.append({"path": file.relative_to(root).as_posix(), "summary": summary})
    else:
        query = args.task.strip().casefold()
        if not query:
            raise ValueError("任务关键词不能为空")
        for area in AREAS:
            folder = inside(root, "active/" + area)
            for file in sorted(folder.glob("*/.context.md")):
                safe = inside(root, file.relative_to(root))
                # Literal keywords and project names, not semantic relevance scores.
                if query in (file.parent.name + " " + safe.read_text(encoding="utf-8")).casefold():
                    records.append({"path": file.relative_to(root).as_posix()})
    print(json.dumps({"records": records[:args.limit], "total": len(records),
                      "truncated": len(records) > args.limit,
                      "warning": "只读导航；需回读相关原文。关键词未命中时扩大检索；多候选不得自动认定。"},
                     ensure_ascii=False, indent=2))


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("必须是正整数")
    return number


def privacy_findings(content):
    # Split marker literals so scanner tests and scanner source contain no real credentials.
    patterns = {
        "GitHub 凭据格式": r"gh[pousr]_" + r"[A-Za-z0-9]{30,}",
        "GitHub 细粒度凭据格式": "github_" + r"pat_[A-Za-z0-9_]{40,}",
        "API 凭据格式": "sk" + r"-[A-Za-z0-9_-]{24,}",
        "私钥格式": "-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "个人主目录绝对路径": r"/(?:Users|home)/[A-Za-z0-9_.-]+/",
        "电子邮箱": r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    }
    return [label for label, pattern in patterns.items() if re.search(pattern, content)]


def release_data(source):
    manifest_file = source / "share-manifest.json"
    if manifest_file.is_symlink():
        raise ValueError("分享清单不能是符号链接")
    manifest_bytes = manifest_file.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("files") != list(RELEASE_FILES) or manifest.get("version") != VERSION:
        raise ValueError("分享清单与程序内精确白名单不一致")
    data = {}
    for relative in (*RELEASE_FILES, "share-manifest.json"):
        parts = Path(relative).parts
        current = source
        for part in parts:
            current = current / part
            if current.is_symlink():
                raise ValueError("分享范围含符号链接：" + relative)
        content = current.read_bytes()
        findings = privacy_findings(content.decode("utf-8"))
        if findings:
            raise ValueError("隐私检查未通过：" + relative + "；" + "、".join(findings))
        data[relative] = content
    return data


def share(args):
    source = Path(args.source).expanduser().resolve()
    output_raw = Path(args.output).expanduser()
    if output_raw.is_symlink():
        raise ValueError("输出不能是符号链接")
    output = output_raw.resolve()
    if output.exists():
        raise ValueError("输出文件已存在，拒绝覆盖")
    if source == output or source in output.parents:
        raise ValueError("分享 ZIP 必须输出到源目录之外")
    data = release_data(source)
    checksums = "".join(hashlib.sha256(content).hexdigest() + "  " + name + "\n"
                        for name, content in sorted(data.items()))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as package:
        for name, content in data.items():
            package.writestr(name, content)
        package.writestr("CHECKSUMS.sha256", checksums)
    print("PASS 精确白名单 " + str(len(data)) + " 个源文件；隐私模式扫描无命中")
    print("已生成：" + str(output))
    print("自动扫描不能识别所有私人内容，发布前仍需人工审阅清单与差异。")


def main():
    parser = argparse.ArgumentParser(description="Aidam Starter — 本地知识库工作方式")
    parser.add_argument("--version", action="version", version=VERSION)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("init", initialize), ("doctor", doctor)):
        command = commands.add_parser(name)
        command.add_argument("path")
        command.set_defaults(handler=handler)
    command = commands.add_parser("project")
    command.add_argument("path")
    command.add_argument("--area", choices=AREAS, required=True)
    command.add_argument("--name", required=True)
    command.set_defaults(handler=project)
    sessions = commands.add_parser("session").add_subparsers(dest="action", required=True)
    command = sessions.add_parser("start")
    command.add_argument("path")
    command.add_argument("--entry", required=True)
    command.add_argument("--claim", action="append", default=[])
    command.set_defaults(handler=session_start)
    command = sessions.add_parser("finish")
    command.add_argument("path")
    command.add_argument("--id", required=True)
    command.add_argument("--summary", required=True)
    command.set_defaults(handler=session_finish)
    navigation = commands.add_parser("context").add_subparsers(dest="action", required=True)
    for action in ("recent", "assemble"):
        command = navigation.add_parser(action)
        command.add_argument("path")
        command.add_argument("--limit", type=positive_int, default=20)
        if action == "recent":
            command.add_argument("--days", type=positive_int, default=3)
        else:
            command.add_argument("--task", required=True)
        command.set_defaults(handler=context)
    command = commands.add_parser("share")
    command.add_argument("--source", default=str(SOURCE))
    command.add_argument("--output", required=True)
    command.set_defaults(handler=share)
    args = parser.parse_args()
    try:
        return args.handler(args) or 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        # Never echo file contents or credentials in diagnostics.
        if isinstance(error, OSError):
            print("ERROR: 文件操作失败（" + type(error).__name__ + "）", file=sys.stderr)
        else:
            print("ERROR: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
