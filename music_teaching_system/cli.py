from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import convert_pdf_to_teaching_system


def main() -> None:
    parser = argparse.ArgumentParser(description="将包含乐谱与分析图表的 PDF 转化为互动教学系统")
    parser.add_argument("pdf", help="输入 PDF 路径（或可读取的文本文件）")
    parser.add_argument("-o", "--output", default="teaching_system_output", help="输出目录")
    args = parser.parse_args()

    bundle = convert_pdf_to_teaching_system(Path(args.pdf), Path(args.output))
    print(f"✅ 已生成系统：{args.output}")
    print(f"- 章节数: {len(bundle.sections)}")
    print(f"- 审计日志条数: {len(bundle.audit_log)}")


if __name__ == "__main__":
    main()
