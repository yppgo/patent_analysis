from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from lxml import etree
from PIL import Image


ROOT_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT_DIR / "中国人民大学信息学院硕士毕业论文latex模板__1_ (1)"
TEXTFILES_DIR = TEMPLATE_DIR / "textfiles"
OUTPUT_PATH = ROOT_DIR / "基于数据感知的多智能体专利分析系统_论文Word版.docx"

ORDERED_TEX_FILES = [
    "0Abstract.tex",
    "1Introduction.tex",
    "2Related_work.tex",
    "3FirstResearch.tex",
    "4SecondResearch.tex",
    "5ThirdResearch.tex",
    "6Application.tex",
    "7Summary.tex",
]

MANUAL_SECTIONS = [
    (
        "攻读硕士期间发表学术论文情况",
        [
            "截至论文提交日期，暂无公开发表的学术论文成果。",
        ],
    )
]

DOCX_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "dcmitype": "http://purl.org/dc/dcmitype/",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
EMU_PER_INCH = 914400
DEFAULT_BODY_MAX_WIDTH_IN = 6.1


def qn(tag: str) -> str:
    prefix, local = tag.split(":", 1)
    return f"{{{DOCX_NS[prefix]}}}{local}"


def xml_space(text: str) -> bool:
    return text.startswith(" ") or text.endswith(" ") or "  " in text


def strip_comments(text: str) -> str:
    out_lines: list[str] = []
    for line in text.splitlines():
        escaped = False
        result = []
        for ch in line:
            if ch == "%" and not escaped:
                break
            result.append(ch)
            escaped = ch == "\\" and not escaped
            if ch != "\\":
                escaped = False
        out_lines.append("".join(result))
    return "\n".join(out_lines)


def read_group(text: str, start: int, open_char: str = "{", close_char: str = "}") -> tuple[str, int]:
    if start >= len(text) or text[start] != open_char:
        raise ValueError(f"Expected {open_char!r} at position {start}")
    depth = 0
    buf: list[str] = []
    i = start
    while i < len(text):
        ch = text[i]
        if ch == open_char:
            depth += 1
            if depth > 1:
                buf.append(ch)
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return "".join(buf), i + 1
            buf.append(ch)
        else:
            buf.append(ch)
        i += 1
    raise ValueError(f"Unclosed group starting at {start}")


def skip_optional_groups(text: str, start: int) -> int:
    i = start
    while i < len(text) and text[i] == "[":
        _, i = read_group(text, i, "[", "]")
        while i < len(text) and text[i].isspace():
            i += 1
    return i


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+([，。；：！？、）】》])", r"\1", text)
    text = re.sub(r"([（【《])\s+", r"\1", text)
    return text.strip()


def flatten_math(expr: str) -> str:
    replacements = {
        r"\times": "×",
        r"\pm": "±",
        r"\rightarrow": "→",
        r"\to": "→",
        r"\leq": "≤",
        r"\geq": "≥",
        r"\neq": "≠",
        r"\beta": "β",
        r"\alpha": "α",
        r"\gamma": "γ",
        r"\infty": "∞",
        r"\%": "%",
        r"\_": "_",
    }
    for src, dst in replacements.items():
        expr = expr.replace(src, dst)
    expr = expr.replace("{", "").replace("}", "")
    expr = expr.replace("^2", "²").replace("^3", "³")
    expr = expr.replace("\\", "")
    return normalize_text(expr)


def format_citation(keys: str, cite_map: dict[str, int]) -> str:
    numbers = []
    for key in [part.strip() for part in keys.split(",") if part.strip()]:
        number = cite_map.get(key)
        numbers.append(str(number) if number is not None else key)
    return "[" + ", ".join(numbers) + "]" if numbers else ""


