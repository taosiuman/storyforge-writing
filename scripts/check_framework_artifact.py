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
"""
from __future__ import annotations

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


def parse_schema_tables():
    """从 references/schema-tables.md 解析全部表名（123 张）。

    **v2 修正（U2 `REV-20261007-030` F2）**：索引表里有两张表的 store 定义**不以 `++id` 开头**
    （`importFiles` / `referenceAnalysisSources`），旧正则只认 `++id` 前缀 → 实得 **121 ≠ 123**，
    产物若用这两表会被**误报**假 ERROR。现改为在 §2 全文按"表格行"解析，并保留 §1 标题回退。
    """
    st_path = os.path.join(SKILL_ROOT, "references", "schema-tables.md")
    if not os.path.isfile(st_path):
        print(f"错误：找不到 {st_path}", file=sys.stderr)
        return set()
    sc = open(st_path, encoding="utf-8").read()
    # §2 索引表：任意形状的 store 定义行 | `tableName` | `store 定义` |
    if "## 2." in sc:
        sec2 = sc.split("## 2.", 1)[1]
        sec2 = sec2.split("## 3.", 1)[0] if "## 3." in sec2 else sec2
    else:
        sec2 = sc
    names = set(re.findall(r"^\|\s*`([A-Za-z0-9_]+)`\s*\|\s*`[^`]+`\s*\|\s*$", sec2, re.M))
    # §1 详细表：每节形如 ### `tableName`（回退，防 §2 缺行）
    names |= set(re.findall(r"^\s*### `([A-Za-z0-9_]+)`", sc, re.M))
    return names


def check(path, spec, schema_tables):
    """校验单个 framework.json，返回 {path, status, tables, errors, warnings}。"""
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
            
            # 必需字段：id 和 projectId 必须是数字
            if not isinstance(r.get("id"), int):
                errs.append("%s[%d] missing numeric `id`" % (t, i))
            if not isinstance(r.get("projectId"), int):
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
                
                # FK 悬挂警告
                if isinstance(v, int) and f.endswith("Id") and v not in all_ids:
                    warns.append("%s[%d].%s=%s dangling (no such id anywhere)" % (t, i, f, v))
                
                # null/empty 警告
                if v is None or v == []:
                    warns.append("%s[%d].%s null/empty (unresolved)" % (t, i, f))
    
    res = {"path": path, "tables": len(blocks), "errors": errs, "warnings": warns}
    res["status"] = "PASS" if not errs else "FAIL"
    return res


def sidecar(path):
    """校验旁车文件（context-manifest.json + *.provenance.json）。

    **v2 修正（U2 `REV-20261007-030` F1）**：非规范键名（如历史产物用的 `blocks`）
    由 `NOTE` 升为 **WARN** —— 契约（`S-data-envelope.md` §3）规定的规范键名是 `blockProvenance`；
    偏离可见但不算 error（否则历史产物一律 FAIL）。
    """
    out = []
    dirn = os.path.dirname(path)
    if not os.path.isdir(dirn):
        return ["ERROR: sidecar directory not found: %s" % dirn]
    
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
                if not isinstance(it, dict) or not need.issubset(it.keys()):
                    missing = sorted(need - set(it.keys() if isinstance(it, dict) else []))
                    out.append("ERROR: blockProvenance[%d] missing %s" % (i, missing))
                    break
    
    return out


def main():
    if len(sys.argv) < 2:
        print("用法：python check_framework_artifact.py <framework.json> [<framework2.json> ...]", file=sys.stderr)
        return 2
    
    spec = parse_registry()
    schema_tables = parse_schema_tables()
    print("registry tables: %d | schema index tables: %d" % (len(spec), len(schema_tables)))
    
    # **v2 修正（U4 `REV-20261007-031` #1）**：路径不存在曾抛未捕获 FileNotFoundError，
    #   且退出码 1 与"业务 FAIL"同码 → 外部无法区分。现归为**环境错误**：友好提示 + 退出码 2。
    missing_paths = [p for p in sys.argv[1:] if not os.path.exists(p)]
    for mp in missing_paths:
        print("ERROR: artifact not found: %s" % mp, file=sys.stderr)
    
    total_errors = 0
    for p in sys.argv[1:]:
        if p in missing_paths:
            continue
        r = check(p, spec, schema_tables)
        sc = sidecar(p)
        
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
        total_errors += len(r["errors"]) + len([x for x in sc if x.startswith("ERROR")])
    
    print("=" * 72)
    if missing_paths:
        # 不打印 TOTAL ERRORS —— 否则 "TOTAL ERRORS: 0" 会被误读为"校验通过"
        print("ABORTED: %d path(s) not found — 校验未完成" % len(missing_paths))
        return 2          # 环境错误优先于业务判定（结果不可信）
    print("TOTAL ERRORS:", total_errors)
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
