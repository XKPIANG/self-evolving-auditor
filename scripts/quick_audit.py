#!/usr/bin/env python3
"""
快速审核数据准备脚本 — novel-audit 技能
用法:
  python3 quick_audit.py prepare <书名>              # 准备审核上下文
  python3 quick_audit.py prepare <书名> --chapter N  # 指定章节号
  python3 quick_audit.py update <书名> <章节号> <json_file>  # 审核后更新存档
  
输出 JSON，供 AI 直接用于审核分析，无需多次读取文件。
"""

import json
import sys
import os
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_FILE = SKILL_DIR / "knowledge" / "knowledge.json"
ARCHIVES_DIR = SKILL_DIR / "archives"
REFERENCES_DIR = SKILL_DIR / "references"


def load_file(path):
    """读取文件，不存在返回空字符串"""
    p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def prepare_context(book_name, chapter=None):
    """准备审核上下文（一次性读取所有需要的数据）"""
    book_dir = ARCHIVES_DIR / book_name

    # 1. 读取知识库
    knowledge = {}
    if KNOWLEDGE_FILE.exists():
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            knowledge = json.load(f)

    # 2. 读取存档数据
    archive_data = {}
    if book_dir.exists():
        archive_files = [
            "characters.md", "settings.md", "timeline.md",
            "hooks.md", "foreshadowing.md", "reader-notes.md",
            "index.md"
        ]
        for fname in archive_files:
            key = fname.replace(".md", "").replace("-", "_")
            archive_data[key] = load_file(book_dir / fname)

        # 读取最近的章节档案
        chapters_dir = book_dir / "chapters"
        if chapters_dir.exists():
            ch_files = sorted(chapters_dir.glob("ch*.md"))
            if ch_files:
                # 最近 3 章
                recent = ch_files[-3:]
                archive_data["recent_chapters"] = {
                    f.stem: load_file(f) for f in recent
                }

    # 3. 组装输出
    output = {
        "book_name": book_name,
        "chapter": chapter,
        "knowledge_summary": {
            "version": knowledge.get("version", 0),
            "total_books_analyzed": knowledge.get("total_books_analyzed", 0),
            "rhythm_patterns_count": len(knowledge.get("rhythm_patterns", [])),
            "hook_patterns_count": len(knowledge.get("hook_patterns", [])),
            "logic_rules_count": len(knowledge.get("logic_rules", [])),
            "style_patterns_count": len(knowledge.get("style_patterns", [])),
            "anti_patterns_count": len(knowledge.get("anti_patterns", [])),
            "ai_style_patterns_count": len(knowledge.get("ai_style_patterns", [])),
            "platform_insights_count": len(knowledge.get("platform_insights", [])),
        },
        "knowledge": knowledge,
        "archive": archive_data,
        "archive_exists": book_dir.exists(),
    }

    return output


def update_after_audit(book_name, chapter_num, json_file):
    """审核后更新存档（调用 archive_ops.py 的逻辑）"""
    # 导入 archive_ops
    sys.path.insert(0, str(Path(__file__).parent))
    from archive_ops import cmd_ingest

    cmd_ingest(book_name, chapter_num, json_file)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    book_name = sys.argv[2]

    if cmd == "prepare":
        chapter = None
        if "--chapter" in sys.argv:
            idx = sys.argv.index("--chapter")
            if idx + 1 < len(sys.argv):
                chapter = int(sys.argv[idx + 1])

        result = prepare_context(book_name, chapter)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "update":
        if len(sys.argv) < 5:
            print("用法: quick_audit.py update <书名> <章节号> <json_file>")
            sys.exit(1)
        update_after_audit(sys.argv[2], sys.argv[3], sys.argv[4])

    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