def flatten_latex(text: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> str:
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "$":
            end = text.find("$", i + 1)
            if end == -1:
                out.append("$")
                i += 1
            else:
                out.append(flatten_math(text[i + 1 : end]))
                i = end + 1
            continue
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        if i + 1 >= len(text):
            break
        nxt = text[i + 1]
        if nxt in "%&_#${}":
            out.append(nxt)
            i += 2
            continue
        if nxt == "\\":
            out.append("\n")
            i += 2
            continue

        j = i + 1
        while j < len(text) and (text[j].isalpha() or text[j] == "_"):
            j += 1
        command = text[i + 1 : j]
        if not command:
            out.append(nxt)
            i += 2
            continue

        k = skip_optional_groups(text, j)

        if command in {"textbf", "textit", "emph", "texttt", "path", "url", "underline", "mbox", "textrm", "textsf"}:
            if k < len(text) and text[k] == "{":
                inner, i = read_group(text, k)
                out.append(flatten_latex(inner, cite_map, ref_map))
                continue
        elif command == "makebox":
            while k < len(text) and text[k] == "[":
                _, k = read_group(text, k, "[", "]")
                while k < len(text) and text[k].isspace():
                    k += 1
            if k < len(text) and text[k] == "{":
                inner, i = read_group(text, k)
                out.append(flatten_latex(inner, cite_map, ref_map))
                continue
        elif command == "dunderline":
            if k < len(text) and text[k] == "{":
                _, k = read_group(text, k)
            while k < len(text) and text[k].isspace():
                k += 1
            if k < len(text) and text[k] == "{":
                inner, i = read_group(text, k)
                out.append(flatten_latex(inner, cite_map, ref_map))
                continue
        elif command == "cite":
            if k < len(text) and text[k] == "{":
                inner, i = read_group(text, k)
                out.append(format_citation(inner, cite_map))
                continue
        elif command == "ref":
            if k < len(text) and text[k] == "{":
                inner, i = read_group(text, k)
                out.append(ref_map.get(inner, inner))
                continue
        elif command == "eref":
            if k < len(text) and text[k] == "{":
                inner, i = read_group(text, k)
                out.append(f"({ref_map.get(inner, inner)})")
                continue
        elif command == "footnote":
            if k < len(text) and text[k] == "{":
                inner, i = read_group(text, k)
                out.append(f"（注：{flatten_latex(inner, cite_map, ref_map)}）")
                continue
        elif command == "hspace":
            if k < len(text) and text[k] == "{":
                _, i = read_group(text, k)
            else:
                i = k
            out.append(" ")
            continue
        elif command in {
            "vspace",
            "vfill",
            "centering",
            "flushleft",
            "raggedright",
            "noindent",
            "heiti",
            "large",
            "Large",
            "LARGE",
            "small",
            "footnotesize",
            "zihao",
            "arraybackslash",
            "allowbreak",
            "renewcommand",
        }:
            if k < len(text) and text[k] == "{":
                _, i = read_group(text, k)
            else:
                i = k
            continue
        elif command == "tcp":
            if k < len(text) and text[k] == "{":
                inner, i = read_group(text, k)
                out.append(f"注：{flatten_latex(inner, cite_map, ref_map)}")
                continue
        elif command == "phantom":
            if k < len(text) and text[k] == "{":
                _, i = read_group(text, k)
            else:
                i = k
            continue

        i = k

    return normalize_text("".join(out))


def collect_environment(lines: list[str], start: int, env_name: str) -> tuple[str, int]:
    begin_token = f"\\begin{{{env_name}}}"
    end_token = f"\\end{{{env_name}}}"
    depth = 0
    buf: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if begin_token in line:
            depth += line.count(begin_token)
        if end_token in line:
            depth -= line.count(end_token)
        buf.append(line)
        i += 1
        if depth == 0:
            return "\n".join(buf), i
    raise ValueError(f"Environment {env_name!r} not closed")


@dataclass
class Block:
    kind: str
    data: dict


def extract_heading(line: str, command: str) -> str:
    prefix = f"\\{command}"
    start = line.find("{", len(prefix))
    if start == -1:
        return ""
    inner, _ = read_group(line, start)
    return inner


def split_paragraph_lines(lines: Iterable[str]) -> str:
    return " ".join(line.strip() for line in lines if line.strip())


def parse_items_from_enumerate(block_text: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> list[str]:
    inner = re.sub(r"^.*?\\begin\{enumerate\}(?:\[[^\]]*\])?", "", block_text, count=1, flags=re.S)
    inner = re.sub(r"\\end\{enumerate\}\s*$", "", inner, count=1, flags=re.S)
    lines = inner.splitlines()
    items: list[str] = []
    current: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith(r"\item"):
            if current:
                items.append(flatten_latex(split_paragraph_lines(current), cite_map, ref_map))
            current = [stripped[5:].strip()]
        else:
            current.append(raw)
    if current:
        items.append(flatten_latex(split_paragraph_lines(current), cite_map, ref_map))
    return [item for item in items if item]


def parse_quote_block(block_text: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> str:
    inner = re.sub(r"^.*?\\begin\{quote\}", "", block_text, count=1, flags=re.S)
    inner = re.sub(r"\\end\{quote\}\s*$", "", inner, count=1, flags=re.S)
    return flatten_latex(inner, cite_map, ref_map)


def parse_tabular(tabular_text: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> list[list[str]]:
    content = strip_comments(tabular_text)
    content = re.sub(r"\\(toprule|midrule|bottomrule|hline)\b", "", content)
    content = content.replace("\n", " ")
    rows: list[list[str]] = []
    row_buf: list[str] = []
    cell_buf: list[str] = []
    depth = 0
    i = 0
    while i < len(content):
        if content[i] == "{":
            depth += 1
            cell_buf.append(content[i])
            i += 1
            continue
        if content[i] == "}":
            depth = max(0, depth - 1)
            cell_buf.append(content[i])
            i += 1
            continue
        if content.startswith("\\\\", i) and depth == 0:
            row_buf.append("".join(cell_buf).strip())
            row = [flatten_latex(cell, cite_map, ref_map) for cell in row_buf]
            row = [cell for cell in row if cell]
            if row:
                rows.append(row)
            row_buf = []
            cell_buf = []
            i += 2
            continue
        if content[i] == "&" and depth == 0:
            row_buf.append("".join(cell_buf).strip())
            cell_buf = []
            i += 1
            continue
        cell_buf.append(content[i])
        i += 1
    tail = "".join(cell_buf).strip()
    if tail:
        row_buf.append(tail)
    if row_buf:
        row = [flatten_latex(cell, cite_map, ref_map) for cell in row_buf]
        row = [cell for cell in row if cell]
        if row:
            rows.append(row)
    return rows


def parse_table_block(block_text: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> dict:
    clean = strip_comments(block_text)
    caption_match = re.search(r"\\caption\{(.+?)\}", clean, re.S)
    label_match = re.search(r"\\label\{([^}]+)\}", clean)
    tabular_match = re.search(r"\\begin\{tabular\}\{.*?\}(.*?)\\end\{tabular\}", clean, re.S)
    note_match = re.search(r"\\begin\{minipage\}\{.*?\}(.*?)\\end\{minipage\}", clean, re.S)
    rows = parse_tabular(tabular_match.group(1), cite_map, ref_map) if tabular_match else []
    note = flatten_latex(note_match.group(1), cite_map, ref_map) if note_match else ""
    return {
        "caption": flatten_latex(caption_match.group(1), cite_map, ref_map) if caption_match else "",
        "label": label_match.group(1) if label_match else "",
        "rows": rows,
        "note": note,
    }


def parse_figure_block(block_text: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> dict:
    clean = strip_comments(block_text)
    image_match = re.search(r"\\includegraphics(?:\[([^\]]+)\])?\{([^}]+)\}", clean, re.S)
    caption_match = re.search(r"\\caption\{(.+?)\}", clean, re.S)
    label_match = re.search(r"\\label\{([^}]+)\}", clean)
    width_factor = 1.0
    if image_match and image_match.group(1):
        width_match = re.search(r"width\s*=\s*([0-9.]+)\\textwidth", image_match.group(1))
        if width_match:
            width_factor = float(width_match.group(1))
    image_path = TEMPLATE_DIR / image_match.group(2) if image_match else None
    return {
        "image_path": image_path,
        "caption": flatten_latex(caption_match.group(1), cite_map, ref_map) if caption_match else "",
        "label": label_match.group(1) if label_match else "",
        "width_factor": width_factor,
    }


def transform_algorithm_line(line: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> str:
    text = strip_comments(line).strip()
    if not text or text.startswith(r"\caption{"):
        return ""
    replacements = [
        (r"\\KwIn\{(.+?)\}", lambda m: f"输入: {flatten_latex(m.group(1), cite_map, ref_map)}"),
        (r"\\KwOut\{(.+?)\}", lambda m: f"输出: {flatten_latex(m.group(1), cite_map, ref_map)}"),
        (r"\\Return\{(.+?)\}", lambda m: f"Return {flatten_latex(m.group(1), cite_map, ref_map)}"),
        (r"\\ForEach\{(.+?)\}\{", lambda m: f"ForEach {flatten_latex(m.group(1), cite_map, ref_map)} {{"),
        (r"\\eIf\{(.+?)\}\{", lambda m: f"If {flatten_latex(m.group(1), cite_map, ref_map)} {{"),
        (r"\\tcp\{(.+?)\}", lambda m: f"// {flatten_latex(m.group(1), cite_map, ref_map)}"),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    text = text.replace(r"\;", "")
    return flatten_latex(text, cite_map, ref_map)


def parse_algorithm_block(block_text: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> dict:
    clean = strip_comments(block_text)
    caption_match = re.search(r"\\caption\{(.+?)\}", clean, re.S)
    body = [transform_algorithm_line(line, cite_map, ref_map) for line in clean.splitlines()]
    body = [line for line in body if line]
    return {
        "caption": flatten_latex(caption_match.group(1), cite_map, ref_map) if caption_match else "",
        "body": "\n".join(body),
    }


def parse_listing_block(block_text: str) -> str:
    inner = re.sub(r"^.*?\\begin\{lstlisting\}(?:\[[^\]]*\])?", "", block_text, count=1, flags=re.S)
    inner = re.sub(r"\\end\{lstlisting\}\s*$", "", inner, count=1, flags=re.S)
    return inner.strip("\n")


def parse_tex_blocks(tex_text: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> list[Block]:
    lines = tex_text.splitlines()
    blocks: list[Block] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        raw = split_paragraph_lines(paragraph_lines)
        paragraph_lines.clear()
        text = flatten_latex(raw, cite_map, ref_map)
        if text:
            blocks.append(Block("paragraph", {"text": text}))

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        if stripped.startswith(r"\newpage"):
            flush_paragraph()
            blocks.append(Block("page_break", {}))
            i += 1
            continue

        heading_commands = [
            ("section*", 1),
            ("section", 1),
            ("subsection", 2),
            ("subsubsection", 3),
            ("paragraph", 4),
        ]
        matched_heading = False
        for command, level in heading_commands:
            if stripped.startswith(f"\\{command}"):
                flush_paragraph()
                title = flatten_latex(extract_heading(stripped, command), cite_map, ref_map)
                blocks.append(Block("heading", {"level": level, "title": title}))
                matched_heading = True
                break
        if matched_heading:
            i += 1
            continue

        handled_env = False
        for env_name, kind in [
            ("figure", "figure"),
            ("table", "table"),
            ("algorithm", "algorithm"),
            ("lstlisting", "listing"),
            ("enumerate", "enumerate"),
            ("quote", "quote"),
        ]:
            if stripped.startswith(f"\\begin{{{env_name}}}"):
                flush_paragraph()
                env_text, i = collect_environment(lines, i, env_name)
                if kind == "figure":
                    blocks.append(Block("figure", parse_figure_block(env_text, cite_map, ref_map)))
                elif kind == "table":
                    blocks.append(Block("table", parse_table_block(env_text, cite_map, ref_map)))
                elif kind == "algorithm":
                    blocks.append(Block("algorithm", parse_algorithm_block(env_text, cite_map, ref_map)))
                elif kind == "listing":
                    blocks.append(Block("listing", {"text": parse_listing_block(env_text)}))
                elif kind == "enumerate":
                    blocks.append(Block("enumerate", {"items": parse_items_from_enumerate(env_text, cite_map, ref_map)}))
                elif kind == "quote":
                    blocks.append(Block("quote", {"text": parse_quote_block(env_text, cite_map, ref_map)}))
                handled_env = True
                break
        if handled_env:
            continue

        paragraph_lines.append(lines[i])
        i += 1

    flush_paragraph()
    return blocks


def parse_bibliography(bbl_text: str, cite_map: dict[str, int], ref_map: dict[str, str]) -> list[str]:
    items = re.findall(r"\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem\{|\\end\{thebibliography\})", bbl_text, re.S)
    bibliography: list[str] = []
    for key, body in items:
        cite_number = cite_map.get(key, len(bibliography) + 1)
        body = body.replace(r"\newblock", " ")
        bibliography.append(f"[{cite_number}] {flatten_latex(body, cite_map, ref_map)}")
    return bibliography


def build_citation_map(bbl_text: str) -> dict[str, int]:
    return {key: index for index, key in enumerate(re.findall(r"\\bibitem\{([^}]+)\}", bbl_text), start=1)}


def extract_cover_fields(cover_text: str) -> dict:
    image_match = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", cover_text)
    fields = re.findall(r"\\makebox\[[^\]]+\]\[[^\]]+\]\{([^{}]+)\}", cover_text)
    if len(fields) < 7:
        raise ValueError("Unexpected cover.tex structure")
    return {
        "image_path": TEMPLATE_DIR / image_match.group(1) if image_match else None,
        "title_cn_lines": fields[0:2],
        "title_en_lines": fields[2:4],
        "author": fields[4],
        "advisor": fields[5],
        "date": fields[6],
    }


def build_reference_map() -> dict[str, str]:
    ref_map: dict[str, str] = {}
    section_index = 0
    ordered_paths = [TEXTFILES_DIR / name for name in ORDERED_TEX_FILES]
    for path in ordered_paths:
        text = strip_comments(path.read_text(encoding="utf-8"))
        figure_count = 0
        table_count = 0
        section_index += len(re.findall(r"\\section\{", text))
        if section_index == 0:
            continue
        for match in re.finditer(r"\\begin\{(figure|table)\}.*?\\label\{([^}]+)\}.*?\\end\{\1\}", text, re.S):
            kind = match.group(1)
            label = match.group(2)
            if kind == "figure":
                figure_count += 1
                ref_map[label] = f"{section_index}-{figure_count}"
            else:
                table_count += 1
                ref_map[label] = f"{section_index}-{table_count}"
    return ref_map


class DocxWriter:
    def __init__(self) -> None:
        self.body: list[etree._Element] = []
        self.relationships: list[tuple[str, str, str]] = []
        self.images: list[tuple[str, bytes, str]] = []
        self.image_targets: dict[Path, tuple[str, str]] = {}
        self.rel_index = 1
        self.docpr_index = 1

    def _new_rel_id(self) -> str:
        rel_id = f"rId{self.rel_index}"
        self.rel_index += 1
        return rel_id

    def _paragraph(
        self,
        text: str = "",
        *,
        style: str | None = None,
        align: str | None = None,
        page_break_before: bool = False,
    ) -> etree._Element:
        p = etree.Element(qn("w:p"))
        if style or align:
            ppr = etree.SubElement(p, qn("w:pPr"))
            if style:
                etree.SubElement(ppr, qn("w:pStyle"), {qn("w:val"): style})
            if align:
                etree.SubElement(ppr, qn("w:jc"), {qn("w:val"): align})

        if page_break_before:
            run = etree.SubElement(p, qn("w:r"))
            etree.SubElement(run, qn("w:br"), {qn("w:type"): "page"})

        if text:
            parts = text.split("\n")
            for idx, part in enumerate(parts):
                run = etree.SubElement(p, qn("w:r"))
                if part:
                    t = etree.SubElement(run, qn("w:t"))
                    if xml_space(part):
                        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                    t.text = part
                if idx != len(parts) - 1:
                    etree.SubElement(run, qn("w:br"))
        return p

    def add_paragraph(self, text: str, *, style: str | None = None, align: str | None = None) -> None:
        self.body.append(self._paragraph(text, style=style, align=align))

    def add_page_break(self) -> None:
        self.body.append(self._paragraph(page_break_before=True))

    def add_heading(self, text: str, level: int) -> None:
        style = {0: "Title", 1: "Heading1", 2: "Heading2", 3: "Heading3"}.get(level, "Heading4")
        self.add_paragraph(text, style=style)

    def add_table(self, rows: list[list[str]], caption: str = "", note: str = "") -> None:
        if caption:
            self.add_paragraph(caption, style="Caption", align="center")
        if not rows:
            return
        max_cols = max(len(row) for row in rows)
        tbl = etree.Element(qn("w:tbl"))
        tbl_pr = etree.SubElement(tbl, qn("w:tblPr"))
        etree.SubElement(tbl_pr, qn("w:tblW"), {qn("w:w"): "0", qn("w:type"): "auto"})
        borders = etree.SubElement(tbl_pr, qn("w:tblBorders"))
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            etree.SubElement(
                borders,
                qn(f"w:{edge}"),
                {
                    qn("w:val"): "single",
                    qn("w:sz"): "4",
                    qn("w:space"): "0",
                    qn("w:color"): "auto",
                },
            )
        grid = etree.SubElement(tbl, qn("w:tblGrid"))
        for _ in range(max_cols):
            etree.SubElement(grid, qn("w:gridCol"), {qn("w:w"): "3000"})

        for row_index, row in enumerate(rows):
            tr = etree.SubElement(tbl, qn("w:tr"))
            padded = row + [""] * (max_cols - len(row))
            for cell_text in padded:
                tc = etree.SubElement(tr, qn("w:tc"))
                tc_pr = etree.SubElement(tc, qn("w:tcPr"))
                etree.SubElement(tc_pr, qn("w:tcW"), {qn("w:w"): "0", qn("w:type"): "auto"})
                p = etree.SubElement(tc, qn("w:p"))
                ppr = etree.SubElement(p, qn("w:pPr"))
                etree.SubElement(ppr, qn("w:jc"), {qn("w:val"): "center" if row_index == 0 else "left"})
                run = etree.SubElement(p, qn("w:r"))
                if row_index == 0:
                    rpr = etree.SubElement(run, qn("w:rPr"))
                    etree.SubElement(rpr, qn("w:b"))
                t = etree.SubElement(run, qn("w:t"))
                if xml_space(cell_text):
                    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                t.text = cell_text
        self.body.append(tbl)
        if note:
            self.add_paragraph(note, style="Quote")

    def _register_image(self, path: Path) -> tuple[str, str]:
        resolved = path.resolve()
        existing = self.image_targets.get(resolved)
        if existing:
            return existing
        rel_id = self._new_rel_id()
        ext = resolved.suffix.lower()
        image_name = f"image{len(self.images) + 1}{ext}"
        self.relationships.append((rel_id, f"{DOC_REL_NS}/image", f"media/{image_name}"))
        self.images.append((image_name, resolved.read_bytes(), ext))
        self.image_targets[resolved] = (rel_id, image_name)
        return rel_id, image_name

    def add_image(self, path: Path | None, caption: str = "", width_factor: float = 1.0) -> None:
        if not path or not path.exists():
            self.add_paragraph(f"[缺失图片] {path}", style="Quote")
            if caption:
                self.add_paragraph(caption, style="Caption", align="center")
            return

        rel_id, image_name = self._register_image(path)
        with Image.open(path) as image:
            width_px, height_px = image.size
            dpi_x, dpi_y = image.info.get("dpi", (96, 96))
        width_in = width_px / (dpi_x or 96)
        height_in = height_px / (dpi_y or 96)
        max_width_in = max(2.5, DEFAULT_BODY_MAX_WIDTH_IN * min(width_factor, 1.0))
        scale = min(1.0, max_width_in / max(width_in, 0.1))
        cx = int(width_in * scale * EMU_PER_INCH)
        cy = int(height_in * scale * EMU_PER_INCH)

        p = etree.Element(qn("w:p"))
        ppr = etree.SubElement(p, qn("w:pPr"))
        etree.SubElement(ppr, qn("w:jc"), {qn("w:val"): "center"})
        run = etree.SubElement(p, qn("w:r"))
        drawing = etree.SubElement(run, qn("w:drawing"))
        pic_id = self.docpr_index
        self.docpr_index += 1
        inline = etree.SubElement(
            drawing,
            qn("wp:inline"),
            nsmap={"wp": DOCX_NS["wp"], "a": DOCX_NS["a"], "pic": DOCX_NS["pic"], "r": DOCX_NS["r"]},
        )
        etree.SubElement(inline, qn("wp:extent"), cx=str(cx), cy=str(cy))
        etree.SubElement(inline, qn("wp:effectExtent"), l="0", t="0", r="0", b="0")
        etree.SubElement(inline, qn("wp:docPr"), id=str(pic_id), name=image_name)
        c_nv = etree.SubElement(inline, qn("wp:cNvGraphicFramePr"))
        etree.SubElement(c_nv, qn("a:graphicFrameLocks"), noChangeAspect="1")

        graphic = etree.SubElement(inline, qn("a:graphic"))
        graphic_data = etree.SubElement(graphic, qn("a:graphicData"), uri="http://schemas.openxmlformats.org/drawingml/2006/picture")
        pic = etree.SubElement(graphic_data, qn("pic:pic"))
        nv = etree.SubElement(pic, qn("pic:nvPicPr"))
        etree.SubElement(nv, qn("pic:cNvPr"), id=str(pic_id), name=image_name)
        etree.SubElement(nv, qn("pic:cNvPicPr"))
        blip_fill = etree.SubElement(pic, qn("pic:blipFill"))
        etree.SubElement(blip_fill, qn("a:blip"), {qn("r:embed"): rel_id})
        stretch = etree.SubElement(blip_fill, qn("a:stretch"))
        etree.SubElement(stretch, qn("a:fillRect"))
        sp_pr = etree.SubElement(pic, qn("pic:spPr"))
        xfrm = etree.SubElement(sp_pr, qn("a:xfrm"))
        etree.SubElement(xfrm, qn("a:off"), x="0", y="0")
        etree.SubElement(xfrm, qn("a:ext"), cx=str(cx), cy=str(cy))
        geom = etree.SubElement(sp_pr, qn("a:prstGeom"), prst="rect")
        etree.SubElement(geom, qn("a:avLst"))

        self.body.append(p)
        if caption:
            self.add_paragraph(caption, style="Caption", align="center")

    def build_document_xml(self) -> bytes:
        document = etree.Element(
            qn("w:document"),
            nsmap={"w": DOCX_NS["w"], "r": DOCX_NS["r"], "wp": DOCX_NS["wp"], "a": DOCX_NS["a"], "pic": DOCX_NS["pic"]},
        )
        body = etree.SubElement(document, qn("w:body"))
        for element in self.body:
            body.append(element)
        sect_pr = etree.SubElement(body, qn("w:sectPr"))
        etree.SubElement(sect_pr, qn("w:pgSz"), {qn("w:w"): "11906", qn("w:h"): "16838"})
        etree.SubElement(
            sect_pr,
            qn("w:pgMar"),
            {
                qn("w:top"): "1440",
                qn("w:right"): "1440",
                qn("w:bottom"): "1440",
                qn("w:left"): "1440",
                qn("w:header"): "708",
                qn("w:footer"): "708",
                qn("w:gutter"): "0",
            },
        )
        return etree.tostring(document, xml_declaration=True, encoding="UTF-8", standalone="yes")

    def build_document_rels_xml(self) -> bytes:
        relationships = etree.Element("Relationships", nsmap={None: REL_NS})
        rels = [("rIdStyles", f"{DOC_REL_NS}/styles", "styles.xml"), ("rIdSettings", f"{DOC_REL_NS}/settings", "settings.xml"), *self.relationships]
        for rel_id, rel_type, target in rels:
            etree.SubElement(relationships, "Relationship", Id=rel_id, Type=rel_type, Target=target)
        return etree.tostring(relationships, xml_declaration=True, encoding="UTF-8", standalone="yes")

    def save(self, output_path: Path) -> None:
        content_types = etree.Element("Types", nsmap={None: CONTENT_TYPES_NS})
        etree.SubElement(content_types, "Default", Extension="rels", ContentType="application/vnd.openxmlformats-package.relationships+xml")
        etree.SubElement(content_types, "Default", Extension="xml", ContentType="application/xml")
        image_content_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
        for ext in sorted({ext for _, _, ext in self.images}):
            etree.SubElement(content_types, "Default", Extension=ext.lstrip("."), ContentType=image_content_types[ext])
        for part_name, content_type in [
            ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
            ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
            ("/word/settings.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"),
            ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
            ("/docProps/app.xml", "application/vnd.openxmlformats-officedocument.extended-properties+xml"),
        ]:
            etree.SubElement(content_types, "Override", PartName=part_name, ContentType=content_type)

        root_rels = etree.Element("Relationships", nsmap={None: REL_NS})
        etree.SubElement(root_rels, "Relationship", Id="rId1", Type=f"{DOC_REL_NS}/officeDocument", Target="word/document.xml")
        etree.SubElement(root_rels, "Relationship", Id="rId2", Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", Target="docProps/core.xml")
        etree.SubElement(root_rels, "Relationship", Id="rId3", Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties", Target="docProps/app.xml")

        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", etree.tostring(content_types, xml_declaration=True, encoding="UTF-8", standalone="yes"))
            zf.writestr("_rels/.rels", etree.tostring(root_rels, xml_declaration=True, encoding="UTF-8", standalone="yes"))
            zf.writestr("docProps/core.xml", build_core_properties_xml())
            zf.writestr("docProps/app.xml", build_app_properties_xml())
            zf.writestr("word/document.xml", self.build_document_xml())
            zf.writestr("word/_rels/document.xml.rels", self.build_document_rels_xml())
            zf.writestr("word/styles.xml", build_styles_xml())
            zf.writestr("word/settings.xml", build_settings_xml())
            for image_name, image_bytes, _ in self.images:
                zf.writestr(f"word/media/{image_name}", image_bytes)


def build_core_properties_xml() -> bytes:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    root = etree.Element(
        qn("cp:coreProperties"),
        nsmap={
            "cp": DOCX_NS["cp"],
            "dc": DOCX_NS["dc"],
            "dcterms": DOCX_NS["dcterms"],
            "dcmitype": DOCX_NS["dcmitype"],
            "xsi": DOCX_NS["xsi"],
        },
    )
    etree.SubElement(root, qn("dc:title")).text = "基于数据感知的多智能体专利分析系统设计与实现"
    etree.SubElement(root, qn("dc:creator")).text = "Codex"
    etree.SubElement(root, qn("cp:lastModifiedBy")).text = "Codex"
    created = etree.SubElement(root, qn("dcterms:created"), {qn("xsi:type"): "dcterms:W3CDTF"})
    created.text = now
    modified = etree.SubElement(root, qn("dcterms:modified"), {qn("xsi:type"): "dcterms:W3CDTF"})
    modified.text = now
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def build_app_properties_xml() -> bytes:
    root = etree.Element(
        "Properties",
        nsmap={
            None: "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
            "vt": "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes",
        },
    )
    etree.SubElement(root, "Application").text = "Microsoft Office Word"
    etree.SubElement(root, "AppVersion").text = "16.0000"
    etree.SubElement(root, "SharedDoc").text = "false"
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def build_styles_xml() -> bytes:
    root = etree.Element(qn("w:styles"), nsmap={"w": DOCX_NS["w"]})

    doc_defaults = etree.SubElement(root, qn("w:docDefaults"))
    rpr_default = etree.SubElement(doc_defaults, qn("w:rPrDefault"))
    rpr = etree.SubElement(rpr_default, qn("w:rPr"))
    etree.SubElement(rpr, qn("w:rFonts"), {qn("w:ascii"): "Times New Roman", qn("w:hAnsi"): "Times New Roman", qn("w:eastAsia"): "宋体"})
    etree.SubElement(rpr, qn("w:sz"), {qn("w:val"): "24"})
    etree.SubElement(rpr, qn("w:lang"), {qn("w:eastAsia"): "zh-CN"})
    ppr_default = etree.SubElement(doc_defaults, qn("w:pPrDefault"))
    ppr = etree.SubElement(ppr_default, qn("w:pPr"))
    etree.SubElement(ppr, qn("w:spacing"), {qn("w:before"): "0", qn("w:after"): "160", qn("w:line"): "360", qn("w:lineRule"): "auto"})

    def add_style(style_id: str, name: str, *, size: int = 24, bold: bool = False, italic: bool = False, align: str | None = None, east_font: str = "宋体", ascii_font: str = "Times New Roman") -> None:
        style = etree.SubElement(root, qn("w:style"), {qn("w:type"): "paragraph", qn("w:styleId"): style_id})
        etree.SubElement(style, qn("w:name"), {qn("w:val"): name})
        ppr = etree.SubElement(style, qn("w:pPr"))
        etree.SubElement(ppr, qn("w:spacing"), {qn("w:before"): "0", qn("w:after"): "160", qn("w:line"): "360", qn("w:lineRule"): "auto"})
        if align:
            etree.SubElement(ppr, qn("w:jc"), {qn("w:val"): align})
        rpr = etree.SubElement(style, qn("w:rPr"))
        etree.SubElement(rpr, qn("w:rFonts"), {qn("w:ascii"): ascii_font, qn("w:hAnsi"): ascii_font, qn("w:eastAsia"): east_font})
        etree.SubElement(rpr, qn("w:sz"), {qn("w:val"): str(size)})
        if bold:
            etree.SubElement(rpr, qn("w:b"))
        if italic:
            etree.SubElement(rpr, qn("w:i"))

    add_style("Normal", "Normal")
    add_style("Title", "Title", size=36, bold=True, align="center", east_font="黑体")
    add_style("Subtitle", "Subtitle", size=24, align="center", east_font="黑体")
    add_style("Heading1", "Heading 1", size=32, bold=True, east_font="黑体")
    add_style("Heading2", "Heading 2", size=28, bold=True, east_font="黑体")
    add_style("Heading3", "Heading 3", size=24, bold=True, east_font="黑体")
    add_style("Heading4", "Heading 4", size=24, bold=True)
    add_style("Caption", "Caption", size=22, italic=True, align="center")
    add_style("Code", "Code", size=20, east_font="Consolas", ascii_font="Consolas")
    add_style("Quote", "Quote", size=22, italic=True)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def build_settings_xml() -> bytes:
    root = etree.Element(qn("w:settings"), nsmap={"w": DOCX_NS["w"]})
    etree.SubElement(root, qn("w:zoom"), {qn("w:percent"): "100"})
    etree.SubElement(root, qn("w:characterSpacingControl"), {qn("w:val"): "doNotCompress"})
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def render_cover(writer: DocxWriter, cover_fields: dict) -> None:
    if cover_fields["image_path"]:
        writer.add_image(cover_fields["image_path"], width_factor=0.55)
    writer.add_paragraph("硕士学位论文", style="Title", align="center")
    writer.add_paragraph("THESIS OF MASTER DEGREE", style="Subtitle", align="center")
    writer.add_paragraph("")
    writer.add_paragraph(f"论文题目：{cover_fields['title_cn_lines'][0]}", style="Heading2", align="center")
    writer.add_paragraph(cover_fields["title_cn_lines"][1], style="Heading2", align="center")
    writer.add_paragraph(f"英文题目：{cover_fields['title_en_lines'][0]}", style="Heading3", align="center")
    writer.add_paragraph(cover_fields["title_en_lines"][1], style="Heading3", align="center")
    writer.add_paragraph("")
    writer.add_paragraph(f"作者：{cover_fields['author']}", style="Heading3", align="center")
    writer.add_paragraph(f"指导教师：{cover_fields['advisor']}", style="Heading3", align="center")
    writer.add_paragraph(f"完成日期：{cover_fields['date']}", style="Heading3", align="center")
    writer.add_page_break()


def convert_thesis() -> None:
    cover_text = (TEXTFILES_DIR / "Cover.tex").read_text(encoding="utf-8")
    bbl_text = (TEMPLATE_DIR / "main.bbl").read_text(encoding="utf-8")
    cite_map = build_citation_map(bbl_text)
    ref_map = build_reference_map()
    cover_fields = extract_cover_fields(cover_text)
    bibliography = parse_bibliography(bbl_text, cite_map, ref_map)

    writer = DocxWriter()
    render_cover(writer, cover_fields)

    for tex_name in ORDERED_TEX_FILES:
        tex_text = (TEXTFILES_DIR / tex_name).read_text(encoding="utf-8")
        for block in parse_tex_blocks(tex_text, cite_map, ref_map):
            if block.kind == "page_break":
                writer.add_page_break()
            elif block.kind == "heading":
                writer.add_heading(block.data["title"], block.data["level"])
            elif block.kind == "paragraph":
                writer.add_paragraph(block.data["text"])
            elif block.kind == "quote":
                writer.add_paragraph(block.data["text"], style="Quote")
            elif block.kind == "enumerate":
                for index, item in enumerate(block.data["items"], start=1):
                    writer.add_paragraph(f"（{index}）{item}")
            elif block.kind == "figure":
                writer.add_image(block.data["image_path"], caption=block.data["caption"], width_factor=block.data["width_factor"])
            elif block.kind == "table":
                writer.add_table(block.data["rows"], caption=block.data["caption"], note=block.data["note"])
            elif block.kind == "algorithm":
                if block.data["caption"]:
                    writer.add_paragraph(f"算法：{block.data['caption']}", style="Caption", align="center")
                writer.add_paragraph(block.data["body"], style="Code")
            elif block.kind == "listing":
                writer.add_paragraph(block.data["text"], style="Code")

    writer.add_page_break()
    writer.add_heading("参考文献", 1)
    for item in bibliography:
        writer.add_paragraph(item)

    ack_text = (TEXTFILES_DIR / "7Acknowledgement.tex").read_text(encoding="utf-8")
    for block in parse_tex_blocks(ack_text, cite_map, ref_map):
        if block.kind == "heading":
            writer.add_heading(block.data["title"], block.data["level"])
        elif block.kind == "paragraph":
            writer.add_paragraph(block.data["text"])

    for title, paragraphs in MANUAL_SECTIONS:
        writer.add_heading(title, 1)
        for paragraph in paragraphs:
            writer.add_paragraph(paragraph)

    writer.save(OUTPUT_PATH)


if __name__ == "__main__":
    convert_thesis()
    print(OUTPUT_PATH)
