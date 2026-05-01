#!/usr/bin/env python3
"""
存档操作脚本 — novel-audit 技能
用法:
  python3 archive_ops.py init <书名>              # 初始化书的存档目录
  python3 archive_ops.py ingest <书名> <章节号> <json_file>  # 录入章节
  python3 archive_ops.py lint <书名> [--chapter N]  # 自检
  python3 archive_ops.py query <书名> [--section characters|settings|timeline|hooks|foreshadowing]  # 查询
  python3 archive_ops.py list                     # 列出所有书
"""

import json
import sys
import os
import shutil
from datetime import datetime, date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ARCHIVES_DIR = SKILL_DIR / "archives"
TEMPLATE_DIR = ARCHIVES_DIR / "TEMPLATE"


def get_book_dir(book_name):
    """获取书的存档目录"""
    return ARCHIVES_DIR / book_name


def load_md_sections(filepath):
    """解析 markdown 为 {标题: 内容} 字典"""
    if not filepath.exists():
        return {}
    content = filepath.read_text(encoding="utf-8")
    sections = {}
    current_key = None
    current_lines = []

    for line in content.split("\n"):
        if line.startswith("## ") or line.startswith("# "):
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = line.lstrip("#").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections


# ==================== init ====================
def cmd_init(book_name):
    """初始化书的存档目录"""
    book_dir = get_book_dir(book_name)

    if book_dir.exists():
        print(f"⚠️ 存档已存在: {book_dir}")
        return

    # 从模板复制
    shutil.copytree(TEMPLATE_DIR, book_dir)

    # 替换模板中的书名
    for md_file in book_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        content = content.replace("《书名》", f"《{book_name}》")
        content = content.replace("书名", book_name)
        md_file.write_text(content, encoding="utf-8")

    print(f"✅ 存档已初始化: {book_dir}")
    print(f"  目录结构:")
    for item in sorted(book_dir.rglob("*")):
        if item.is_file():
            rel = item.relative_to(book_dir)
            print(f"    {rel}")


# ==================== ingest ====================
def cmd_ingest(book_name, chapter_num, json_file):
    """录入章节数据到存档"""
    book_dir = get_book_dir(book_name)

    if not book_dir.exists():
        print(f"❌ 存档不存在: {book_dir}")
        print(f"  请先运行: python3 archive_ops.py init {book_name}")
        sys.exit(1)

    # 读取章节数据
    with open(json_file, "r", encoding="utf-8") as f:
        chapter_data = json.load(f)

    ch_num = int(chapter_num)
    ch_file = book_dir / "chapters" / f"ch{ch_num:03d}.md"

    # 1. 创建章节档案
    write_chapter_file(ch_file, ch_num, chapter_data)

    # 2. 更新 characters.md
    if chapter_data.get("characters"):
        update_characters(book_dir, chapter_data["characters"], ch_num)

    # 3. 更新 timeline.md
    if chapter_data.get("data_changes"):
        update_timeline(book_dir, chapter_data["data_changes"], ch_num)

    # 4. 更新 hooks.md
    if chapter_data.get("hooks"):
        update_hooks(book_dir, chapter_data["hooks"], ch_num)

    # 5. 更新 foreshadowing.md
    if chapter_data.get("foreshadowing"):
        update_foreshadowing(book_dir, chapter_data["foreshadowing"], ch_num)

    # 6. 更新 settings.md
    if chapter_data.get("new_settings"):
        update_settings(book_dir, chapter_data["new_settings"], ch_num)

    # 7. 更新 index.md
    update_index(book_dir, chapter_data, ch_num)

    # 8. 追加 log.md
    append_log(book_dir, ch_num, chapter_data)

    # 9. 写读者笔记
    if chapter_data.get("reader_notes"):
        write_reader_notes(book_dir, ch_num, chapter_data["reader_notes"])

    print(f"✅ 第{ch_num}章录入完成")
    print(f"  章节档案: chapters/ch{ch_num:03d}.md")
    updated = []
    if chapter_data.get("characters"):
        updated.append("characters.md")
    if chapter_data.get("data_changes"):
        updated.append("timeline.md")
    if chapter_data.get("hooks"):
        updated.append("hooks.md")
    if chapter_data.get("foreshadowing"):
        updated.append("foreshadowing.md")
    if chapter_data.get("new_settings"):
        updated.append("settings.md")
    if updated:
        print(f"  更新文件: {', '.join(updated)}")


