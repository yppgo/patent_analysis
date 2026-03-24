#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to LaTeX converter for thesis
自动将 Markdown 论文章节转换为 LaTeX 格式
"""

import re
import os
from pathlib import Path

class MarkdownToLatexConverter:
    def __init__(self):
        # LaTeX 特殊字符转义映射
        self.special_chars = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
            '\\': r'\textbackslash{}',
        }

    def escape_latex(self, text):
        """转义 LaTeX 特殊字符，但保留已经是 LaTeX 命令的部分"""
        # 先保护已有的 LaTeX 命令
        latex_commands = re.findall(r'\\[a-zA-Z]+(?:\{[^}]*\})?', text)
        placeholders = {}
        for i, cmd in enumerate(latex_commands):
            placeholder = f"__LATEX_CMD_{i}__"
            placeholders[placeholder] = cmd
            text = text.replace(cmd, placeholder, 1)

        # 转义特殊字符
        for char, escaped in self.special_chars.items():
            if char != '\\':  # 反斜杠已经在保护命令时处理了
                text = text.replace(char, escaped)

        # 恢复 LaTeX 命令
        for placeholder, cmd in placeholders.items():
            text = text.replace(placeholder, cmd)

        return text

    def convert_heading(self, line):
        """转换标题"""
        match = re.match(r'^(#{1,3})\s+(.+)$', line)
        if not match:
            return None

        level = len(match.group(1))
        title = match.group(2).strip()
        title = self.escape_latex(title)

        # 移除标题中的编号（如 "1.1"），LaTeX 会自动编号
        title = re.sub(r'^\d+(\.\d+)*\s+', '', title)

        if level == 1:
            return f'\\section{{{title}}}'
        elif level == 2:
            return f'\\subsection{{{title}}}'
        elif level == 3:
            return f'\\subsubsection{{{title}}}'
        return None

    def convert_table(self, lines, start_idx):
        """转换 Markdown 表格为 LaTeX tabular"""
        # 找到表格结束位置
        end_idx = start_idx
        while end_idx < len(lines) and lines[end_idx].strip().startswith('|'):
            end_idx += 1

        table_lines = lines[start_idx:end_idx]
        if len(table_lines) < 2:
            return None, start_idx

        # 解析表头
        header = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
        num_cols = len(header)

        # 跳过分隔行
        data_lines = table_lines[2:]

        # 构建 LaTeX 表格
        latex_lines = []
        latex_lines.append('\\begin{table}[htbp]')
        latex_lines.append('\\centering')
        latex_lines.append('\\caption{表格标题}')  # 需要手动填写
        latex_lines.append('\\label{tab:label}')  # 需要手动填写

        # 列格式：居中对齐
        col_format = '|' + 'c|' * num_cols
        latex_lines.append(f'\\begin{{tabular}}{{{col_format}}}')
        latex_lines.append('\\hline')

        # 表头
        header_escaped = [self.escape_latex(h) for h in header]
        latex_lines.append(' & '.join(header_escaped) + ' \\\\')
        latex_lines.append('\\hline')

        # 数据行
        for line in data_lines:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(cells) == num_cols:
                cells_escaped = [self.escape_latex(c) for c in cells]
                latex_lines.append(' & '.join(cells_escaped) + ' \\\\')
                latex_lines.append('\\hline')

        latex_lines.append('\\end{tabular}')
        latex_lines.append('\\end{table}')

        return '\n'.join(latex_lines), end_idx

    def convert_list(self, lines, start_idx):
        """转换列表"""
        end_idx = start_idx
        list_items = []
        list_type = None

        while end_idx < len(lines):
            line = lines[end_idx].strip()

            # 无序列表
            if re.match(r'^[-*+]\s+', line):
                if list_type is None:
                    list_type = 'itemize'
                item = re.sub(r'^[-*+]\s+', '', line)
                list_items.append(self.escape_latex(item))
                end_idx += 1
            # 有序列表
            elif re.match(r'^\d+\.\s+', line):
                if list_type is None:
                    list_type = 'enumerate'
                item = re.sub(r'^\d+\.\s+', '', line)
                list_items.append(self.escape_latex(item))
                end_idx += 1
            # 列表结束
            elif line == '':
                end_idx += 1
                break
            else:
                break

        if not list_items:
            return None, start_idx

        latex_lines = [f'\\begin{{{list_type}}}']
        for item in list_items:
            latex_lines.append(f'\\item {item}')
        latex_lines.append(f'\\end{{{list_type}}}')

        return '\n'.join(latex_lines), end_idx

    def convert_paragraph(self, line):
        """转换普通段落"""
        line = line.strip()
        if not line:
            return ''

        # 转义特殊字符
        line = self.escape_latex(line)

        # 处理粗体 **text** -> \textbf{text}
        line = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', line)

        # 处理斜体 *text* -> \textit{text}
        line = re.sub(r'\*(.+?)\*', r'\\textit{\1}', line)

        # 处理行内代码 `code` -> \texttt{code}
        line = re.sub(r'`(.+?)`', r'\\texttt{\1}', line)

        return line

    def convert_file(self, md_path, tex_path):
        """转换单个 Markdown 文件为 LaTeX"""
        print(f"Converting {md_path} -> {tex_path}")

        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        latex_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            # 跳过空行
            if not line.strip():
                latex_lines.append('')
                i += 1
                continue

            # 标题
            heading = self.convert_heading(line)
            if heading:
                latex_lines.append('')
                latex_lines.append(heading)
                latex_lines.append('')
                i += 1
                continue

            # 表格
            if line.strip().startswith('|'):
                table_latex, new_idx = self.convert_table(lines, i)
                if table_latex:
                    latex_lines.append('')
                    latex_lines.append(table_latex)
                    latex_lines.append('')
                    i = new_idx
                    continue

            # 列表
            if re.match(r'^[-*+]\s+', line.strip()) or re.match(r'^\d+\.\s+', line.strip()):
                list_latex, new_idx = self.convert_list(lines, i)
                if list_latex:
                    latex_lines.append('')
                    latex_lines.append(list_latex)
                    latex_lines.append('')
                    i = new_idx
                    continue

            # 普通段落
            para = self.convert_paragraph(line)
            if para:
                latex_lines.append(para)

            i += 1

        # 写入 LaTeX 文件
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(latex_lines))

        print(f"  [OK] Converted successfully")


def main():
    """主函数：批量转换所有章节"""
    converter = MarkdownToLatexConverter()

    # 定义文件映射
    thesis_dir = Path(__file__).parent
    latex_dir = thesis_dir / "中国人民大学信息学院硕士毕业论文latex模板" / "textfiles"

    file_mapping = {
        "08_摘要.md": "0Abstract.tex",
        "01_绪论.md": "1Introduction.tex",
        "02_研究综述.md": "2Related_work.tex",
        "03_系统设计方案.md": "3FirstResearch.tex",
        "04_系统原型实现.md": "4SecondResearch.tex",
        "05_实验与评估.md": "5ThirdResearch.tex",
        "06_系统应用示例.md": "6Conclusion_part1.tex",
        "07_总结与展望.md": "6Conclusion_part2.tex",
    }

    print("=" * 60)
    print("Markdown to LaTeX Converter")
    print("=" * 60)
    print()

    for md_file, tex_file in file_mapping.items():
        md_path = thesis_dir / md_file
        tex_path = latex_dir / tex_file

        if not md_path.exists():
            print(f"[WARNING] {md_file} not found, skipping...")
            continue

        try:
            converter.convert_file(md_path, tex_path)
        except Exception as e:
            print(f"[ERROR] Error converting {md_file}: {e}")

    print()
    print("=" * 60)
    print("Conversion completed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. 检查生成的 .tex 文件")
    print("2. 手动调整表格标题和标签")
    print("3. 添加图片引用 \\includegraphics{}")
    print("4. 检查引用标记 \\cite{}")
    print("5. 合并 6Conclusion_part1.tex 和 6Conclusion_part2.tex 到 6Conclusion.tex")


if __name__ == "__main__":
    main()
