# Changelog — storyforge-writing

本项目版本独立于上游 StoryForge 的版本号；上游基线以**逐文档版本**记录（见 `SKILL.md`《来源与验证》）。

## v0.2.1 — 2026-10-06

- **修复跨文件规则矛盾（用户使用中发现）**：`SKILL.md` §五 曾写「每块带 provenance（在 JSON 里）」，与 `S-data-envelope.md` §3 的「必须放旁车文件」冲突。
  现统一以 **`contracts/S-data-envelope.md` §3 为唯一权威**（旁车文件），`SKILL.md` 改为指向它；
  并新增检查器断言 **`C4`**（provenance 存放规则单源一致）防止复发。

- 新增 `skill-card.md`（ClawHub 的 `verify` 曾报 `card.missing`：卡片文件此前不存在；
  内容含诚实的已知风险与缓解措施）
- 说明：`verify` 的安全判定为 **clean / benign**（confidence: high）—— 本技能不包含隐藏安装钩子、
  不使用凭据、不自动改数据库/运行态
- 标注：本技能的 JSON 产物**不是备份包**（不含 `version` 字段），导入由用户在应用内完成

## v0.2.0 — 2026-10-05

### 基线与覆盖
- **基线重钉**：单一日期 `2026-09-27` → **逐文档版本**（10 条），并区分 `primary_source`
  与 `auxiliary_source`（后者仅用于 agent 纪律/证据分级，不混入数据契约）
- **新增 3 个子契约**，补上原版覆盖缺口：
  - `contracts/C-screenplay.md` —— 小说转剧本（改编 Brief / Beat·Scene Card / 兼顾三态 / 完成判据 / 工程边界）
  - `contracts/A-world-engine.md` —— 世界引擎（worldCode / WorldRelease 字段闭集 / 出口四类 / 分享包）
  - `contracts/S-data-envelope.md` —— 数据契约与导入/导出（横切）
- 路由表：基线的 **8 行** → **10 行**（新增两行；产品「漫剧前期」按上游改为「漫剧素材前期」）

### 契约修正
- `A-longform.md`：补节点模式**字段闭集**（9 项）+ 图执行前 5 项检查 + **跨模式验收 5 条**；
  长铗传示例 70 集 → **90 集**、`scripts/act1-4` → `episode-01..04`
- `A-interactive.md`：补现行内核 `AdventureContentV2`（**八能力**）与唯一权威写入
  `commitAdventureAction` / `commitAdventureNarrativeChoice`
- 三处旧契约的**溯源错位 / 表述过强**修正（并入上游原文口径）

### 治理
- 新增**证据分级**（`OBSERVED` / `INFERRED` / `UNKNOWN` + 主张与证据等量 + 逐块 provenance），
  并明确其**效力边界**：应用不校验该字段，不能指望系统拦住虚构入 Canon
- 凡「达芬奇」等**环境来源**内容，逐行标注为非源仓库基线

### 机制
- 新增 `scripts/check_consistency.py`（13 项断言，零依赖）
- 修正一处**会导致导入必然被拒**的契约错误：早期草稿把自造顶层键标为"可核验"，
  且把 IndexedDB `schema v10` 与备份版本 `v14` 混用

## v0.1.0 — 初始版本

- 从上游文档提炼 6 份子契约（长篇/短篇、角色、交互、漫画、漫剧、后期）+ 总入口 SKILL.md
- 基线标注为单一日期 `2026-09-27`

---

## 校验方式

```bash
python scripts/check_consistency.py     # 13 项断言；期望 0 fail 0 warn
```
