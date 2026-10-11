#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_framework_artifact.py — storyforge framework 产物级校验器（零依赖）

规则来源：
  - references/field-registry.md（字段/类型/枚举）
  - references/schema-tables.md（§2 全部表索引 123 张）
  - contracts/S-data-envelope.md（语料结构 / 旁车 / 对齐清单）

用法：
  python scripts/check_framework_artifact.py <framework.json> [<framework2.json> ...]

退出码：0 = 全部 PASS；1 = 至少一个 FAIL；2 = 用法/环境错误

v1（2026-10-07）：由电影大师在长铗传 v0.3.0 → v0.3.1 修复过程中编写，
  后由技能开发 agent 提升进技能包。覆盖 6 类契约违规（FK 类型 / 必需字段 /
  枚举闭集 / 顶层结构 / 旁车结构 / context-manifest）+ FK 悬挂警告。
v3（2026-10-07，大扫除 P1）：表名来源改为 **§2 单源** —— 原先额外做了一次**全文**
  标题扫描，任何 `### <反引号>非表名` 都会被当成合法表（**假 PASS**）；且 §2 定位
  硬编码、标题改形时静默退化。现改为节号/关键词正则定位，找不到 §2 或自述张数
  不符即报错并退出 2。
"""
import json
import os
import re
import sys

# 技能包根目录（本脚本在 scripts/ 下，向上找一级）
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_registry():
    """从 references/field-registry.md 解析每张表的字段规格（字段名 / 类型 / 枚举闭集）。"""
    reg_path = os.path.join(SKILL_ROOT, "references", "field-registry.md")
    if not os.path.isfile(reg_path):
        print(f"错误：找不到 {reg_path}", file=sys.stderr)
        return {}
    reg = open(reg_path, encoding="utf-8").read()
    spec = {}
    for s in re.split(r"\n### ", reg):
        m = re.match(r"`([A-Za-z0-9_]+)`", s)
        if not m:
            continue
        t = m.group(1)
        fields = {}
        for line in s.split("\n"):
            mm = re.match(r"\|\s*`([A-Za-z0-9_]+)`\s*\|\s*`([a-z]+)`\s*\|([^|]*)\|", line)
            if mm:
                f, ty, vals = mm.group(1), mm.group(2), mm.group(3).strip()
                # 枚举值用 · 分隔（中文间隔号 U+00B7）
                ev = [v.strip("` ") for v in vals.split(chr(183))] if vals and vals != chr(8212) else []
                fields[f] = {"type": ty, "enum": ev}
        spec[t] = fields
    return spec


def _strip_noise(s):
    """剥离围栏代码块与 HTML 注释（防正文样例被当作真标题）。"""
    s = re.sub(r"```.*?```", "", s, flags=re.S)
    return re.sub(r"<!--.*?-->", "", s, flags=re.S)


def parse_schema_tables():
    """从 references/schema-tables.md 的 **§2「全部表索引」** 解析全部表名（**单一来源**）。

    **v3（大扫除 P1）修正**：旧版在 §2 表格行之外**又做了一次全文** `### <反引号>表名`
    标题扫描，两个后果 ——
      ① 任何形如 `### <反引号>非表名` 的标题都会被当成**合法表名**
         （实测：注入假标题后产物用该名**不报错** = **假 PASS**）；
      ② §2 定位用硬编码 `split("## 2.")`，标题改形时**静默退化为全文扫描**。
    现改为：**§2 单源** + 节号/关键词正则定位 + **找不到即报错**（不静默）；
    并额外返回标题自述的张数，供调用方核对（"123" 不再是不可验证的宣称）。
    """
    st_path = os.path.join(SKILL_ROOT, "references", "schema-tables.md")
    if not os.path.isfile(st_path):
        print(f"错误：找不到 {st_path}", file=sys.stderr)
        return set(), None
    sc = _strip_noise(open(st_path, encoding="utf-8").read())
    # 必须**唯一**命中：否则可被"在真 §2 之前插入伪造同名节"旁路
    # （`REV-20261007-034` M-bypass：取首个匹配 → 伪表名假 PASS、真表名假红）。
    cands = [mm for mm in re.finditer(r"^##[ \t\u3000]*[2２][ \t\u3000]*[.、．][^\n]*$", sc, re.M)
             if "全部表索引" in mm.group(0)]
    if len(cands) != 1:
        print("错误：schema-tables.md 的「§2 全部表索引」节命中 %d 个（应为 1）—— 表名来源不可信"
              % len(cands), file=sys.stderr)
        return set(), None
    head = cands[0]
    rest = sc[head.end():]
    nxt = re.search(r"^##[ \t\u3000]", rest, re.M)
    sec2 = rest[:nxt.start()] if nxt else rest
    names = set(re.findall(r"^\|\s*`([A-Za-z0-9_]+)`\s*\|\s*`[^`]+`\s*\|\s*$", sec2, re.M))
    mtxt = re.search(r"（\**(\d+)\s*张", head.group(0))
    return names, (int(mtxt.group(1)) if mtxt else None)


def _is_int(v):
    """**严格整数**：排除 `bool`（Python `isinstance(True, int)` 为真 ——
    `REV-20261007-035` L1 实测 `id: true` 会绕过整数门）。"""
    return isinstance(v, int) and not isinstance(v, bool)


def check(path, spec, schema_tables, unresolved=frozenset()):
    """校验单个 framework.json，返回 {path, status, tables, errors, warnings}。

    `unresolved`：旁车 `unresolvedRefs` 登记的 `(table, field, value)` 集合 ——
    T7（v0.4.0）用它区分「**登记过的**悬空引用」（WARN）与「**未登记的**静默悬空」（ERROR）。
    """
    errs, warns = [], []
    if not os.path.exists(path):
        return {"path": path, "status": "ERROR", "errors": ["artifact not found"], "warnings": []}
    
    try:
        d = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"path": path, "status": "ERROR", "errors": [f"JSON parse error: {e}"], "warnings": []}
    
    # 顶层结构：不能有 version 字段（避免冒充备份包）
    if "version" in d:
        errs.append("top-level `version` must NOT be present (would mimic a backup package)")
    
    # 顶层结构：blocks 必须是 list
    blocks = d.get("blocks")
    if not isinstance(blocks, list):
        errs.append("top-level `blocks` must be a list, got %s" % type(blocks).__name__)
        blocks = []
    
    # 第一遍：收集所有表的 id 集合（用于 FK 悬挂检查）
    ids_by_table = {}
    for b in blocks:
        ids_by_table[b.get("table")] = {r.get("id") for r in (b.get("records") or []) if isinstance(r, dict)}
    all_ids = set().union(*ids_by_table.values()) if ids_by_table else set()
    
    # 第二遍：逐表逐记录校验
    for b in blocks:
        t = b.get("table")
        recs = b.get("records") or []
        
        # 表存在性
        if t not in spec:
            warns.append("table has no FIELD_REGISTRY entry: %s (schema 存在但无可写字段登记)" % t)
        if t not in schema_tables:
            errs.append("table not in schema-tables.md index: %s" % t)
        
        fs = spec.get(t, {})
        for i, r in enumerate(recs):
            if not isinstance(r, dict):
                errs.append("%s[%d] not an object" % (t, i))
                continue
            
            # T7（v0.4.0）：chapters 的 id 必须是**整数** —— 不得用 `ep30` 这类字符串代号
            #   （上游 chapters 以数字 id 标识、以 order 排序；见 contracts/A-longform.md §8）
            if t == "chapters" and isinstance(r.get("id"), str):
                errs.append("%s[%d] 的 `id` 是字符串 %r —— 章节必须用**整数 id**，代号只能进 title/文件名" % (t, i, r.get("id")))

            # 必需字段：id 和 projectId 必须是数字
            if not _is_int(r.get("id")):
                errs.append("%s[%d] missing numeric `id`" % (t, i))
            if not _is_int(r.get("projectId")):
                errs.append("%s[%d] missing numeric `projectId`" % (t, i))
            
            # 字段类型与枚举闭集
            for f, fsp in fs.items():
                if f not in r:
                    continue
                v = r.get(f)
                if v is None:
                    continue
                
                # 枚举闭集
                if fsp["type"] == "enum" and v not in fsp["enum"]:
                    errs.append("%s[%d].%s enum violation: %r not in %s" % (t, i, f, v, fsp["enum"]))
                
                # FK 字段必须是数字
                if fsp["type"] == "number" and (f.endswith("Id") or f.endswith("Ids")) and not isinstance(v, (int, float)):
                    errs.append("%s[%d].%s must be number, got %s" % (t, i, f, type(v).__name__))
                
                # T7（v0.4.0）：FK 悬空 —— **登记过**降 WARN；**未登记 = ERROR**
                #   依据「缺失 ≠ 空」：未解析的引用必须**显式留痕**（旁车 unresolvedRefs）。
                if fsp["type"] == "number" and (f.endswith("Id") or f.endswith("Ids")) and _is_int(v) and v not in all_ids:  # L2/F2：判据对齐 + 类型约束
                    if (t, f, v) in unresolved:
                        warns.append("%s[%d].%s=%s dangling（旁车 unresolvedRefs 已登记，留痕可见）"
                                     % (t, i, f, v))
                    else:
                        errs.append("%s[%d].%s=%s dangling 且**未登记** —— 须置 null 并在旁车 "
                                    "unresolvedRefs 留痕（A-LONGFORM §8）" % (t, i, f, v))
                
                # T10（v0.4.0）：章节若带 continuityHandoff，按 A-longform.md §9.1 校验其形状
                if t == "chapters":
                    h_ = r.get("continuityHandoff")
                    if isinstance(h_, dict):
                        need_h = ("finalScene", "stateChanges", "knowledgeChanges", "commitments",
                                  "openLoops", "evidenceQuotes", "sourceTextHash")
                        miss_h = [k for k in need_h if k not in h_]
                        if miss_h:
                            errs.append("%s[%d].continuityHandoff 缺必需字段 %s（A-longform.md §9.1）"
                                        % (t, i, miss_h))
                        eq = h_.get("evidenceQuotes")
                        if not isinstance(eq, list) or not eq:
                            errs.append("%s[%d].continuityHandoff.evidenceQuotes 必须是非空数组"
                                        "（须为带偏移的原文引用，见 §9.1）" % (t, i))
                        else:
                            for k2, q in enumerate(eq):
                                if not (isinstance(q, dict) and q.get("quote")
                                        and isinstance(q.get("startOffset"), int)
                                        and isinstance(q.get("endOffset"), int)):
                                    errs.append("%s[%d].continuityHandoff.evidenceQuotes[%d] 必须含 "
                                                "quote + startOffset + endOffset" % (t, i, k2))
                # null/empty 警告
                if v is None or v == []:
                    warns.append("%s[%d].%s null/empty (unresolved)" % (t, i, f))
    
    # T7（v0.4.0）：chapters.order 若存在必须唯一（章序必须可唯一映射）
    orders = [r.get("order") for b in blocks if b.get("table") == "chapters"
              for r in (b.get("records") or []) if isinstance(r, dict)]
    seen_o, dup_o = set(), set()
    for o in orders:
        if o is None:
            continue
        if not _is_int(o):
            errs.append("chapters 的 `order` 必须是整数，得到 %r" % (o,))
        elif o in seen_o:
            dup_o.add(o)
        else:
            seen_o.add(o)
    if dup_o:
        errs.append("chapters 的 `order` 重复：%s（章序必须唯一）" % sorted(dup_o)[:5])

    res = {"path": path, "tables": len(blocks), "errors": errs, "warnings": warns}
    res["status"] = "PASS" if not errs else "FAIL"
    return res


def sidecar(path):
    """校验旁车文件（context-manifest.json + *.provenance.json）。

    **v2 修正（U2 `REV-20261007-030` F1）**：非规范键名（如历史产物用的 `blocks`）
    由 `NOTE` 升为 **WARN** —— 契约（`S-data-envelope.md` §3）规定的规范键名是 `blockProvenance`；
    偏离可见但不算 error（否则历史产物一律 FAIL）。
    """
    out, unresolved = [], set()
    dirn = os.path.dirname(path)
    if not os.path.isdir(dirn):
        return ["ERROR: sidecar directory not found: %s" % dirn], unresolved
    
    # context-manifest.json 必须存在
    if not os.path.exists(os.path.join(dirn, "context-manifest.json")):
        out.append("ERROR: context-manifest.json missing")
    
    # *.provenance.json 的 blockProvenance 必须是 list
    provs = [f for f in os.listdir(dirn) if f.endswith(".provenance.json")]
    if not provs:
        out.append("WARN: provenance sidecar missing")
    
    for f in provs:
        try:
            pr = json.load(open(os.path.join(dirn, f), encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            out.append(f"ERROR: {f} unreadable: {e}")
            continue
        
        # T7：收集旁车登记的未解析引用（(table, field, value) 三元组）
        for u in (pr.get("unresolvedRefs") or []):
            if isinstance(u, dict) and {"table", "field", "value", "reason"} <= set(u) and str(u.get("reason") or "").strip():  # L3：reason 必须非空
                unresolved.add((u["table"], u["field"], u["value"]))

        bp = pr.get("blockProvenance")
        if bp is None:
            others = [k for k in ("blocks",) if k in pr]
            if others:
                out.append("WARN: sidecar uses non-canonical key %s (contract: `blockProvenance`) — "
                           "见 S-data-envelope.md §3" % ",".join(others))
            else:
                out.append("WARN: no `blockProvenance` key (sidecar uses: %s)" % ",".join(list(pr.keys())[:6]))
        elif not isinstance(bp, list):
            out.append("ERROR: blockProvenance must be a list, got %s" % type(bp).__name__)
        else:
            # 每项必须有 5 个字段
            need = {"table", "recordCount", "contentHash", "evidenceGrade", "sources"}
            for i, it in enumerate(bp):
                if not isinstance(it, dict):
                    out.append("ERROR: blockProvenance[%d] 不是对象" % i)
                    continue
                missing = sorted(need - set(it.keys()))
                if missing:
                    out.append("ERROR: blockProvenance[%d] missing %s" % (i, missing))
                    continue
                # ---- T2（v0.4.0）证据门槛：证据必须**可核验**，不只是一个键名 ----
                grade = it.get("evidenceGrade")
                if grade not in ("OBSERVED", "INFERRED", "UNKNOWN"):
                    out.append("ERROR: blockProvenance[%d].evidenceGrade=%r 不在闭集 "
                               "{OBSERVED,INFERRED,UNKNOWN}" % (i, grade))
                ch = it.get("contentHash")
                if not isinstance(ch, str) or not ch.strip():
                    out.append("ERROR: blockProvenance[%d].contentHash 为空（证据不可核验）" % i)
                elif not ch.startswith("sha256:") and "fnv1a64" not in ch:
                    out.append("WARN: blockProvenance[%d].contentHash 非 sha256 形态且未标注占位算法：%r"
                               % (i, ch[:24]))
                srcs = it.get("sources")
                rc_ = it.get("recordCount")
                if not isinstance(srcs, list):
                    out.append("ERROR: blockProvenance[%d].sources 必须是 list" % i)
                elif rc_ and len(srcs) == 0:
                    # 「显式 ≠ 空」：有记录却无来源时，**必须显式声明原因**（notes 非空）。
                    # 实测参照物：广陵散 5 个派生块即以此形式合规（sources=[] + notes 说明 + INFERRED）。
                    # 只有「有记录 + 无 sources + **无 notes**」才是**静默缺失**。
                    if (it.get("notes") or "").strip():
                        out.append("blockProvenance[%d] recordCount=%s 但 sources 为空（notes 已声明原因，按「显式≠空」接受）" % (i, rc_))
                    else:
                        out.append("ERROR: blockProvenance[%d] recordCount=%s 但**既无 sources 也无 notes**"
                                   " —— 静默缺失（见 A-longform.md §8 / S-data-envelope.md §3）" % (i, rc_))
                else:
                    for j, s in enumerate(srcs):
                        if not isinstance(s, dict):
                            out.append("ERROR: blockProvenance[%d].sources[%d] 不是对象" % (i, j))
                            continue
                        # 来源标记：兼容实测到的两种形态 —— {md|path|file, ...} 与 {key, sources:[...]}
                        if not (any(s.get(k) for k in ("md", "path", "file")) or (s.get("key") and isinstance(s.get("sources"), list) and len(s["sources"]) > 0)):  # L4：key 须带嵌套 sources
                            out.append("ERROR: blockProvenance[%d].sources[%d] 缺来源标记（md/path/file/key 任一）"
                                       % (i, j))
                        lvl = s.get("grade") or s.get("evidence")
                        if lvl not in ("OBSERVED", "INFERRED", "UNKNOWN"):
                            out.append("WARN: blockProvenance[%d].sources[%d] 等级缺省或非闭集：%r" % (i, j, lvl))
                        nested = s.get("sources")
                        if nested is not None and not (isinstance(nested, list)
                                                       and all(isinstance(x, str) for x in nested)):
                            out.append("ERROR: blockProvenance[%d].sources[%d].sources 必须是字符串数组" % (i, j))
    
    return out, unresolved


ISSUE_RULES = (
    ("MISSING_ID", "missing numeric `id`"),
    ("MISSING_PROJECT_ID", "missing numeric `projectId`"),
    ("CHAPTER_ID_NOT_INT", "章节必须用**整数 id**"),
    ("CHAPTER_ORDER", "chapters 的 `order`"),
    ("FK_DANGLING", "dangling"),
    ("FK_TYPE", "must be number"),
    ("ENUM_VIOLATION", "enum violation"),
    ("EVIDENCE_GRADE", "evidenceGrade"),
    ("EVIDENCE_NO_HASH", "contentHash 为空"),
    ("EVIDENCE_SILENT_ABSENT", "既无 sources 也无 notes"),
    ("EVIDENCE_NO_SOURCES", "sources 必须是非空 list"),
    ("EVIDENCE_ABSENT_DECLARED", "但 sources 为空"),
    ("FIELD_NULL_OR_EMPTY", "null/empty"),
    ("EVIDENCE_NO_MARKER", "缺来源标记"),
    ("EVIDENCE_NESTED", "必须是字符串数组"),
    ("SIDECAR_KEY", "blockProvenance"),
    ("SIDECAR_MISSING", "context-manifest.json missing"),
    ("TABLE_UNKNOWN", "not in schema-tables.md index"),
    ("TOP_LEVEL_VERSION", "top-level `version`"),
    ("TOP_LEVEL_BLOCKS", "top-level `blocks`"),
    ("NOT_OBJECT", "not an object"),
)
_PATH_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*\[\d+\](?:\.[A-Za-z0-9_]+)*)")


def issue(msg):
    """把消息归为稳定三元组 `{code, field_path, message}`（T4，v0.4.0）。

    `code` 由**显式关键字规则表**得出：改文案必须同步改规则表，故对既有检查是稳定标识；
    新增检查若忘登记会落到 `OTHER`（可被回归测出）。
    """
    code = "OTHER"
    for c, kw in ISSUE_RULES:
        if kw in msg:
            code = c
            break
    m = _PATH_RE.match(msg)
    return {"code": code, "field_path": m.group(1) if m else "", "message": msg}


def main():
    argv = [a for a in sys.argv[1:] if a != "--json"]
    want_json = "--json" in sys.argv
    if not argv:
        print("用法：python check_framework_artifact.py <framework.json> [<framework2.json> ...]", file=sys.stderr)
        return 2
    
    spec = parse_registry()
    schema_tables, declared_tables = parse_schema_tables()
    # T4：--json 模式下，从最早处即抑制人类可读输出（否则污染 JSON）
    _saved = sys.stdout
    if want_json:
        sys.stdout = open(os.devnull, "w")
    print("registry tables: %d | schema index tables: %d" % (len(spec), len(schema_tables)))
    # v3（大扫除 P1）：表名来源必须可信 —— 缺失或与 §2 标题自述不符时，产物判定不可依赖。
    # 自述张数缺失也算不可信：否则删掉标题里的「（N 张）」即可让交叉核对**静默跳过**
    # （`REV-20261007-034` 弱化项）。
    if not schema_tables or declared_tables is None or declared_tables != len(schema_tables):
        print("ERROR: schema-tables.md §2 表名来源不可信（自述 %s 张 / 实际解析 %d 张；自述缺失亦不可信）"
              "—— 校验未完成" % (declared_tables, len(schema_tables)), file=sys.stderr)
        return 2
    
    # **v2 修正（U4 `REV-20261007-031` #1）**：路径不存在曾抛未捕获 FileNotFoundError，
    #   且退出码 1 与"业务 FAIL"同码 → 外部无法区分。现归为**环境错误**：友好提示 + 退出码 2。
    missing_paths = [p for p in argv if not os.path.exists(p)]
    for mp in missing_paths:
        print("ERROR: artifact not found: %s" % mp, file=sys.stderr)
    
    total_errors = 0
    results = []
    for p in argv:
        if p in missing_paths:
            continue
        sc, unresolved = sidecar(p)          # T7：先取旁车登记，再据此判定悬空引用
        r = check(p, spec, schema_tables, unresolved)
        
        print("=" * 72)
        print("ARTIFACT:", r["path"])
        print("STATUS: %s | tables: %s | errors: %d | warnings: %d" % (
            r["status"], r.get("tables"), len(r["errors"]), len(r["warnings"])))
        
        for e in r["errors"][:10]:
            print("   ERROR ", e)
        if len(r["errors"]) > 10:
            print("   ... +%d more" % (len(r["errors"]) - 10))
        
        for x in sc:
            print("   ", x)
        
        print("   warnings sample:", r["warnings"][:3])
        results.append({"path": r["path"], "status": r["status"],
                        "tables": r.get("tables"),
                        "errors": [issue(x) for x in r["errors"]],
                        "warnings": [issue(x) for x in r["warnings"]],
                        "sidecar": sc})
        total_errors += len(r["errors"]) + len([x for x in sc if x.startswith("ERROR")])
    
    sys.stdout = _saved            # T4：恢复 stdout（此后只输出 JSON 或 TOTAL）
    if not want_json:
        print("=" * 72)
    if missing_paths:
        # 不打印 TOTAL ERRORS —— 否则 "TOTAL ERRORS: 0" 会被误读为"校验通过"
        print("ABORTED: %d path(s) not found — 校验未完成" % len(missing_paths))
        return 2          # 环境错误优先于业务判定（结果不可信）
    if want_json:
        print(json.dumps({"schema": "storyforge.artifact-check.v1",
                          "registryTables": len(spec),
                          "schemaIndexTables": len(schema_tables),
                          "artifacts": results}, ensure_ascii=False, indent=1))
        return 0 if total_errors == 0 else 1
    print("TOTAL ERRORS:", total_errors)
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
