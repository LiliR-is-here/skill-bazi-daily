# Classics Text Cache

三本经典使用预抽取的 UTF-8 文本文件作为主读取源：

- `A_滴天髓.txt`（原理层）
- `B_渊海子平.txt`（结构层）——**完整版**：通行七卷本，304 章，约 25 万字
- `C_穷通宝鉴.txt`（调候层）——**完整版**：通行六卷本，十天干分月喜忌与命例齐全，约 3.3 万字

> **覆盖状态**：B/C 为完整版（B 七卷 304 章、C 六卷十天干齐全），无已知缺口；仅 `A_滴天髓.txt` 为节选（上篇通神论、下篇六亲论），暂无已知缺口；若需更完整可自行补充。

## 检索方式（Retrieval Guide，强制）

B 完整版约 25 万字，**禁止整篇读入上下文**。引用经典原文前，必须先用检索定位，再按需精读单个章节。

### 1. 结构化检索脚本（推荐）

```bash
# 检索单本（按知识层分开，最常用）
python3 scripts/query_classics.py --book B --kw 正官格
python3 scripts/query_classics.py --book C --kw 丙火 --kw 正月   # 多词同时命中
python3 scripts/query_classics.py --book A --kw 从格

# 只看命中的章节清单（快速定位，不带正文）
python3 scripts/query_classics.py --book B --kw 化格 --section-only

# 浏览某本书全部章节结构
python3 scripts/query_classics.py --book C --list

# 提取指定章节完整正文（精读用）
python3 scripts/query_classics.py --book B --chapter 内十八格-正官格
python3 scripts/query_classics.py --book C --chapter 十一月癸水
```

关键参数：`--book A|B|C`、`--kw`（可重复）、`--context N`（上下文行数，缺省 2）、`--limit N`（每书最多命中章节数，缺省 12）、`--section-only`、`--list`、`--chapter NAME`。

### 2. 直接 grep（备用）

脚本不可用时，用 grep 快速定位行号再 `sed` 精读：

```bash
grep -n "正官格\|从财格" references/classics/B_渊海子平.txt
grep -n "十一月癸水\|十二月癸水" references/classics/C_穷通宝鉴.txt
```

### 3. 检索效率规则

1. Step2（B 结构）/ Step3（C 调候）必须先检索定位，再决定是否精读单个章节；不得无差别整读大文件。
2. B 用格局/十神/用神关键词检索；C 用「天干 + 月份」或「调候字」检索（如 `丙火 正月`、`癸水 十一月`）。
3. 检索命中章节后，若需完整条文，用 `--chapter` 提取该章；其余按上下文片段即可。
4. 引用原文时保留出处（B/C 卷章 + 行号），便于溯源与日志记录。

## 三源职责边界

- B《渊海子平》→ 结构层：格局判定、十神结构、用神框架
- C《穷通宝鉴》→ 调候层：月令寒暖燥湿、调候药方
- A《滴天髓》→ 原理层：气机、取用总纲

路由细则见 [classic-sources-routing.md](../classic-sources-routing.md)。

## Regenerate（备用）

如需从 PDF 源重新生成经典文本（输出含 `=== PAGE N ===` 分页标记），执行：

```bash
python3 scripts/extract_classics_text.py \
  --pdf-a /path/to/滴天髓.pdf \
  --pdf-b /path/to/渊海子平.pdf \
  --pdf-c /path/to/穷通宝鉴.pdf \
  --output-dir references/classics
```

如需同时生成 markdown：追加 `--md`。

## Source PDFs

PDF 源文件由使用者自行提供，不随 skill 包分发；当前完整版 txt 已直接内置，一般无需再准备 PDF。
