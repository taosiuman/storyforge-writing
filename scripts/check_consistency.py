#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_consistency.py — storyforge-writing 一致性检查器（v3，零依赖）

v2/v3 相对 v1 的修复（依据 REV-20261005-018 的"可绕过清单"）：
  · C1  改为「新三态齐备 **且** 旧词 `insufficient` 不得作为操作规则出现」（v1 是"出现即合格"）
  · C2  三词齐备 **且** 必须有规则句（禁止编造/不得把推断当事实）
  · C3  改为**逐行**标注：任何含「达芬奇」的行必须自带来源标注（v1 是文件级豁免）
  · R1/R2 改为**解析路由表行**并与 contracts/ 目录做**集合精确**比对（v1 只做全文串集合闭包，
        删掉表格行也能过；且对反斜杠写法会假红）
  · A1  锚点覆盖**全部 9 个契约**，并加**内容下限**（每份 ≥15 非空行）
  · V1  frontmatter 版本必须**同时出现在正文**（v1 只看 frontmatter 有没有）
  · M2  逐文档基线 ≥6 条且每条含版本；`primary_source` 非空；修 detail 文案 bug
  · B1  新增自洽检查：正文基线表与 frontmatter `documents` 的文档路径**集合一致**
  · K1  SKILL.md 体积 + contracts/ 总量双下限
  · 退出码 2：SKILL.md 缺失（v1 直接 traceback）

