#!/usr/bin/env python3
"""Sinh hướng dẫn và skill Codex từ nguồn Claude; --check chỉ kiểm độ khớp."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent

def convert(text):
    text = text.replace('.claude/skills/', '.agents/skills/')
    text = text.replace('.claude/commands/', '.agents/skills/')
    text = re.sub(r'(?<![\w./-])/viper-', '$viper-', text)
    return text.replace('AskUserQuestion', 'request_user_input')

note = '''> Bản sinh từ `CLAUDE.md` bằng `python3 scripts/gen_codex.py`; sửa nguồn rồi sinh lại.
>
> **Tích hợp Codex:** `.claude/settings.json` và `.mcp.json` là cấu hình Claude,
> không phải bằng chứng hook hoặc trình duyệt đã hoạt động trong Codex.
> Bản mẫu này chưa nối hook/MCP tự động cho Codex. Dùng công cụ tương ứng thực sự
> có trong phiên; không giả định tên tool hoặc khả năng chạy subagent giống Claude.
> Nếu thiếu trình duyệt/subagent cần cho dogfood, ghi rõ phần chưa kiểm chứng.
> Các guard vẫn phải được tôn trọng theo hướng dẫn; không báo gate hoặc dogfood đạt khi chưa chạy.

'''
text = convert((ROOT / 'CLAUDE.md').read_text()).replace('— CLAUDE.md', '— AGENTS.md', 1)
outputs = {ROOT / 'AGENTS.md': note + text}
for source in sorted((ROOT / '.claude/skills').glob('*/SKILL.md')):
    outputs[ROOT / '.agents/skills' / source.parent.name / 'SKILL.md'] = convert(source.read_text())
for source in sorted((ROOT / '.claude/commands').glob('viper-*.md')):
    text = source.read_text()
    if not text.startswith('---\n'):
        raise SystemExit(f'Thiếu frontmatter: {source}')
    text = text.replace('---\n', f'---\nname: {source.stem}\n', 1)
    outputs[ROOT / '.agents/skills' / source.stem / 'SKILL.md'] = convert(text)
failed = []
for path, text in outputs.items():
    if path.name == 'SKILL.md':
        parts = text.split('---', 2)
        if len(parts) == 3:
            parts[1] = '\n'.join(line if line.strip() in ('description: >', 'description: >-', 'description: |', 'description: |-') else line.replace('<', '‹').replace('>', '›') for line in parts[1].split('\n'))
            text = '---'.join(parts)
    if '--check' in sys.argv:
        if not path.exists() or path.read_text() != text:
            failed.append(str(path.relative_to(ROOT)))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
if failed:
    raise SystemExit('Cần sinh lại: ' + ', '.join(failed))
print(f'Codex: {len(outputs)} tệp ' + ('khớp nguồn.' if '--check' in sys.argv else 'đã sinh.'))