def write_chapter_file(filepath, ch_num, data):
    """写章节档案"""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    content = f"# 第{ch_num}章{'：' + data['title'] if data.get('title') else ''}\n\n"

    # 数据库层
    content += "## 📊 数据库记录\n\n"
    content += f"- **字数：** {data.get('word_count', '未知')}\n"
    content += f"- **情绪值：** {data.get('emotion', '未知')}\n"
    if data.get("story_time"):
        content += f"- **故事时间：** {data['story_time']}\n"
    content += "\n"

    if data.get("summary"):
        content += f"### 内容摘要\n{data['summary']}\n\n"

    if data.get("characters"):
        content += "### 人物出场\n"
        content += "| 人物 | 状态变化 | 依据 |\n"
        content += "|------|----------|------|\n"
        for c in data["characters"]:
            content += f"| {c['name']} | {c.get('change', '无变化')} | {c.get('source', '—')} |\n"
        content += "\n"

    if data.get("data_changes"):
        content += "### 数据变动\n"
        content += "| 项目 | 变动 | 新值 | 依据 |\n"
        content += "|------|------|------|------|\n"
        for d in data["data_changes"]:
            content += f"| {d['item']} | {d.get('change', '—')} | {d.get('new_value', '—')} | {d.get('source', '—')} |\n"
        content += "\n"

    if data.get("hooks"):
        content += "### 钩子\n"
        for h in data["hooks"]:
            content += f"- {h.get('status', '埋下')}: {h['content']}\n"
        content += "\n"

    if data.get("foreshadowing"):
        content += "### 伏笔\n"
        for f in data["foreshadowing"]:
            content += f"- {f.get('status', '埋下')}: {f['content']}\n"
        content += "\n"

    # 读者层
    if data.get("reader_notes"):
        rn = data["reader_notes"]
        content += "---\n\n## 📖 读者理解\n\n"
        if rn.get("saw"):
            content += f"### 我看到的\n{rn['saw']}\n\n"
        if rn.get("know"):
            content += f"### 我知道的\n"
            for item in rn["know"]:
                content += f"- {item}\n"
            content += "\n"
        if rn.get("thinking"):
            content += f"### 我在想的\n"
            for item in rn["thinking"]:
                content += f"- {item}\n"
            content += "\n"
        if rn.get("key_understanding"):
            content += f"### 关键理解\n"
            for item in rn["key_understanding"]:
                content += f"- {item}\n"
            content += "\n"

    # 审核备注
    if data.get("audit_notes"):
        content += "---\n\n## 审核备注\n"
        for key, val in data["audit_notes"].items():
            content += f"- **{key}：** {val}\n"

    filepath.write_text(content, encoding="utf-8")


def update_characters(book_dir, characters, ch_num):
    """更新人物档案"""
    filepath = book_dir / "characters.md"
    existing = filepath.read_text(encoding="utf-8") if filepath.exists() else "# 人物档案\n\n"

    for c in characters:
        name = c["name"]
        change = c.get("change", "")
        if change and change != "无变化":
            # 追加状态变化记录
            marker = f"\n### {name}"
            if marker not in existing:
                existing += f"\n### {name}\n"
                existing += f"- 初始状态: {c.get('initial', '待补充')}\n"
            existing += f"- 第{ch_num}章: {change}\n"

    filepath.write_text(existing, encoding="utf-8")


def update_timeline(book_dir, data_changes, ch_num):
    """更新时间线"""
    filepath = book_dir / "timeline.md"
    existing = filepath.read_text(encoding="utf-8") if filepath.exists() else "# 时间线 & 关键数据\n\n"

    existing += f"\n## 第{ch_num}章\n"
    for d in data_changes:
        existing += f"- {d['item']}: {d.get('change', '—')} → {d.get('new_value', '—')}\n"

    filepath.write_text(existing, encoding="utf-8")


def update_hooks(book_dir, hooks, ch_num):
    """更新钩子追踪"""
    filepath = book_dir / "hooks.md"
    existing = filepath.read_text(encoding="utf-8") if filepath.exists() else "# 钩子追踪\n\n"

    for h in hooks:
        status = h.get("status", "埋下")
        existing += f"- [{status}] 第{ch_num}章: {h['content']}\n"

    filepath.write_text(existing, encoding="utf-8")


def update_foreshadowing(book_dir, foreshadowing, ch_num):
    """更新伏笔追踪"""
    filepath = book_dir / "foreshadowing.md"
    existing = filepath.read_text(encoding="utf-8") if filepath.exists() else "# 伏笔追踪\n\n"

    for f in foreshadowing:
        status = f.get("status", "埋下")
        existing += f"- [{status}] 第{ch_num}章: {f['content']}\n"

    filepath.write_text(existing, encoding="utf-8")


