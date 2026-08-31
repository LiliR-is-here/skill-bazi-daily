#!/usr/bin/env python3
"""
query_classics.py —— 三本经典文本的结构化检索工具

用途
----
Bazi-Daily 技能在 Step2（结构）/ Step3（调候）/ Step4（原理）需要引用经典原文时，
用本脚本做关键词检索，返回命中的「卷/章节 + 原文行 + 上下文」，避免把大文件整篇读入
上下文。其中 B《渊海子平》完整版约 25 万字、C《穷通宝鉴》完整版约 3.3 万字，必须检索
定位后再按需精读，禁止无差别整读。

用法
----
  # 检索单本（推荐：按知识层分开）
  python3 scripts/query_classics.py --book B --kw 正官格
  python3 scripts/query_classics.py --book C --kw 丙火 --kw 正月
  python3 scripts/query_classics.py --book A --kw 从格

  # 全库检索（B/C/A 一起命中）
  python3 scripts/query_classics.py --kw 从财

  # 只看命中的章节清单（不带正文，用于快速定位）
  python3 scripts/query_classics.py --book B --kw 化格 --section-only

  # 浏览某本书的全部章节结构
  python3 scripts/query_classics.py --book B --list

  # 提取指定章节的完整正文（精读用）
  python3 scripts/query_classics.py --book B --chapter 内十八格-正官格
  python3 scripts/query_classics.py --book C --chapter 三冬癸水

参数
----
  --book A|B|C        只检索指定书（缺省检索全部三本）
  --kw KEYWORD        检索关键词，可重复（多词之间取“同时命中同一段”）
  --context N         每个命中行前后附带 N 行上下文（缺省 2）
  --limit N           每本书最多返回的命中条目数（缺省 12）
  --section-only      只输出命中的章节标题，不输出正文
  --list              列出指定书（或全部）的章节结构
  --chapter NAME      提取指定章节完整正文（配合 --book 使用）
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CLASSICS_DIR = Path(__file__).resolve().parent.parent / "references" / "classics"
FILES: dict[str, str] = {
    "A": "A_滴天髓.txt",
    "B": "B_渊海子平.txt",
    "C": "C_穷通宝鉴.txt",
}

# ---------- 章节切分规则（按文件结构） ----------

def _b_patterns() -> tuple[list, list]:
    # B《渊海子平》：卷头 "# 卷X"；章头 "■ 篇名"
    vol_re = re.compile(r"^#\s*卷[一二三四五六七]")
    ch_re = re.compile(r"^■\s+")
    return [vol_re], [ch_re]


def _c_patterns() -> tuple[list, list]:
    # C《穷通宝鉴》：卷头 "卷X · 论Y"；节头（论X / X之总论 / 三春X总论 / N月X干 等，可带尾"："）
    vol_re = re.compile(r"^卷[一二三四五六]")
    section_re = re.compile(
        r"^(三[春夏秋冬](?:[甲乙丙丁戊己庚辛壬癸])?[木火土金水]总论|"
        r"三[春夏秋冬](?:[甲乙丙丁戊己庚辛壬癸])?[木火土金水]|"
        r"[木火土金水]之总论|[木火土金水]性总论|"
        r"论[甲乙丙丁戊己庚辛壬癸][木火土金水]|论[木火土金水]|"
        r"[一二三四五六七八九十正]{1,2}月[甲乙丙丁戊己庚辛壬癸][木火土金水]|"
        r"[春夏秋冬]月之[木火土金水]|"
        r"[甲乙丙丁戊己庚辛壬癸][木火土金水]喜用提要)[：:]?$"
    )
    return [vol_re], [section_re]


def _a_patterns() -> tuple[list, list]:
    # A《滴天髓》：页头 "=== PAGE N ==="；篇头 "上篇/下篇"；节头 "一、"
    page_re = re.compile(r"^=== PAGE \d+ ===")
    part_re = re.compile(r"^(上篇|下篇)")
    sec_re = re.compile(r"^[一二三四五六七八九十]+、")
    return [page_re, part_re], [sec_re]


def split_sections(book: str, text: str) -> list[dict]:
    """把一本书切成“章节块”，每块含卷/篇归属、标题、行号范围、正文行。"""
    vol_pats, sec_pats = {
        "A": _a_patterns,
        "B": _b_patterns,
        "C": _c_patterns,
    }[book]()
    lines = text.split("\n")
    # B 书：跳过题记/目录等卷前内容，从第一个“# 卷”开始
    if book == "B":
        start = 0
        for i, ln in enumerate(lines):
            if vol_pats[0].match(ln.strip()):
                start = i
                break
        lines = lines[start:]
    sections: list[dict] = []
    cur_vol = ""
    cur_title = ""
    cur_lines: list[tuple[int, str]] = []

    def flush():
        nonlocal cur_lines, cur_title
        if cur_lines:
            sections.append({
                "vol": cur_vol,
                "title": cur_title,
                "lines": cur_lines,
            })
            cur_lines = []

    for idx, raw in enumerate(lines):
        ln = raw.rstrip("\n")
        stripped = ln.strip()
        if not stripped:
            continue
        is_vol = any(p.match(stripped) for p in vol_pats)
        is_sec = any(p.match(stripped) for p in sec_pats)
        if is_vol:
            flush()
            cur_vol = stripped
            cur_title = ""
            continue  # 卷头只作归属标记，不进入正文行
        elif is_sec:
            flush()
            cur_title = stripped
        else:
            # 块内首行非标题时兜底为标题（截断避免超长）
            if not cur_title:
                cur_title = stripped[:24] + ("…" if len(stripped) > 24 else "")
        cur_lines.append((idx + 1, ln))
    flush()
    return sections


def _load(book: str) -> str:
    path = CLASSICS_DIR / FILES[book]
    if not path.exists():
        sys.stderr.write(f"错误：经典文本缺失 {path}\n")
        sys.exit(2)
    return path.read_text(encoding="utf-8")


def list_sections(books: list[str]) -> None:
    for b in books:
        sections = split_sections(b, _load(b))
        print(f"===== {b}《{'滴天髓' if b=='A' else '渊海子平' if b=='B' else '穷通宝鉴'}》 =====")
        for s in sections:
            head = f"[{s['vol']}] {s['title']}" if s["vol"] else s["title"]
            print(f"  L{s['lines'][0][0]:>5}  {head}")
        print()


def get_chapter(book: str, name: str) -> None:
    sections = split_sections(book, _load(book))
    hits = [s for s in sections if s["title"] == name or name in s["title"]]
    if not hits:
        sys.stderr.write(f"未找到章节「{name}」（书 {book}）。可用 --list 查看全部章节名。\n")
        sys.exit(1)
    for s in hits:
        print(f"===== [{book}] {s['vol']} · {s['title']} =====")
        for ln_no, ln in s["lines"]:
            print(ln)
        print()


def search(books: list[str], keywords: list[str], context: int, limit: int,
           section_only: bool) -> None:
    for b in books:
        sections = split_sections(b, _load(b))
        results = []
        for s in sections:
            block_text = "\n".join(l for _, l in s["lines"])
            if not all(k in block_text for k in keywords):
                continue
            # 命中行（含至少一个关键词）
            hit_idx = [i for i, (_, l) in enumerate(s["lines"]) if any(k in l for k in keywords)]
            results.append((s, hit_idx))
            if len(results) >= limit:
                break
        if not results:
            continue
        book_name = {"A": "滴天髓", "B": "渊海子平", "C": "穷通宝鉴"}[b]
        print(f"========== {b}《{book_name}》命中 {len(results)} 个章节 ==========")
        for s, hit_idx in results:
            head = f"[{s['vol']}] {s['title']}" if s["vol"] else s["title"]
            print(f"\n▍ {head}")
            if section_only:
                continue
            shown = set()
            for i in hit_idx:
                lo = max(0, i - context)
                hi = min(len(s["lines"]), i + context + 1)
                for j in range(lo, hi):
                    if j in shown:
                        continue
                    shown.add(j)
                    ln_no, ln = s["lines"][j]
                    marker = ">>" if j == i else "  "
                    print(f"  {marker} L{ln_no}: {ln}")
        print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", choices=["A", "B", "C"], action="append",
                    help="检索的书（可多次指定；缺省全部）")
    ap.add_argument("--kw", action="append", default=[], help="检索关键词（可多次）")
    ap.add_argument("--context", type=int, default=2, help="命中行上下文行数（缺省2）")
    ap.add_argument("--limit", type=int, default=12, help="每本最多返回命中章节数（缺省12）")
    ap.add_argument("--section-only", action="store_true", help="只列命中章节标题")
    ap.add_argument("--list", action="store_true", help="列出章节结构")
    ap.add_argument("--chapter", help="提取指定章节完整正文")
    args = ap.parse_args()

    books = args.book or ["A", "B", "C"]

    if args.list:
        list_sections(books)
        return
    if args.chapter:
        if len(books) != 1:
            sys.stderr.write("--chapter 需与单个 --book 配合使用。\n")
            sys.exit(1)
        get_chapter(books[0], args.chapter)
        return
    if not args.kw:
        ap.print_help()
        sys.exit(1)

    search(books, args.kw, args.context, args.limit, args.section_only)


if __name__ == "__main__":
    main()
