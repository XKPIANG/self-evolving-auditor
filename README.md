# 📖 Novel Audit — 自进化小说审核系统

> 不是静态工具，是一个**会学习的审核员**。拆解越多，审核越准。

## ✨ 核心特性

- **双层存档** — 数据库层记录"是什么"，读者层记录"为什么"，交叉验证抓硬伤
- **六维审核** — 节奏 / 爽点 / 逻辑 / 发布水平 / 设定一致性 / AI味检测
- **自进化知识库** — 每拆解一本书自动学习新模式，遗忘低价值知识，整合重复知识
- **双平台适配** — 番茄小说（快节奏爽文）/ 起点小说（宏大世界观），各有专属标准
- **编译式 Wiki** — 每读一章就编译进 Wiki，审核第50章时不需要重读前49章
- **自动化脚本** — 知识库管理、存档操作、拆书、快速审核全部脚本化

## 🧠 双层存档

```
数据库层：张三获得100灵石（记录事实）
读者层：  因为系统发放初始资源，张三的属性决定了100灵石（记录理解）
```

审核新章节时，两层交叉验证：
- 数据库说灵石余额250，新章节说只剩10块 → **数据不一致**
- 读者层记录"张三性格谨慎"，新章节写他冲动赌博 → **人物崩了**

## 🔍 六维审核

| 维度 | 检测内容 | 评分逻辑 |
|------|----------|----------|
| 节奏 | 张弛周期、高潮间隔、情绪曲线 | 分数越高越好 |
| 爽点 | 铺垫精准度、释放力度、余韵 | 分数越高越好 |
| 逻辑 | 世界观自洽、角色动机、因果链 | 分数越高越好 |
| 发布水平 | 平台标准、字数、格式、钩子 | 分数越高越好 |
| 设定一致性 | 数据前后一致、人物状态连贯 | 分数越高越好 |
| **AI味检测** | 高频用词、套路比喻、长难句、过度解释 | ⚠️ **分数越低越好**（1-2=S, 3-4=A, 5-6=B, 7-8=C, 9-10=F） |

## 📂 项目结构

```
references/          ← 基础框架（静态）
  rhythm.md            节奏分析理论
  hooks.md             爽点类型库
  logic.md             逻辑检查清单
  standards-fanqie.md  番茄小说发布标准
  standards-qidian.md  起点小说发布标准
  ai-style.md          AI味检测基准

knowledge/           ← 自进化知识库（动态）
  knowledge.json       核心知识库
  book_log.json        拆解记录
  version.txt          知识库版本号

scripts/             ← 自动化工具
  novel_audit.py       统一入口
  knowledge_ops.py     知识库管理（状态/遗忘/整合/添加/导出）
  archive_ops.py       存档管理（初始化/录入/自检/查询）
  book_split.py        拆书为章节
  quick_audit.py       快速审核数据准备

archives/            ← 小说 Wiki（每本书独立目录）
  {书名}/
    ├── index.md           总索引
    ├── log.md             操作日志
    ├── book.md            整本书概览
    ├── characters.md      人物档案（数据库层）
    ├── timeline.md        时间线 & 关键数据（数据库层）
    ├── hooks.md           钩子追踪（数据库层）
    ├── foreshadowing.md   伏笔追踪（数据库层）
    ├── settings.md        设定档案（数据库层）
    ├── reader-notes.md    读者笔记（读者层）★
    ├── chapters/          逐章档案（双层合并）
    └── topics/            主题页
```

## 🚀 使用方式

### 对话触发

```
# 拆解样板书（学习模式）
拆解这本书 /path/to/novel.txt，书名《xxx》

# 审核小说（应用模式）
审核这段小说，发布到起点 [粘贴文本]

# 存档追踪
审核第X章 [粘贴文本]

# AI味检测
查AI味 [粘贴文本]

# 知识库管理
知识库状态
```

### 脚本命令

```bash
# 知识库管理
python3 scripts/novel_audit.py knowledge status
python3 scripts/novel_audit.py knowledge forget --dry-run
python3 scripts/novel_audit.py knowledge integrate
python3 scripts/novel_audit.py knowledge add 'rhythm_patterns' '{"pattern":"..."}'

# 拆书
python3 scripts/novel_audit.py split /path/to/novel.txt

# 存档管理
python3 scripts/novel_audit.py archive init "书名"
python3 scripts/novel_audit.py archive ingest "书名" 1 chapter_data.json
python3 scripts/novel_audit.py archive lint "书名"

# 快速审核
python3 scripts/novel_audit.py audit prepare "书名"
```

## 📊 审核输出

```
六维评分
| 维度 | 分数 | 等级 |
|------|------|------|
| 节奏 | 8/10 | A    |
| 爽点 | 6/10 | B    |
| 逻辑 | 9/10 | S    |
| 发布水平 | 7/10 | A |
| 设定一致性 | 8/10 | A |
| AI味检测 | 3/10 | S  |  ← 反向：越低越好

连续性检查：✅ 通过 / ❌ 问题列表
AI味命中项：原文 + 建议修改
```

## 🧬 自进化机制

### 知识入库
```
拆解一本书 → 提取知识点 → 查重 → 评估价值(confidence≥0.6入库) → 整合
```

### 遗忘机制
```
低置信度(confidence<0.3) → 直接删除
长期未见(times_seen=1 且 超过5本书未更新) → 标记→再检查→删除
```

### 知识整合
```
相似条目 → 合并(times_seen累加, confidence加权平均, tags取并集)
```

## 📈 知识库统计

- 已分析书籍：0 本
- 知识库版本：v1

---

*审核能力随使用次数持续提升。用得越多，它越懂你写的是什么。*
