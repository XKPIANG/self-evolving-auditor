#!/usr/bin/env python3
"""
知识库操作脚本 — novel-audit 技能
用法:
  python3 knowledge_ops.py status              # 查看知识库状态
  python3 knowledge_ops.py forget [--dry-run]  # 运行遗忘检查
  python3 knowledge_ops.py integrate           # 去重整合
  python3 knowledge_ops.py add <type> <json>   # 添加知识条目
  python3 knowledge_ops.py export              # 导出可读格式
  python3 knowledge_ops.py check-similar <type> <description>  # 查重
"""

import json
import sys
import os
from datetime import datetime, date
from pathlib import Path
from difflib import SequenceMatcher

SKILL_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_FILE = SKILL_DIR / "knowledge" / "knowledge.json"
BOOK_LOG_FILE = SKILL_DIR / "knowledge" / "book_log.json"
VERSION_FILE = SKILL_DIR / "knowledge" / "version.txt"

VALID_TYPES = [
    "rhythm_patterns", "hook_patterns", "logic_rules",
    "style_patterns", "anti_patterns", "ai_style_patterns",
    "platform_insights"
]


def load_knowledge():
    """加载知识库"""
    if not KNOWLEDGE_FILE.exists():
        return {
            "version": 1,
            "last_updated": str(date.today()),
            "total_books_analyzed": 0,
            **{t: [] for t in VALID_TYPES}
        }
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_knowledge(data):
    """保存知识库"""
    data["last_updated"] = str(date.today())
    KNOWLEDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_book_log():
    """加载拆解记录"""
    if not BOOK_LOG_FILE.exists():
        return {"books": []}
    with open(BOOK_LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_book_log(data):
    """保存拆解记录"""
    with open(BOOK_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_version():
    """获取当前版本号"""
    if VERSION_FILE.exists():
        raw = VERSION_FILE.read_text().strip().lstrip("vV")
        return int(raw) if raw.isdigit() else 1
    return 1


def bump_version():
    """版本号 +1"""
    v = get_version() + 1
    VERSION_FILE.write_text(f"v{v}")
    return v


def count_all_entries(knowledge):
    """统计所有条目数"""
    return sum(len(knowledge.get(t, [])) for t in VALID_TYPES)


# ==================== status ====================
def cmd_status():
    """查看知识库状态"""
    knowledge = load_knowledge()
    book_log = load_book_log()
    version = get_version()
    total = count_all_entries(knowledge)

    print(f"📚 知识库状态")
    print(f"{'='*40}")
    print(f"版本:        v{version}")
    print(f"最后更新:    {knowledge.get('last_updated', '未知')}")
    print(f"已分析书籍:  {knowledge.get('total_books_analyzed', 0)} 本")
    print(f"总条目数:    {total}")
    print()
    print(f"📊 各分类条目:")
    for t in VALID_TYPES:
        count = len(knowledge.get(t, []))
        print(f"  {t:<25} {count:>3} 条")

    if book_log.get("books"):
        print(f"\n📖 最近拆解:")
        for book in book_log["books"][-5:]:
            print(f"  - {book.get('title', '未知')} ({book.get('analyzed', '未知')})")


# ==================== forget ====================
def cmd_forget(dry_run=False):
    """运行遗忘检查"""
    knowledge = load_knowledge()
    total_books = knowledge.get("total_books_analyzed", 0)

    removed = []
    marked = []

    for entry_type in VALID_TYPES:
        entries = knowledge.get(entry_type, [])
        to_keep = []

        for entry in entries:
            confidence = entry.get("confidence", 0.5)
            times_seen = entry.get("times_seen", 1)
            last_updated = entry.get("added", entry.get("last_updated", "2000-01-01"))

            # 规则一：低置信度直接删除
            if confidence < 0.3:
                removed.append({
                    "id": entry.get("id", "unknown"),
                    "type": entry_type,
                    "reason": f"置信度过低 ({confidence} < 0.3)"
                })
                continue

            # 规则二：只出现过一次 + 超过 5 本书未更新
            if times_seen == 1 and total_books >= 5:
                try:
                    added_date = datetime.strptime(last_updated, "%Y-%m-%d")
                    days_since = (datetime.now() - added_date).days
                    books_since = days_since / 7  # 简化估算
                    if books_since > 5:
                        if entry.get("marked_forget", False):
                            # 连续两次标记 → 删除
                            removed.append({
                                "id": entry.get("id", "unknown"),
                                "type": entry_type,
                                "reason": f"长期未见 (times_seen=1, 已过约{int(books_since)}本书)"
                            })
                            continue
                        else:
                            entry["marked_forget"] = True
                            marked.append({
                                "id": entry.get("id", "unknown"),
                                "type": entry_type
                            })
                except ValueError:
                    pass

            to_keep.append(entry)

        knowledge[entry_type] = to_keep

    label = "[DRY RUN] " if dry_run else ""
    print(f"🔍 {label}遗忘检查结果")
    print(f"{'='*40}")
    print(f"待删除: {len(removed)} 条")
    print(f"新标记: {len(marked)} 条")

    if removed:
        print(f"\n❌ 将删除的条目:")
        for r in removed:
            print(f"  [{r['type']}] {r['id']} — {r['reason']}")

    if marked:
        print(f"\n⚠️ 新标记为「待遗忘」:")
        for m in marked:
            print(f"  [{m['type']}] {m['id']} — 下次检查若仍为待遗忘则删除")

    if not removed and not marked:
        print("\n✅ 所有条目健康，无需遗忘")

    if not dry_run and (removed or marked):
        save_knowledge(knowledge)
        print(f"\n💾 已保存（删除 {len(removed)}，标记 {len(marked)}）")


# ==================== integrate ====================
def similar(a, b, threshold=0.6):
    """判断两个字符串是否相似"""
    return SequenceMatcher(None, a, b).ratio() >= threshold


def cmd_integrate():
    """去重整合知识库"""
    knowledge = load_knowledge()
    merged_count = 0

    for entry_type in VALID_TYPES:
        entries = knowledge.get(entry_type, [])
        if len(entries) <= 1:
            continue

        desc_key = None
        for key in ["pattern", "rule", "insight", "structure"]:
            if key in entries[0]:
                desc_key = key
                break

        if not desc_key:
            continue

        merged = []
        skip = set()

        for i, a in enumerate(entries):
            if i in skip:
                continue

            for j in range(i + 1, len(entries)):
                if j in skip:
                    continue
                b = entries[j]

                if similar(a.get(desc_key, ""), b.get(desc_key, "")):
                    a["times_seen"] = a.get("times_seen", 1) + b.get("times_seen", 1)
                    a["confidence"] = round(
                        (a.get("confidence", 0.5) + b.get("confidence", 0.5)) / 2, 2
                    )
                    a["tags"] = list(set(a.get("tags", []) + b.get("tags", [])))
                    if b.get("example") and not a.get("example"):
                        a["example"] = b["example"]
                    skip.add(j)
                    merged_count += 1

            merged.append(a)

        knowledge[entry_type] = merged

    if merged_count > 0:
        new_ver = bump_version()
        save_knowledge(knowledge)
        print(f"🔄 知识整合完成")
        print(f"  合并条目: {merged_count} 个")
        print(f"  知识库版本: v{new_ver}")
    else:
        print("✅ 无需整合，所有条目都是唯一的")


# ==================== add ====================
def cmd_add(entry_type, json_str):
    """添加知识条目（自动查重）"""
    if entry_type not in VALID_TYPES:
        print(f"❌ 无效类型: {entry_type}")
        print(f"  可选: {', '.join(VALID_TYPES)}")
        sys.exit(1)

    try:
        new_entry = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        sys.exit(1)

    knowledge = load_knowledge()
    entries = knowledge.get(entry_type, [])

    # 查重
    desc_key = None
    for key in ["pattern", "rule", "insight", "structure"]:
        if key in new_entry:
            desc_key = key
            break

    if desc_key:
        for existing in entries:
            if similar(existing.get(desc_key, ""), new_entry.get(desc_key, ""), 0.7):
                existing["times_seen"] = existing.get("times_seen", 1) + 1
                existing["confidence"] = round(
                    (existing.get("confidence", 0.5) + new_entry.get("confidence", 0.5)) / 2, 2
                )
                existing["tags"] = list(set(existing.get("tags", []) + new_entry.get("tags", [])))
                save_knowledge(knowledge)
                print(f"🔄 发现相似条目，已合并: {existing.get('id', 'unknown')}")
                print(f"  times_seen: {existing['times_seen']}")
                print(f"  confidence: {existing['confidence']}")
                return

    # 无重复，添加新条目
    if "id" not in new_entry:
        prefix = entry_type.split("_")[0][:4]
        max_num = 0
        for e in entries:
            eid = e.get("id", "")
            if eid.startswith(prefix):
                try:
                    num = int(eid.split("_")[-1])
                    max_num = max(max_num, num)
                except ValueError:
                    pass
        new_entry["id"] = f"{prefix}_{max_num + 1:03d}"

    if "added" not in new_entry:
        new_entry["added"] = str(date.today())

    entries.append(new_entry)
    knowledge[entry_type] = entries
    save_knowledge(knowledge)
    print(f"✅ 已添加: {new_entry['id']} ({entry_type})")


# ==================== export ====================
def cmd_export():
    """导出知识库为可读格式"""
    knowledge = load_knowledge()
    version = get_version()

    print(f"# 知识库导出 — v{version}")
    print(f"# 更新日期: {knowledge.get('last_updated', '未知')}")
    print(f"# 已分析: {knowledge.get('total_books_analyzed', 0)} 本书")
    print(f"# 总条目: {count_all_entries(knowledge)}")

    for entry_type in VALID_TYPES:
        entries = knowledge.get(entry_type, [])
        if not entries:
            continue

        print(f"\n## {entry_type} ({len(entries)}条)")
        print("-" * 50)

        for e in entries:
            desc_key = None
            for key in ["pattern", "rule", "insight", "structure", "type"]:
                if key in e:
                    desc_key = key
                    break

            print(f"\n  [{e.get('id', '?')}] ", end="")
            if desc_key:
                print(f"{e[desc_key]}")
            else:
                print("(无描述)")

            print(f"    置信度: {e.get('confidence', '?')} | 出现: {e.get('times_seen', '?')}次")
            if e.get("tags"):
                print(f"    标签: {', '.join(e['tags'])}")
            if e.get("source"):
                print(f"    来源: {e['source']}")
            if e.get("fix"):
                print(f"    修改建议: {e['fix']}")


# ==================== check-similar ====================
def cmd_check_similar(entry_type, description):
    """查重检查"""
    if entry_type not in VALID_TYPES:
        print(f"❌ 无效类型: {entry_type}")
        sys.exit(1)

    knowledge = load_knowledge()
    entries = knowledge.get(entry_type, [])

    desc_key = None
    for key in ["pattern", "rule", "insight", "structure"]:
        if entries and key in entries[0]:
            desc_key = key
            break

    if not desc_key:
        print("⚠️ 该类型无描述字段，无法查重")
        return

    matches = []
    for e in entries:
        ratio = SequenceMatcher(None, description, e.get(desc_key, "")).ratio()
        if ratio >= 0.4:
            matches.append((ratio, e))

    matches.sort(key=lambda x: -x[0])

    if matches:
        print(f"🔍 找到 {len(matches)} 个相似条目:")
        for ratio, e in matches:
            print(f"  [{e.get('id', '?')}] {e.get(desc_key, '?')}")
            print(f"    相似度: {ratio:.0%} | 置信度: {e.get('confidence', '?')}")
    else:
        print("✅ 无相似条目，可放心添加")


# ==================== main ====================
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        cmd_status()
    elif cmd == "forget":
        cmd_forget(dry_run="--dry-run" in sys.argv)
    elif cmd == "integrate":
        cmd_integrate()
    elif cmd == "add":
        if len(sys.argv) < 4:
            print("用法: knowledge_ops.py add <type> '<json>'")
            sys.exit(1)
        cmd_add(sys.argv[2], sys.argv[3])
    elif cmd == "export":
        cmd_export()
    elif cmd == "check-similar":
        if len(sys.argv) < 4:
            print("用法: knowledge_ops.py check-similar <type> '<description>'")
            sys.exit(1)
        cmd_check_similar(sys.argv[2], sys.argv[3])
    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
