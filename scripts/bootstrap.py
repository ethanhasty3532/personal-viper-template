#!/usr/bin/env python3
"""bootstrap.py — tạo một dự án VIPER mới từ template này.

COPY template ra thư mục mới (template giữ nguyên, dùng lại được cho dự án sau),
thay placeholder, git init + first commit.

Usage:
    python3 scripts/bootstrap.py <project-code> [--target PATH] [--name "Tên dự án"]
                                 [--authority "Tên <email>"] [--dry-run]

Ví dụ:
    python3 scripts/bootstrap.py garahen --name "GaraHẹn" \\
        --authority "Lê Khắc Việt <viet@example.com>"

<project-code>: chữ thường + số + gạch nối. Mặc định --target là ../<project-code>

Windows: dùng `python scripts\\bootstrap.py` nếu không có lệnh `python3`.

Exit codes: 0 ok · 1 lỗi tham số · 2 target đã tồn tại · 3 verify thất bại
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
UNFILLED = "_CHƯA ĐIỀN_"  # giống scripts/gate.py — dấu "chỗ này chưa ai điền"

TEXT_SUFFIXES = {
    ".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt",
    ".toml", ".mjs", ".ts", ".js",
}
TEXT_NAMES = {".gitignore", ".env.example", "Makefile"}
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "__pycache__", "dist", "build", ".next",
    # Vết chạy của chính template — copy sang là dự án mới sinh ra đã có "lịch sử"
    # không phải của nó, làm bẩn `reanchor.py --audit` ngay từ ngày đầu.
    ".viper", ".playwright-mcp",
}
SKIP_FILES = {".DS_Store", "Thumbs.db"}

REQUIRED = [
    "VIPER.md", "CLAUDE.md", "STATE.md", "Makefile",
    "context/PRD.md", "context/INTERVIEW.md", "context/PERSONAS.md",
    "context/DESIGN-SYSTEM.md", "context/PROTOTYPE.md",
    "context/BACKWARD-COMPATIBILITY-CHECKLIST.md",
    "context/CAPABILITIES-MAP.md",
    "intake/README.md", "intake/_PRD-TEMPLATE.md",
    "intake/_ARCHITECTURE-TEMPLATE.md", "intake/_TECHSTACK-TEMPLATE.md",
    "intake/_ROADMAP-TEMPLATE.md",
    # Cửa vào pha V của vòng ≥2 (tài liệu vòng) — nằm dưới intake/ nên copy verbatim.
    "intake/loops/_TEMPLATE.md",
    # {{ds-name}} là tên thư mục NGUYÊN VĂN (đặc tả "một thư mục cho mỗi design
    # system") — intake/ không qua substitute nên tên này giữ nguyên ở dự án mới.
    "intake/design-systems/{{ds-name}}/_DESIGN-SYSTEM-TEMPLATE.md",
    "intake/design-systems/{{ds-name}}/_TOKENS-TEMPLATE.json",
    "intake/design-systems/{{ds-name}}/components/_COMPONENT-TEMPLATE.md",
    "intake/loops/_PROPOSAL-TEMPLATE.md",
    "srcroot/README.md",
    "deployment/README.md", "deployment/.env.example",
    "scripts/gate.py", "scripts/reanchor.py", "scripts/guard_ask.py",
    "scripts/repeat.py", "scripts/guard_bc.py", "scripts/guard_ds.py",
    "scripts/compact.py",
]

# Thư mục copy NGUYÊN VĂN — không thay placeholder, không quét leftover.
# intake/ chứa đặc tả định dạng MESH-render với {{P-XXX}}, {{DATE}}… là một phần
# của chính đặc tả; thay chúng là phá hợp đồng đầu vào của đường intake.
VERBATIM_PREFIXES = ("intake/",)

# Công cụ của TEMPLATE, dự án thật không dùng tới — không copy sang.
# Đường dẫn tương đối so với gốc template, khớp chính xác chứ không theo tên file.
TEMPLATE_ONLY = {
    "START-HERE.md",  # hướng dẫn của template, không mang sang sản phẩm

    "scripts/bootstrap.py",  # dự án không sinh dự án khác
    "scripts/selftest.py",   # kiểm chính template
    "README.md",             # bản template nói về "khởi tạo dự án mới" — thay bằng README của dự án
}

# Dùng placeholder để Step 2 thay tên dự án như với mọi file khác.
PROJECT_README = """# {{PROJECT_NAME}}

