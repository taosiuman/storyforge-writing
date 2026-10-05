# COMPAT — storyforge-writing 工作副本说明

本目录是**外部技能的受控副本**，用于优化与产出差异包。**原件的改动必须经用户逐项确认后另行执行**。

## 1. 位置与身份

| 项 | 值 |
| --- | --- |
| 原件（WSL） | `\\wsl.localhost\OpenClawGateway\home\openclaw\.openclaw\agents\main\workspace\skills\storyforge-writing` |
| 工作副本 | `work/storyforge-writing/`（本目录） |
| 原始快照 | `work/_baseline/storyforge-writing/`（v0.1.0 逐字节副本，用于出差异包） |
| 版本基线 git 仓库 | **无** —— 该技能不是 git 仓库，因此差异以**快照对比**方式产出 |
| 上游来源 | `github.com/yuanbw2025/storyforge` → 本地主基线 `H:\storyforge-main`；辅助来源 `H:\StoryForge-master` |
| 原始版本 | v0.1.0（`source_version_baseline: 2026-09-27 (…v1.7.0)`，**已过期**） |
| 当前版本 | **v0.2.0** |

## 2. 基线判定（依据 `REV-20261005-015`）

- **主基线 = `H:\storyforge-main`**，且**改为逐文档记版本**（旧版单一日期 `2026-09-27` 已过期：
  多份权威文档落在 09-28/09-29，施工契约甚至 2026-10-04）。
- **辅助来源 = `H:\StoryForge-master`**，**仅**用于 "agent 纪律 / 证据分级"；
  该仓库是 Desktop IDE 线（`apps/desktop`+`apps/api`、FastAPI/Tauri、**SQLite**），
  与本技能的浏览器 `Dexie/IndexedDB + schema v10` **不同源**，不得混入数据契约。

## 3. v0.1.0 → v0.2.0 改动清单

| 类别 | 改动 | 依据 |
| --- | --- | --- |
| 基线 | 单一日期 → **逐文档版本表**（8 份文档）+ `primary_source` / `auxiliary_source` 分列 | `REV-20261005-015` #1、#2 |
| 路由表 | 基线路由表 **8 行** → 现行 **10 行**（新增「小说转剧本」「世界引擎（封存/出口）」）；「漫剧前期」→「漫剧素材前期」；标题行数由脚本实测写入（曾误写为 12 类，`REV-20261005-017` #4） | `REV-20261005-016` #4、#7；`REV-20261005-015` #7 |
| 新增契约 | `contracts/C-screenplay.md`（小说转剧本，含忠实/改编/新增三态与完成判据） | `REV-20261005-016` #4 |
| 新增契约 | `contracts/A-world-engine.md`（worldCode / WorldRelease 字段闭集 / 出口四类 / 分享包） | `REV-20261005-016` #7 |
| 新增契约 | `contracts/S-data-envelope.md`（三注册表登记字段 / 导入导出规则 / **JSON 信封 + 待实测项** / 证据分级要求） | `REV-20261005-016` #1–#3 |
| 数据契约 | 三注册表补齐登记字段（`CONTEXT_SOURCES` 7 项 / `adopt()` 6 项 / `PROJECT_TABLES` 7 项）；裁剪三态修正为 `missing`/`omitted`/`partial-selection` | `REV-20261005-016` #6；`REV-20261005-015` #6 |
| 治理红线 | 新增 **证据分级**（`OBSERVED`/`INFERRED`/`UNKNOWN` + 主张与证据等量 + 逐块 provenance） | `REV-20261005-016` #8 |
| 契约加厚 | `A-longform.md`：节点模式**字段闭集**（9 项）+ 图执行前 5 项检查 + **跨模式验收 5 条**；长铗传 70→**90 集**、`scripts/act1-4`→`episode-01..04` | `REV-20261005-016` #5；`REV-20261005-015` #3 |
| 契约加厚 | `A-interactive.md`：补 `AdventureContentV2` **八能力** + 唯一权威写入 `commitAdventureAction`/`commitAdventureNarrativeChoice` + `text-adventure-production/` 入口 | `REV-20261005-015` #4 |
| 来源标注 | `C-post.md` / `B-motion-drama.md` / `SKILL.md`：凡「达芬奇」相关内容一律标注为**环境来源（`INFERRED`）**，非源仓库基线（源仓库 0 命中） | `REV-20261005-015` #5 |
| 机制 | 新增 `scripts/check_consistency.py`（**11 项断言**，含路由↔契约集合一致性、术语一致性、来源标注、契约锚点） | 同 seedancer 模式 |

## 4. 验收

```bash
python scripts/check_consistency.py     # 期望：RESULT: PASS (0 fail, 0 warn)
```

记录：`generated/storyforge_consistency_p3*.out`（父仓库）。

## 5. 已知限制（如实声明）

1. **JSON 信封的确切字段名仍为 `待实测`** —— 需要一次真实导出样本（`/long` 作品库导出 JSON 包）；
   在取得样本前，产物按 `S-data-envelope.md` 的**结构**输出，并显式标注未定项，**禁止补造字段**。
2. 各表**完整字段名与取值域**需读 `src/lib/db/schema.ts` 对应表定义（当前只列了部分 id 列）。
3. 契约内容与上游文档的**逐字一致性**不由脚本校验（需人工或上游对比）。
4. 上游文档若再次更新，需人工重读并更新版本表（脚本不检测上游变化）。
5. 路由表的**分类语义**（某个产品该归 A 还是 C）无法断言，属判断项。

## 6. 回写规矩（与 seedancer 同）

- 本副本的改动**不自动回写**；回写前须：① 差等级独立复审通过 ② 用户逐项确认 ③ 原件备份 ④ hash 比对。
- 回写方式：优先对原件目录做快照对比 + 应用差异（该技能无 git，故不使用 `git apply`）。
