from __future__ import annotations

import argparse
import fnmatch
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
MIN_LAST_PAGE_CODE_LINES = 40
MIN_RAW_CODE_LINES = (TOTAL_PAGES - 1) * LINES_PER_PAGE + MIN_LAST_PAGE_CODE_LINES
DEFAULT_VERSION = "V1.0"
MAX_LEFT_PATH_LEN = 30
ZH_FONT_NAME = "ZhFont"
ZH_FONT_FILE = Path(r"C:\Windows\Fonts\simhei.ttf")
# 仅收录用户编写的源程序，不含配置、数据、锁文件、IDE/构建产物
SOURCE_EXTS = {
    ".c",
    ".cpp",
    ".cs",
    ".css",
    ".dart",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".less",
    ".lua",
    ".m",
    ".mm",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".swift",
    ".ts",
    ".tsx",
    ".vb",
    ".vue",
}

EXCLUDE_DIRS = {
    # 依赖与包管理
    "node_modules",
    "bower_components",
    "vendor",
    "uni_modules",
    # 构建 / 发布 / IDE 产物
    "dist",
    "build",
    "out",
    "output",
    "target",
    "bin",
    "obj",
    "unpackage",
    ".next",
    ".nuxt",
    ".output",
    ".svelte-kit",
    ".hbuilderx",
    ".idea",
    ".vscode",
    ".vs",
    ".fleet",
    ".settings",
    ".gradle",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "coverage",
    "htmlcov",
    # 生成代码
    "generated",
    "gen",
    "__generated__",
    "auto-generated",
    # 数据 / 资源（非源程序）
    "data",
    "dataset",
    "datasets",
    "fixtures",
    "mock-data",
    "migrations",
    "seeds",
    "dump",
    "uploads",
    "static",
    "public",
    "assets",
    "resources",
    # 软著输出与其它
    "software-copyright",
    ".git",
    ".cursor",
    ".svn",
    ".hg",
}

# 路径段命中则降权或排除（测试、示例、文档目录）
LOW_PRIORITY_DIR_NAMES = {
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
    "e2e",
    "integration",
    "mock",
    "mocks",
    "__mocks__",
    "fixture",
    "fixtures",
    "example",
    "examples",
    "demo",
    "demos",
    "sample",
    "samples",
    "docs",
    "doc",
    "documentation",
}

HIGH_PRIORITY_DIR_NAMES = {
    "src",
    "source",
    "app",
    "apps",
    "lib",
    "libs",
    "core",
    "modules",
    "module",
    "pages",
    "page",
    "views",
    "view",
    "components",
    "component",
    "api",
    "apis",
    "services",
    "service",
    "server",
    "client",
    "backend",
    "frontend",
    "controllers",
    "models",
    "handlers",
    "routes",
    "router",
    "store",
    "stores",
    "sdk",
    "utils",
    "common",
    "shared",
}

EXCLUDE_FILE_NAMES = frozenset(
    {
        # 包管理与锁文件
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "npm-shrinkwrap.json",
        "bun.lock",
        "bun.lockb",
        "composer.json",
        "composer.lock",
        "gemfile",
        "gemfile.lock",
        "cargo.lock",
        "go.mod",
        "go.sum",
        "pipfile",
        "pipfile.lock",
        "poetry.lock",
        "requirements.txt",
        # 编译 / 构建配置
        "tsconfig.json",
        "tsconfig.app.json",
        "tsconfig.node.json",
        "jsconfig.json",
        "project.config.json",
        "app.json",
        "app.config.js",
        "app.config.ts",
        "manifest.json",
        "pages.json",
        "android.json",
        "ios.json",
        "gradle.properties",
        "settings.gradle",
        "settings.gradle.kts",
        "build.gradle",
        "build.gradle.kts",
        "pom.xml",
        "cmakeLists.txt",
        "makefile",
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        # 环境与 CI 配置
        ".editorconfig",
        ".prettierrc",
        ".prettierrc.json",
        ".eslintrc",
        ".eslintrc.json",
        ".eslintrc.js",
        ".eslintrc.cjs",
        ".stylelintrc",
        ".stylelintrc.json",
        "eslint.config.js",
        "eslint.config.mjs",
        "eslint.config.cjs",
        "prettier.config.js",
        "babel.config.js",
        "babel.config.json",
        "jest.config.js",
        "jest.config.ts",
        "vitest.config.ts",
        "playwright.config.ts",
        "cypress.config.js",
        "tailwind.config.js",
        "tailwind.config.ts",
        "postcss.config.js",
        "uno.config.ts",
        "components.d.ts",
        "auto-imports.d.ts",
        "typed-router.d.ts",
        ".env",
        ".env.example",
        ".env.local",
        ".env.development",
        ".env.production",
        ".gitignore",
        ".gitattributes",
        ".npmrc",
        ".nvmrc",
        ".yarnrc",
        ".yarnrc.yml",
    }
)