_Một dòng: sản phẩm này giải quyết nỗi đau gì, cho ai. Điền sau pha V — nguồn: `context/PRD.md §1`._

Dựng theo quy trình **VIPER**: solo, một tuần, production-ready.
Luật và năm pha: [VIPER.md](VIPER.md) · Đang ở đâu: [STATE.md](STATE.md)

---

## Chạy

```bash
make dev      # chạy local (app + db)
make check    # lint + typecheck + build
make test     # smoke + luồng quan trọng
make migrate  # DB migration có version
make deploy   # đẩy lên PaaS
make doctor   # kiểm env + kết nối
```

Sáu lệnh này là hợp đồng chung. Phần thân điền ở pha I theo
`.claude/skills/stack-<tên>/SKILL.md §4`; stack đang dùng ghi ở `context/TECHSTACK.md`.

## Trạng thái

```bash
python3 scripts/gate.py     # gate của pha hiện tại còn thiếu gì
```

## Tài liệu

| File | Nội dung |
|---|---|
| [context/PRD.md](context/PRD.md) | Pain point · đối tượng · AC · out-of-scope · success metric |
| [context/INTERVIEW.md](context/INTERVIEW.md) | Sổ phỏng vấn pha V — 14 mục, mỗi mục có bằng chứng |
| [context/PERSONAS.md](context/PERSONAS.md) | Persona · năng lực được cấp · ma trận vai × hành động |
| [context/CAPABILITIES-MAP.md](context/CAPABILITIES-MAP.md) | Đường intake: bản đồ năng lực tách từ `intake/PRD.md §3` |
| [context/DESIGN-SYSTEM.md](context/DESIGN-SYSTEM.md) | Token · tương phản · kho component — nguồn sự thật cho hình thức |
| [context/PROTOTYPE.md](context/PROTOTYPE.md) | Bản đồ màn hình · map AC ↔ màn hình · vết Authority chốt prototype |
| [context/ARCHITECTURE.md](context/ARCHITECTURE.md) | Sơ đồ · mô hình dữ liệu · luồng lõi · ranh giới module |
| [context/TECHSTACK.md](context/TECHSTACK.md) | Stack + version đã chốt |
| [context/DECISIONS.md](context/DECISIONS.md) | Mọi quyết định, append-only |
| [context/ROADMAP.md](context/ROADMAP.md) | Tuần này + backlog Phase 2 |
| [context/shared/DEPLOY.md](context/shared/DEPLOY.md) | Nơi chạy · env · migration · **rollback** |

## Bắt đầu

```bash
claude
/viper-validate     # pha V — nơi DUY NHẤT được hỏi Authority
```

Có sẵn tài liệu MESH-render? Thả vào `intake/` (xem [intake/README.md](intake/README.md))
trước khi chạy `/viper-validate` — pha V sẽ đi **đường intake**: dịch tài liệu thay cho
phỏng vấn (`VIPER.md §1.3`).
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="bootstrap.py",
        description="Tạo một dự án VIPER mới từ template.",
    )
    p.add_argument("code", help="project-code: chữ thường + số + gạch nối")
    p.add_argument("--target", help="thư mục đích (mặc định ../<project-code>)")
    p.add_argument("--name", help="tên dự án hiển thị (mặc định = project-code)")
    p.add_argument("--authority", help='Authority duy nhất, dạng "Tên <email>"')
    p.add_argument("--dry-run", action="store_true", help="xem trước, không ghi gì")
    return p.parse_args(argv)


def validate_code(code: str) -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", code):
        sys.exit(
            f"ERROR: project-code '{code}' không hợp lệ — chỉ a-z, 0-9, '-', "
            "và phải bắt đầu bằng chữ thường hoặc số."
        )


def is_text_file(path: Path) -> bool:
    return path.suffix in TEXT_SUFFIXES or path.name in TEXT_NAMES


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f in SKIP_FILES:
                continue
            p = Path(dirpath) / f
            if root == SRC and rel_posix(p, root) in TEMPLATE_ONLY:
                continue
            yield p


