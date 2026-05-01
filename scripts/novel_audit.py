#!/usr/bin/env python3
"""
novel-audit 技能 — 主入口脚本
用法:
  python3 novel_audit.py knowledge status|forget|integrate|export|add|check-similar
  python3 novel_audit.py archive init|ingest|lint|query|list
  python3 novel_audit.py split <txt文件> [选项]
  python3 novel_audit.py audit prepare|update <书名> [选项]
"""

import sys
import os

# 把 scripts 目录加入 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import knowledge_ops
import archive_ops
import book_split
import quick_audit


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    module = sys.argv[1]

    if module == "knowledge":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        knowledge_ops.main()
    elif module == "archive":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        archive_ops.main()
    elif module == "split":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        book_split.main()
    elif module == "audit":
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        quick_audit.main()
    else:
        print(f"❌ 未知模块: {module}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