EXCLUDE_BASENAME_PATTERNS = (
    "*.config.js",
    "*.config.ts",
    "*.config.mjs",
    "*.config.cjs",
    "*.config.json",
    "vite.config.*",
    "webpack.config.*",
    "rollup.config.*",
    "next.config.*",
    "nuxt.config.*",
    "uno.config.*",
    "*.min.js",
    "*.min.css",
    "*.bundle.js",
    "*.chunk.js",
    "*.map",
    "*.d.ts",
    "*.generated.*",
    "*.g.dart",
    "*.lock",
)

EXCLUDE_PATH_MARKERS = (
    "/.idea/",
    "/.vscode/",
    "/node_modules/",
    "/__generated__/",
    "/auto-generated/",
)

_cfg: "RunConfig | None" = None


@dataclass(frozen=True)
class RunConfig:
    project_root: Path
    output_dir: Path
    project_name: str
    version: str

    @property
    def total_pages(self) -> int:
        return TOTAL_PAGES

    @property
    def header(self) -> str:
        ver = self.version.strip()
        if ver and not ver.upper().startswith("V"):
            ver = f"V{ver}"
        return f"{self.project_name}{ver}"

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
    p.add_argument(
        "--version",
        default=DEFAULT_VERSION,
        help="Version for page header, e.g. V1.0 (default: V1.0).",
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
        version=args.version.strip() or DEFAULT_VERSION,
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


def _basename_matches_patterns(name: str, patterns: tuple[str, ...]) -> bool:
    lower = name.lower()
    return any(fnmatch.fnmatch(lower, pat.lower()) for pat in patterns)


def _is_excluded_source_file(rel: Path) -> bool:
    name = rel.name
    lower_name = name.lower()
    if lower_name in EXCLUDE_FILE_NAMES:
        return True
    if _basename_matches_patterns(name, EXCLUDE_BASENAME_PATTERNS):
        return True
    posix = rel.as_posix().lower()
    if any(marker in posix for marker in EXCLUDE_PATH_MARKERS):
        return True
    if lower_name.startswith("."):
        return True
    if lower_name in {
        "config.js",
        "config.ts",
        "config.mjs",
        "config.cjs",
        "settings.js",
        "settings.ts",
        "env.js",
        "env.ts",
        "constants.js",
        "constants.ts",
        "data.js",
        "data.ts",
    }:
        return True
    return False


def _source_collect_priority(rel: Path) -> tuple[int, str]:
    """数值越小越优先：0=业务源码目录，1=其它，2=测试/示例/文档目录。"""
    parts = {p.lower() for p in rel.parts[:-1]}
    if parts & LOW_PRIORITY_DIR_NAMES:
        return (2, rel.as_posix().lower())
    if parts & HIGH_PRIORITY_DIR_NAMES:
        return (0, rel.as_posix().lower())
    return (1, rel.as_posix().lower())


def _should_collect_file(path: Path, root: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() not in SOURCE_EXTS:
        return False
    rel = path.relative_to(root)
    if set(rel.parts) & EXCLUDE_DIRS:
        return False
    return not _is_excluded_source_file(rel)


def collect_raw_code_lines() -> list[str]:
    root = cfg().project_root
    files: list[Path] = []
    for p in root.rglob("*"):
        if not _should_collect_file(p, root):
            continue
        files.append(p)
    files.sort(key=lambda p: _source_collect_priority(p.relative_to(root)))

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


def _count_code_lines(rows: list[str]) -> int:
    return sum(1 for r in rows if not r.startswith("模块:"))


def _ends_at_module_boundary(all_lines: list[str], end: int) -> bool:
    if end <= 0 or end > len(all_lines):
        return False
    if all_lines[end - 1].startswith("模块:"):
        return False
    if end < len(all_lines) and not all_lines[end].startswith("模块:"):
        return False
    return True


def _paginate_raw(display_lines: list[str]) -> list[list[str]]:
    """分页（不含页内行号前缀）；模块行不计入每页 50 行代码统计。"""
    pages: list[list[str]] = []
    cur: list[str] = []
    code_count = 0
    for row in display_lines:
        is_module = row.startswith("模块:")
        if not is_module and code_count >= LINES_PER_PAGE:
            pages.append(cur)
            cur = []
            code_count = 0
        if is_module:
            cur.append(row)
        else:
            code_count += 1
            cur.append(row)
    if cur:
        pages.append(cur)
    return pages


def _is_valid_60_page_layout(pages: list[list[str]]) -> bool:
    if len(pages) != TOTAL_PAGES:
        return False
    for page in pages[:-1]:
        if _count_code_lines(page) != LINES_PER_PAGE:
            return False
    last = _count_code_lines(pages[-1])
    return MIN_LAST_PAGE_CODE_LINES <= last <= LINES_PER_PAGE


def select_lines_for_60_pages(all_lines: list[str]) -> list[str]:
    best_end: int | None = None
    best_last_codes = -1
    for end in range(1, len(all_lines) + 1):
        if not _ends_at_module_boundary(all_lines, end):
            continue
        pages = _paginate_raw(all_lines[:end])
        if not _is_valid_60_page_layout(pages):
            continue
        last_codes = _count_code_lines(pages[-1])
        if last_codes > best_last_codes:
            best_end = end
            best_last_codes = last_codes
    if best_end is None:
        raise ValueError(
            "Cannot form 60 pages: need 59 full pages (50 code lines each), "
            f"last page {MIN_LAST_PAGE_CODE_LINES}-{LINES_PER_PAGE} code lines ending "
            "at a complete module boundary. Add more source code or check exclusions."
        )
    return all_lines[:best_end]


def build_display_lines_for_submission() -> list[str]:
    raw = collect_raw_code_lines()
    if len(raw) < MIN_RAW_CODE_LINES:
        raise ValueError(
            f"Not enough raw code lines: {len(raw)} < {MIN_RAW_CODE_LINES} "
            f"(need at least {(TOTAL_PAGES - 1) * LINES_PER_PAGE + MIN_LAST_PAGE_CODE_LINES} "
            "lines of user source code after filtering)."
        )
    return select_lines_for_60_pages(format_display_lines(raw))


def with_page_line_prefix(row: str, line_index_in_page: int) -> str:
    return f"{line_index_in_page:02d}   {row}"


def paginate_by_code_lines(display_lines: list[str]) -> list[list[str]]:
    raw_pages = _paginate_raw(display_lines)
    if not _is_valid_60_page_layout(raw_pages):
        raise ValueError(
            f"Invalid pagination: expected {TOTAL_PAGES} pages with "
            f"{LINES_PER_PAGE} code lines on pages 1-{TOTAL_PAGES - 1} and "
            f"{MIN_LAST_PAGE_CODE_LINES}-{LINES_PER_PAGE} on the last page."
        )
    pages: list[list[str]] = []
    for raw_page in raw_pages:
        page: list[str] = []
        code_count = 0
        for row in raw_page:
            if row.startswith("模块:"):
                page.append(row)
            else:
                code_count += 1
                page.append(with_page_line_prefix(row, code_count))
        pages.append(page)
    return pages


def write_markdown(display_lines: list[str]) -> None:
    c = cfg()
    pages = paginate_by_code_lines(display_lines)
    lines: list[str] = [f"# {c.header}", "", "```text"]
    for page in range(1, len(pages) + 1):
        lines.append(f"---- 第{page}页 页眉:{c.header} ----")
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
        ".page-header{display:flex;justify-content:space-between;align-items:center;"
        "border-bottom:1px solid #000;padding-bottom:4px;margin-bottom:8px;font-size:12px;}",
        ".page-header .title{flex:1;text-align:center;font-weight:700;}",
        ".page-header .num{min-width:4em;text-align:right;}",
        ".line{white-space:pre;font-size:12px;line-height:18px;}",
        ".module{font-size:13px;font-weight:700;}",
        "</style></head><body>",
    ]
    for page in range(len(pages)):
        page_no = page + 1
        html.append('<div class="page">')
        html.append(
            f'<div class="page-header"><span class="title">{c.header}</span>'
            f'<span class="num">第 {page_no} 页</span></div>'
        )
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
        c.drawRightString(right, header_y, f"第 {page} 页")
        c.setLineWidth(0.4)
        c.line(left, header_y - 4, right, header_y - 4)
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

    lines = build_display_lines_for_submission()
    assert_naming_consistency(lines)
    write_markdown(lines)
    write_debug_html(lines)
    write_pdf(lines)
    print(f"OK: {_cfg.md_path}")
    print(f"OK: {_cfg.html_path}")
    print(f"OK: {_cfg.pdf_path}")


if __name__ == "__main__":
    main()