def rel_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return ""


def build_substitutions(args: argparse.Namespace) -> list[tuple[str, str]]:
    subs = [
        ("{{PROJECT-CODE}}", args.code),
        ("{{PROJECT_NAME}}", args.name or args.code),
        ("{{DATE}}", date.today().isoformat()),
    ]
    # Luôn thay AUTHORITY_*, kể cả khi không truyền --authority. Bỏ trống thì để
    # _CHƯA ĐIỀN_ — dự án mới hiện rõ chỗ còn nợ, thay vì mang placeholder thô suốt đời.
    name, email = UNFILLED, UNFILLED
    auth = (args.authority or "").strip()
    if auth:
        m = re.match(r"^(.*?)\s*<([^>]+)>\s*$", auth)
        if m:
            name, email = m.group(1).strip(), m.group(2).strip()
        else:
            name = auth
    subs += [("{{AUTHORITY_NAME}}", name), ("{{AUTHORITY_EMAIL}}", email)]
    return subs


def copy_template(target: Path) -> int:
    def ignore(dirpath: str, names: list[str]) -> set[str]:
        skip = {n for n in names if n in SKIP_DIRS or n in SKIP_FILES}
        base = rel_posix(Path(dirpath), SRC)
        for n in names:
            if (f"{base}/{n}" if base else n) in TEMPLATE_ONLY:
                skip.add(n)
        return skip

    shutil.copytree(SRC, target, ignore=ignore)
    (target / "README.md").write_text(PROJECT_README, encoding="utf-8")
    return sum(1 for _ in iter_files(target))


def substitute(target: Path, subs: list[tuple[str, str]]) -> int:
    changed = 0
    for path in iter_files(target):
        if not is_text_file(path):
            continue
        if rel_posix(path, target).startswith(VERBATIM_PREFIXES):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new = text
        for old, repl in subs:
            new = new.replace(old, repl)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def make_executable(target: Path) -> None:
    if sys.platform == "win32":
        return
    for path in (target / "scripts").glob("*.py"):
        path.chmod(path.stat().st_mode | 0o111)


def patch_windows_hooks(target: Path) -> None:
    """Windows không có lệnh `python3` — hook trong settings.json sẽ hỏng im lặng.

    Vá ngay lúc bootstrap thay vì dặn người dùng sửa tay: đổi "command": "python3"
    thành "python" trong .claude/settings.json của dự án mới.
    """
    if sys.platform != "win32":
        return
    p = target / ".claude" / "settings.json"
    try:
        text = p.read_text(encoding="utf-8")
        patched = text.replace('"command": "python3"', '"command": "python"')
        if patched != text:
            p.write_text(patched, encoding="utf-8")
            print('  ✓ Windows: hook đổi "python3" → "python" trong .claude/settings.json')
    except OSError as e:
        print(f"  ⚠ không vá được settings.json cho Windows: {e}", file=sys.stderr)


def verify(target: Path) -> bool:
    ok = True

    leftovers = []
    for path in iter_files(target):
        if not is_text_file(path):
            continue
        if rel_posix(path, target).startswith(VERBATIM_PREFIXES):
            continue
        try:
            if re.search(r"\{\{(PROJECT-CODE|PROJECT_NAME|DATE"
                         r"|AUTHORITY_NAME|AUTHORITY_EMAIL)\}\}",
                         path.read_text(encoding="utf-8")):
                leftovers.append(path.relative_to(target))
        except (UnicodeDecodeError, OSError):
            continue

    if leftovers:
        print("  ✗ vẫn còn placeholder trong:", file=sys.stderr)
        for f in leftovers:
            print(f"      {f}", file=sys.stderr)
        ok = False
    else:
        print("  ✓ không còn placeholder")

    for rel in REQUIRED:
        if (target / rel).is_file():
            print(f"  ✓ {rel}")
        else:
            print(f"  ✗ thiếu {rel}", file=sys.stderr)
            ok = False

    # Gate V ở dự án mới PHẢI đỏ — context chưa điền.
    try:
        res = subprocess.run(
            [sys.executable, str(target / "scripts" / "gate.py"), "V"],
            cwd=target, capture_output=True, text=True, timeout=30,
        )
        if res.returncode == 0:
            print("  ⚠ gate.py V đã xanh ở dự án mới — bất thường, "
                  "context lẽ ra phải trống", file=sys.stderr)
        else:
            print("  ✓ gate.py V báo đỏ đúng như mong đợi (context chưa điền)")
    except (OSError, subprocess.SubprocessError) as e:
        print(f"  ⚠ không chạy được gate.py: {e}", file=sys.stderr)

    return ok


