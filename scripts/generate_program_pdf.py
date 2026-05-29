from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

LINES_PER_PAGE = 50
TOTAL_PAGES = 60
NEEDED = LINES_PER_PAGE * TOTAL_PAGES
MAX_LEFT_PATH_LEN = 30
ZH_FONT_NAME = "ZhFont"
ZH_FONT_FILE = Path(r"C:\Windows\Fonts\simhei.ttf")
INCLUDE_EXTS = {".vue", ".js", ".ts", ".json"}
EXCLUDE_DIRS = {
    "uni_modules",
    "unpackage",
    ".hbuilderx",
    "software-copyright",
    "node_modules",
    ".git",
    ".cursor",
    "dump",
}

_cfg: "RunConfig | None" = None


@dataclass(frozen=True)
class RunConfig:
    project_root: Path
    output_dir: Path
    project_name: str

    @property
    def total_pages(self) -> int:
        return TOTAL_PAGES

    @property
    def needed(self) -> int:
        return NEEDED

    @property
    def header(self) -> str:
        return f"{self.project_name}-源程序"

    @property
    def md_path(self) -> Path:
        return self.output_dir / "程序鉴别材料.md"

    @property
    def html_path(self) -> Path:
        return self.output_dir / "code-pages-60.html"

    @property
    def pdf_path(self) -> Path:
        return self.output_dir / "程序鉴别材料.pdf"


def cfg() -> RunConfig:
    if _cfg is None:
        raise RuntimeError("RunConfig not initialized; call main() first.")
    return _cfg


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate 60-page program identification materials (md/html/pdf)."
    )
    p.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Target repository root (scanned for source files).",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output folder (default: <project-root>/software-copyright).",
    )
    p.add_argument(
        "--project-name",
        default="PROJECT_NAME",
        help="Software full name for PDF header (must match 基本信息).",
    )
    return p.parse_args()


def build_config(args: argparse.Namespace) -> RunConfig:
    project_root = args.project_root.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else project_root / "software-copyright"
    )
    return RunConfig(
        project_root=project_root,
        output_dir=output_dir,
        project_name=args.project_name.strip(),
    )


def name_replacements() -> tuple[tuple[str, str], ...]:
    if cfg().project_name == "PROJECT_NAME":
        return (
            ("艾宾浩斯背诗工具", "PROJECT_NAME"),
            ("关于艾宾浩斯背诗工具", "关于PROJECT_NAME"),
            ("艾宾浩斯背诗笔记系统", "PROJECT_NAME"),
            ("古诗词智能背诵系统", "PROJECT_NAME"),
            ("ILovePoems", "PROJECT_NAME"),
        )
    return ()


def clean_line(text: str) -> str:
    text = text.replace("\t", "    ").replace("\uFFFD", " ")
    text = "".join(ch if (ch >= " " or ch in "\n\r") else " " for ch in text)
    for old, new in name_replacements():
        text = text.replace(old, new)
    return text


def strip_inline_double_slash(line: str) -> str:
    out: list[str] = []
    in_single = False
    in_double = False
    escape = False
    i = 0
    while i < len(line):
        ch = line[i]
        if escape:
            out.append(ch)
            escape = False
            i += 1
            continue
        if ch == "\\":
            out.append(ch)
            escape = True
            i += 1
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            out.append(ch)
            i += 1
            continue
        if (
            not in_single
            and not in_double
            and ch == "/"
            and i + 1 < len(line)
            and line[i + 1] == "/"
        ):
            break
        out.append(ch)
        i += 1
    return "".join(out).rstrip()


def strip_comments(rel: str, lines: list[str]) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    in_c_block = False
    in_html_block = False

    for idx, raw in enumerate(lines, start=1):
        line = raw
        working = []
        i = 0
        while i < len(line):
            if in_c_block:
                end = line.find("*/", i)
                if end == -1:
                    i = len(line)
                    break
                in_c_block = False
                i = end + 2
                continue
            if in_html_block:
                end = line.find("-->", i)
                if end == -1:
                    i = len(line)
                    break
                in_html_block = False
                i = end + 3
                continue
            if line.startswith("/*", i):
                in_c_block = True
                i += 2
                continue
            if line.startswith("<!--", i):
                in_html_block = True
                i += 4
                continue
            working.append(line[i])
            i += 1

        candidate = "".join(working)
        stripped = candidate.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("//"):
            continue

        candidate = strip_inline_double_slash(candidate)
        if not candidate.strip():
            continue

        out.append((idx, candidate))

    return out


def shorten_left_path(path: str, max_len: int = MAX_LEFT_PATH_LEN) -> str:
    if len(path) <= max_len:
        return path
    return "…" + path[-(max_len - 1) :]


def collect_raw_code_lines() -> list[str]:
    root = cfg().project_root
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in INCLUDE_EXTS:
            continue
        parts = set(p.relative_to(root).parts)
        if parts & EXCLUDE_DIRS:
            continue
        files.append(p)
    files.sort(key=lambda x: str(x).lower())

    rows: list[str] = []
    for f in files:
        rel = f.relative_to(root).as_posix()
        raw_lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        for idx, line in strip_comments(rel, raw_lines):
            rows.append(f"{rel}:{idx:04d}:{line}")
    return rows


