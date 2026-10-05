# S-data-envelope — 数据契约与导入/导出（v0.2.0）

> 来源（一手核实）：`src/lib/export/json-export.ts`、`src/lib/export/backup-trust.ts`、
> `src/lib/export/registry-export.ts`、`src/lib/db/schema.ts`、`docs/DATA-GOVERNANCE.md`（v1.8.0）。
>
> ⚠️ **本文件的早期草稿曾把自造的顶层键标为"可核验"**，被 `REV-20261005-017` 直接证伪。
> 现版本只写**有出处**的内容；无出处的部分一律标 `待实测` 并给出取得方法。

## 1. 备份/导出契约的**真实**形态（源：`json-export.ts:109-132`）

```ts
export interface ProjectExportData {      // 「完整项目导出数据结构(导出格式契约)」
  version: number                          // 备份协议版本
  exportedAt: number
  ownership: {
    contractVersion: number                // registry-export.ts: 当前 = 1
    worldExportId: number
    workExportId: number
  }
  project: { workspaceUid, workspacePurpose, name, enableMultiWorld,
             productPlatformOptIns, createdAt, updatedAt, ... }   // 精确键集见 backup-trust.ts:27+
  worlds: (Omit<World,'id'|'projectId'> & { _exportId: number })[]
  works:  (Omit<Work,'id'|'projectId'|'worldId'|...> & { _exportId: number })[]
  // …（其余表同构）
}
```

**关键事实（每条都有出处）**：

| 事实 | 出处 |
| --- | --- |
| 导入**只接受**备份版本 `v14`；`version !== 14` 直接报「只接受当前备份版本 v14」 | `backup-trust.ts:10,98-103` |
| 预检是**只读**检查：表清单来自 `PROJECT_TABLES`，**不复制一套导出枚举**，**不访问 IndexedDB** | `backup-trust.ts:1-8` |
| 只接受与当前架构**完全一致**的备份：**不执行升级，也不缺表补空** | 同上 |
| 项目对象按**精确键集**检查（`CURRENT_PROJECT_EXPORT_KEYS` / `inspectExactKeys`） | `backup-trust.ts:27+,110-113` |
| `ownership.contractVersion` 当前 = `1` | `registry-export.ts:651-652,684`（注：同文件 `:24` 是 `CURRENT_EXPORT_VERSION = 14`） |

## 2. ⚠️ 两个"版本号"完全不同，不得混用（v0.2.0 修正）

| 常量 | 值 | 用途 |
| --- | --- | --- |
| `STORYFORGE_SCHEMA_VERSION` | **10** | **IndexedDB（Dexie）schema 版本** —— 与导入信封无关 |
| `CURRENT_BACKUP_VERSION` | **14** | **备份/导出协议版本** —— 导入边界只认它 |

> 早期草稿把 `schema v10` 写成信封的 `schemaVersion` 字段，属**事实错误**（`REV-20261005-017` #2）。

## 3. 本技能产物的定位（修正后）

**本技能的产物是"框架语料"，不是备份包。** 两者的差别是硬的：

| 项 | StoryForge 备份/导出 | 本技能产出 |
| --- | --- | --- |
| 顶层结构 | `ProjectExportData`（见 §1） | 本技能自有结构（见下） |
| 版本字段 | `version: 14`（不符即拒） | **不加 `version` 字段**（避免伪装成备份） |
| 未知字段 | **精确键集**，多余字段导致拒收 | 因此**不得**把 `provenance`/`evidenceGrade` 塞进记录内 |
| 导入方式 | 应用内导入器 | 由**用户**在应用内另行处理；agent 不代操作 |

**本技能的语料结构（自有，不冒充备份）**：

```jsonc
{
  "storyforgeFramework": "0.2.0",     // 本技能版本（非备份版本）
  "baseline": { "docs/DATA-GOVERNANCE.md": "v1.8.0", "docs/products/LONGFORM-AND-NODE.md": "v1.6.0" },
  "blocks": [
    { "table": "characters",          // 表名必须 ∈ PROJECT_TABLES 派生清单
      "records": [ /* 字段闭集见 SKILL.md §二 */ ] }
  ]
}
```

**provenance 与证据分级放"旁车文件"**（`storyforge-framework.provenance.md` 或 `.json`），
**不放进导入候选**：因为导入走精确键集，多一个键就会被拒（`backup-trust.ts:110-113`）。
旁车文件记录：来源 md + revision + contentHash + `evidenceGrade`（逐块）。

## 4. 三条主干规则（源：`docs/DATA-GOVERNANCE.md`）

1. **清单必须派生**：导出/导入/删除/世界切换清单**从 `PROJECT_TABLES` 派生**；
   schema/required table 数量由代码与 `npm run check:required-tables` 决定，**不在手写文档中复制清单**。
2. **精确字段闭集**：导入拒绝旧镜像与未知字段（实现见 `backup-trust.ts` 的精确键集检查）。
3. **候选 ≠ Canon**：模型输出先是候选；`adopt()` 校验（field / schema / 外键 / owner / 作用域 / stale）通过且作者确认后才进 Canon。

## 5. `待实测` 项（给出取得方法，禁止补造）

| 未定项 | 取得方法 |
| --- | --- |
| 各表**完整字段名与取值域** | 读 `src/lib/db/schema.ts` 对应表定义（逐表抄录，不推断） |
| `worlds`/`works` 等数组元素的**全字段** | 读 `json-export.ts` 的 `Omit<...>` 组合后展开 |
| blob/OPFS 等外部对象在包内的引用形式 | 需一次**含媒资的真实导出样本** |
| 用户实际希望走哪种导入路径 | 需向用户确认（本技能不代操作浏览器） |

## 6. 交付前对齐清单

- [ ] 语料**不含** `version` 字段（不冒充备份）、**不含**记录外的未知键
- [ ] 每个 `table` 来自 `PROJECT_TABLES` 派生清单
- [ ] 每条记录字段不超出闭集
- [ ] **provenance 与 evidenceGrade 在旁车文件**，不混入候选记录
- [ ] 交付说明列出所有 `待实测` 项与取得方法
- [ ] 导入由用户在应用内执行（agent 不代操作）