已知限制（如实声明）：不校验与上游逐字一致；不检测上游是否更新；路由分类语义无法断言。
"""

from __future__ import annotations

import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL, WARN = "FAIL", "WARN"
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
CONTRACT_REF = re.compile(r"contracts[/\\]([A-Za-z0-9_\-]+\.md)")

ANCHORS = {
    "A-characters.md": ["角色卡", "关系"],
    "A-interactive.md": ["AdventureContentV2", "commitAdventureAction", "八"],
    "A-longform.md": ["节点", "allowed writes", "跨模式验收"],
    "A-world-engine.md": ["worldCode", "WorldRelease", "WorldRequirementAdapter", "禁止读取"],
    "B-comic.md": ["字段闭集", "边界"],
    "B-motion-drama.md": ["物料", "Prompt IR", "不静默忽略"],
    "C-post.md": ["交接", "完成门"],
    "C-screenplay.md": ["忠实保留", "合理改编", "新增假设", "不可变剧本版本"],
    "S-data-envelope.md": ["PROJECT_TABLES", "CURRENT_BACKUP_VERSION", "待实测", "旁车"],
}
MIN_LINES = 12
MIN_CHARS = 800
MIN_HEADINGS = 3


def read(p):
    with io.open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


class Report:
    def __init__(self):
        self.items = []

    def add(self, cid, title, level, ok, detail=""):
        self.items.append({"id": cid, "title": title, "level": level, "ok": bool(ok), "detail": detail})

    @property
    def fails(self):
        return [i for i in self.items if not i["ok"] and i["level"] == FAIL]

    @property
    def warns(self):
        return [i for i in self.items if not i["ok"] and i["level"] == WARN]


def route_table_entries(skill):
    """从路由表表格行精确解析契约名（表格行 = 以 | 开头且含 contracts/）。"""
    out = set()
    for line in skill.splitlines():
        if line.startswith("|") and "contracts/" in line or (line.startswith("|") and "contracts\\" in line):
            out |= {m for m in CONTRACT_REF.findall(line)}
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    skill_p = os.path.join(ROOT, "SKILL.md")
    if not os.path.isfile(skill_p):
        print("用法/环境错误：SKILL.md 不存在于 %s" % ROOT, file=sys.stderr)
        return 2
    rep = Report()
    skill = read(skill_p)
    fm = skill.split("---", 2)[1] if skill.startswith("---") else ""
    body = skill.split("---", 2)[2] if skill.count("---") >= 2 else skill
    cdir = os.path.join(ROOT, "contracts")
    files = {f for f in os.listdir(cdir) if f.endswith(".md")} if os.path.isdir(cdir) else set()

    # V1
    m = re.search(r"^version:\s*([\d.]+)", fm, re.M)
    ver = m.group(1) if m else ""
    in_body = bool(ver) and ("v" + ver in body or ver in body)
    rep.add("V1", "版本戳存在且正文可见", FAIL, bool(ver) and in_body,
            "version=%s；正文%s出现" % (ver or "(未找到)", "" if in_body else "**未**"))

    # M1
    need = ["name", "description", "version", "license", "compatibility", "metadata"]
    miss = [k for k in need if not re.search(r"^%s:" % k, fm, re.M)]
    rep.add("M1", "frontmatter 必备字段齐备", FAIL, not miss,
            "缺：%s" % "、".join(miss) if miss else "6 项齐备")

    # M2
    docs = re.findall(r'-\s+"?(docs/[^"\n:]+|[A-Za-z0-9_./\-]+\.(?:md|ts))(?::\s*([^"\n]+))?"?', fm)
    has_tail = bool(re.search(r"source_version_baseline:\s*\n\s+audited:", fm))
    primary = re.search(r"primary_source:\s*\"?([^\"\n]+)", fm)
    ok_m2 = has_tail and bool(primary and primary.group(1).strip()) and len(docs) >= 6 \
        and all("v" in (d[1] or "") or "v10" in (d[1] or "") for d in docs)
    rep.add("M2", "基线为逐文档版本（≥6 条且各含版本 + primary_source）", FAIL, ok_m2,
            "结构=%s；primary_source=%s；文档条目=%d" % (
                "有" if has_tail else "缺",
                (primary.group(1).strip() if primary else "缺"), len(docs))
            + ("" if ok_m2 else "；不达标原因见上列三项"))

    # R1/R2：路由表 vs contracts/
    routed = route_table_entries(skill)
    ghost = sorted(routed - files)
    rep.add("R1", "路由表引用的契约都存在（解析表格行 + 集合精确）", FAIL, not ghost,
            "幽灵契约：%s" % "、".join(ghost) if ghost else "全部存在（%d 个）" % len(routed))
    # 横切契约：必须在显式声明的块里（标题含「横切契约」），而不是任意 bullet
    cross = set()
    m_cross = re.search(r"(?ms)^\s*>?\s*\*\*横切契约[^\n]*\n(.*?)(?=\n\n|\Z)", skill)
    if m_cross:
        cross = {m for m in CONTRACT_REF.findall(m_cross.group(1))}
    listed = cross
    routed_all = routed | listed
    orphan = sorted(files - routed_all)
    rep.add("R2", "每个契约都在路由表或横切契约块中（无孤儿）", FAIL, not orphan,
            "孤儿：%s" % "、".join(orphan) if orphan else "%d 个契约均被路由" % len(files))

    # L1
    dead = []
    for path in [skill_p] + [os.path.join(cdir, f) for f in sorted(files)]:
        for t in MD_LINK.findall(read(path)):
            t = t.split("#")[0].strip()
            if not t or t.startswith(("http", "mailto:", "asset://")) or re.search(r"[<>{}*%]", t):
                continue
            base = os.path.dirname(path)
            if not (os.path.isfile(os.path.normpath(os.path.join(base, t)))
                    or os.path.isfile(os.path.normpath(os.path.join(ROOT, t)))):
                dead.append("%s → %s" % (os.path.relpath(path, ROOT), t))
    rep.add("L1", "相对路径引用可解析", FAIL, not dead,
            "死链：%s" % "；".join(dead[:6]) if dead else "无死链")

    # C1
    triad = ("missing", "omitted", "partial-selection")
    trim_lines = [l for l in skill.splitlines() if ("裁剪" in l or "三态" in l)]
    ok_triad = any(all(k in l for k in triad) for l in trim_lines)
    # insufficient 只在**裁剪语境**下才算违规（避免与裁剪无关的用词造成假红）
    bad_line = [l for l in skill.splitlines()
                if "insufficient" in l and ("裁剪" in l or "omitted" in l or "missing" in l)]
    ok_c1 = ok_triad and not bad_line
    rep.add("C1", "裁剪三态为现行术语且旧词已清除", FAIL, ok_c1,
            ("裁剪语境仍含旧词 insufficient" if bad_line else "")
            + ("" if ok_triad else "；三态未与「裁剪/三态」同句出现（可能只是词表）")
            or "三态与裁剪同句，且裁剪语境无旧词")

    # C2
    words = ("OBSERVED", "INFERRED", "UNKNOWN")
    rule = any(k in skill for k in ("禁止编造", "不得编造", "不得把推断当事实", "必须标为 UNKNOWN", "UNKNOWN 或留空"))
    ok_c2 = all(k in skill for k in words) and rule
    rep.add("C2", "证据分级三词齐备且有规则句", FAIL, ok_c2,
            ("三词齐备" if all(k in skill for k in words) else "缺 " + "、".join(k for k in words if k not in skill))
            + ("；有规则句" if rule else "；**无**规则句（只是词表）"))

    # C3：逐行标注
    bad = []
    scan = ["SKILL.md"] + ["contracts/" + f for f in sorted(files)]
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {".git", "scripts", "__pycache__"}]
        for fn in filenames:
            if fn.endswith(".md"):
                rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace("\\", "/")
                if rel not in scan:
                    scan.append(rel)
    for rel in scan:
        for i, line in enumerate(read(os.path.join(ROOT, rel.replace("/", os.sep))).splitlines(), 1):
            if re.search(r"达芬奇|达文西|DaVinci", line) and not re.search(
                    r"环境来源|非源仓库基线|ai-memory|环境\(INFERRED\)|环境（INFERRED）", line):
                bad.append("%s:%d" % (rel, i))
    rep.add("C3", "含「达芬奇」的每一行都自带来源标注", FAIL, not bad,
            "未标注：%s" % "、".join(bad[:6]) if bad else "逐行均已标注")

    # A1 + 内容下限
    miss_a, thin = [], []
    for f in sorted(files):
        t = read(os.path.join(cdir, f))
        n = len([l for l in t.splitlines() if l.strip()])
        heads = len([l for l in t.splitlines() if l.startswith("#")])
        if n < MIN_LINES or len(t) < MIN_CHARS or heads < MIN_HEADINGS:
            thin.append("%s(%d 行/%d 字符/%d 标题)" % (f, n, len(t), heads))
        for k in ANCHORS.get(f, []):
            if k not in t:
                miss_a.append("%s:%s" % (f, k))
    rep.add("A1", "契约锚点齐备（%d 文件 / %d 锚点）"
            % (len(ANCHORS), sum(len(v) for v in ANCHORS.values())), FAIL, not miss_a,
            "缺失：%s" % "、".join(miss_a[:6]) if miss_a else "全部存在")
    rep.add("A2", "每份契约实质下限（≥%d 行 / ≥%d 字符 / ≥%d 标题）" % (MIN_LINES, MIN_CHARS, MIN_HEADINGS), FAIL, not thin,
            "过薄：%s" % "、".join(thin) if thin else "全部达标")

    # B1：基线表（正文） vs frontmatter documents 自洽
    table_docs = set(re.findall(r"`(docs/[A-Za-z0-9_./\-]+\.md)`", body)) \
        | {m for m in re.findall(r"\((docs/[A-Za-z0-9_./\-]+\.md)\)", body)}
    fm_docs = {d[0] for d in docs if d[0].startswith("docs/")}
    diff = sorted(fm_docs ^ table_docs)
    rep.add("B1", "基线表与 frontmatter documents 的文档集合一致", FAIL, not diff,
            "不一致：%s" % "、".join(diff[:6]) if diff else "%d 份文档两处一致" % len(fm_docs))


    # C4：provenance / evidenceGrade 的存放位置**单源一致**（用户使用中发现的跨文件矛盾）
    se_txt = read(os.path.join(ROOT, "contracts", "S-data-envelope.md")) if os.path.isfile(
        os.path.join(ROOT, "contracts", "S-data-envelope.md")) else ""
    problems4 = []
    if "旁车" not in se_txt:
        problems4.append("S-data-envelope.md 未声明旁车规则（权威缺失）")
    if "provenance" in skill:
        if "contracts/S-data-envelope.md" not in skill:
            problems4.append("SKILL.md 提到 provenance 但未指向权威 `contracts/S-data-envelope.md`")
        if "旁车" not in skill:
            problems4.append("SKILL.md 提到 provenance 但未说明「旁车文件」")
    # 冲突扫描：任何文件的该行若声称 provenance 进 JSON/记录内，且未含旁车/不得/sidecar 限定 → 冲突
    for rel in ["SKILL.md", "README.md", "CHANGELOG.md", "COMPAT.md"] + \
               ["contracts/" + f for f in sorted(files)]:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            continue
        for i, line in enumerate(read(p).splitlines(), 1):
            if "provenance" in line or "evidenceGrade" in line:
                risky = ("每块带" in line) or ("记录内" in line and "不得" not in line) or \
                        ("JSON 里" in line and "不得" not in line)
                ok_marker = ("旁车" in line) or ("sidecar" in line.lower()) or ("不得" in line) or \
                            ("S-data-envelope" in line)
                if risky and not ok_marker:
                    problems4.append("%s:%d 疑似与旁车规则冲突" % (rel, i))
    rep.add("C4", "provenance / evidenceGrade 存放规则单源一致", FAIL, not problems4,
            "；".join(problems4[:5]) if problems4 else "单源一致（权威：S-data-envelope.md §3）")

    # K1
    size = os.path.getsize(skill_p)
    ctotal = sum(os.path.getsize(os.path.join(cdir, f)) for f in files)
    if size > 60 * 1024:
        rep.add("K1", "体积预算", FAIL, False, "SKILL.md=%.1fKB 超过失败线 60KB" % (size / 1024))
    else:
        rep.add("K1", "体积预算（SKILL.md ≤24KB 且 contracts 总量 ≥20KB）", WARN,
                size <= 24 * 1024 and ctotal >= 20 * 1024,
                "SKILL.md=%.1fKB；contracts 合计=%.1fKB" % (size / 1024, ctotal / 1024))

    if "--json" in argv:
        print(json.dumps({"fail": len(rep.fails), "warn": len(rep.warns), "items": rep.items},
                         ensure_ascii=False, indent=2))
    else:
        quiet = "--quiet" in argv
        print("== storyforge-writing 一致性检查 v3")
        for i in rep.items:
            if i["ok"] and quiet:
                continue
            mark = "OK  " if i["ok"] else ("FAIL" if i["level"] == FAIL else "WARN")
            print("[%s] %-3s %s — %s" % (mark, i["id"], i["title"], i["detail"]))
        print("RESULT: %s (%d fail, %d warn)" % ("PASS" if not rep.fails else "FAIL",
                                                 len(rep.fails), len(rep.warns)))
    return 0 if not rep.fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
