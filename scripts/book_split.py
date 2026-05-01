#!/usr/bin/env python3
"""
拆书脚本 — 将 txt 小说按章节拆分
用法:
  python3 book_split.py <txt文件> [--output-dir <输出目录>] [--pattern <正则>]
  
默认章节匹配模式: 第[一二三四五六七八九十百千\d]+章|Chapter\s*\d+|第\d+章
"""

import re
import sys
import os
import json
from pathlib import Path

DEFAULT_PATTERNS = [
    r'^第[一二三四五六七八九十百千\d]+章',
    r'^第\s*\d+\s*章',
    r'^Chapter\s*\d+',
    r'^CHAPTER\s*\d+',
    r'^\d+\.\s+',  # 1. 标题格式
]


def find_chapter_pattern(content):
    """自动检测章节格式"""
    lines = content.split("\n")
    for pattern in DEFAULT_PATTERNS:
        matches = []
        for i, line in enumerate(lines):
            if re.match(pattern, line.strip()):
                matches.append((i, line.strip()))
        # 如果匹配到合理数量的章节（至少2个，不超过5000个）
        if 2 <= len(matches) <= 5000:
            return pattern, matches
    return None, []


def split_book(txt_path, output_dir=None, custom_pattern=None):
    """拆分小说为章节文件"""
    txt_path = Path(txt_path)
    if not txt_path.exists():
        print(f"❌ 文件不存在: {txt_path}")
        sys.exit(1)

    # 读取文件
    try:
        content = txt_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = txt_path.read_text(encoding="gbk")

    # 检测或使用自定义模式
    if custom_pattern:
        pattern = custom_pattern
        lines = content.split("\n")
        matches = []
        for i, line in enumerate(lines):
            if re.match(pattern, line.strip()):
                matches.append((i, line.strip()))
        if not matches:
            print(f"❌ 自定义模式未匹配到任何章节: {pattern}")
            sys.exit(1)
    else:
        pattern, matches = find_chapter_pattern(content)

    if not matches:
        print("❌ 未检测到章节格式")
        print("  请用 --pattern 参数指定章节匹配正则")
        print(f"  例如: --pattern '^第\\d+章'")
        sys.exit(1)

    # 输出目录
    if output_dir is None:
        output_dir = txt_path.parent / f"{txt_path.stem}_chapters"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    lines = content.split("\n")
    chapters = []

    # 按章节拆分
    for idx, (line_num, title) in enumerate(matches):
        # 章节内容：从当前章节标题到下一个章节标题
        start = line_num
        end = matches[idx + 1][0] if idx + 1 < len(matches) else len(lines)

        chapter_content = "\n".join(lines[start:end]).strip()

        # 提取章节号
        ch_num = idx + 1
        num_match = re.search(r'\d+', title)
        if num_match:
            ch_num = int(num_match.group())

        # 写入文件
        ch_file = output_dir / f"ch{ch_num:03d}.txt"
        ch_file.write_text(chapter_content, encoding="utf-8")

        # 统计
        char_count = len(chapter_content)
        word_count = len(re.sub(r'\s+', '', chapter_content))  # 中文字符数

        chapters.append({
            "chapter": ch_num,
            "title": title,
            "file": str(ch_file),
            "char_count": char_count,
            "word_count": word_count,
            "line_start": line_num + 1,
        })

    # 写入元数据
    meta = {
        "source": str(txt_path),
        "total_chapters": len(chapters),
        "total_chars": len(content),
        "total_words": len(re.sub(r'\s+', '', content)),
        "pattern": pattern,
        "chapters": chapters,
    }

    meta_file = output_dir / "meta.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 输出统计
    print(f"📚 拆书完成: {txt_path.name}")
    print(f"{'='*40}")
    print(f"总章节数: {len(chapters)}")
    print(f"总字数:   {meta['total_words']:,}")
    print(f"输出目录: {output_dir}")
    print(f"元数据:   {meta_file}")
    print()
    print(f"📖 章节列表:")
    for ch in chapters[:20]:
        print(f"  ch{ch['chapter']:03d}.txt  {ch['title']:<30} {ch['word_count']:>6} 字")
    if len(chapters) > 20:
        print(f"  ... 共 {len(chapters)} 章")

    return meta


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    txt_path = sys.argv[1]
    output_dir = None
    custom_pattern = None

    # 解析参数
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--output-dir" and i + 1 < len(args):
            output_dir = args[i + 1]
            i += 2
        elif args[i] == "--pattern" and i + 1 < len(args):
            custom_pattern = args[i + 1]
            i += 2
        else:
            i += 1

    split_book(txt_path, output_dir, custom_pattern)


if __name__ == "__main__":
    main()