def update_settings(book_dir, new_settings, ch_num):
    """更新设定档案"""
    filepath = book_dir / "settings.md"
    existing = filepath.read_text(encoding="utf-8") if filepath.exists() else "# 设定档案\n\n"

    for s in new_settings:
        existing += f"- 第{ch_num}章新增: {s}\n"

    filepath.write_text(existing, encoding="utf-8")


def update_index(book_dir, chapter_data, ch_num):
    """更新总索引"""
    filepath = book_dir / "index.md"
    existing = filepath.read_text(encoding="utf-8") if filepath.exists() else "# Wiki 索引\n\n"

    # 确保有追踪部分
    if "## 追踪" not in existing:
        existing += "\n## 追踪\n"

    filepath.write_text(existing, encoding="utf-8")


def append_log(book_dir, ch_num, chapter_data):
    """追加操作日志"""
    filepath = book_dir / "log.md"
    today = date.today().isoformat()

    log_entry = f"\n## [{today}] ingest | 第{ch_num}章\n"
    if chapter_data.get("title"):
        log_entry += f"- 章节标题: {chapter_data['title']}\n"
    if chapter_data.get("characters"):
        names = [c["name"] for c in chapter_data["characters"]]
        log_entry += f"- 涉及人物: {', '.join(names)}\n"
    if chapter_data.get("hooks"):
        log_entry += f"- 新增/更新钩子: {len(chapter_data['hooks'])} 个\n"
    if chapter_data.get("foreshadowing"):
        log_entry += f"- 新增/更新伏笔: {len(chapter_data['foreshadowing'])} 个\n"

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(log_entry)


def write_reader_notes(book_dir, ch_num, reader_notes):
    """写读者笔记"""
    filepath = book_dir / "reader-notes.md"
    existing = filepath.read_text(encoding="utf-8") if filepath.exists() else "# 读者笔记\n\n"

    existing += f"\n## 第{ch_num}章\n\n"

    if reader_notes.get("saw"):
        existing += f"### 📖 我看到的\n{reader_notes['saw']}\n\n"
    if reader_notes.get("know"):
        existing += "### 🧠 我知道的\n"
        for item in reader_notes["know"]:
            existing += f"- {item}\n"
        existing += "\n"
    if reader_notes.get("thinking"):
        existing += "### 🔍 我在想的\n"
        for item in reader_notes["thinking"]:
            existing += f"- {item}\n"
        existing += "\n"
    if reader_notes.get("key_understanding"):
        existing += "### 💡 关键理解\n"
        for item in reader_notes["key_understanding"]:
            existing += f"- {item}\n"
        existing += "\n"

    filepath.write_text(existing, encoding="utf-8")


# ==================== lint ====================
def cmd_lint(book_name, chapter=None):
    """自检"""
    book_dir = get_book_dir(book_name)

    if not book_dir.exists():
        print(f"❌ 存档不存在: {book_dir}")
        sys.exit(1)

    issues = []
    warnings = []

    # 1. 检查文件完整性
    expected_files = [
        "index.md", "log.md", "book.md", "characters.md",
        "timeline.md", "settings.md", "hooks.md",
        "foreshadowing.md", "reader-notes.md"
    ]
    for f in expected_files:
        if not (book_dir / f).exists():
            issues.append(f"缺失文件: {f}")

    # 2. 检查伏笔健康度
    ff_file = book_dir / "foreshadowing.md"
    if ff_file.exists():
        content = ff_file.read_text(encoding="utf-8")
        open_ff = [l for l in content.split("\n") if "[埋下]" in l and "[回收]" not in l]
        if len(open_ff) > 10:
            warnings.append(f"未回收伏笔过多: {len(open_ff)} 个")

    # 3. 检查钩子健康度
    hooks_file = book_dir / "hooks.md"
    if hooks_file.exists():
        content = hooks_file.read_text(encoding="utf-8")
        open_hooks = [l for l in content.split("\n") if "[埋下]" in l and "[解决]" not in l]
        if len(open_hooks) > 10:
            warnings.append(f"未解决钩子过多: {len(open_hooks)} 个")

    # 4. 检查章节连续性
    chapters_dir = book_dir / "chapters"
    if chapters_dir.exists():
        ch_files = sorted(chapters_dir.glob("ch*.md"))
        if ch_files:
            nums = []
            for f in ch_files:
                try:
                    num = int(f.stem.replace("ch", ""))
                    nums.append(num)
                except ValueError:
                    pass
            if nums:
                expected = set(range(min(nums), max(nums) + 1))
                missing = expected - set(nums)
                if missing:
                    issues.append(f"缺失章节: {sorted(missing)}")

    # 5. 检查人物档案
    char_file = book_dir / "characters.md"
    if char_file.exists():
        content = char_file.read_text(encoding="utf-8")
        if content.count("###") == 0:
            warnings.append("人物档案为空，未记录任何人物")

    # 输出报告
    print(f"🏥 自检报告 — 《{book_name}》")
    print(f"{'='*40}")

    if not issues and not warnings:
        print("✅ 全部通过，无问题")
    else:
        if issues:
            print(f"\n❌ 问题 ({len(issues)}):")
            for i in issues:
                print(f"  - {i}")
        if warnings:
            print(f"\n⚠️ 警告 ({len(warnings)}):")
            for w in warnings:
                print(f"  - {w}")

    # 追加 log
    log_file = book_dir / "log.md"
    today = date.today().isoformat()
    log_entry = f"\n## [{today}] lint"
    if chapter:
        log_entry += f" | 第{chapter}章"
    log_entry += f"\n- 问题: {len(issues)}\n- 警告: {len(warnings)}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)