def git_init(target: Path, code: str) -> None:
    if shutil.which("git") is None:
        print("  ⚠ không có git trong PATH — bỏ qua", file=sys.stderr)
        return

    def git(*a: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *a], cwd=target, capture_output=True, text=True)

    if git("init", "-q", "-b", "main").returncode != 0:
        git("init", "-q")
        git("symbolic-ref", "HEAD", "refs/heads/main")
    git("add", "-A")
    if git("commit", "-q", "-m", f"khởi tạo {code} từ template VIPER").returncode == 0:
        print("  ✓ git init + commit đầu (branch main)")
    else:
        print("  ⚠ git init xong nhưng commit lỗi — cấu hình user.name/user.email "
              "rồi commit tay", file=sys.stderr)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    validate_code(args.code)

    target = Path(args.target).expanduser().resolve() if args.target \
        else SRC.parent / args.code
    name = args.name or args.code

    print("=== VIPER bootstrap ===")
    print(f"  project-code : {args.code}")
    print(f"  tên dự án    : {name}")
    print(f"  template     : {SRC}")
    print(f"  target       : {target}")
    if args.authority:
        print(f"  authority    : {args.authority}")
    else:
        print(f"  authority    : {UNFILLED} — điền tay vào CLAUDE.md §10, "
              "hoặc chạy lại với --authority \"Tên <email>\"")
    if args.dry_run:
        print("  chế độ       : DRY-RUN (không ghi gì)")
    print()

    if target.exists() and not args.dry_run:
        print(f"ERROR: '{target}' đã tồn tại. Chọn --target khác hoặc xoá nó trước.",
              file=sys.stderr)
        return 2

    subs = build_substitutions(args)

    print("Step 1: Copy template → target")
    print(f"  bỏ lại (công cụ của template): {' · '.join(sorted(TEMPLATE_ONLY))}")
    print("  README.md sẽ được thay bằng bản của dự án")
    if args.dry_run:
        print(f"  (dry-run) sẽ copy {sum(1 for _ in iter_files(SRC))} file")
    else:
        print(f"  ✓ đã copy {copy_template(target)} file")
    print()

    print("Step 2: Thay placeholder")
    if args.dry_run:
        for old, repl in subs:
            print(f"  (dry-run) {old} → {repl}")
        print("\nDRY-RUN xong. Chạy lại không có --dry-run để áp dụng.")
        return 0
    print(f"  ✓ đã thay trong {substitute(target, subs)} file")
    make_executable(target)
    patch_windows_hooks(target)
    print()

    print("Step 3: Verify")
    ok = verify(target)
    print()
    if not ok:
        print("Bootstrap xong NHƯNG verify có cảnh báo — xem trên.", file=sys.stderr)
        return 3

    print("Step 4: Git")
    git_init(target, args.code)
    print()

    print(f"""✓ Dự án '{args.code}' đã sẵn sàng tại:
    {target}

Bước tiếp theo:
  cd "{target}"
  claude              # mở phiên
  /viper-validate     # pha V — phỏng vấn gộp, 2–3 tiếng, chốt PRD + persona + stack
                      # + kiến trúc + design system + prototype (Authority bấm thử và chốt nếu có UI)
                      # Có tài liệu MESH-render? Thả vào intake/ TRƯỚC khi chạy —
                      # pha V sẽ đi đường intake: dịch tài liệu thay cho phỏng vấn (VIPER.md §1.3)

Nhớ: pha V là nơi DUY NHẤT được hỏi. Đường phỏng vấn hỏi cho đủ 14 mục của
/viper-validate; đường intake vá lỗ hổng cũng chỉ được hỏi tại đây —
vì sau khi khoá scope thì agent tự quyết và chỉ ghi lại vào DECISIONS.md.""")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
