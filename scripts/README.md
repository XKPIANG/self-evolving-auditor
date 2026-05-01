# novel-audit 脚本工具

自动化 novel-audit 技能的关键流程，解决纯 prompt 驱动的不确定性问题。

## 脚本列表

| 脚本 | 功能 | 替代的手动操作 |
|------|------|---------------|
| `knowledge_ops.py` | 知识库管理 | 状态/遗忘/整合/添加/导出/查重 |
| `archive_ops.py` | 存档管理 | 初始化/录入/自检/查询 |
| `book_split.py` | 拆书为章节 | 按章节标题自动拆分 txt |
| `quick_audit.py` | 快速审核 | 一次性读取所有审核所需数据 |
| `novel_audit.py` | 主入口 | 统一调用上述所有脚本 |

## 使用方式

### 统一入口

```bash
python3 novel_audit.py <模块> <命令> [参数]

# 示例
python3 novel_audit.py knowledge status
python3 novel_audit.py archive init "书名"
python3 novel_audit.py split /path/to/novel.txt
python3 novel_audit.py audit prepare "书名"
```

### 知识库操作

```bash
SCRIPT=~/.openclaw/skills/novel-audit/scripts/knowledge_ops.py

# 查看状态
python3 $SCRIPT status

# 添加知识条目（自动查重，相似则合并）
python3 $SCRIPT add 'rhythm_patterns' '{"pattern":"3章一爽点","confidence":0.8,"tags":["玄幻"]}'

# 遗忘检查（dry-run 预览）
python3 $SCRIPT forget --dry-run

# 执行遗忘
python3 $SCRIPT forget

# 去重整合
python3 $SCRIPT integrate

# 导出可读格式
python3 $SCRIPT export

# 查重
python3 $SCRIPT check-similar 'rhythm_patterns' '3章一高潮'
```

### 存档操作

```bash
SCRIPT=~/.openclaw/skills/novel-audit/scripts/archive_ops.py

# 列出所有书
python3 $SCRIPT list

# 初始化存档（从模板创建）
python3 $SCRIPT init "书名"

# 录入章节（需要准备 JSON 数据文件）
python3 $SCRIPT ingest "书名" 1 chapter_data.json

# 自检
python3 $SCRIPT lint "书名"

# 查询存档
python3 $SCRIPT query "书名"
python3 $SCRIPT query "书名" --section characters
python3 $SCRIPT query "书名" --section hooks
```

### 录入章节的 JSON 格式

```json
{
  "title": "章节标题",
  "word_count": 3000,
  "emotion": 3,
  "story_time": "第三天清晨",
  "summary": "100-200字概括",
  "characters": [
    {"name": "张三", "change": "获得玉佩", "source": "第1章原文"}
  ],
  "data_changes": [
    {"item": "灵石", "change": "+100", "new_value": "200", "source": "原文引用"}
  ],
  "hooks": [
    {"content": "神秘老者的话", "status": "埋下"}
  ],
  "foreshadowing": [
    {"content": "黑色塔的梦", "status": "埋下"}
  ],
  "new_settings": ["炼气二层可学火球术"],
  "reader_notes": {
    "saw": "本章核心事件复述",
    "know": ["张三获得系统", "灵石是通用货币"],
    "thinking": ["系统为什么选中张三？"],
    "key_understanding": ["张三的性格从被动变主动"]
  },
  "audit_notes": {
    "节奏": "前松后紧，爽点在结尾",
    "逻辑问题": "无"
  }
}
```

### 拆书

```bash
SCRIPT=~/.openclaw/skills/novel-audit/scripts/book_split.py

# 自动检测章节格式并拆分
python3 $SCRIPT /path/to/novel.txt

# 指定输出目录
python3 $SCRIPT /path/to/novel.txt --output-dir /path/to/output

# 自定义章节匹配正则
python3 $SCRIPT /path/to/novel.txt --pattern '^第\d+章'
```

输出：
- `ch001.txt`, `ch002.txt`, ... 各章节文件
- `meta.json` 拆分元数据（章节列表、字数统计等）

### 快速审核

```bash
SCRIPT=~/.openclaw/skills/novel-audit/scripts/quick_audit.py

# 准备审核上下文（一次性读取所有需要的数据）
python3 $SCRIPT prepare "书名"

# 指定章节
python3 $SCRIPT prepare "书名" --chapter 5
```

输出 JSON 包含：
- 知识库摘要（各分类条目数）
- 完整知识库数据
- 存档数据（人物/设定/时间线/钩子/伏笔/最近3章）

AI 拿到这个 JSON 就可以直接审核，不需要再多次读取文件。

## 与 SKILL.md 的关系

这些脚本是 SKILL.md 工作流的**自动化实现**：

| SKILL.md 流程 | 对应脚本 | 改进 |
|---------------|---------|------|
| 流程一：拆解样板书 | `book_split.py` + `knowledge_ops.py` add | 拆书自动化，知识入库自动查重 |
| 流程二：小说审核 | `quick_audit.py` prepare | 一次读取，减少工具调用 |
| 流程三：知识库管理 | `knowledge_ops.py` | 遗忘/整合真正可执行 |
| 流程四：存档追踪 | `archive_ops.py` ingest | 标准化 JSON 输入，批量更新 |
| 流程五：快速审核 | `quick_audit.py` prepare + update | 完全自动化 |