# ==================== query ====================
def cmd_query(book_name, section=None):
    """查询存档信息"""
    book_dir = get_book_dir(book_name)

    if not book_dir.exists():
        print(f"❌ 存档不存在: {book_dir}")
        sys.exit(1)

    if section:
        # 查询特定部分
        section_map = {
            "characters": "characters.md",
            "settings": "settings.md",
            "timeline": "timeline.md",
            "hooks": "hooks.md",
            "foreshadowing": "foreshadowing.md",
            "reader-notes": "reader-notes.md",
            "index": "index.md",
        }
        filename = section_map.get(section)
        if filename:
            filepath = book_dir / filename
            if filepath.exists():
                print(filepath.read_text(encoding="utf-8"))
            else:
                print(f"⚠️ 文件不存在: {filename}")
        else:
            print(f"❌ 未知部分: {section}")
            print(f"  可选: {', '.join(section_map.keys())}")
    else:
        # 显示总览
        print(f"📖 《{book_name}》存档总览")
        print(f"{'='*40}")
        for item in sorted(book_dir.iterdir()):
            if item.is_file():
                size = item.stat().st_size
                print(f"  {item.name:<25} {size:>6} bytes")
            elif item.is_dir():
                count = len(list(item.glob("*")))
                print(f"  {item.name + '/':<25} {count:>6} 个文件")


# ==================== list ====================
def cmd_list():
    """列出所有书"""
    if not ARCHIVES_DIR.exists():
        print("📚 暂无存档")
        return

    books = [d for d in ARCHIVES_DIR.iterdir() if d.is_dir() and d.name != "TEMPLATE"]

    if not books:
        print("📚 暂无存档")
        return

    print(f"📚 共 {len(books)} 本书:")
    for book_dir in sorted(books):
        ch_count = len(list((book_dir / "chapters").glob("ch*.md"))) if (book_dir / "chapters").exists() else 0
        print(f"  - {book_dir.name} ({ch_count} 章)")


# ==================== main ====================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        if len(sys.argv) < 3:
            print("用法: archive_ops.py init <书名>")
            sys.exit(1)
        cmd_init(sys.argv[2])
    elif cmd == "ingest":
        if len(sys.argv) < 5:
            print("用法: archive_ops.py ingest <书名> <章节号> <json_file>")
            sys.exit(1)
        cmd_ingest(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "lint":
        if len(sys.argv) < 3:
            print("用法: archive_ops.py lint <书名> [--chapter N]")
            sys.exit(1)
        ch = None
        if "--chapter" in sys.argv:
            idx = sys.argv.index("--chapter")
            if idx + 1 < len(sys.argv):
                ch = sys.argv[idx + 1]
        cmd_lint(sys.argv[2], ch)
    elif cmd == "query":
        if len(sys.argv) < 3:
            print("用法: archive_ops.py query <书名> [--section characters|settings|...]")
            sys.exit(1)
        section = None
        if "--section" in sys.argv:
            idx = sys.argv.index("--section")
            if idx + 1 < len(sys.argv):
                section = sys.argv[idx + 1]
        cmd_query(sys.argv[2], section)
    elif cmd == "list":
        cmd_list()
    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
