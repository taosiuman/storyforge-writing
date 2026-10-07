# storyforge-writing

把 **StoryForge**（[yuanbw2025/storyforge](https://github.com/yuanbw2025/storyforge)，MIT）的**数据契约 + 写作 SOP + 治理纪律**
蒸馏成一份 **agent 可直接执行**的写作技能：判定任务属于哪类产品 → 读对应子契约 → 生成框架语料 → 按 SOP 推进。

> 本仓库只包含**契约与工作流**，**不包含**上游应用的源代码、也不操作其浏览器运行时。

## 路由：10 类能力 → 子契约

| 产品 | 分类 | 子契约 | 核心产物 |
| --- | --- | --- | --- |
| 长篇（分步骤） | A 开发创作 | `contracts/A-longform.md` | 世界观/故事核/角色/大纲/细纲/正文 + 长程一致性 |
| 短篇 | A 开发创作 | `contracts/A-longform.md` §短篇 | 故事核/角色/单线大纲/正文 |
| **小说转剧本** | A 开发创作 | `contracts/C-screenplay.md` | 改编 Brief → 场次计划 → 剧本场景 → 不可变剧本版本 |
| **世界引擎（封存/出口）** | A 世界侧 | `contracts/A-world-engine.md` | worldCode / WorldRelease / 数据出口包 |
| 角色聊天（角色卡） | A 开发创作 | `contracts/A-characters.md` | 角色卡/说话风格/记忆/禁区 |
| AVG / 文字冒险 | A 开发创作 | `contracts/A-interactive.md` | `AdventureContentV2` 八能力/场景树/分支/结局 |
| 跑团 TTRPG | A 开发创作 | `contracts/A-interactive.md` §跑团 | 规则包/场景/事件（只读冻结世界） |
| 漫画 | B 视觉化 | `contracts/B-comic.md` | 分镜脚本/页/格/视觉主体卡 |
| 漫剧素材前期 | B + C | `contracts/B-motion-drama.md` | 系列圣经/逐集/分镜/Prompt IR/适配包 |
| 漫剧后期对接 | C 制作后期 | `contracts/C-post.md` | prompt 包 → 生成管线对接 |

横切契约：`contracts/S-data-envelope.md`（数据契约与导入/导出；**全部产品适用**）。

## 基线（逐文档版本，非单一日期）

| 文档 | 版本 | 日期 |
| --- | --- | --- |
| `docs/DATA-GOVERNANCE.md` | **v1.8.0** | 2026-09-28 |
| `docs/PROJECT-MASTER-CHARTER.md` | v1.10.0 | 2026-09-29 |
| `docs/DOCUMENT-AUTHORITY.md` | v2.4.0 | 2026-09-29 |
| `docs/CONTEXT-ROUTING.md` | v2.7.0 | 2026-09-29 |
| `docs/products/UPPER-PRODUCTS.md` | v2.6.0 | 2026-09-28 |
| `docs/products/LONGFORM-AND-NODE.md` | v1.6.0 | 2026-09-27 |
| `docs/products/MOTION-DRAMA.md` | v1.2.0 | 2026-09-15 |
| `docs/products/INDEPENDENT-CREATION.md` | v1.2.0 | 2026-08-31 |
| `docs/products/WORLD-ENGINE.md` | v1.4.0 | 2026-09-10 |
| `src/lib/db/schema.ts` | schema v10 | — |

> 旧版曾用单一日期 `2026-09-27` 作基线 —— **已过期**（多份权威文档落在 09-28/09-29）。现改为逐文档记版本，见 `SKILL.md`。

## 校验

```bash
python scripts/check_consistency.py     # 技能包自检（19 项）；期望：RESULT: PASS (0 fail, 0 warn)
python scripts/check_framework_artifact.py <framework.json>   # 产物校验；期望：TOTAL ERRORS: 0
```

**两个校验器分工不同**（勿混用）：
- `check_consistency.py` —— 校验**技能包自身**（SKILL.md / contracts / references 的文档一致性）。
- `check_framework_artifact.py` —— 校验**生成产物**（framework.json 是否符合字段/枚举/外键契约）。
  覆盖 6 类违规：FK 字段类型（必须 number）/ 必需字段（`id` + `projectId`）/ 枚举闭集 /
  顶层结构（无 `version` 字段）/ 旁车结构（`blockProvenance` 必须是 list）/ `context-manifest.json` 存在性。

19 项断言（摘要，非穷举）：版本戳 / frontmatter / 基线结构 / 路由表↔契约集合（精确）/ 相对路径（链接）/
被引用本地文件存在性（含反引号）/ 横切参考交叉一致 / 参考文件自述计数 / 裁剪三态术语 /
证据分级规则句 / 环境来源逐行标注 / 契约锚点 / 契约实质下限 / 基线自洽 /
provenance 单源 / 体积预算 / 版本与断言数自洽。

## 三个必须知道的硬事实

1. **产物 ≠ 备份包**：本技能产出的"框架语料"**不含 `version` 字段**，且**不得**把 `provenance` / `evidenceGrade`
   塞进记录内 —— 应用导入走**精确键集**，多余键会被**直接拒收**；证据链放**旁车文件**。
2. **两个版本号不得混用**：`STORYFORGE_SCHEMA_VERSION = 10`（IndexedDB schema）≠
   `CURRENT_BACKUP_VERSION = 14`（备份/导入协议，非 14 即拒）。
3. **证据分级是作者/评审侧纪律**：应用不校验该字段、`adopt()` 不含它 —— **不能指望系统拦住虚构入 Canon**。

## 已知限制

见 [`COMPAT.md`](COMPAT.md) §5 与 `scripts/check_consistency.py` 顶部说明。摘要：
JSON 信封的部分字段仍需一次真实导出样本；重点表的 TS 接口见 [`references/schema-tables.md`](references/schema-tables.md)，
其余表仍需读上游 `src/lib/db/schema.ts`；**AI 可写字段**清单见 [`references/field-registry.md`](references/field-registry.md)
（64 表 / 528 项，已抽取）；两份 `references/*.md` 是某一时点的机械快照，上游变更后需重生成；
脚本不检测上游是否又更新；路由分类语义无法断言。

## 归因

- 契约蒸馏自 **[yuanbw2025/storyforge](https://github.com/yuanbw2025/storyforge)**（MIT License）——
  本仓库不包含其源代码，只包含从中提炼的契约与工作流描述。
- "agent 纪律 / 证据分级"部分参考 **StoryForge-master**（Desktop IDE 线）；
  该线与本技能的浏览器 `Dexie/IndexedDB + schema v10` **不同源**，**仅作辅助来源**、不混入数据契约。
- 许可与完整归因见 [`LICENSE`](LICENSE)。

## 版本

v0.3.2 —— 详见 [`CHANGELOG.md`](CHANGELOG.md)。