def format_display_lines(raw_rows: list[str]) -> list[str]:
    out: list[str] = []
    for row in raw_rows:
        parts = row.split(":", 2)
        if len(parts) != 3:
            out.append(clean_line(row))
            continue
        left, line_no, code = parts
        left = clean_line(left)
        filename = left.rsplit("/", 1)[-1]
        if line_no == "0001":
            parent = left.rsplit("/", 1)[0] if "/" in left else left
            out.append(f"模块:{parent}")
        left_display = shorten_left_path(filename)
        out.append(f"{left_display}:{clean_line(line_no)}:  {clean_line(code)}")
    return out


def build_fixed_60_lines() -> list[str]:
    c = cfg()
    raw = collect_raw_code_lines()
    if len(raw) < c.needed:
        raise ValueError(f"Not enough raw code lines: {len(raw)} < {c.needed}")
    return format_display_lines(raw[: c.needed])


def with_page_line_prefix(row: str, line_index_in_page: int) -> str:
    return f"{line_index_in_page:02d}   {row}"


def paginate_by_code_lines(display_lines: list[str]) -> list[list[str]]:
    pages: list[list[str]] = []
    cur: list[str] = []
    code_count = 0
    for row in display_lines:
        is_module = row.startswith("模块:")
        if code_count == LINES_PER_PAGE:
            pages.append(cur)
            cur = []
            code_count = 0
        if is_module:
            cur.append(row)
        else:
            code_count += 1
            cur.append(with_page_line_prefix(row, code_count))
    if cur:
        pages.append(cur)
    if len(pages) != TOTAL_PAGES:
        raise ValueError(
            f"Unexpected page count after pagination: {len(pages)} != {TOTAL_PAGES}"
        )
    return pages


def write_markdown(display_lines: list[str]) -> None:
    c = cfg()
    pages = paginate_by_code_lines(display_lines)
    lines: list[str] = [f"# {c.project_name} V1.0", "", "```text"]
    for page in range(1, len(pages) + 1):
        lines.append(f"---- 第{page}页（本节） ----")
        for row in pages[page - 1]:
            lines.append(row)
        lines.append("")
    lines.append("```")
    c.md_path.write_text("\n".join(lines), encoding="utf-8")


def write_debug_html(display_lines: list[str]) -> None:
    c = cfg()
    pages = paginate_by_code_lines(display_lines)
    html: list[str] = [
        '<!doctype html><html><head><meta charset="utf-8"><style>',
        "body{margin:0;padding:0;font-family:'Microsoft YaHei','Consolas',monospace;color:#000}",
        ".page{page-break-after:always;padding:12mm 10mm;}",
        ".line{white-space:pre;font-size:12px;line-height:18px;}",
        ".module{font-size:13px;font-weight:700;}",
        "</style></head><body>",
    ]
    for page in range(len(pages)):
        html.append('<div class="page">')
        for row in pages[page]:
            escaped = (
                row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )
            cls = "line module" if "模块:" in row else "line"
            html.append(f'<div class="{cls}">{escaped}</div>')
        html.append("</div>")
    html.append("</body></html>")
    c.html_path.write_text("\n".join(html), encoding="utf-8")


def write_pdf(display_lines: list[str]) -> None:
    run = cfg()
    pages = paginate_by_code_lines(display_lines)
    font_name = ZH_FONT_NAME
    if ZH_FONT_FILE.exists():
        pdfmetrics.registerFont(TTFont(font_name, str(ZH_FONT_FILE)))
    else:
        font_name = "STSong-Light"
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))

    c = canvas.Canvas(str(run.pdf_path), pagesize=A4)
    page_w, page_h = A4
    left = 30
    right = page_w - 30
    header_y = page_h - 22
    footer_y = 16
    first_line_y = page_h - 45
    line_h = 14

    for page in range(1, run.total_pages + 1):
        c.setFont(font_name, 10)
        c.setFillColor(colors.black)
        c.drawCentredString(page_w / 2, header_y, run.header)
        c.setLineWidth(0.4)
        c.line(left, header_y - 4, right, header_y - 4)
        c.drawCentredString(
            page_w / 2, footer_y, f"第 {page} 页 共 {run.total_pages} 页"
        )
        c.line(left, footer_y + 10, right, footer_y + 10)

        y = first_line_y
        for row in pages[page - 1]:
            if "模块:" in row:
                c.setFont(font_name, 10)
            else:
                c.setFont(font_name, 9)
            c.drawString(left, y, row[:165])
            y -= line_h
        c.showPage()
    c.save()


def assert_naming_consistency(lines: list[str]) -> None:
    c = cfg()
    if c.project_name == "PROJECT_NAME":
        forbidden = ("古诗词智能背诵系统", "ILovePoems", "艾宾浩斯背诗工具")
        for item in lines[:200]:
            if any(name in item for name in forbidden):
                raise ValueError(
                    f"Template output must not leak real names: {item[:120]}"
                )
    elif "PROJECT_NAME" in "\n".join(lines[:50]):
        raise ValueError("Formal output still contains placeholder PROJECT_NAME")


def main() -> None:
    global _cfg
    args = parse_args()
    _cfg = build_config(args)
    _cfg.output_dir.mkdir(parents=True, exist_ok=True)

    lines = build_fixed_60_lines()
    assert_naming_consistency(lines)
    write_markdown(lines)
    write_debug_html(lines)
    write_pdf(lines)
    print(f"OK: {_cfg.md_path}")
    print(f"OK: {_cfg.html_path}")
    print(f"OK: {_cfg.pdf_path}")


if __name__ == "__main__":
    main()
