#!/usr/bin/env python3
"""selftest.py — chạy trọn quy trình VIPER trên một dự án nháp, kiểm mọi thứ tự động.

VÌ SAO CÓ FILE NÀY
    Template này từng sửa nhiều vòng, và vòng nào review tay cũng lòi bug mới: gate xanh
    nhờ dòng ví dụ trong comment, verify báo sạch trong khi placeholder còn nguyên,
    hook nuốt mất blocker, log của template rò sang dự án mới. Nguyên nhân chung là
    KHÔNG CÓ BỘ TỰ KIỂM — mỗi lần chỉ dò tay được vài nhánh.

    File này biến việc dò tay đó thành lệnh chạy được. Sửa template xong thì chạy nó
    TRƯỚC khi nói là xong.

Usage:
    python3 scripts/selftest.py            # đầy đủ, trừ phần cần mạng
    python3 scripts/selftest.py --browser  # kiểm luôn Playwright MCP (cần mạng, chậm)
    python3 scripts/selftest.py -v         # in chi tiết từng phép kiểm

Exit codes: 0 tất cả đạt · 1 có phép kiểm hỏng
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
PY = sys.executable
UNFILLED_MARK = "_CHƯA ĐIỀN_"
VERBOSE = "-v" in sys.argv or "--verbose" in sys.argv

_C = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
GREEN, RED, GREY, BOLD, RESET = (
    ("\033[32m", "\033[31m", "\033[90m", "\033[1m", "\033[0m") if _C else ("",) * 5
)


class Suite:
    def __init__(self) -> None:
        self.passed = self.failed = 0
        self.fails: list[str] = []

    def group(self, name: str) -> None:
        print(f"\n{BOLD}{name}{RESET}")

    def check(self, label: str, cond: bool, detail: str = "") -> bool:
        if cond:
            self.passed += 1
            if VERBOSE:
                print(f"  {GREEN}✓{RESET} {label}")
        else:
            self.failed += 1
            self.fails.append(label)
            print(f"  {RED}✗{RESET} {label}")
            if detail:
                print(f"    {GREY}{detail}{RESET}")
        return cond

    def report(self) -> int:
        total = self.passed + self.failed
        print()
        if not self.failed:
            print(f"{GREEN}✓ selftest: {self.passed}/{total} đạt{RESET}\n")
            return 0
        print(f"{RED}✗ selftest: {self.passed}/{total} đạt — {self.failed} hỏng{RESET}")
        for f in self.fails:
            print(f"  {RED}·{RESET} {f}")
        print()
        return 1


def run(args: list[str], cwd: Path, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, input=stdin, capture_output=True,
                          text=True, timeout=120)


def gate(proj: Path, phase: str) -> bool:
    """gate.py trả 0 nghĩa là qua."""
    return run([PY, "scripts/gate.py", phase], proj).returncode == 0


def write(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")


def parse_frontmatter(text: str) -> dict | None:
    """Đọc frontmatter YAML của file agent — chỉ dùng thư viện chuẩn.

    Cố tình KHÔNG dùng PyYAML: template hứa 'Python thuần, thư viện chuẩn', mà bộ tự
    kiểm lại đòi cài thêm thì đúng lúc cần xác minh nhất lại không chạy được.
    Chỉ cần đủ cho dạng đang dùng: scalar phẳng + một khối lồng hai tầng + mảng JSON.
    """
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.strip().partition(":")
        val = val.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if val:
            if val.startswith("["):
                try:
                    val = json.loads(val)
                except ValueError:
                    pass
            parent[key] = val
        else:
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def sub(p: Path, old: str, new: str, count: int = -1) -> bool:
    t = p.read_text(encoding="utf-8")
    if old not in t:
        return False
    write(p, t.replace(old, new) if count < 0 else t.replace(old, new, count))
    return True


# --- 1. Bootstrap -----------------------------------------------------------

def test_bootstrap(s: Suite, tmp: Path) -> Path | None:
    s.group("1. Bootstrap")

    # tạo vết chạy trong template để chắc chắn nó KHÔNG rò sang dự án mới
    (SRC / ".viper").mkdir(exist_ok=True)
    (SRC / ".viper" / "reanchor.log").write_text(
        '{"at":"2020-01-01T00:00:00+00:00","source":"compact","session_id":"template",'
        '"transcript":"","phase":"V"}\n', encoding="utf-8")

    proj = tmp / "smoke"
    r = run([PY, "scripts/bootstrap.py", "smoke", "--target", str(proj),
             "--name", "Smoke Test", "--authority", "Người Thử <thu@example.com>"], SRC)
    shutil.rmtree(SRC / ".viper", ignore_errors=True)

    if not s.check("bootstrap chạy xong, exit 0", r.returncode == 0, r.stderr[-500:]):
        return None
    s.check("bootstrap không in cảnh báo", "⚠" not in r.stdout and "✗" not in r.stdout,
            r.stdout[-400:])

    # intake/ copy nguyên văn (VERBATIM_PREFIXES của bootstrap.py) — {{P-XXX}},
    # {{DATE}}… trong đó là một phần của đặc tả định dạng, không phải leftover.
    leftovers = [str(p.relative_to(proj)) for p in proj.rglob("*")
                 if p.is_file() and p.suffix in {".md", ".json", ".py"}
                 and p.relative_to(proj).parts[0] != "intake"
                 and re.search(r"\{\{[A-Z_-]+\}\}", p.read_text(encoding="utf-8", errors="ignore"))]
    s.check("không còn placeholder nào (ngoài intake/)", not leftovers, ", ".join(leftovers))
    s.check("intake/ copy nguyên văn — _PRD-TEMPLATE.md còn giữ {{P-XXX}}",
            "{{P-XXX}}" in (proj / "intake/_PRD-TEMPLATE.md")
            .read_text(encoding="utf-8", errors="ignore"),
            "bootstrap đã thay placeholder trong intake/ — VERBATIM_PREFIXES bị vô hiệu?")
    s.check("AUTHORITY đã thay (không phải _CHƯA ĐIỀN_)",
            "Người Thử" in (proj / "CLAUDE.md").read_text(encoding="utf-8"))
    s.check("vết chạy của template KHÔNG rò sang (.viper)",
            not (proj / ".viper").exists())

    # srcroot chia BA nhóm theo ARCHITECTURE §1–§3 — pha I đặt target vào đúng nhóm,
    # không phẳng. Thư mục nhóm luôn tồn tại kể cả khi hệ thống chưa có mobile.
    for grp in ("boundaries", "web-experiences", "mobile-experiences"):
        s.check(f"srcroot/{grp}/ có sẵn sau bootstrap",
                (proj / "srcroot" / grp).is_dir())
    # deployment/ — nơi CHẠY, tách khỏi code. .env.example không còn ở gốc repo.
    s.check("deployment/.env.example + deployment/README.md + local/ có sẵn",
            (proj / "deployment/.env.example").is_file()
            and (proj / "deployment/README.md").is_file()
            and (proj / "deployment/local").is_dir())
    s.check(".env.example KHÔNG còn ở gốc repo", not (proj / ".env.example").exists(),
            "đã chuyển vào deployment/ — mọi tham chiếu phải trỏ đường dẫn mới")

    # Gói design system mẫu: hai file đặc tả phải có, và _TOKENS-TEMPLATE.json phải
    # parse ra ĐÚNG bộ token mà context/DESIGN-SYSTEM.md §2 khai. Lệch nhau nghĩa là
    # dự án đi đường intake sẽ bị gate báo "bịa token" / "bỏ rơi token" ngay từ đầu.
    ds_dir = proj / "intake/design-systems/{{ds-name}}"
    s.check("gói design system mẫu đủ 3 file đặc tả",
            (ds_dir / "_DESIGN-SYSTEM-TEMPLATE.md").is_file()
            and (ds_dir / "_TOKENS-TEMPLATE.json").is_file()
            and (ds_dir / "components/_COMPONENT-TEMPLATE.md").is_file())
    flat: dict[str, str] = {}

    def walk(node, trail):
        if isinstance(node, dict):
            for key in ("$value", "value"):
                if key in node and not isinstance(node[key], (dict, list)):
                    flat["--" + "-".join(trail)] = str(node[key]).strip()
                    return
            for k, v in node.items():
                if str(k).startswith(("$", "_")):
                    continue
                walk(v, trail + [str(k).strip().lower().replace(" ", "-")])
        elif isinstance(node, (str, int, float)) and trail:
            flat["--" + "-".join(trail)] = str(node).strip()

    try:
        walk(json.loads((ds_dir / "_TOKENS-TEMPLATE.json").read_text(encoding="utf-8")), [])
    except ValueError as e:
        flat = {}
        s.check("_TOKENS-TEMPLATE.json là JSON hợp lệ", False, str(e))
    else:
        s.check("_TOKENS-TEMPLATE.json parse được, bỏ qua khoá metadata ($…)",
                bool(flat) and not any("$" in t for t in flat), ", ".join(sorted(flat))[:200])
    declared = set(re.findall(r"^\|\s*`(--[a-z0-9-]+)`",
                              (proj / "context/DESIGN-SYSTEM.md").read_text(encoding="utf-8"),
                              re.MULTILINE))
    s.check("token của gói mẫu khớp ĐÚNG bảng token context/DESIGN-SYSTEM.md §2",
            set(flat) == declared,
            f"chỉ gói có: {sorted(set(flat) - declared)} · chỉ §2 có: {sorted(declared - set(flat))}")
    # Dòng seed DECISIONS phải mang ngày "(template)" — nếu ai đổi lại thành {{DATE}},
    # bootstrap sẽ dập ngày thật vào và gate V đếm nhầm nó là một quyết định của dự án.
    s.check("dòng seed DECISIONS không mang ngày ISO (gate không được đếm nó)",
            "| (template) |" in (proj / "context/DECISIONS.md").read_text(encoding="utf-8"),
            "seed phải ghi ngày là (template), không phải {{DATE}}")

    for f in ("VIPER.md", "CLAUDE.md", "STATE.md", "Makefile", ".mcp.json",
              ".claude/settings.json", "scripts/gate.py", "scripts/reanchor.py",
              "scripts/guard_ask.py", "scripts/repeat.py", "scripts/guard_bc.py",
              "scripts/guard_ds.py",
              "context/INTERVIEW.md", "context/PERSONAS.md", "context/DESIGN-SYSTEM.md",
              "context/PROTOTYPE.md", "context/BACKWARD-COMPATIBILITY-CHECKLIST.md",
              "context/CAPABILITIES-MAP.md", "intake/README.md",
              "intake/_PRD-TEMPLATE.md", "srcroot/README.md",
              ".claude/skills/viper-browse/SKILL.md"):
        s.check(f"có {f}", (proj / f).is_file())

    # Công cụ của template không được rơi vào dự án thật
    for f in ("scripts/selftest.py", "scripts/bootstrap.py"):
        s.check(f"KHÔNG copy {f} (công cụ của template)", not (proj / f).exists())
    s.check("5 stack skill VẪN còn (stack chỉ chốt ở pha V, sau bootstrap)",
            len(list((proj / ".claude/skills").glob("stack-*"))) == 5)

    # README phải là của dự án, không phải của template
    rd = (proj / "README.md").read_text(encoding="utf-8")
    s.check("README.md là bản của dự án", "Smoke Test" in rd and "Khởi tạo dự án mới" not in rd)
    s.check("README.md không còn link MESH hỏng", "-MESH" not in rd)
    s.check("README.md không nhắc bootstrap/selftest",
            "bootstrap.py" not in rd and "selftest.py" not in rd)

    # Nhánh KHÔNG truyền --authority: đây đúng là chỗ từng có bug — verify báo
    # "không còn placeholder" trong khi {{AUTHORITY_NAME}} vẫn nằm nguyên ở CLAUDE.md §10.
    # Không chạy nhánh này thì đột biến vào verify() sẽ không ai bắt được.
    noauth = tmp / "noauth"
    r2 = run([PY, "scripts/bootstrap.py", "noauth", "--target", str(noauth),
              "--name", "Không Authority"], SRC)
    s.check("bootstrap chạy được khi KHÔNG truyền --authority", r2.returncode == 0,
            r2.stderr[-400:])
    if noauth.is_dir():
        # Regex đủ cặp ngoặc, và bỏ qua chính selftest.py: file này chứa mẫu
        # placeholder như chuỗi literal nên quét lỏng sẽ khớp nhầm chính nó.
        raw = [str(p.relative_to(noauth)) for p in noauth.rglob("*")
               if p.is_file() and p.suffix in {".md", ".json", ".py"}
               and p.name != "selftest.py"
               and re.search(r"\{\{AUTHORITY_(NAME|EMAIL)\}\}",
                             p.read_text(encoding="utf-8", errors="ignore"))]
        s.check("không còn {{AUTHORITY_*}} thô khi thiếu --authority", not raw, str(raw))
        s.check("verify KHÔNG báo sạch khi vẫn còn placeholder",
                not raw or "✓ không còn placeholder" not in r2.stdout,
                "verify phải bắt được AUTHORITY, không chỉ PROJECT_NAME/DATE")
        s.check("CLAUDE.md đánh dấu Authority là _CHƯA ĐIỀN_",
                "_CHƯA ĐIỀN_" in (noauth / "CLAUDE.md").read_text(encoding="utf-8"))
    return proj


# --- 2. Vòng đời gate -------------------------------------------------------

def test_lifecycle(s: Suite, proj: Path) -> None:
    s.group("2. Vòng đời gate V → I → P1 → P2 → E → R")

    for p in ("V", "I", "P1", "P2", "E"):
        s.check(f"gate {p} ĐỎ lúc mới sinh", not gate(proj, p))
    s.check("gate R luôn xanh (không có gate tự động)", gate(proj, "R"))
    s.check("make gate P=R không lỗi",
            run([PY, "scripts/gate.py", "R"], proj).returncode == 0)

    # --- pha V
    for f in ("context/PRD.md", "context/TECHSTACK.md", "context/ARCHITECTURE.md",
              "context/PERSONAS.md"):
        sub(proj / f, "_CHƯA ĐIỀN_", "đã điền")
    # Success metric phải có CON SỐ — bản điền chung "đã điền" không có số nào.
    sub(proj / "context/PRD.md",
        "## 6. Giả thuyết + success metric\n\nđã điền",
        "## 6. Giả thuyết + success metric\n\n≥10 lịch hẹn thật trong 5 ngày — dưới 5 thì kill")
    s.check("gate V ĐỎ khi PROTOTYPE chưa điền và chưa có marker KHÔNG CÓ UI",
            not gate(proj, "V"),
            "hướng dẫn về marker nằm trong <!-- --> nên không được tính")
    # nhánh backend-only: marker cho qua toàn bộ kiểm prototype
    write(proj / "context/PROTOTYPE.md", "KHÔNG CÓ UI — bỏ qua prototype\n")
    s.check("gate V vẫn ĐỎ khi DECISIONS chưa có quyết định thật",
            not gate(proj, "V"),
            "dòng seed (template) và dòng ví dụ trong <!-- --> không được tính")
    with (proj / "context/DECISIONS.md").open("a", encoding="utf-8") as f:
        f.write("| 2026-08-01 | Chọn stack-nextjs-fullstack | Nhanh nhất cho MVP |"
                " Không cần API riêng | Có |\n")
    s.check("gate V vẫn ĐỎ khi INTERVIEW chưa có bằng chứng", not gate(proj, "V"),
            "14 dòng 'Bằng chứng:' phải không rỗng — chống phỏng vấn hời hợt")
    sub(proj / "context/INTERVIEW.md", "_CHƯA ĐIỀN_", "đã điền")
    s.check("gate V vẫn ĐỎ khi chưa challenge pha V", not gate(proj, "V"),
            "tài liệu phải qua chất vấn trước khi khoá scope")
    with (proj / "STATE.md").open("a", encoding="utf-8") as f:
        f.write("| 2026-08-01 | V | AC-2 xử ca gửi hai lần ra sao? | FAIL |"
                " tài liệu chưa nói |\n")
    s.check("gate V ĐỎ khi challenge V gần nhất là FAIL", not gate(proj, "V"),
            "FAIL nghĩa là còn lỗ phỏng vấn — phải quay lại hỏi")
    with (proj / "STATE.md").open("a", encoding="utf-8") as f:
        f.write("| 2026-08-01 | V | AC-2 xử ca gửi hai lần ra sao? | PASS |"
                " đã hỏi lại, chốt chống trùng |\n")
    # Tới đây mọi điều kiện khác đã xanh — cô lập đúng một biến là số quyết định.
    s.check("gate V vẫn ĐỎ khi mới có 1 quyết định thật (seed không được đếm)",
            not gate(proj, "V"),
            "cần ≥2 quyết định có ngày ISO của chính dự án — seed (template) không tính")
    with (proj / "context/DECISIONS.md").open("a", encoding="utf-8") as f:
        f.write("| 2026-08-01 | Clerk cho auth | Đăng nhập Google chốt ở PRD §7 |"
                " Chấp nhận phụ thuộc bên thứ ba | Khó |\n")
    s.check("gate V XANH: backend-only, marker KHÔNG CÓ UI cho qua prototype",
            gate(proj, "V"))

    # --- "PRD đủ mục" không chỉ là hết _CHƯA ĐIỀN_ (bảng gate §1.1 hứa hơn thế)
    sub(proj / "context/PRD.md",
        "≥10 lịch hẹn thật trong 5 ngày — dưới 5 thì kill", "sẽ đo sau khi chạy")
    s.check("gate V ĐỎ khi success metric không có con số", not gate(proj, "V"),
            "không có số thì pha R không có ngưỡng để quyết go/pivot/kill")
    sub(proj / "context/PRD.md", "sẽ đo sau khi chạy",
        "≥10 lịch hẹn thật trong 5 ngày — dưới 5 thì kill")
    sub(proj / "context/PRD.md", "- đã điền\n\n## 6.", "## 6.")
    s.check("gate V ĐỎ khi mục Out-of-scope bị xoá rỗng", not gate(proj, "V"),
            "xoá section là xoá luôn marker _CHƯA ĐIỀN_ — filled() một mình không thấy")
    sub(proj / "context/PRD.md", "## 6.", "- đã điền\n\n## 6.", 1)
    with (proj / "context/PERSONAS.md").open("a", encoding="utf-8") as f:
        f.write("\n### Persona 2 — B (role: b)\n\n### Persona 3 — C (role: c)\n\n"
                "### Persona 4 — D (role: d)\n")
    s.check("gate V ĐỎ khi đường phỏng vấn có 4 persona (tối đa 3)", not gate(proj, "V"),
            "nhiều vai là dấu hiệu vượt cỡ một tuần — trần của đường phỏng vấn")
    sub(proj / "context/PERSONAS.md",
        "\n### Persona 2 — B (role: b)\n\n### Persona 3 — C (role: c)\n\n"
        "### Persona 4 — D (role: d)\n", "")
    s.check("gate V XANH trở lại sau khi trả PRD/PERSONAS về chuẩn", gate(proj, "V"))

    # Neo theo SỐ heading: chữ "Out-of-scope"/"success metric" nhắc sớm trong thân
    # bài không được chiếm quyền phép kiểm (bug neo-cụm-chữ cũ để mention sớm
    # trả lời hộ section thật).
    sub(proj / "context/PRD.md", "## 4. Ưu tiên",
        "Ghi chú: mọi thứ Out-of-scope xem §5; success metric có 1 con số ở §6.\n\n"
        "## 4. Ưu tiên")
    sub(proj / "context/PRD.md", "- đã điền\n\n## 6.", "## 6.")
    s.check("gate V ĐỎ khi §5 rỗng dù 'Out-of-scope' xuất hiện sớm hơn trong PRD",
            not gate(proj, "V"),
            "neo cụm chữ trần thì mention sớm chiếm quyền — phải neo heading số")
    sub(proj / "context/PRD.md", "## 6.", "- đã điền\n\n## 6.", 1)
    sub(proj / "context/PRD.md",
        "≥10 lịch hẹn thật trong 5 ngày — dưới 5 thì kill", "sẽ đo sau khi chạy")
    s.check("gate V ĐỎ khi §6 không số dù 'success metric' + số xuất hiện sớm hơn",
            not gate(proj, "V"))
    sub(proj / "context/PRD.md", "sẽ đo sau khi chạy",
        "≥10 lịch hẹn thật trong 5 ngày — dưới 5 thì kill")
    sub(proj / "context/PRD.md",
        "Ghi chú: mọi thứ Out-of-scope xem §5; success metric có 1 con số ở §6.\n\n"
        "## 4. Ưu tiên", "## 4. Ưu tiên")
    s.check("gate V XANH trở lại sau khi gỡ mention sớm", gate(proj, "V"))

    # nhánh có UI: đòi index.html + Authority chốt + design system + AC map đủ
    proto = proj / "context/PROTOTYPE.md"
    write(proto, "# PROTOTYPE\n\n| AC | Màn hình |\n|---|---|\n"
                 "| AC-1 | S1 |\n| AC-2 | S1 |\n| AC-3 | S2 |\n\n"
                 "Chốt bởi Authority: _CHƯA ĐIỀN_\n")
    s.check("gate V ĐỎ khi có UI mà chưa dựng prototype/index.html",
            not gate(proj, "V"))
    (proj / "prototype").mkdir(exist_ok=True)
    write(proj / "prototype/index.html", "<!doctype html><title>prototype</title>\n")
    s.check("gate V vẫn ĐỎ khi Authority CHƯA chốt prototype", not gate(proj, "V"),
            "chốt prototype là điều kiện khoá scope — dừng lại chờ Authority")
    sub(proto, "Chốt bởi Authority: _CHƯA ĐIỀN_", "Chốt bởi Authority: 2026-08-01")

    # --- design system: có UI thì bắt buộc, và ba phép kiểm máy phải hoạt động
    s.check("gate V vẫn ĐỎ khi có UI mà DESIGN-SYSTEM chưa điền", not gate(proj, "V"),
            "template DESIGN-SYSTEM.md còn _CHƯA ĐIỀN_ — mọi mục khác đã xanh")

    def ds_md(muted: str, screen: str) -> str:
        return ("# DESIGN SYSTEM\n\n## 1. Ba tính từ\n\nGọn · rõ · nhanh\n\n"
                "## 2. Token\n\n| Token | Giá trị | Dùng cho |\n|---|---|---|\n"
                "| `--color-bg` | `#FFFFFF` | nền |\n"
                "| `--color-text` | `#1A1A1A` | chữ |\n"
                f"| `--color-text-muted` | `{muted}` | chữ phụ |\n"
                "| `--color-primary` | `#0B5FFF` | nút |\n"
                "| `--color-on-primary` | `#FFFFFF` | chữ trên nút |\n\n"
                "## 3. Tương phản\n\n| Cặp | Chữ | Nền | Loại |\n|---|---|---|---|\n"
                "| Chữ chính | `--color-text` | `--color-bg` | thường |\n"
                "| Chữ phụ | `--color-text-muted` | `--color-bg` | thường |\n"
                "| Trên nút | `--color-on-primary` | `--color-primary` | thường |\n\n"
                "## 4. Kho component\n\n| # | Component | Dùng ở màn | Trạng thái |\n"
                "|---|---|---|---|\n"
                f"| C1 | Nút chính | {screen} | mặc định · đang gửi |\n")

    ds = proj / "context/DESIGN-SYSTEM.md"
    html_tokens = ("<!doctype html><title>prototype</title>\n<style>:root{"
                   "--color-bg:#FFFFFF;--color-text:#1A1A1A;--color-text-muted:#595959;"
                   "--color-primary:#0B5FFF;--color-on-primary:#FFFFFF}"
                   "body{background:var(--color-bg);color:var(--color-text)}</style>\n")
    write(ds, ds_md("#999999", "S1"))
    write(proj / "prototype/index.html", html_tokens)
    s.check("gate V ĐỎ khi một cặp tương phản dưới WCAG AA", not gate(proj, "V"),
            "#999999 trên #FFFFFF ≈ 2.8:1 < 4.5:1 — gate phải tự tính ra từ mã hex")
    write(ds, ds_md("#595959", "S1"))
    s.check("gate V XANH khi design system đủ và prototype dùng token", gate(proj, "V"))
    write(proj / "prototype/index.html",
          html_tokens.replace("--color-text-muted:#595959;", ""))
    s.check("gate V ĐỎ khi token khai mà prototype không dùng", not gate(proj, "V"),
            "bảng token là danh sách đóng — khai mà không dùng thì phải xoá dòng")
    # Bẫy khớp tiền tố: html chỉ còn --color-text-muted, KHÔNG còn --color-text
    # đứng riêng — kiểm bằng substring thô sẽ tính nhầm là "đã dùng".
    write(proj / "prototype/index.html",
          html_tokens.replace("--color-text:#1A1A1A;", "")
                     .replace("color:var(--color-text)", "color:#000"))
    s.check("gate V ĐỎ khi token chỉ xuất hiện làm tiền tố của token khác",
            not gate(proj, "V"),
            "--color-text nằm trong --color-text-muted không được tính là đã dùng")
    write(proj / "prototype/index.html", html_tokens)
    write(ds, ds_md("#595959", "S9"))
    s.check("gate V ĐỎ khi component trỏ màn không có trong PROTOTYPE §1",
            not gate(proj, "V"), "S9 không tồn tại — component tưởng tượng phải bị bắt")
    write(ds, ds_md("#595959", "S1"))
    s.check("gate V XANH trở lại khi component trỏ đúng màn", gate(proj, "V"))

    # --- Backstop của guard_ds nằm ở gate: hook chỉ chặn lỗi MỚI lúc ghi và fail-open
    # khi DS chưa chốt — vết lọt một lần mà gate không báo là mất dấu vĩnh viễn.
    write(proj / "prototype/index.html",
          html_tokens + "<style>.x{color:#123456}</style>")
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V ĐỎ khi prototype có mã màu thô ngoài :root (backstop guard_ds)",
            not gate(proj, "V") and "mã màu thô" in out, out[-400:])
    # CSS custom property phân biệt hoa thường — tên viết HOA không được đứng ngoài phép kiểm
    write(proj / "prototype/index.html",
          html_tokens + "<style>:root{--EVIL:#FF0000}.x{color:var(--EVIL)}</style>")
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V ĐỎ khi prototype dùng token viết HOA chưa khai (--EVIL)",
            not gate(proj, "V") and "--EVIL" in out, out[-400:])
    # :root là nơi token thành pixel — giá trị lệch bảng §2 phải bị bắt
    write(proj / "prototype/index.html",
          html_tokens.replace("--color-primary:#0B5FFF", "--color-primary:#FF00FF"))
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V ĐỎ khi :root prototype lệch giá trị token §2",
            not gate(proj, "V") and "lệch giá trị §2" in out, out[-400:])
    write(proj / "prototype/index.html", html_tokens)
    s.check("gate V XANH trở lại khi prototype sạch", gate(proj, "V"))

    sub(proto, "| AC-2 | S1 |\n", "", 1)
    s.check("gate V ĐỎ khi một AC không map vào màn hình nào", not gate(proj, "V"))
    sub(proto, "| AC-1 | S1 |\n", "| AC-1 | S1 |\n| AC-2 | S1 |\n", 1)
    s.check("gate V XANH trở lại khi AC map đủ", gate(proj, "V"))

    # Dòng AC không có nội dung (scaffold trống) không được đếm — đây từng là
    # đường lọt: khoá scope được với một AC thật + hai dòng scaffold.
    sub(proj / "context/PRD.md", "| AC-3 | đã điền | |", "| AC-3 | | |")
    s.check("gate V ĐỎ khi một dòng AC không có nội dung", not gate(proj, "V"),
            "chỉ AC có ô 'Làm được gì' không rỗng mới được đếm")
    sub(proj / "context/PRD.md", "| AC-3 | | |", "| AC-3 | đã điền | |")
    s.check("gate V XANH trở lại khi AC đủ nội dung", gate(proj, "V"))

    # Trần 7 AC là ràng buộc của ĐƯỜNG PHỎNG VẤN (bối cảnh một tuần) — giữ nguyên
    # ở đây và bỏ hẳn ở đường intake (kiểm ở nhóm 2b).
    extra_rows = "".join(f"| AC-{i} | đã điền | | |\n" for i in range(4, 10))
    sub(proj / "context/PRD.md", "| AC-3 | đã điền | | |\n",
        "| AC-3 | đã điền | | |\n" + extra_rows, 1)
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V ĐỎ khi đường phỏng vấn có 9 AC (trần 7)",
            not gate(proj, "V") and "nhiều hơn 7" in out, out[-300:])
    s.check("thông điệp nói rõ trần này của đường phỏng vấn",
            "ĐƯỜNG PHỎNG VẤN" in out, out[-300:])
    sub(proj / "context/PRD.md", extra_rows, "", 1)
    s.check("gate V XANH trở lại khi cắt về 3 AC", gate(proj, "V"))

    # --- pha I
    mk = proj / "Makefile"
    for t in ("dev", "check", "test", "migrate", "deploy", "doctor"):
        sub(mk, f"{t}:\n\t$(NOT_IMPLEMENTED)", f"{t}:\n\t@echo {t}")
    s.check("gate I ĐỎ khi chưa challenge / chưa commit", not gate(proj, "I"))

    # Commit TRƯỚC, để phép kiểm dưới đây cô lập đúng một biến là challenge.
    # Nếu để commit lại sau, gate I đỏ sẵn vì thiếu commit và phép kiểm FAIL
    # sẽ đúng vì lý do sai — test rỗng, không bắt được lỗi gì.
    run(["git", "add", "-A"], proj)
    run(["git", "-c", "user.email=t@t.t", "-c", "user.name=T", "commit", "-qm", "code"], proj)
    s.check("gate I vẫn ĐỎ khi đã commit nhưng CHƯA challenge pha I", not gate(proj, "I"),
            "challenge V PASS có sẵn trong STATE.md KHÔNG được tính cho gate I — lọc theo cột Pha")

    with (proj / "STATE.md").open("a", encoding="utf-8") as f:
        f.write("| 2026-08-01 | I | Câu hỏi khó | FAIL | chưa đọc kỹ |\n")
    s.check("gate I ĐỎ khi challenge pha I gần nhất là FAIL", not gate(proj, "I"),
            "FAIL nghĩa là chưa được code — không được tính là qua")
    with (proj / "STATE.md").open("a", encoding="utf-8") as f:
        f.write("| 2026-08-01 | I | Câu hỏi khó hơn | PASS | trả lời được |\n")
    s.check("gate I XANH sau khi challenge pha I PASS", gate(proj, "I"))

    # --- pha P1: tick mọi mục KHÔNG gắn (sau deploy)
    pr = proj / "context/PRODUCTION-READY.md"
    write(pr, "\n".join(l if "(sau deploy)" in l else l.replace("- [ ]", "- [x]")
                        for l in pr.read_text(encoding="utf-8").splitlines()))
    s.check("gate P1 XANH khi CHƯA deploy và CHƯA có DEPLOY.md", gate(proj, "P1"),
            "đây là vòng lặp chết cũ: P1 phải qua được trước khi có production")
    s.check("gate P2 vẫn ĐỎ lúc đó", not gate(proj, "P2"))

    # --- pha P2
    sub(pr, "- [ ]", "- [x]")
    sub(proj / "context/shared/DEPLOY.md", "_CHƯA ĐIỀN_", "đã điền")
    s.check("gate P2 XANH sau khi deploy + điền DEPLOY.md", gate(proj, "P2"))
    # "Đủ §1–§5" là điều kiện thật, không chỉ hết _CHƯA ĐIỀN_
    sub(proj / "context/shared/DEPLOY.md", "## 4. Migration", "#### 4. Migration")
    s.check("gate P2 ĐỎ khi DEPLOY.md mất một mục §1–§5", not gate(proj, "P2"),
            "xoá section thì filled() vẫn xanh — gate phải đếm heading")
    sub(proj / "context/shared/DEPLOY.md", "#### 4. Migration", "## 4. Migration")
    s.check("gate P (cả hai nửa) XANH", gate(proj, "P"))

    # --- pha E
    s.check("gate E ĐỎ khi chưa có số liệu", not gate(proj, "E"))
    sub(proj / "context/EXPERIMENTS.md", "_CHƯA ĐIỀN_", "đã điền")
    # Dòng có ngày ở bảng KHÁC (phản hồi người dùng) không được tính là số liệu —
    # gate E chỉ đếm trong §Số liệu theo ngày.
    s.check("chèn được dòng phản hồi (bảng khác, có ngày)",
            sub(proj / "context/EXPERIMENTS.md",
                "| Ngày | Ai | Nói gì (nguyên văn) | Rút ra |\n|---|---|---|---|\n| | | | |",
                "| Ngày | Ai | Nói gì (nguyên văn) | Rút ra |\n|---|---|---|---|\n"
                "| 2026-08-05 | anh Tú | \"khó tìm nút tạo\" | sửa nhãn |", 1))
    s.check("gate E vẫn ĐỎ — dòng ngày ở bảng phản hồi không phải số liệu",
            not gate(proj, "E"),
            "gate E phải đếm riêng §Số liệu theo ngày, không đếm cả file")
    s.check("chèn được dòng số liệu",
            sub(proj / "context/EXPERIMENTS.md", "| | | | | | |",
                "| 2026-08-05 | 120 | 14 | 9 | 3 | ngày đầu |", 1))
    s.check("gate E XANH sau khi có số liệu thật", gate(proj, "E"))

    # --- gate tự đọc pha từ STATE.md
    sub(proj / "STATE.md", "Pha hiện tại : V", "Pha hiện tại : E")
    r = run([PY, "scripts/gate.py"], proj)
    s.check("gate.py không tham số tự đọc pha từ STATE.md",
            r.returncode == 0 and "đọc pha E" in r.stdout, r.stdout[-200:])

    # Pha ghi dạng P1/P2 (tên gate) cũng phải đọc được — regex cũ [VIPER] trả "?"
    sub(proj / "STATE.md", "Pha hiện tại : E", "Pha hiện tại : P1")
    r = run([PY, "scripts/gate.py"], proj)
    s.check("gate.py tự đọc được cả pha ghi dạng P1",
            r.returncode == 0 and "đọc pha P1" in r.stdout, r.stdout[-200:])
    sub(proj / "STATE.md", "Pha hiện tại : P1", "Pha hiện tại : E")


# --- 2b. Đường intake --------------------------------------------------------

def test_intake(s: Suite, tmp: Path) -> None:
    """Đường vào thứ hai của pha V (VIPER.md §1.3): Authority thả tài liệu
    MESH-render vào intake/, INTERVIEW.md mang marker NGUỒN: INTAKE thay cho
    14 dòng bằng chứng. Dự án riêng để không nhiễm state của test_lifecycle
    (test_hook/guard/repeat còn chạy tiếp trên dự án smoke)."""
    s.group("2b. Đường intake — gate V không cần 14 mục phỏng vấn")

    proj = tmp / "intakeproj"
    r = run([PY, "scripts/bootstrap.py", "intakeproj", "--target", str(proj),
             "--name", "Intake Test", "--authority", "Người Thử <thu@example.com>"], SRC)
    if not s.check("bootstrap dự án riêng cho đường intake", r.returncode == 0,
                   (r.stderr + r.stdout)[-400:]):
        return

    # Dựng mọi điều kiện chung của gate V (giống đường phỏng vấn) — trừ INTERVIEW
    for f in ("context/PRD.md", "context/TECHSTACK.md", "context/ARCHITECTURE.md",
              "context/PERSONAS.md"):
        sub(proj / f, UNFILLED_MARK, "đã điền")
    sub(proj / "context/PRD.md",
        "## 6. Giả thuyết + success metric\n\nđã điền",
        "## 6. Giả thuyết + success metric\n\n≥5 gara dùng thật trong wave 1 — dưới 2 thì xét lại")
    # Đường intake giữ mã P-… của intake PRD để truy vết ngược
    sub(proj / "context/PERSONAS.md",
        "| Mã (intake) | — (đường phỏng vấn để `—`) |", "| Mã (intake) | P-OWNER |")
    write(proj / "context/PROTOTYPE.md", "KHÔNG CÓ UI — bỏ qua prototype\n")
    with (proj / "context/DECISIONS.md").open("a", encoding="utf-8") as f:
        f.write("| 2026-08-01 | Stack theo intake TECHSTACK | intake thắng default skill |"
                " render đúng | Có |\n"
                "| 2026-08-01 | Auth: tự quyết Clerk | intake không nói |"
                " Authority review lô cuối buổi | Khó |\n")
    with (proj / "STATE.md").open("a", encoding="utf-8") as f:
        f.write("| 2026-08-01 | V | Lát cắt tuần này đủ nhỏ chưa? | PASS |"
                " CAPABILITIES-MAP §2 trả lời |\n")

    marker = "NGUỒN: INTAKE — render nhận ngày 2026-08-01\n\n"
    trace = ("## Truy vết intake → context\n\n"
               "| Mục context | Nguồn intake |\n|---|---|\n"
               "| PRD.md | intake/PRD.md §1–§6 |\n"
               "| PERSONAS.md + CAPABILITIES-MAP.md | intake/PRD.md §2–§3 |\n\n"
               "## Lỗ hổng & cách xử\n\n"
               "| Lỗ hổng | Cách xử |\n|---|---|\n"
               "| auth | tự quyết — DECISIONS 2026-08-01 |\n")
    write(proj / "context/INTERVIEW.md", marker + trace)
    # AC-1..AC-3 của PRD template đều phải truy được về capability — đường intake bỏ
    # trần 7 AC và thay bằng phép truy vết này.
    cap_ok = ("# CAPABILITIES MAP\n\n## 1. Bảng năng lực\n\n"
              "| Capability | Phase | Personas | Vòng giao | AC vòng này | Trạng thái |\n"
              "|---|---|---|---|---|---|\n"
              "| CAP-TEST-01 — Đặt lịch hẹn | MVP | P-OWNER | 1 | AC-1, AC-2 | vòng này |\n"
              "| CAP-TEST-02 — Xem lịch tuần | MVP | P-OWNER | 1 | AC-3 | vòng này |\n"
              "| CAP-TEST-03 — Nhắc lịch | Phase 2 | P-OWNER | 2 | — | chờ vòng 2 |\n\n"
              "## 2. Lát cắt vòng này\n\nWave 1 của intake ROADMAP — đặt lịch trước.\n")
    write(proj / "context/CAPABILITIES-MAP.md", cap_ok)

    # Pin bằng MESSAGE, không chỉ exit code: lúc này gate còn đỏ vì kế hoạch vòng
    # chưa lập, assert `not gate(V)` suông là assertion rỗng nghĩa — xoá phép kiểm
    # khỏi gate.py suite vẫn xanh.
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V nêu 'marker không tự đứng' khi intake/PRD.md không tồn tại",
            not gate(proj, "V") and "marker không tự đứng" in out, out[-400:])

    write(proj / "intake/PRD.md",
          "# PRD\n\n## 2. Personas\n\n## {{P-XXX}} — {{Tên persona}}\n")
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V nêu 'chưa resolve' khi intake/PRD.md còn {{…}} (copy template)",
            not gate(proj, "V") and "chưa resolve" in out, out[-400:])

    prd_render = ("# PRD — Intake Test\n\n## 1. Problem statement\n\n"
                  "Chủ gara mất khách vì quên lịch hẹn.\n\n## 3. Capabilities\n\n"
                  "| Capability | Phase | P-OWNER | Business outcome |\n|---|---|---|---|\n"
                  "| CAP-TEST-01 — Đặt lịch hẹn | MVP | ✓ | giữ khách quay lại |\n")
    write(proj / "intake/PRD.md", prd_render)

    # --- kế hoạch chia vòng (VIPER.md §1.4): ROADMAP §1 phải khớp _PROPOSAL.md
    s.check("gate V ĐỎ khi chưa lập kế hoạch vòng (ROADMAP §1 còn scaffold)",
            not gate(proj, "V"),
            "đường intake nhận cả hệ thống — pha V vòng 1 phải cắt nó thành N vòng")

    def roadmap(n_rows: int) -> str:
        rows = "".join(
            f"| {i} | wave {i} | {'V, I' if i == 1 else 'V, I, P, E, R'} | "
            f"{'—' if i == 1 else i - 1} | {'đang chạy' if i == 1 else 'chưa mở'} |\n"
            for i in range(1, n_rows + 1))
        return ("# ROADMAP\n\n## 1. Kế hoạch vòng\n\n"
                "| Vòng | Phạm vi | Pha chạy | Phụ thuộc | Trạng thái |\n"
                "|---|---|---|---|---|\n" + rows +
                "\n## 2. Vòng này\n\n| AC | Trạng thái |\n|---|---|\n| AC-1 | ☐ |\n")

    def proposal(n: int, phases: str, extra: str = "") -> str:
        return (f"NGUỒN: KẾ HOẠCH VÒNG — lập ở vòng 1 ngày 2026-08-01\n"
                f"Pha vòng này: {phases}\n"
                f"UI vòng này: không có màn mới\n"
                f"{extra}"
                f"\n## Mục tiêu vòng\n\nGiao wave {n}.\n"
                f"\n## Phạm vi\n\n| Capability | Target |\n|---|---|\n"
                f"| CAP-TEST-0{n} | srcroot/api |\n")

    write(proj / "context/ROADMAP.md", roadmap(2))
    s.check("gate V vẫn ĐỎ khi ROADMAP §1 có 2 vòng mà thiếu _PROPOSAL.md",
            not gate(proj, "V"),
            "mỗi dòng kế hoạch phải có intake/loops/l<N>/_PROPOSAL.md tương ứng")
    for n in (1, 2):
        (proj / f"intake/loops/l{n}").mkdir(parents=True, exist_ok=True)
    write(proj / "intake/loops/l1/_PROPOSAL.md",
          proposal(1, "V, I", "Rà lại vòng 1: 2026-08-01\n"))
    s.check("gate V vẫn ĐỎ khi mới có _PROPOSAL.md của vòng 1 (kế hoạch nói 2 vòng)",
            not gate(proj, "V"))
    write(proj / "intake/loops/l2/_PROPOSAL.md", proposal(2, "V, I, P, E, R"))
    s.check("gate V XANH đường intake — KHÔNG cần 14 dòng Bằng chứng, kế hoạch vòng đủ",
            gate(proj, "V"))

    # --- KHÔNG có trần AC ở đường intake: một vòng = một lát cắt hệ thống lớn,
    # ép 7 là ép sai cỡ. Hàng rào thay thế là truy vết AC ↔ capability (ca dưới).
    extra_rows = "".join(f"| AC-{i} | đã điền | | CAP-TEST-01 |\n" for i in range(4, 10))
    sub(proj / "context/PRD.md", "| AC-3 | đã điền | | |\n",
        "| AC-3 | đã điền | | |\n" + extra_rows, 1)
    sub(proj / "context/CAPABILITIES-MAP.md", "AC-1, AC-2",
        "AC-1, AC-2, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9")
    out9 = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V XANH đường intake với 9 AC — KHÔNG có trần 7",
            gate(proj, "V") and "PRD có 9 AC" in out9,
            "trần 7 AC là ràng buộc của bối cảnh một tuần, không phải luật của VIPER\n"
            + out9[-300:])
    sub(proj / "context/PRD.md", extra_rows, "", 1)
    write(proj / "context/CAPABILITIES-MAP.md", cap_ok)

    # --- AC không truy được về capability: hàng rào thay cho trần 7 AC
    sub(proj / "context/CAPABILITIES-MAP.md", "AC-3", "—")
    s.check("gate V ĐỎ khi một AC không truy được về CAPABILITIES-MAP",
            not gate(proj, "V"),
            "đường intake bỏ trần AC, đổi lại đòi truy vết AC ↔ capability")
    write(proj / "context/CAPABILITIES-MAP.md", cap_ok)

    # AC nằm ở cột KHÁC (Trạng thái) không tính — truy vết đếm đúng cột "AC vòng này"
    sub(proj / "context/CAPABILITIES-MAP.md",
        "| CAP-TEST-02 — Xem lịch tuần | MVP | P-OWNER | 1 | AC-3 | vòng này |",
        "| CAP-TEST-02 — Xem lịch tuần | MVP | P-OWNER | 1 | — | AC-3 dời vòng 3 |")
    s.check("gate V ĐỎ khi AC chỉ xuất hiện ở cột Trạng thái (sai cột)",
            not gate(proj, "V"),
            "tìm cả file thì 'AC-3 dời vòng 3' cũng được tính là truy vết được")
    write(proj / "context/CAPABILITIES-MAP.md", cap_ok)

    # Đường intake phải giữ mã P-… của intake PRD (gate V, VIPER.md §1.1)
    sub(proj / "context/PERSONAS.md", "| Mã (intake) | P-OWNER |",
        "| Mã (intake) | — |")
    s.check("gate V ĐỎ khi PERSONAS đường intake bỏ mã P-…", not gate(proj, "V"),
            "mã P-… là dây truy vết ngược về intake PRD §2")
    sub(proj / "context/PERSONAS.md", "| Mã (intake) | — |",
        "| Mã (intake) | P-OWNER |")

    write(proj / "context/CAPABILITIES-MAP.md",
          f"# CAPABILITIES MAP\n\n{UNFILLED_MARK}\n")
    s.check("gate V ĐỎ khi CAPABILITIES-MAP chưa tách từ intake PRD §3",
            not gate(proj, "V"), "đường intake bắt buộc tách PERSONAS + CAPABILITIES-MAP")
    write(proj / "context/CAPABILITIES-MAP.md", cap_ok)
    s.check("gate V XANH trở lại khi CAPABILITIES-MAP đủ", gate(proj, "V"))

    write(proj / "context/INTERVIEW.md", marker + "\n")
    s.check("gate V ĐỎ khi marker không kèm bảng truy vết", not gate(proj, "V"),
            "một dòng NGUỒN: INTAKE suông không phải là đã dịch tài liệu")

    write(proj / "context/INTERVIEW.md", trace)
    s.check("gate V ĐỎ khi bỏ marker — luật 14 bằng chứng áp trở lại",
            not gate(proj, "V"),
            "nhánh intake khoá theo marker cả hai chiều, không theo file intake/")
    write(proj / "context/INTERVIEW.md", marker + trace)
    s.check("gate V XANH trở lại khi marker + truy vết đủ", gate(proj, "V"))

    # --- pha theo vòng (VIPER.md §1.4): vòng 1 khai "V, I" → gate P/E tự bỏ qua
    out_p1 = run([PY, "scripts/gate.py", "P1"], proj).stdout
    s.check("gate P1 XANH + nêu lý do khi vòng khai `Pha vòng này: V, I`",
            gate(proj, "P1") and "không chạy pha P" in out_p1, out_p1[-300:])
    out_e = run([PY, "scripts/gate.py", "E"], proj).stdout
    s.check("gate E XANH + nêu lý do ở vòng chỉ V+I",
            gate(proj, "E") and "không chạy pha E" in out_e, out_e[-300:])
    write(proj / "intake/loops/l1/_PROPOSAL.md",
          proposal(1, "V, I, P, E, R", "Rà lại vòng 1: 2026-08-01\n"))
    s.check("gate P1 ĐỎ trở lại khi vòng khai chạy pha P", not gate(proj, "P1"),
            "bỏ qua pha là quyết định của kế hoạch, không phải cửa lách gate")
    write(proj / "intake/loops/l1/_PROPOSAL.md",
          proposal(1, "V, I", "Rà lại vòng 1: 2026-08-01\n"))

    # --- round-trip: repeat --go phải move drop intake và re-arm vòng mới
    sub(proj / "STATE.md", "Pha hiện tại : V", "Pha hiện tại : R")
    run(["git", "add", "-A"], proj)
    run(["git", "-c", "user.email=t@t.t", "-c", "user.name=T", "commit",
         "-qm", "vòng 1 intake"], proj)
    r = run([PY, "scripts/repeat.py", "--go"], proj)
    s.check("repeat --go chạy xong trên dự án intake", r.returncode == 0,
            (r.stderr + r.stdout)[-400:])
    arch = proj / "context/archive/vong-1"
    s.check("drop intake/PRD.md được MOVE vào archive/vong-1/intake/",
            (arch / "intake/PRD.md").is_file()
            and not (proj / "intake/PRD.md").exists())
    s.check("template _*.md và intake/README.md ở lại (không phải drop)",
            (proj / "intake/_PRD-TEMPLATE.md").is_file()
            and (proj / "intake/README.md").is_file())
    s.check("CAPABILITIES-MAP được archive nhưng KHÔNG reset (tài liệu sống)",
            (arch / "CAPABILITIES-MAP.md").is_file()
            and "CAP-TEST-01" in (proj / "context/CAPABILITIES-MAP.md")
            .read_text(encoding="utf-8"))
    # INTERVIEW KHÔNG bị reset — marker còn nguyên, nhưng gate vòng ≥2 rẽ nhánh
    # theo số vòng TRƯỚC nhánh marker nên không bao giờ đọc INTERVIEW nữa.
    s.check("INTERVIEW đóng băng — marker NGUỒN: INTAKE còn nguyên (không reset)",
            re.search(r"^NGUỒN\s*:\s*INTAKE\b",
                      (proj / "context/INTERVIEW.md").read_text(encoding="utf-8"),
                      re.MULTILINE) is not None)
    s.check("intake/loops/l2/_PROPOSAL.md (kế hoạch lập từ vòng 1) không bị đụng",
            (proj / "intake/loops/l2/_PROPOSAL.md").is_file())
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V ĐỎ lại ở vòng 2 — đòi dòng `Rà lại vòng 2`",
            not gate(proj, "V") and "Rà lại vòng 2" in out, out[-500:])

    # Ngày rà lại phải ≥ `Vòng mở` — dấu vết cũ không xanh hộ vòng mới.
    with (proj / "intake/loops/l2/_PROPOSAL.md").open("a", encoding="utf-8") as f:
        f.write("Rà lại vòng 2: 2020-01-01\n")
    # Pin bằng message "cũ hơn": lúc này challenge/DECISIONS vòng 2 cũng chưa có nên
    # gate đỏ sẵn — chỉ exit code thì chiều TỪ CHỐI ngày cũ chưa từng được kiểm.
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V nêu 'cũ hơn' khi `Rà lại vòng 2` ghi ngày trước `Vòng mở`",
            not gate(proj, "V") and "cũ hơn" in out, out[-400:])
    today = date.today().isoformat()
    sub(proj / "intake/loops/l2/_PROPOSAL.md",
        "Rà lại vòng 2: 2020-01-01", f"Rà lại vòng 2: {today}")
    with (proj / "STATE.md").open("a", encoding="utf-8") as f:
        f.write(f"| {today} | V | Vòng 2 chạm gì vào legacy vòng 1? | PASS |"
                " _PROPOSAL §Legacy trả lời |\n")
    with (proj / "context/DECISIONS.md").open("a", encoding="utf-8") as f:
        f.write(f"| {today} | Giữ API v1 của vòng 1 | legacy là hợp đồng |"
                " thêm endpoint mới | Có |\n"
                f"| {today} | Nhắc lịch qua email | intake không chốt kênh |"
                " đổi được sang Zalo | Có |\n")
    s.check("gate V XANH ở vòng 2 khi đã rà lại kế hoạch + challenge + 2 quyết định",
            gate(proj, "V"),
            "Authority không phải thả tài liệu mỗi vòng — đã ký một lần cho cả kế hoạch")

    # Kế hoạch hết vòng: mở vòng 3 mà không có _PROPOSAL.md → repeat.py phải cảnh báo
    sub(proj / "STATE.md", "Pha hiện tại : V", "Pha hiện tại : R")
    run(["git", "add", "-A"], proj)
    run(["git", "-c", "user.email=t@t.t", "-c", "user.name=T", "commit",
         "-qm", "vòng 2"], proj)
    r = run([PY, "scripts/repeat.py", "--go"], proj)
    s.check("repeat --go cảnh báo khi kế hoạch vòng dừng trước vòng mới",
            r.returncode == 0 and "CHƯA có _PROPOSAL.md" in r.stdout,
            (r.stdout + r.stderr)[-400:])


# --- 3. Hook reanchor -------------------------------------------------------

def test_hook(s: Suite, proj: Path) -> None:
    s.group("3. Hook reanchor (chống quên luật sau compact)")

    sub(proj / "STATE.md", "Pha hiện tại : E", "Pha hiện tại : I")
    sub(proj / "STATE.md",
        "| Ngày | Blocker | Đã thử gì | Trạng thái |\n|---|---|---|---|\n| | | | |",
        "| Ngày | Blocker | Đã thử gì | Trạng thái |\n|---|---|---|---|\n"
        "| 2026-08-01 | Neon rate-limit | đổi pooler | đang mở |")

    payload = json.dumps({"session_id": "s1", "transcript_path": str(proj / "t.jsonl"),
                          "cwd": str(proj), "hook_event_name": "SessionStart",
                          "source": "compact"})
    r = run([PY, "scripts/reanchor.py"], proj, stdin=payload)
    s.check("hook exit 0 (không bao giờ được chặn phiên)", r.returncode == 0, r.stderr[-300:])

    try:
        ctx = json.loads(r.stdout)["hookSpecificOutput"]
    except Exception as e:
        s.check("hook in ra JSON đúng schema", False, f"{e} · {r.stdout[:200]}")
        return
    s.check("hookEventName = SessionStart", ctx.get("hookEventName") == "SessionStart")
    body = ctx.get("additionalContext", "")
    s.check("có additionalContext", bool(body))
    s.check("nhồi lại được luật (đọc từ CLAUDE.md, không chép cứng)",
            "AskUserQuestion" in body and "TÁM LUẬT" in body)
    s.check("luật KHÔNG bị chép cứng trong reanchor.py",
            "Scope khoá sau pha V** — phát sinh"
            not in (SRC / "scripts/reanchor.py").read_text(encoding="utf-8"),
            "chép cứng là tạo bản sao thứ tư của luật, sẽ trôi")
    s.check("nêu đúng pha hiện tại", "**I**" in body)
    s.check("BLOCKER đang mở có hiện ra", "Neon rate-limit" in body,
            "từng bị nuốt vì lỗi off-by-one khi cắt dòng bảng")
    s.check("AC có hiện ra", "AC-1" in body)
    s.check("không kéo theo comment HTML", "<!--" not in body)
    s.check("gọn (dưới 4000 ký tự)", len(body) < 4000, f"{len(body)} ký tự")
    s.check("hook ghi log để đo được sau này", (proj / ".viper/reanchor.log").is_file())

    # --- audit: phân biệt đúng trước/sau mốc và đúng pha
    log = json.loads((proj / ".viper/reanchor.log").read_text(encoding="utf-8").splitlines()[0])
    from datetime import datetime, timedelta
    at = datetime.fromisoformat(log["at"])

    def rec(dt, tool):
        return json.dumps({"type": "assistant",
                           "timestamp": dt.isoformat().replace("+00:00", "Z"),
                           "message": {"content": [{"type": "tool_use", "name": tool}]}})

    write(proj / "t.jsonl", "\n".join([
        rec(at - timedelta(seconds=5), "AskUserQuestion"),   # trước mốc — bỏ qua
        rec(at + timedelta(seconds=5), "Edit"),
        rec(at + timedelta(seconds=9), "AskUserQuestion"),   # sau mốc, pha I — phải bắt
    ]))
    out = run([PY, "scripts/reanchor.py", "--audit"], proj).stdout
    s.check("audit bắt được vi phạm SAU mốc compact", "✗" in out and "AskUserQuestion" in out)
    s.check("audit đếm đúng 1 vi phạm (không tính cái trước mốc)",
            "Tổng vi phạm đo được bằng máy: 1" in out, out[-200:])

    # pha V thì hỏi là ĐÚNG luật — không được báo vi phạm
    shutil.rmtree(proj / ".viper", ignore_errors=True)
    sub(proj / "STATE.md", "Pha hiện tại : I", "Pha hiện tại : V")
    run([PY, "scripts/reanchor.py"], proj, stdin=payload)
    log = json.loads((proj / ".viper/reanchor.log").read_text(encoding="utf-8").splitlines()[0])
    at = datetime.fromisoformat(log["at"])
    write(proj / "t.jsonl", rec(at + timedelta(seconds=5), "AskUserQuestion"))
    out = run([PY, "scripts/reanchor.py", "--audit"], proj).stdout
    s.check("audit KHÔNG báo vi phạm ở pha V (hỏi ở pha V là đúng luật)",
            "Tổng vi phạm đo được bằng máy: 0" in out, out[-300:])


# --- 3b. Hook guard_ask -----------------------------------------------------

def test_guard(s: Suite, proj: Path) -> None:
    s.group("3b. Hook guard_ask (chặn AskUserQuestion ngoài pha V)")

    # test_hook kết thúc với STATE.md ở pha V
    r = run([PY, "scripts/guard_ask.py"], proj, stdin="{}")
    s.check("pha V: cho qua (exit 0) — phỏng vấn là việc của pha V", r.returncode == 0,
            r.stderr[-200:])

    sub(proj / "STATE.md", "Pha hiện tại : V", "Pha hiện tại : I")
    r = run([PY, "scripts/guard_ask.py"], proj, stdin="{}")
    s.check("pha I: CHẶN (exit 2)", r.returncode == 2, f"exit {r.returncode}")
    s.check("stderr nhắc lại luật #2 (DECISIONS thay cho hỏi)",
            "DECISIONS" in r.stderr and "LUẬT #2" in r.stderr, r.stderr[:200])

    # Pha ghi dạng P1 (tên gate) — regex cũ [VIPER] không khớp "P1" nên fail-open
    # đúng lúc đang ở pha P. Phải CHẶN.
    sub(proj / "STATE.md", "Pha hiện tại : I", "Pha hiện tại : P1")
    r = run([PY, "scripts/guard_ask.py"], proj, stdin="{}")
    s.check("pha P1 (biến thể hay gặp): vẫn CHẶN (exit 2)", r.returncode == 2,
            f"exit {r.returncode} — P1 phải được nhận là pha P, không fail-open")
    sub(proj / "STATE.md", "Pha hiện tại : P1", "Pha hiện tại : V")

    # Quên đổi pha là lỗ thực chiến số 1: scope ĐÃ KHOÁ mà dòng pha còn ghi V → vẫn chặn
    sub(proj / "STATE.md", "- [ ] **Scope khoá**", "- [x] **Scope khoá**")
    r = run([PY, "scripts/guard_ask.py"], proj, stdin="{}")
    s.check("Scope khoá đã tick + pha còn ghi V: vẫn CHẶN (exit 2)", r.returncode == 2,
            f"exit {r.returncode} — luật thật là 'sau khoá scope', pha chỉ là proxy")
    s.check("stderr nhắc cập nhật `Pha hiện tại : I`", "Pha hiện tại : I" in r.stderr,
            r.stderr[:300])
    sub(proj / "STATE.md", "- [x] **Scope khoá**", "- [ ] **Scope khoá**")
    # Dòng pha ghi sai định dạng: chặn kèm hướng dẫn — không fail-open đúng chỗ hiểm
    sub(proj / "STATE.md", "Pha hiện tại : V", "Pha hiện tại : Đang Implement")
    r = run([PY, "scripts/guard_ask.py"], proj, stdin="{}")
    s.check("pha ghi sai định dạng ('Đang Implement'): CHẶN + hướng dẫn sửa STATE",
            r.returncode == 2 and "mã pha" in r.stderr,
            f"exit {r.returncode} · {r.stderr[:200]}")
    sub(proj / "STATE.md", "Pha hiện tại : Đang Implement", "Pha hiện tại : V")

    # STATE.md hỏng → fail-open, không được chặn nhầm
    st = (proj / "STATE.md").read_text(encoding="utf-8")
    write(proj / "STATE.md", "hỏng\n")
    r = run([PY, "scripts/guard_ask.py"], proj, stdin="{}")
    s.check("STATE.md không đọc được pha: fail-open (exit 0)", r.returncode == 0)
    write(proj / "STATE.md", st)


# --- 3b2. Hook guard_ds -----------------------------------------------------

def test_guard_ds(s: Suite, proj: Path) -> None:
    """Design system đã chốt thì prototype phải lắp từ token, không tự bịa.

    Chạy trên dự án smoke — test_lifecycle để lại DESIGN-SYSTEM.md đã điền đủ
    (5 token) và prototype/index.html dùng chúng.
    """
    s.group("3b2. Hook guard_ds (prototype phải theo design system đã chốt)")

    # Nhóm này sửa DESIGN-SYSTEM.md để thử; trả lại nguyên trạng ở cuối, không thì
    # test_repeat chạy sau sẽ đỏ vì lý do chẳng liên quan gì tới nó.
    ds_orig = (proj / "context/DESIGN-SYSTEM.md").read_text(encoding="utf-8")

    def hook(rel: str, content: str) -> subprocess.CompletedProcess:
        payload = json.dumps({"tool_input": {
            "file_path": str(proj / rel), "content": content}})
        return run([PY, "scripts/guard_ds.py"], proj, stdin=payload)

    ok_html = ("<style>:root{--color-bg:#FFFFFF;--color-text:#1A1A1A}"
               "body{background:var(--color-bg);color:var(--color-text)}</style>")
    r = hook("prototype/index.html", ok_html)
    s.check("prototype lắp từ token: cho qua (exit 0)", r.returncode == 0,
            r.stderr[-300:])

    r = hook("prototype/index.html", ok_html + "<style>.b{background:#3B82F6}</style>")
    s.check("mã màu thô ngoài :root: CHẶN (exit 2)", r.returncode == 2,
            f"exit {r.returncode}")
    s.check("stderr chỉ đúng mã màu vi phạm",
            "#3b82f6" in r.stderr.lower() and "MÃ MÀU THÔ" in r.stderr,
            r.stderr[:300])

    r = hook("prototype/index.html", "<style>.b{color:var(--color-accent)}</style>")
    s.check("dùng var(--…) chưa khai ở §2: CHẶN (exit 2)", r.returncode == 2,
            f"exit {r.returncode}")
    s.check("stderr nêu đúng token chưa khai", "--color-accent" in r.stderr,
            r.stderr[:300])

    r = hook("src/app.ts", 'const c = "#3B82F6"')
    s.check("file ngoài prototype/ và DESIGN-SYSTEM.md: cho qua ngay",
            r.returncode == 0, r.stderr[-200:])

    # --- Edit (new_string) soi theo NỘI DUNG SAU-EDIT, không soi fragment rời —
    # fragment rời thiếu ngữ cảnh :root nên từng chặn oan đúng thao tác hợp lệ nhất
    # (đổi giá trị MỘT token theo phản hồi của Authority).
    def hook_edit(rel: str, old: str, new: str) -> subprocess.CompletedProcess:
        payload = json.dumps({"tool_input": {"file_path": str(proj / rel),
                                             "old_string": old, "new_string": new}})
        return run([PY, "scripts/guard_ds.py"], proj, stdin=payload)

    r = hook_edit("prototype/index.html", "--color-bg:#FFFFFF", "--color-bg:#F8F8F8")
    s.check("Edit đổi giá trị token NGAY TRONG :root: cho qua (exit 0)",
            r.returncode == 0, r.stderr[-300:])
    r = hook_edit("prototype/index.html",
                  "body{background:var(--color-bg);color:var(--color-text)}",
                  "body{background:#EEEEEE;color:var(--color-text)}")
    s.check("Edit chèn mã màu thô NGOÀI :root: CHẶN (exit 2)", r.returncode == 2,
            f"exit {r.returncode}")
    r = hook_edit("prototype/index.html", "chuỗi không có trong file", "x")
    s.check("Edit với old_string không khớp file: fail-open (tầng tool sẽ tự báo lỗi)",
            r.returncode == 0, r.stderr[-200:])
    # Chỉ chặn lỗi MỚI: file bẩn sẵn (viết lúc hook chưa có hiệu lực) thì edit
    # không thêm lỗi vẫn đi qua — không thì Edit không sửa dần nổi, lỗi cũ gate báo.
    html_orig = (proj / "prototype/index.html").read_text(encoding="utf-8")
    write(proj / "prototype/index.html",
          html_orig + "<style>.cu{color:#111111}</style>")
    r = hook_edit("prototype/index.html", "<title>prototype</title>", "<title>x</title>")
    s.check("lỗi CŨ trên đĩa không bắt đền edit không liên quan (chỉ chặn lỗi mới)",
            r.returncode == 0, r.stderr[-300:])
    r = hook_edit("prototype/index.html", "<style>.cu{color:#111111}</style>",
                  "<style>.cu{color:#111111}.moi{background:#333333}</style>")
    s.check("file bẩn sẵn nhưng edit THÊM lỗi mới: vẫn CHẶN, chỉ nêu lỗi mới",
            r.returncode == 2 and "#333333" in r.stderr and "#111111" not in r.stderr,
            r.stderr[:300])
    write(proj / "prototype/index.html", html_orig)

    # --- gói token của intake là hợp đồng: không bịa, không lệch giá trị
    dsdir = proj / "intake/design-systems/acme"
    dsdir.mkdir(parents=True, exist_ok=True)
    # Dạng Design Token Format ($value) + khoá metadata ($comment/$type/$breakpoints):
    # parser phải lấy đúng 5 token và KHÔNG đẻ token ma từ chú thích.
    write(dsdir / "tokens.json",
          '{"$comment":"gói mẫu","color":{"$comment":"bảng màu",'
          '"bg":{"$value":"#FFFFFF","$type":"color"},"text":{"$value":"#1A1A1A"},'
          '"text-muted":{"value":"#595959"},"primary":{"$value":"#0B5FFF"},'
          '"on-primary":{"$value":"#FFFFFF"}},"$breakpoints":{"narrow":"768px"}}')
    row = "| `--color-primary` | `%s` | nút |\n"
    r = hook("context/DESIGN-SYSTEM.md", row % "#0B5FFF")
    s.check("token khớp gói intake: cho qua", r.returncode == 0, r.stderr[-300:])
    r = hook("context/DESIGN-SYSTEM.md", row % "#0A5CF0")
    s.check("token lệch giá trị gói intake: CHẶN", r.returncode == 2,
            f"exit {r.returncode}")
    r = hook("context/DESIGN-SYSTEM.md", "| `--color-fancy` | `#123456` | vui |\n")
    s.check("token bịa thêm ngoài gói intake: CHẶN", r.returncode == 2,
            f"exit {r.returncode}")

    # gate.py cũng phải bắt được chiều "bỏ rơi token của gói"
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V XANH khi bảng token khớp đủ gói intake",
            gate(proj, "V") and "dịch trung thành" in out, out[-400:])
    sub(proj / "context/DESIGN-SYSTEM.md",
        "| `--color-text-muted` | `#595959` | chữ phụ |\n", "")
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V ĐỎ khi bỏ rơi một token của gói intake",
            not gate(proj, "V") and "bị bỏ rơi" in out, out[-400:])

    # --- NHIỀU gói design system: từ v1.9 đối chiếu TỪNG gói, không hợp nhất nữa.
    # Bảng §2 chưa có cột `DS` thì không biết dòng nào thuộc gói nào — hook fail-open,
    # gate đỏ và đòi khai. Ca sâu hơn (trùng tên, trộn DS) nằm ở nhóm 3b3.
    write(proj / "context/DESIGN-SYSTEM.md", ds_orig)
    dsdir2 = proj / "intake/design-systems/beta"
    dsdir2.mkdir(parents=True, exist_ok=True)
    write(dsdir2 / "tokens.json", '{"radius":"8px"}')
    r = hook("context/DESIGN-SYSTEM.md", "| `--radius` | `8px` | bo góc |\n")
    s.check("nhiều gói mà §2 chưa có cột DS: hook fail-open (gate là chỗ đòi)",
            r.returncode == 0, r.stderr[-300:])
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V ĐỎ khi nhiều gói mà §2 chưa khai token thuộc gói nào",
            not gate(proj, "V") and "chưa khai thuộc design system nào" in out,
            out[-600:])
    shutil.rmtree(dsdir2, ignore_errors=True)

    write(proj / "context/DESIGN-SYSTEM.md", ds_orig)
    shutil.rmtree(proj / "intake/design-systems/acme", ignore_errors=True)

    # JSON gói hỏng → hook fail-open (gate.py mới là chỗ báo đỏ)
    dsdir.mkdir(parents=True, exist_ok=True)
    write(dsdir / "tokens.json", "{ hỏng")
    r = hook("context/DESIGN-SYSTEM.md", "| `--color-fancy` | `#123456` | vui |\n")
    s.check("gói tokens.json hỏng: hook fail-open (exit 0)", r.returncode == 0,
            "hook an toàn không được chặn nhầm phiên")
    shutil.rmtree(proj / "intake/design-systems/acme", ignore_errors=True)

    # DESIGN-SYSTEM chưa chốt / backend-only → không có gì để mà theo
    write(proj / "context/DESIGN-SYSTEM.md", "KHÔNG CÓ UI — bỏ qua design system\n")
    r = hook("prototype/index.html", "<style>.b{background:#3B82F6}</style>")
    s.check("marker KHÔNG CÓ UI: fail-open (exit 0)", r.returncode == 0)
    # Template khai sẵn TÊN token (giá trị _CHƯA ĐIỀN_) — dự án vừa bootstrap chưa
    # chốt gì thì hook không được chặn; chuẩn "chưa chốt" = còn dấu _CHƯA ĐIỀN_,
    # giống filled() của gate.py.
    write(proj / "context/DESIGN-SYSTEM.md",
          "# DESIGN SYSTEM\n\n## 2. Token\n\n| Token | Giá trị | Dùng cho |\n"
          "|---|---|---|\n| `--color-bg` | _CHƯA ĐIỀN_ | nền |\n")
    r = hook("prototype/index.html", "<style>.b{background:#3B82F6}</style>")
    s.check("DS còn _CHƯA ĐIỀN_ (scaffold sau bootstrap): fail-open (exit 0)",
            r.returncode == 0, f"exit {r.returncode} — chưa chốt thì chưa có gì để theo")

    write(proj / "context/DESIGN-SYSTEM.md", ds_orig)
    s.check("nhóm này trả DESIGN-SYSTEM.md về nguyên trạng cho nhóm sau",
            gate(proj, "V"), "test_repeat chạy tiếp trên chính dự án này")


# --- 3b3. Nhiều design system -----------------------------------------------

def test_multi_ds(s: Suite, proj: Path) -> None:
    """Nhiều gói design system: đối chiếu TỪNG gói, và không cho trộn token giữa gói.

    Bản trước hợp nhất mọi gói vào một từ điển phẳng, nên hai gói cùng khai
    `color.primary` khác giá trị thì §2 chỉ cần một dòng khớp MỘT trong hai là qua
    sạch cả ba phép kiểm — gói còn lại biến mất khỏi nguồn sự thật mà gate vẫn in
    "dịch trung thành". Nhóm này chốt lỗi đó lại.
    """
    s.group("3b3. Nhiều design system (đối chiếu từng gói, cấm trộn token)")

    ds_orig = (proj / "context/DESIGN-SYSTEM.md").read_text(encoding="utf-8")
    arch_orig = (proj / "context/ARCHITECTURE.md").read_text(encoding="utf-8")
    itv_orig = (proj / "context/INTERVIEW.md").read_text(encoding="utf-8")
    html_orig = (proj / "prototype/index.html").read_text(encoding="utf-8")

    def hook(rel: str, content: str) -> subprocess.CompletedProcess:
        payload = json.dumps({"tool_input": {
            "file_path": str(proj / rel), "content": content}})
        return run([PY, "scripts/guard_ds.py"], proj, stdin=payload)

    def gate_out() -> str:
        return run([PY, "scripts/gate.py", "V"], proj).stdout

    # Hai gói TRÙNG TÊN token, khác giá trị — đúng tình huống bản cũ nuốt mất một gói.
    for name in ("acme", "shop"):
        (proj / f"intake/design-systems/{name}").mkdir(parents=True, exist_ok=True)
    write(proj / "intake/design-systems/acme/tokens.json",
          '{"color":{"primary":{"$value":"#0B5FFF"},'
          '"on-primary":{"$value":"#FFFFFF"},'
          '"admin-only":{"$value":"#123456"}}}')
    write(proj / "intake/design-systems/shop/tokens.json",
          '{"color":{"primary":{"$value":"#E11D48"}},"radius":{"$value":"8px"}}')

    def ds_two(rows: str) -> str:
        return ("# DESIGN SYSTEM\n\n## 1. Ba tính từ\n\nGọn · rõ · nhanh\n\n"
                "## 2. Token\n\n| Token | Giá trị | Dùng cho | DS |\n|---|---|---|---|\n"
                + rows +
                "\n## 3. Tương phản\n\n| Cặp | Chữ | Nền | Loại | DS |\n|---|---|---|---|---|\n"
                "| Nút acme | `--color-on-primary` | `--color-primary` | thường | acme |\n"
                "\n## 4. Kho component\n\n| # | Component | Dùng ở màn | Trạng thái | DS |\n"
                "|---|---|---|---|---|\n"
                "| C1 | Nút chính | S1 | mặc định | acme |\n")

    # 1. §2 chưa có cột DS trong khi có hai gói → không biết dòng nào thuộc gói nào.
    write(proj / "context/DESIGN-SYSTEM.md",
          ds_orig.replace("| `--color-primary` | `#0B5FFF` | nút |",
                          "| `--color-primary` | `#0B5FFF` | nút |"))
    out = gate_out()
    s.check("hai gói mà §2 chưa khai token thuộc gói nào: gate V ĐỎ",
            not gate(proj, "V") and "chưa khai thuộc design system nào" in out,
            out[-500:])
    r = hook("context/DESIGN-SYSTEM.md", "| `--color-primary` | `#0B5FFF` | nút |\n")
    s.check("cùng tình huống đó: hook fail-open (không hiểu chắc thì không chặn)",
            r.returncode == 0, r.stderr[-300:])

    # 2. Khai đủ cột DS, đúng giá trị từng gói → dịch trung thành, đối chiếu RIÊNG.
    good = ("| `--color-primary` | `#0B5FFF` | nút | acme |\n"
            "| `--color-on-primary` | `#FFFFFF` | chữ trên nút | acme |\n"
            "| `--color-admin-only` | `#123456` | riêng admin | acme |\n"
            "| `--color-primary` | `#E11D48` | nút | shop |\n"
            "| `--radius` | `8px` | bo góc | shop |\n")
    write(proj / "context/DESIGN-SYSTEM.md", ds_two(good))
    out = gate_out()
    s.check("hai gói trùng tên token thành HAI dòng riêng: fidelity XANH",
            "dịch trung thành" in out and "2 gói, đối chiếu riêng từng gói" in out,
            out[-700:])

    # Gói acme không khai --radius; gán nhầm nó cho acme phải lòi ra là BỊA + BỎ RƠI,
    # trong khi bản hợp nhất cũ thấy --radius có ở "một gói nào đó" là cho qua.
    write(proj / "context/DESIGN-SYSTEM.md",
          ds_two(good.replace("| `--radius` | `8px` | bo góc | shop |",
                              "| `--radius` | `8px` | bo góc | acme |")))
    out = gate_out()
    s.check("token gán nhầm sang gói khác: bắt được cả BỊA lẫn BỎ RƠI",
            "bịa thêm" in out and "--radius [acme]" in out
            and "bị bỏ rơi" in out and "--radius [shop]" in out, out[-700:])

    # 3. Chép nhầm GIÁ TRỊ của gói kia sang — lỗi gốc mà bản hợp nhất cho qua sạch.
    drifted = good.replace("| `--color-primary` | `#E11D48` | nút | shop |",
                           "| `--color-primary` | `#0B5FFF` | nút | shop |")
    write(proj / "context/DESIGN-SYSTEM.md", ds_two(drifted))
    out = gate_out()
    s.check("gói shop mang giá trị của gói acme: gate V ĐỎ vì LỆCH GIÁ TRỊ",
            "lệch giá trị" in out and "[shop]" in out, out[-700:])

    # Hook chỉ chặn lỗi MỚI so với bản trên đĩa — trả file về bản sạch trước đã,
    # không thì lỗi đang nằm sẵn ở đó làm delta rỗng và hook im lặng cho qua.
    write(proj / "context/DESIGN-SYSTEM.md", ds_two(good))
    r = hook("context/DESIGN-SYSTEM.md",
             "| Token | Giá trị | Dùng cho | DS |\n|---|---|---|---|\n"
             "| `--color-primary` | `#0B5FFF` | nút | shop |\n")
    s.check("cùng lỗi đó: hook CHẶN (exit 2)", r.returncode == 2,
            f"exit {r.returncode} — {r.stderr[:200]}")
    s.check("stderr nêu đúng gói bị lệch", "[shop]" in r.stderr, r.stderr[:300])

    # 4. Trộn design system: prototype của experience này mượn token của gói kia.
    sub(proj / "context/ARCHITECTURE.md",
        "| Experience | Persona | Năng lực lộ ra | Vòng | Design system |\n"
        "|---|---|---|---|---|\n| đã điền | | | | — |",
        "| Experience | Persona | Năng lực lộ ra | Vòng | Design system |\n"
        "|---|---|---|---|---|\n"
        "| admin | chủ | quản trị | 1 | acme |\n"
        "| shop | khách | đặt hàng | 1 | shop |")
    arch = (proj / "context/ARCHITECTURE.md").read_text(encoding="utf-8")
    if not s.check("dựng được ánh xạ experience → gói ở ARCHITECTURE §2",
                   "| admin |" in arch and "| acme |" in arch,
                   "bảng template đổi shape → sửa lại phép sub() này"):
        write(proj / "context/ARCHITECTURE.md", arch_orig)
        write(proj / "context/DESIGN-SYSTEM.md", ds_orig)
        return

    r = hook("prototype/shop/index.html",
             "<style>.b{color:var(--color-admin-only)}</style>")
    s.check("experience `shop` mượn token của gói `acme`: hook CHẶN (exit 2)",
            r.returncode == 2 and "TRỘN DESIGN SYSTEM" in r.stderr,
            f"exit {r.returncode} — {r.stderr[:300]}")
    s.check("stderr gọi đúng tên gói chủ của token",
            "--color-admin-only" in r.stderr and "acme" in r.stderr, r.stderr[:300])

    r = hook("prototype/shop/index.html",
             "<style>.b{color:var(--color-primary)}</style>")
    s.check("token cùng tên có ở CẢ HAI gói: `shop` dùng được, cho qua",
            r.returncode == 0, r.stderr[-300:])

    r = hook("prototype/la-hoac/index.html",
             "<style>.b{color:var(--color-admin-only)}</style>")
    s.check("experience không có trong ánh xạ: hook fail-open, gate là backstop",
            r.returncode == 0, r.stderr[-300:])

    # 5. Gate cũng phải thấy việc trộn — cần đường intake để prototype tách theo thư mục.
    write(proj / "context/INTERVIEW.md",
          "NGUỒN: INTAKE — dựng tạm cho phép kiểm multi-DS\n\n" + itv_orig)
    for exp, token in (("admin", "--color-admin-only"), ("shop", "--color-admin-only")):
        (proj / f"prototype/{exp}").mkdir(parents=True, exist_ok=True)
        write(proj / f"prototype/{exp}/index.html",
              f"<style>:root{{}}.b{{color:var({token})}}</style>S1\n")
    out = gate_out()
    s.check("gate V nêu đích danh experience trộn design system",
            "dùng token của design system khác" in out and "(shop)" in out,
            out[-600:])
    s.check("gate KHÔNG báo oan experience dùng đúng gói của mình",
            out.count("dùng token của design system khác") == 1, out[-600:])

    # 6. Thiếu ánh xạ trong khi có nhiều gói → đỏ, vì mọi phép kiểm sau đó sai địa chỉ.
    sub(proj / "context/ARCHITECTURE.md", "| admin | chủ | quản trị | 1 | acme |",
        "| admin | chủ | quản trị | 1 |  |")
    out = gate_out()
    s.check("experience bỏ trống cột Design system khi có nhiều gói: gate V ĐỎ",
            "experience chưa khai design system" in out and "admin" in out, out[-500:])

    # 7. HỒI QUY một design system: bỏ gói thứ hai, bảng không cột DS → như trước.
    shutil.rmtree(proj / "prototype/admin", ignore_errors=True)
    shutil.rmtree(proj / "prototype/shop", ignore_errors=True)
    shutil.rmtree(proj / "prototype/la-hoac", ignore_errors=True)
    shutil.rmtree(proj / "intake/design-systems/acme", ignore_errors=True)
    shutil.rmtree(proj / "intake/design-systems/shop", ignore_errors=True)
    write(proj / "context/INTERVIEW.md", itv_orig)
    write(proj / "context/ARCHITECTURE.md", arch_orig)
    write(proj / "context/DESIGN-SYSTEM.md", ds_orig)
    write(proj / "prototype/index.html", html_orig)
    s.check("một design system, §2 không cột DS: gate V XANH y như trước",
            gate(proj, "V"),
            "đây là ràng buộc cứng của bản 1.9 — sửa multi-DS không được làm chết "
            "đường phỏng vấn và mọi dự án đang chạy")

    # Dự án tạo từ template CŨ: bảng experience ở ARCHITECTURE §2–§3 không hề có cột
    # `Design system`. Chúng không được phải sửa một chữ nào để chạy tiếp trên bản 1.9.
    legacy_arch = arch_orig
    for new, old in (
        ("| Experience | Persona | Năng lực lộ ra | Vòng | Design system |\n"
         "|---|---|---|---|---|",
         "| Experience | Persona | Năng lực lộ ra | Vòng |\n|---|---|---|---|"),
        ("| Experience | Nền tảng | Persona | Vòng | Design system |\n"
         "|---|---|---|---|---|",
         "| Experience | Nền tảng | Persona | Vòng |\n|---|---|---|---|"),
        ("| đã điền | | | | — |", "| đã điền | | | |"),
        ("| — | | | | — |", "| — | | | |"),
    ):
        legacy_arch = legacy_arch.replace(new, old)
    headers = [ln for ln in legacy_arch.splitlines()
               if ln.startswith("| Experience")]
    if s.check("dựng được bảng experience kiểu CŨ để thử",
               len(headers) == 2 and not any("Design system" in h for h in headers),
               str(headers)):
        write(proj / "context/ARCHITECTURE.md", legacy_arch)
        s.check("ARCHITECTURE kiểu CŨ (bảng không có cột Design system): gate V vẫn XANH",
                gate(proj, "V"),
                "dự án đang chạy trên bản 1.8 nâng lên 1.9 không phải sửa tài liệu")
    write(proj / "context/ARCHITECTURE.md", arch_orig)


# --- 3c. Vòng lặp repeat ----------------------------------------------------

def test_repeat(s: Suite, proj: Path) -> None:
    s.group("3c. Vòng lặp — repeat.py đóng vòng 1, mở vòng 2")

    # test_guard kết thúc với STATE ở pha V; chuẩn bị pha R + đánh dấu để kiểm
    # những gì phải GIỮ NGUYÊN qua vòng (không reset gì).
    sub(proj / "STATE.md", "Pha hiện tại : V", "Pha hiện tại : R")
    sub(proj / "STATE.md", "Stack         : (chưa chốt — pha V)", "Stack         : nextjs")
    # repeat chỉ được bỏ tick TRONG §Gate — checkbox nơi khác của STATE phải giữ nguyên
    with (proj / "STATE.md").open("a", encoding="utf-8") as f:
        f.write("\n- [x] mốc thử NGOÀI §Gate — repeat không được trắng dòng này\n")
    # Vá (c): repeat chỉ được bỏ tick TRONG §3 của BC — tick sẵn một mục §3 + cài một
    # dòng tick GIẢ ngoài §3 để chứng minh phạm vi.
    bc = proj / "context/BACKWARD-COMPATIBILITY-CHECKLIST.md"
    s.check("tick sẵn được một mục §3 của BC (fixture còn khớp template)",
            sub(bc, "- [ ] **Sổ hợp đồng §1 cập nhật**",
                "- [x] **Sổ hợp đồng §1 cập nhật**"))
    sub(bc, "## 2. Luật đổi từng loại — additive-first",
        "## 2. Luật đổi từng loại — additive-first\n\n"
        "- [x] mốc thử ngoài §3 (không được bỏ tick)")

    r = run([PY, "scripts/repeat.py", "--go"], proj)
    s.check("repeat --go TỪ CHỐI khi working tree chưa sạch", r.returncode != 0,
            "quay vòng trộn với thay đổi chưa commit là mất dấu — phải chặn")
    run(["git", "add", "-A"], proj)
    run(["git", "-c", "user.email=t@t.t", "-c", "user.name=T", "commit", "-qm", "vòng 1"], proj)

    r = run([PY, "scripts/repeat.py"], proj)
    s.check("repeat dry-run: exit 0, nêu kế hoạch, chưa ghi gì",
            r.returncode == 0 and "--go" in r.stdout
            and not (proj / "context/archive").exists(), r.stdout[-300:])

    def guard_bc(cmd: str):
        return run([PY, "scripts/guard_bc.py"], proj,
                   stdin=json.dumps({"tool_name": "Bash",
                                     "tool_input": {"command": cmd}}))

    s.check("guard_bc: vòng 1 KHÔNG chặn deploy (chưa có legacy)",
            guard_bc("make deploy").returncode == 0)

    iv_before = (proj / "context/INTERVIEW.md").read_text(encoding="utf-8")
    r = run([PY, "scripts/repeat.py", "--go"], proj)
    s.check("repeat --go chạy xong exit 0", r.returncode == 0,
            (r.stderr + r.stdout)[-400:])

    arch = proj / "context/archive/vong-1"
    for f in ("PRD.md", "INTERVIEW.md", "PROTOTYPE.md", "DESIGN-SYSTEM.md",
              "CAPABILITIES-MAP.md", "ROADMAP.md",
              "EXPERIMENTS.md", "BACKWARD-COMPATIBILITY-CHECKLIST.md", "STATE.md"):
        s.check(f"archive vòng 1 có {f}", (arch / f).is_file())
    s.check("archive giữ vết challenge của vòng 1",
            "PASS" in (arch / "STATE.md").read_text(encoding="utf-8"))

    st = (proj / "STATE.md").read_text(encoding="utf-8")
    s.check("STATE: vòng 2 + ngày mở vòng",
            bool(re.search(r"Vòng\s*:\s*2", st)) and "Vòng mở" in st, st[:300])
    s.check("STATE: pha V, ngày D1 — challenge log vòng 1 GIỮ NGUYÊN (không reset)",
            "Pha hiện tại : V" in st and "Ngày          : D1" in st
            and "| PASS |" in st)
    s.check("STATE: giữ lại Stack đã chốt (sửa tại chỗ, không ghi đè)",
            "Stack         : nextjs" in st)
    s.check("STATE: checkbox tick NGOÀI §Gate giữ nguyên (bỏ tick giới hạn đúng §Gate)",
            "- [x] mốc thử NGOÀI §Gate" in st)
    s.check("INTERVIEW ĐÓNG BĂNG — byte-identical, hiện vật vòng 1 (không reset)",
            (proj / "context/INTERVIEW.md").read_text(encoding="utf-8") == iv_before)
    s.check("EXPERIMENTS.md vòng 1 nguyên vẹn — số liệu cũ còn tại chỗ làm insight",
            "2026-08-05" in (proj / "context/EXPERIMENTS.md").read_text(encoding="utf-8"))
    exp2 = proj / "context/EXPERIMENTS-v2.md"
    s.check("tạo sổ mới EXPERIMENTS-v2.md cho vòng 2 (scaffold chưa điền)",
            exp2.is_file() and UNFILLED_MARK in exp2.read_text(encoding="utf-8"))
    pt = (proj / "context/PROTOTYPE.md").read_text(encoding="utf-8")
    s.check("PROTOTYPE: giữ bản đồ màn hình VÀ ngày chốt (tài liệu vòng là chữ ký mới)",
            "| AC-1 | S1 |" in pt and "Chốt bởi Authority: 2026-08-01" in pt)
    s.check("DESIGN-SYSTEM giữ nguyên (tài liệu sống, không reset)",
            "#0B5FFF" in (proj / "context/DESIGN-SYSTEM.md").read_text(encoding="utf-8"))
    pr = (proj / "context/PRODUCTION-READY.md").read_text(encoding="utf-8")
    s.check("PRODUCTION-READY: bỏ tick đúng 6 mục (mỗi vòng), hạ tầng giữ tick",
            pr.count("- [ ]") == 6 and all("(mỗi vòng)" in l for l in pr.splitlines()
                                           if l.startswith("- [ ]")), f"{pr.count('- [ ]')} mục")
    bc_text = bc.read_text(encoding="utf-8")
    s.check("BC: mục §3 đã tick bị trắng lại (vòng mới rà lại)",
            "- [ ] **Sổ hợp đồng §1 cập nhật**" in bc_text)
    s.check("BC: dòng tick ngoài §3 giữ nguyên — bỏ tick giới hạn đúng §3 (vá c)",
            "- [x] mốc thử ngoài §3" in bc_text)

    # Hàng rào theo vòng (thay cho reset): vết vòng 1 không được gánh hộ vòng 2
    s.check("gate V ĐỎ lại sau khi mở vòng", not gate(proj, "V"))
    s.check("gate E ĐỎ lại sau khi mở vòng (sổ v2 trắng)", not gate(proj, "E"))
    s.check("gate P1 ĐỎ lại sau khi mở vòng (mục mỗi vòng)", not gate(proj, "P1"))
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("gate V đếm DECISIONS theo vòng — quyết định vòng 1 không được tính",
            "0 quyết định (từ khi mở vòng)" in out, out[-400:])
    with (proj / "context/DECISIONS.md").open("a", encoding="utf-8") as f:
        f.write("| 2099-01-01 | AC vòng 2 | delta | ít | Có |\n"
                "| 2099-01-01 | giữ legacy AC-1..3 | hợp đồng vòng 1 | không phá | Có |\n")
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("2 quyết định mới của vòng 2 được đếm",
            "có 2 quyết định (từ khi mở vòng)" in out, out[-400:])

    # --- Vòng 2 vào pha V bằng TÀI LIỆU VÒNG (không phỏng vấn)
    loop2 = proj / "intake/loops/l2"
    s.check("repeat --go tạo sẵn intake/loops/l2/", loop2.is_dir())
    s.check("gate V nêu rõ thiếu tài liệu vòng ở intake/loops/l2",
            "intake/loops/l2" in out, out[-400:])
    write(loop2 / "_nhap.md", "nháp nội bộ — không phải tài liệu của Authority\n")
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("file _*.md trong l2/ không được tính — gate vẫn đòi tài liệu vòng",
            "chưa có tài liệu vòng" in out, out[-400:])
    write(loop2 / "delta.md", "")
    s.check("gate V ĐỎ khi tài liệu vòng rỗng", not gate(proj, "V"))
    write(loop2 / "delta.md", "# Vòng 2\n\n## Thêm mới\n\n{{Y_MUON_THEM}}\n")
    s.check("gate V ĐỎ khi tài liệu vòng còn {{placeholder}} (copy template)",
            not gate(proj, "V"))
    write(loop2 / "delta.md",
          "# Vòng 2 — nhắc lịch\n\n## Thêm mới\n\nNhắc khách qua Zalo trước hẹn 1 ngày"
          " — vòng 1 có 3 khách quên hẹn/tuần (EXPERIMENTS.md).\n\n"
          "## Bỏ đi\n\nKhông có.\n\n## Legacy được phép phá\n\nKhông phá gì.\n")
    # Tài liệu vòng đủ — còn thiếu challenge CỦA VÒNG: dòng V PASS vòng 1
    # (2026-08-01) nằm trước ngày Vòng mở nên bị lọc, không được tính.
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("challenge V vòng 1 không gánh hộ vòng 2 (lọc theo ngày Vòng mở)",
            "chưa có challenge pha V" in out, out[-400:])
    with (proj / "STATE.md").open("a", encoding="utf-8") as f:
        f.write("| 2099-01-02 | V | Nhắc lịch đụng gì luồng đặt lịch vòng 1? | PASS |"
                " delta.md: không phá |\n")
    s.check("gate V vòng 2 XANH: tài liệu vòng + 2 quyết định + challenge mới",
            gate(proj, "V"))
    out = run([PY, "scripts/gate.py", "E"], proj).stdout
    s.check("gate E vòng 2 đọc sổ EXPERIMENTS-v2.md", "EXPERIMENTS-v2.md" in out,
            out[-300:])

    # --- Hàng rào đếm theo vòng phải FAIL-CLOSED khi vòng không mở bằng repeat.py:
    # bump số vòng bằng tay / STATE mất `Vòng mở` thì vết vòng cũ không được đếm.
    st_ok = (proj / "STATE.md").read_text(encoding="utf-8")
    sub(proj / "STATE.md", "Vòng          : 2", "Vòng          : 3")
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("bump vòng bằng tay (không có mốc (vòng 3)): gate V ĐỎ, nêu rõ thiếu mốc",
            not gate(proj, "V") and "(vòng 3)" in out, out[-400:])
    write(proj / "STATE.md", st_ok)
    write(proj / "STATE.md", re.sub(r"^Vòng mở.*\n", "", st_ok, flags=re.MULTILINE))
    out = run([PY, "scripts/gate.py", "V"], proj).stdout
    s.check("vòng ≥2 mà STATE thiếu `Vòng mở`: gate V ĐỎ (fail-closed)",
            not gate(proj, "V") and "Vòng mở" in out, out[-400:])
    write(proj / "STATE.md", st_ok)

    r = run([PY, "scripts/repeat.py", "--go"], proj)
    s.check("repeat --go lần hai bị chặn (không đóng trùng vòng)", r.returncode != 0)
    r = run([PY, "scripts/guard_ask.py"], proj, stdin="{}")
    s.check("pha V vòng 2: guard_ask cho hỏi Authority lại (exit 0)", r.returncode == 0)

    # --- tương thích ngược: gate P1 đếm + hook guard_bc chặn deploy
    out = run([PY, "scripts/gate.py", "P1"], proj).stdout
    s.check("gate P1 vòng 2 có mục tương thích ngược ĐỎ",
            "tương thích ngược" in out and "chưa rà" in out, out[-400:])
    r = guard_bc("make deploy")
    s.check("guard_bc: vòng 2 CHẶN deploy khi checklist §3 chưa rà (exit 2)",
            r.returncode == 2 and "tương thích ngược" in r.stderr, f"exit {r.returncode}")
    s.check("guard_bc: `fly deploy` (CLI hiện hành của Fly.io) cũng bị chặn",
            guard_bc("fly deploy").returncode == 2,
            "regex `flyctl?` cũ không khớp `fly deploy` — đường lách quen nhất")
    s.check("guard_bc: `flyctl deploy` bị chặn", guard_bc("flyctl deploy").returncode == 2)
    # Cờ/biến đứng giữa `make` và `deploy` không phải đường thoát — quét theo token
    for cmd in ("make -j4 deploy", "make --directory=srcroot/boundaries/x deploy",
                "make -Csrcroot/boundaries/x deploy", "make ENV=prod deploy",
                "fly --app myapp deploy"):
        s.check(f"guard_bc: `{cmd}` bị chặn", guard_bc(cmd).returncode == 2)
    s.check("guard_bc: `make deploy-docs` KHÔNG bị coi là deploy",
            guard_bc("make deploy-docs").returncode == 0)
    s.check("guard_bc: lệnh thường vẫn qua (chỉ soi lệnh deploy)",
            guard_bc("npm run build && git status").returncode == 0)
    s.check("guard_bc: vercel dev KHÔNG bị coi là deploy",
            guard_bc("vercel dev").returncode == 0)
    bc = proj / "context/BACKWARD-COMPATIBILITY-CHECKLIST.md"
    sub(bc, "- [ ]", "- [x]")
    s.check("guard_bc: tick đủ §3 thì deploy được (exit 0)",
            guard_bc("make deploy").returncode == 0)
    out = run([PY, "scripts/gate.py", "P1"], proj).stdout
    s.check("gate P1: mục tương thích ngược XANH sau khi rà đủ",
            "checklist §3 xanh" in out, out[-400:])
    # Checkbox NGOÀI §3 (ghi chú ở §4) không được chặn deploy / làm gate đỏ —
    # guard_bc + gate P1 đếm đúng §3, khớp phạm vi repeat.py bỏ tick.
    sub(bc, "## 4. Đã cố tình bỏ qua",
        "## 4. Đã cố tình bỏ qua\n\n- [ ] ghi chú riêng ngoài §3")
    s.check("guard_bc: checkbox chưa tick NGOÀI §3 không chặn deploy",
            guard_bc("make deploy").returncode == 0)
    out = run([PY, "scripts/gate.py", "P1"], proj).stdout
    s.check("gate P1: checkbox ngoài §3 không làm mục tương thích ngược đỏ",
            "checklist §3 xanh" in out, out[-400:])
    sub(bc, "\n\n- [ ] ghi chú riêng ngoài §3", "", 1)
    # "## 30" không phải "§ 3" — regex đầu-heading phải chặn khớp tiền tố số
    sub(bc, "## 4. Đã cố tình bỏ qua",
        "## 30. Ghi chú tạm\n\n- [ ] mục ba mươi\n\n## 4. Đã cố tình bỏ qua")
    s.check("guard_bc: '## 30' không bị nhận nhầm là §3 (checkbox trong đó không chặn)",
            guard_bc("make deploy").returncode == 0)
    sub(bc, "## 30. Ghi chú tạm\n\n- [ ] mục ba mươi\n\n## 4. Đã cố tình bỏ qua",
        "## 4. Đã cố tình bỏ qua", 1)
    # STATE hỏng → fail-open, không chặn nhầm phiên
    st_bak = (proj / "STATE.md").read_text(encoding="utf-8")
    write(proj / "STATE.md", "hỏng\n")
    sub(bc, "- [x]", "- [ ]")
    s.check("guard_bc: STATE.md hỏng → fail-open (exit 0)",
            guard_bc("make deploy").returncode == 0)
    write(proj / "STATE.md", st_bak)
    sub(bc, "- [ ]", "- [x]")


# --- 3d. Vệ sinh tài liệu ---------------------------------------------------

def test_compact(s: Suite, proj: Path) -> None:
    """compact.py CHỈ ĐỌC: nó chỉ được nói, không được sửa.

    Chạy sau test_repeat nên dự án đã ở vòng 2 và DECISIONS.md đã có mốc `(vòng 2)`.
    Đẩy lên vòng 3 để phần A có ranh giới `(vòng N-1)` mà cắt.
    """
    s.group("3d. compact.py — báo cáo vệ sinh tài liệu, không tự ghi")

    src = (SRC / "scripts/compact.py").read_text(encoding="utf-8")
    for api in ("write_text(", ".unlink(", ".mkdir(", "shutil.", 'open(', "os.remove"):
        if not s.check(f"compact.py không dùng {api} — chỉ đọc theo CẤU TRÚC",
                       api not in src,
                       "đọc bằng read_text là đủ; có API ghi trong file là mất bảo chứng"):
            break

    def snapshot() -> dict[str, bytes]:
        out = {}
        for p in sorted((proj / "context").rglob("*")):
            if p.is_file():
                out[p.relative_to(proj).as_posix()] = p.read_bytes()
        out["STATE.md"] = (proj / "STATE.md").read_bytes()
        return out

    before = snapshot()
    r = run([PY, "scripts/compact.py"], proj)
    s.check("chạy được, exit 0 (báo cáo chứ không phải gate)", r.returncode == 0,
            (r.stderr + r.stdout)[-300:])
    s.check("không sửa một byte nào trong context/ và STATE.md", snapshot() == before,
            "chỉ cần ghi nhầm một lần trên sổ append-only là mất vĩnh viễn")

    # Phần C phải in ra KỂ CẢ khi không có rác — đây là thứ làm việc dọn tay an toàn.
    s.check("luôn in dòng neo: quyết định chốt stack",
            "dòng chốt stack" in r.stdout and "đỏ vĩnh viễn" in r.stdout,
            r.stdout[-500:])
    s.check("luôn cảnh báo mẹo gấp bằng <!-- -->",
            "KHÔNG gấp bằng cách bọc <!-- -->" in r.stdout, r.stdout[-500:])
    s.check("luôn liệt kê tiêu đề đang là mỏ neo regex",
            "## 1. Kế hoạch vòng" in r.stdout and "## Số liệu theo ngày" in r.stdout,
            r.stdout[-500:])

    # --- gieo rác rồi xem báo cáo có gọi đúng tên không
    sub(proj / "STATE.md", "Vòng          : 2", "Vòng          : 3")
    with (proj / "context/DECISIONS.md").open("a", encoding="utf-8") as f:
        f.write("| 2026-08-02 | Quyết định vòng 1 đã hết hiệu lực | cũ | — | Có |\n")
    # mốc (vòng 2) do repeat.py ghi nằm DƯỚI dòng trên → dòng trên là ứng viên gấp
    dec = (proj / "context/DECISIONS.md").read_text(encoding="utf-8")
    lines = [ln for ln in dec.splitlines() if ln.strip()]
    mark = next((i for i, ln in enumerate(lines) if ln.startswith("| (vòng 2)")), None)
    if mark is not None:
        lines.insert(mark, "| 2026-08-02 | Quyết định vòng cũ | cũ | — | Có |")
        write(proj / "context/DECISIONS.md", "\n".join(lines) + "\n")

    ds = proj / "context/DESIGN-SYSTEM.md"
    with ds.open("a", encoding="utf-8") as f:
        f.write("| C9 | Khối ma | S9 | mặc định |\n")
    with (proj / "context/PRD.md").open("a", encoding="utf-8") as f:
        f.write(f"\n<!-- rác thử -->\nGhi chú: {UNFILLED_MARK}\n")

    before = snapshot()
    r = run([PY, "scripts/compact.py"], proj)
    s.check("vẫn không sửa gì kể cả khi có rác", snapshot() == before)
    s.check("gọi tên dòng DECISIONS nằm trên mốc `(vòng 2)`",
            "DECISIONS.md" in r.stdout and "nằm TRÊN mốc" in r.stdout, r.stdout[:1500])
    s.check("gọi tên component trỏ màn không còn ở PROTOTYPE §1",
            "S9" in r.stdout, r.stdout[:1500])
    s.check("gọi tên file còn dấu chưa điền",
            "PRD.md" in r.stdout and UNFILLED_MARK in r.stdout, r.stdout[:1500])
    s.check("đích gấp là archive/ledger/, KHÔNG phải archive/vong-N/",
            "archive/ledger/" in r.stdout and "archive/vong-" not in r.stdout,
            "vong-N/ kiêm cờ 'vòng đã đóng' của repeat.py — đổ thêm file vào là làm bẩn cờ")

    # gate.py nhắc chạy compact từ vòng 3, và KHÔNG được đổi kết quả gate
    out = run([PY, "scripts/gate.py", "I"], proj)
    s.check("gate nhắc chạy compact.py từ vòng ≥3",
            "compact.py" in out.stdout, out.stdout[-400:])


# --- 4. Cấu hình ------------------------------------------------------------

def test_config(s: Suite, proj: Path) -> None:
    s.group("4. Cấu hình: permission · agent · skill · gitignore")

    perms = json.loads((proj / ".claude/settings.json").read_text(encoding="utf-8"))
    p = perms["permissions"]
    s.check("Edit/Write/Bash để TRẦN (tên tool trần = allow toàn bộ)",
            "Edit" in p["allow"] and "Write" in p["allow"] and "Bash" in p["allow"],
            "liệt kê prefix lệnh đã được thực chiến chứng minh là thua — xem VIPER.md §3c")
    s.check("mcp__browser được allow (dogfood không prompt, subagent không bị từ chối im lặng)",
            "mcp__browser" in p["allow"])
    s.check("defaultMode = acceptEdits", p.get("defaultMode") == "acceptEdits")
    s.check("enableAllProjectMcpServers bật (duyệt sẵn server .mcp.json)",
            perms.get("enableAllProjectMcpServers") is True)
    bad = [r for r in p["allow"] + p["ask"] + p["deny"]
           if re.match(r"^(Write|Glob|NotebookEdit|MultiEdit)\(", r)]
    s.check("không có rule path cho tool không được kiểm", not bad, str(bad))
    s.check("make deploy nằm ở 'ask' (hành động hướng ra ngoài)",
            any("make deploy" in r for r in p["ask"]))
    s.check("git push nằm ở 'ask' — ask xét TRƯỚC allow nên vẫn dừng dù Bash trần",
            any(r.startswith("Bash(git push") for r in p["ask"]))
    s.check(".env bị deny đọc", any(r == "Read(.env)" for r in p["deny"]))

    hooks = perms.get("hooks", {}).get("SessionStart", [])
    s.check("có hook SessionStart matcher 'compact'",
            any(h.get("matcher") == "compact" for h in hooks))
    s.check("hook dùng exec form (args) cho đường dẫn",
            all("args" in hh for h in hooks for hh in h.get("hooks", [])))
    pre = perms.get("hooks", {}).get("PreToolUse", [])
    s.check("có hook PreToolUse matcher 'AskUserQuestion' (guard_ask)",
            any(h.get("matcher") == "AskUserQuestion" for h in pre))
    s.check("có hook PreToolUse matcher 'Bash' (guard_bc — chặn deploy khi nợ tương thích)",
            any(h.get("matcher") == "Bash" for h in pre))
    s.check("có hook PreToolUse matcher 'Write|Edit|MultiEdit' (guard_ds — prototype "
            "phải theo design system)",
            any(h.get("matcher") == "Write|Edit|MultiEdit" for h in pre))
    s.check("hook PreToolUse dùng exec form (args)",
            bool(pre) and all("args" in hh for h in pre for hh in h.get("hooks", [])))
    # Hook trỏ tới script không tồn tại thì im lặng không chạy — bug khó thấy nhất.
    hook_scripts = [Path(a).name for h in hooks + pre for hh in h.get("hooks", [])
                    for a in hh.get("args", [])]
    s.check("mọi script hook được khai đều có thật trong scripts/",
            all((proj / "scripts" / n).is_file() for n in hook_scripts),
            ", ".join(n for n in hook_scripts if not (proj / "scripts" / n).is_file()))

    agents = sorted((proj / ".claude/agents").glob("*.md"))
    s.check("có đủ 9 agent", len(agents) == 9, str(len(agents)))
    for f in agents:
        d = parse_frontmatter(f.read_text(encoding="utf-8"))
        if not s.check(f"{f.stem}: frontmatter parse được", bool(d and d.get("name"))):
            continue
        s.check(f"{f.stem}: không ghi được file dự án",
                "Write" not in (d.get("tools") or "") or f.stem == "viper-test-writer",
                "chỉ viper-test-writer được ghi (file test)")
        if f.stem.startswith("viper-user-"):
            s.check(f"{f.stem}: dùng disallowedTools (giữ MCP cho trình duyệt)",
                    "Write" in (d.get("disallowedTools") or ""),
                    "dùng tools: sẽ cắt sạch MCP → mất tool browser_*")
            srv = (d.get("mcpServers") or {}).get("browser", {})
            s.check(f"{f.stem}: khai inline trình duyệt riêng",
                    srv.get("command") == "npm" and "@playwright/mcp@latest" in srv.get("args", []),
                    "inline mới có browser riêng → các vai trong cùng một đợt chạy "
                    "song song không giẫm chân")

    skills = sorted(x.parent.name for x in (proj / ".claude/skills").rglob("SKILL.md"))
    s.check("có 9 skill kể cả viper-browse", len(skills) == 9 and "viper-browse" in skills,
            str(skills))

    # tham chiếu chéo trong tài liệu phải tồn tại thật
    cmds = {x.stem for x in (proj / ".claude/commands").glob("*.md")}
    names = {x.stem for x in agents} | set(skills) | cmds
    dangling = set()
    for f in proj.rglob("*.md"):
        if ".git" in f.parts:
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        for ref in re.findall(r"/(viper-[a-z-]+)", t):
            if ref not in cmds:
                dangling.add(f"/{ref} ({f.name})")
        for ref in re.findall(r"`(viper-user-[a-z]+|viper-bug-hunter|viper-reviewer"
                              r"|viper-test-writer|stack-[a-z-]+|addon-graphql"
                              r"|shared-production-ready|viper-browse)`", t):
            if ref not in names:
                dangling.add(f"{ref} ({f.name})")
    s.check("mọi tham chiếu command/agent/skill đều tồn tại", not dangling, str(dangling))

    # Mỗi lệnh pha phải bắt cập nhật `Pha hiện tại` — hook guard_ask đọc dòng này;
    # thiếu chỉ dẫn là STATE kẹt ở V và luật #2 mất hiệu lực máy (lỗ thực chiến số 1).
    for cmd_name, ph in (("viper-implement", "I"), ("viper-polish", "P1"),
                         ("viper-publish", "P2"), ("viper-evaluate", "E"),
                         ("viper-repeat", "R")):
        cmd_text = (proj / f".claude/commands/{cmd_name}.md").read_text(encoding="utf-8")
        s.check(f"{cmd_name} bắt cập nhật `Pha hiện tại : {ph}`",
                f"Pha hiện tại : {ph}" in cmd_text)
    s.check("không còn tham chiếu gstack /browse",
            not any("/browse" in f.read_text(encoding="utf-8", errors="ignore")
                    for f in proj.rglob("*.md") if ".git" not in f.parts))

    # --- /viper-dogfood: 6 vai, HAI ĐỢT, tối đa 3 vai một đợt.
    # Trình duyệt riêng cho từng vai không cứu được việc DB dùng chung: thả cả 6 cùng
    # lúc thì vai ghi dữ liệu đè lên cảnh vai khác, và trạng thái rỗng chết ngay khi
    # có bản ghi đầu tiên. Luật này sống trong văn bản lệnh nên phải kiểm bằng văn bản.
    dog = (proj / ".claude/commands/viper-dogfood.md").read_text(encoding="utf-8")
    roles = ["viper-user-newbie", "viper-user-rushed", "viper-user-breaker",
             "viper-user-mobile", "viper-user-edge", "viper-user-picky"]
    s.check("viper-dogfood gọi đủ 6 vai",
            all(x in dog for x in roles),
            str([x for x in roles if x not in dog]))
    s.check("viper-dogfood ràng 'tối đa 3 vai một đợt'",
            "tối đa 3 vai" in dog and "HAI ĐỢT" in dog)
    d1 = dog.split("Đợt 2")[0]
    s.check("đợt 1 là nhóm cần DB SẠCH (edge · newbie · picky)",
            all(x in d1 for x in ("viper-user-edge", "viper-user-newbie",
                                  "viper-user-picky")),
            "trạng thái rỗng phải đo TRƯỚC khi vai nào ghi bản ghi đầu tiên")
    s.check("vai ghi/phá KHÔNG lọt vào đợt 1",
            "viper-user-breaker" not in d1 and "viper-user-rushed" not in d1)
    s.check("bắt seed lại giữa hai đợt", "seed lại" in dog and "deployment/local/" in dog)
    s.check("khuôn báo cáo có dòng Design system",
            "Design system:" in dog and "trộn DS" in dog)
    s.check("bảng phân loại phát hiện có dòng trộn design system",
            "Trộn design system" in dog)
    picky = (proj / ".claude/agents/viper-user-picky.md").read_text(encoding="utf-8")
    s.check("vai picky đòi SỐ ĐO chứ không đòi cảm nhận",
            "getComputedStyle" in picky and "computed style" in picky,
            "báo 'trông hơi lệch tông' thì không phải phát hiện — phải có giá trị thật")
    s.check("vai picky nhận đúng MỘT experience mỗi lượt",
            "một experience" in picky.lower(),
            "trộn hai bảng token vào một lượt là mất nghĩa của chữ 'màu lạ'")

    # gitignore — KHÔNG đụng deployment/.env.example, để nó không hiện ra dạng "đã sửa"
    for f in (".env", ".env.production", ".env.staging"):
        (proj / f).write_text("X=1\n", encoding="utf-8")
    (proj / ".playwright-mcp").mkdir(exist_ok=True)
    (proj / ".playwright-mcp/p.yml").write_text("x\n", encoding="utf-8")

    # so khớp ĐÚNG đường dẫn, không phải chuỗi con: ".env" nằm trong ".env.example"
    st = run(["git", "status", "--porcelain", "-uall"], proj).stdout
    paths = {l[3:].strip() for l in st.splitlines() if len(l) > 3}
    for f in (".env", ".env.production", ".env.staging", ".playwright-mcp", ".viper"):
        hit = [p for p in paths if p == f or p.startswith(f + "/")]
        s.check(f"{f} bị chặn khỏi git", not hit, str(hit))
    s.check("deployment/.env.example VẪN được commit",
            "deployment/.env.example" in run(["git", "ls-files"], proj).stdout.splitlines())
    # .env thật của local nằm SÂU trong deployment/local/ — mẫu không có dấu / nên
    # phải khớp ở mọi cấp; đây là chỗ dễ hỏng nhất khi đổi bố cục thư mục.
    write(proj / "deployment/local/.env", "DATABASE_URL=postgres://that/khong-duoc-commit\n")
    st2 = run(["git", "status", "--porcelain", "-uall"], proj).stdout
    s.check("deployment/local/.env bị chặn khỏi git",
            "deployment/local/.env" not in st2, st2[-200:])
    (proj / "deployment/local/.env").unlink()


# --- 5. Trình duyệt (tuỳ chọn, cần mạng) ------------------------------------

def test_browser(s: Suite) -> None:
    s.group("5. Trình duyệt Playwright MCP (--browser)")
    if shutil.which("npm") is None:
        s.check("có npm", False, "cần Node.js để dogfood")
        return
    probe = (
        'const {spawn}=require("child_process");'
        'const p=spawn("npm",["exec","-y","--","@playwright/mcp@latest","--isolated","--headless"],'
        '{stdio:["pipe","pipe","ignore"]});let b="";'
        'p.stdout.on("data",d=>{b+=d;let i;while((i=b.indexOf("\\n"))>=0){const l=b.slice(0,i);b=b.slice(i+1);'
        'if(!l.trim())continue;let m;try{m=JSON.parse(l)}catch{continue}'
        'if(m.id===1){p.stdin.write(JSON.stringify({jsonrpc:"2.0",id:2,method:"tools/list"})+"\\n")}'
        'if(m.id===2){console.log(m.result.tools.length);p.kill();process.exit(0)}}});'
        'p.stdin.write(JSON.stringify({jsonrpc:"2.0",id:1,method:"initialize",params:{protocolVersion:"2024-11-05",'
        'capabilities:{},clientInfo:{name:"t",version:"1"}}})+"\\n");'
        'setTimeout(()=>process.exit(1),240000);'
    )
    try:
        r = subprocess.run(["node", "-e", probe], capture_output=True, text=True, timeout=300)
        n = int((r.stdout or "0").strip() or 0)
    except Exception as e:
        s.check("Playwright MCP lên được", False, str(e))
        return
    s.check("Playwright MCP lên được và có tool browser_*", n >= 20, f"{n} tool")


def main() -> int:
    s = Suite()
    print(f"{BOLD}VIPER selftest{RESET}  {GREY}template: {SRC}{RESET}")
    with tempfile.TemporaryDirectory(prefix="viper-selftest-") as td:
        proj = test_bootstrap(s, Path(td))
        if proj:
            test_lifecycle(s, proj)
            test_intake(s, Path(td))
            test_hook(s, proj)
            test_guard(s, proj)
            test_guard_ds(s, proj)
            test_multi_ds(s, proj)
            test_repeat(s, proj)
            test_compact(s, proj)
            test_config(s, proj)
        else:
            print(f"{RED}bootstrap hỏng — bỏ qua các nhóm sau{RESET}")
    if "--browser" in sys.argv:
        test_browser(s)
    else:
        print(f"\n{GREY}(bỏ qua kiểm trình duyệt — thêm --browser để chạy, cần mạng){RESET}")
    return s.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
