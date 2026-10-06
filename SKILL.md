---
name: storyforge-writing
description: >-
  StoryForge 叙事写作框架（蒸馏自 github.com/yuanbw2025/storyforge 数据契约 + 写作 SOP）。
  用于生成框架性语料并受控写作：长篇/短篇/AVG/文字冒险/角色人设/跑团世界（A 类）、
  漫画分镜/漫剧 prompt 包（B 类）、漫剧后期对接生成管线（C 类）。
  使用场景（含「小说转剧本/剧本改编」「世界封存/世界引擎/世界出口包」「生成可导入语料」）：用户要求"按 StoryForge 框架写长篇/短篇/剧本/漫画/漫剧/AVG/跑团"、
  "生成框架语料"、"按写作 SOP 推进"、"对齐 StoryForge 数据契约"。
version: 0.2.1
license: MIT
compatibility: >-
  电影大师 agent 专属 H 类知识资产。依赖 projects/<项目>/ 已有 md 设定资产与
  knowledge/ 考据库。产物为 JSON 框架语料（可导入 StoryForge /long 作品库）+
  结构化 md。不操作浏览器 IndexedDB，导入动作由用户执行。
metadata:
  author: 电影大师
  source: https://github.com/yuanbw2025/storyforge
  source_version_baseline:
    audited: "2026-10-05（实测复核，见 REV-20261005-015）"
    note: "旧版曾是单一日期 2026-09-27，已过期；现改为**逐文档记版本**"
    primary_source: "H:\\storyforge-main（唯一数据契约基线）"
    documents:
      - "docs/DATA-GOVERNANCE.md: v1.8.0（2026-09-28）"
      - "docs/PROJECT-MASTER-CHARTER.md: v1.10.0（2026-09-29）"
      - "docs/DOCUMENT-AUTHORITY.md: v2.4.0（2026-09-29）"
      - "docs/CONTEXT-ROUTING.md: v2.7.0（2026-09-29）"
      - "docs/products/UPPER-PRODUCTS.md: v2.6.0（2026-09-28）"
      - "docs/products/LONGFORM-AND-NODE.md: v1.6.0"
      - "docs/products/MOTION-DRAMA.md: v1.2.0"
      - "docs/products/INDEPENDENT-CREATION.md: v1.2.0"
      - "docs/products/WORLD-ENGINE.md: v1.4.0"
      - "src/lib/db/schema.ts: schema v10（comic v5 迁移步）"
    auxiliary_source:
      path: "H:\\StoryForge-master\\docs\\ai\\anti-hallucination.md"
      scope: "**仅** agent 纪律/证据分级；**不是**数据契约基线（该仓库是 Desktop IDE 线：SQLite，与本技能的 Dexie/IndexedDB + schema v10 不同源）"
  openclaw:
    requires:
      bins: []
      env: []
      credentials: none
    optional_env: []
---

# storyforge-writing — StoryForge 写作框架总入口

把 StoryForge 的**数据契约 + 写作 SOP + 治理纪律**蒸馏成电影大师可自主执行的工作流。
本 skill 是**总入口**：判定任务属于哪类产品 → 读对应子契约 → 生成框架语料 → 按 SOP 推进。

## 何时加载

- 用户要求"按 StoryForge / 故事熔炉 框架写作"或"生成框架性语料"
- 需要长篇/短篇/AVG/文字冒险/角色人设/跑团世界/漫画/漫剧的**结构化创作**
- 任务涉及"世界观-故事核-角色-大纲-细纲-正文"任一层的受控生成
- 白名单项目（长铗传等）的叙事开发需要与 StoryForge 作品库对齐
- 需要**小说转剧本**（改编 Brief / 场次计划 / Scene Card）或**世界引擎**侧产物（worldCode / WorldRelease / 数据出口包）

## 一、产品路由表（10 类能力 → 任务分类）

先判定任务属于哪类产品，再读对应子契约文件。

| 产品 | 归属分类 | 子契约 | 核心产物 |
|---|---|---|---|
| 长篇（分步骤） | A 开发创作 | `contracts/A-longform.md` | 世界观/故事核/角色/大纲/细纲/正文 + 长程一致性 |
| 短篇 | A 开发创作 | `contracts/A-longform.md` §短篇 | 故事核/角色/单线大纲/正文 |
| **小说转剧本** | A 开发创作 | `contracts/C-screenplay.md` | 事实/人物/场景提取 → 改编 Brief → 场次计划 → 剧本场景 → 连续性/格式审校 → 不可变剧本版本 |
| **世界引擎（封存/出口）** | A 开发创作（世界侧） | `contracts/A-world-engine.md` | worldCode / WorldRelease（code+version+hash+能力画像）/ 数据出口 / 分享包 |
| 角色聊天（角色卡） | A 开发创作 | `contracts/A-characters.md` | 角色卡/说话风格/记忆/禁区 |
| AVG / 文字冒险 | A 开发创作 | `contracts/A-interactive.md` | 场景树/分支/对白/结局/物品/状态机 |
| 跑团 TTRPG | A 开发创作 | `contracts/A-interactive.md` §跑团 | 规则包/场景/事件（只读冻结世界） |
| 漫画 | B 视觉化 | `contracts/B-comic.md` | 分镜脚本/页/格/视觉主体卡 |
| 漫剧素材前期（原称"漫剧前期"） | B + C | `contracts/B-motion-drama.md` | 系列圣经/逐集/分镜/Image·Video Prompt IR/适配包 |
| 漫剧后期对接 | C 制作后期 | `contracts/C-post.md` | prompt 包 → 生成管线（达芬奇〔环境来源〕/Seedance） |

> 注：「达芬奇」相关条目来自 **agent 环境（`ai-memory`）**，**非** StoryForge 源仓库基线
> （在 `H:\storyforge-main` 全文检索 0 命中，见 `REV-20261005-015` #5）。按其操作前必须先在
> `ai-memory` 检索到对应条目；检不到就停下问用户。

**判定顺序**：
1. 关键词命中（"长篇/小说/剧本"→A；"分镜/漫画/漫剧"→B；"达芬奇〔环境来源〕/剪辑/调色"→C）
2. 意图（生成设定语料=A；出视觉料=B；接后期管线=C）
3. 项目归属（白名单直接开工；非白名单先汇报）

## 二、数据契约（字段闭集，可执行架构）

StoryForge 三个单一事实源——生成语料时必须遵守，不得手拼旁路：

1. **AI 读什么**：`CONTEXT_SOURCES` + `assembleContext()` / Context Gateway。
   按层次：任务/作用域/硬约束 → 目录与能力画像 → 相关摘要/事实/关系/事件 → 按需详情 → token 预算保护。
   每个 `CONTEXT_SOURCES` 条目至少表达 **7 项**：稳定 key、owner、允许作用域、revision/版本来源、预算类别、加载器、可见性。
   运行时生成 **Context Manifest**，记录实际选择、哈希、预算与遗漏。
   **裁剪必须留证据（三态，不得混淆）**：`missing`（冻结世界中**不存在**满足要求的资源）、`omitted`（资源**存在但未选入**本次 release/plan/run）、`partial-selection`（该语义域**仅选入部分**资源）。禁止把"没读"当"不存在"，禁止用"固定前缀/前 N 条"当主要检索算法。
2. **AI 能写什么**：`FIELD_REGISTRY` + `AdoptionSchema` + `adopt()`。
   模型输出只是**候选（CreativeArtifact）**，作者确认 `adopt()` 后才进 Canon；
   采纳校验至少覆盖 6 项：field / schema / 外键 / owner / 作用域 / stale（目标变化即拒绝）。
   禁止模型输出直接写库、禁止面板私有字段映射。
3. **表生命周期**：`PROJECT_TABLES`。导出/导入/删除/迁移/作用域/引用重映射统一收口，不得各写一份表清单。
   每个表的登记应覆盖 **7 项**：owner 与作用域字段 / 是否导出·导入·分享·仅本机 / 项目·世界·作品·实例的删除行为 /
   refs·nullable·重映射与导入顺序 / 当前 schema 版本与拒绝边界 / blob 等外部对象引用与回收 / 冻结版本·session·运行账本保留策略。
   ⚠️ **表清单不在文档中手抄**：以代码与 `npm run check:required-tables` 为准（源仓库治理要求）。

### 长篇核心表字段闭集（src/lib/db/schema.ts v10）

```
works          id, projectId, worldId, code, status, activeNarrativeModuleId
worldviews     id, projectId                       # 起源/自然/人文/种族/势力/地点/历史/规则
storyCores     id, projectId                       # 主题/核心冲突/叙事策略/主支线
powerSystems   id, projectId                       # 力量/体系
characters     id, projectId, name, roleWeight, moralAxis, orderAxis, statusEvidenceChapterId
characterRelations  id, projectId, fromCharacterId, toCharacterId
outlineNodes   id, projectId, parentId, order, type # 全书/卷/章 树
chapters       id, projectId, outlineNodeId, order, status
detailedOutlines  id, projectId, outlineNodeId      # 场景/目标/节拍/视角/承接/伏笔
foreshadows    id, projectId, status, type
stateCards     id, projectId, category, entityName, lastChapterId
storyTimelineEvents  id, projectId, chapterId, order
emotionBeatCards     id, projectId, chapterId
storyArcs      id, projectId, type, sourceStoryCoreId, producerRunId
codexCategories      id, projectId, domain, parentId, builtInKey, order
codexEntries         id, projectId, categoryId, worldGroupId, order, producerRunId
temporalFacts    id, projectId, worldGroupId, characterId, locationId, codexEntryId, predicate, status, sourceChapterId
knowledgeLedger  id, projectId, worldGroupId, characterId, knowledgeKey, factId, sourceChapterId, status
itemLedger       id, projectId, itemName, chapterId
narrativeSummaryNodes  id, projectId, worldGroupId, level, sourceChapterId, sourceOutlineNodeId, status
```

### 数据所有权（每条记录必须能回答）

`projectId`（工作区）→ `worldId/worldGroupId`（世界作用域）→ `workId`（独立作品）→ 产品实例/production/build/release/session。
- **Project 只存工作区壳**（身份/用途/活动 World/Work 指针）。
- **Work 拥有**作品标题/简介/流派/状态/字数/文风/活动叙事计划。
- **World 拥有**世界编号/版本/社区来源。
- 禁止在 Project 上镜像 World/Work 语义，禁止导入时展开旧 Project 对象。

### 三阶段所有权（世界衍生产品）

| 阶段 | 可读 | 新数据 owner | 交接证据 | 禁止 |
|---|---|---|---|---|
| S1 世界封存 | 世界草稿及来源 | world draft/release | 可引用 WorldRelease(code, 不可变 release id/hash, 能力画像) | 产品设置/媒资/session 进世界 |
| S2 产品定向 | 可引用 WorldRelease | product draft/intent | WorldReference + Brief + ProductSourcePlan + 用户开始授权 | 未授权正式生产；改来源世界 |
| S3 产品执行 | 冻结 Brief/plan | production/build/release/session | 每 run Context Manifest + ProductSourceManifest + 不可变 Release | 超 plan 读可变世界；自动回写世界 |

## 三、写作 SOP（单字段/切片生成合同）

所有字段统一遵守（以"种族与民族"为代表）：

```
1. 保存当前人工输入与补充说明
2. 建立当前作用域与 revision
3. 读取目标字段、相关目录与按需证据（Context Manifest 记录读/遗漏）
4. 选择动作：create / expand / rewrite / polish
5. durable 生成候选（CreativeArtifact，非 Canon）
6. 展示候选与运行证据
7. 作者编辑 / 拒绝 / 采纳
8. stale 检查 + adopt()（校验 field/schema/外键/owner/作用域；目标变化则拒绝 stale 候选）
9. 回读字段、触发索引/事实/下游失效与重建
```

**纪律**：
- 空项目：允许 AI 自主创造，标题只作低权重提示，不把空白生成变标题解释。
- 有关联内容：作为约束和启发，不围绕已有句子重复描述。
- 扩写/润色：展示原版+新版；事实硬验证按风险开启，不以字符 diff 冒充语义。
- 重写：整体替换，清楚标为新版候选。
- 非法 JSON：保留原始输出，schema 解析，至多一次定向修复。
- 超长：尊重长度合同，仍受模型/运行预算与持久化保护。
- **影响只向未来传播**，已确认历史不被后台静默改写。
- **连续性检查（强制）**：写新集/新章节前，**必须先读上一集剧本**，提取：
  1. 时间戳（故事内时间，如"天宝十四载秋·某日黄昏"）
  2. 场景快照（上一集结尾的场景、画面、角色位置）
  3. 角色状态（上一集结束时角色的物理/情感状态）
  4. 时间推进方式（同一天后续 / 第二天 / 数日后）
  5. 避免场景/画面重复（如上一集已出现"阿鸾缝衣"，新集不应再写同一画面，除非明确标注"数日后同一习惯"）
  若时间线不合理或画面重复，必须调整新集开场或标注时间跳跃。

## 四、治理红线（与"密钥零明文""删除前校验"同级）

1. **AI 输出只是候选**，作者确认才进 Canon；不自动采纳、不静默写入。
2. **只出创作语料，不碰 runtime**：活体 AI 小镇模拟、可玩开放世界、产品 build/release/session 运行态不属于本 skill 范围。
3. **冻结世界引用**：上层产品（跑团/AVG/文字冒险/开放世界）只读引用已封存 WorldRelease，运行结果不回写世界引擎。
4. **裁剪留证据（三态）**：`missing`（世界中不存在）/ `omitted`（存在但未选入）/ `partial-selection`（仅选入部分）；**不得混淆三者**，不得把未读当不存在，不得用「固定前缀/前 N 条」当主要检索算法。
5. **stale 不可跳过**：目标或关键来源变化后拒绝 stale 候选，刷新不得自动重发模型请求。
6. **证据分级（v0.2.0 新增）**：每条生成内容必须可标注来源等级，且不得把推断当事实写入 Canon：
   - `OBSERVED`：由**实际检查过的**源文件/原文直接支持（给出文件与偏移/行号）
   - `INFERRED`：由已有事实推导（须写推导链，作者可复核）
   - `UNKNOWN`：无来源支持 → **必须标为 UNKNOWN 或留空**，禁止编造补全
   “主张与证据等量”：一句主张配一条证据；provenance 必须逐块标注（来源 md + revision + contentHash）。
   > 素材来源：`H:\StoryForge-master\docs\ai\anti-hallucination.md`（**辅助来源**，非数据契约基线）。

7. **完整复刻边界**：本 skill 复刻"创作语料 + 数据契约 + SOP"，**不**复刻 StoryForge 的浏览器 IndexedDB 运行时与产品引擎。

## 五、产物形态（与 StoryForge 对齐）

- **框架语料 JSON**：按字段闭集生成，`projects/<项目>/storyforge-framework.json`，每块带 provenance（来源 md + revision + contentHash）。
- **长篇试点**：`projects/长铗传/storyforge-framework.json`（首个闭环验证）。
- **导入**：用户在 StoryForge `/long` 作品库执行导入（浏览器本地，agent 不代操作）。

## 六、执行清单

1. 判定产品 → 读对应子契约（A/B/C）
2. 装配上下文：读项目 md 设定 + knowledge/ 考据，生成 Context Manifest（读了什么/遗漏什么）
3. **连续性检查（写新集/章节时）**：
   - 读取上一集/章剧本（如存在）
   - 提取时间戳、场景快照、角色状态、结尾画面
   - 确认新集时间推进方式（同日后续 / 次日 / 数日后）
   - 检查场景/画面是否重复，避免上一集结尾画面在新集重复出现
   - 若需重复场景，必须标注时间跳跃（如"三日后同一场景"）
4. 按字段闭集生成框架语料（候选态，非 Canon）
5. 交付用户确认/采纳；采纳后更新一致性（事实/伏笔/时间线/角色状态）
6. 对齐基线：确认所依据的源文档版本与上表一致（不一致先停下问，不按记忆推进）
7. 验证：字段完整、provenance 齐全（含证据分级标注）、stale 检查通过、无越类（B/C 只视觉化/后期侧）
8. 交付前跑 `python scripts/check_consistency.py`（应为 0 fail）

## 子契约文件（按需读取）

- `contracts/A-longform.md` — 长篇/短篇：世界观·故事核·角色·大纲·细纲·正文 + 长程一致性
- `contracts/A-characters.md` — 角色卡/人设/记忆/禁区
- `contracts/A-interactive.md` — AVG/文字冒险/跑团：场景树·分支·对白·结局·物品·状态机
- `contracts/B-comic.md` — 漫画：分镜脚本·页·格·视觉主体卡
- `contracts/B-motion-drama.md` — 漫剧前期：系列圣经·逐集·分镜·Image/Video Prompt IR
- `contracts/C-post.md` — 漫剧后期：prompt 包 → 达芬奇〔环境来源〕/生成管线对接
> **横切契约（不属任何单一产品，全部产品适用）**：`contracts/S-data-envelope.md`

- `contracts/C-screenplay.md` — 小说转剧本：改编 Brief·Beat·Scene Card·场次 AST·版本与导出（v0.2.0 新增）
- `contracts/A-world-engine.md` — 世界引擎：worldCode·WorldRelease 字段闭集·能力画像·数据出口·分享包（v0.2.0 新增）
- `contracts/S-data-envelope.md` — 数据契约与 JSON 导入/导出信封（v0.2.0 新增；含**待实测项**）

## 来源与验证

### 基线（v0.2.0 重钉为逐文档版本）

| 文档 | 版本 | 日期 |
| --- | --- | --- |
| `docs/DATA-GOVERNANCE.md` | **v1.8.0** | 2026-09-28 |
| `docs/PROJECT-MASTER-CHARTER.md` | v1.10.0 | 2026-09-29 |
| `docs/DOCUMENT-AUTHORITY.md` | v2.4.0 | 2026-09-29 |
| `docs/CONTEXT-ROUTING.md` | v2.7.0 | 2026-09-29 |
| `docs/products/UPPER-PRODUCTS.md` | v2.6.0 | 2026-09-28 |
| `docs/products/LONGFORM-AND-NODE.md` | v1.6.0 | 2026-09-27 |
| `docs/products/MOTION-DRAMA.md` | v1.2.0 | 2026-09-15 |
| `docs/products/INDEPENDENT-CREATION.md` | 1.2.0 | 2026-08-31 |
| `docs/products/WORLD-ENGINE.md` | 1.4.0 | 2026-09-10 |
| `src/lib/db/schema.ts` | schema v10（comic v5 迁移步） | — |

- **主基线**：`H:\storyforge-main`（唯一数据契约基线）。旧版单一日期 `2026-09-27` **已过期**
  （多份权威文档落在 09-28/09-29，施工契约甚至 2026-10-04）—— 见 `REV-20261005-015`。
- **辅助来源（不混入契约）**：`H:\StoryForge-master\docs\ai\anti-hallucination.md`
  （仅"agent 纪律/证据分级"；该仓库是 Desktop IDE 线，SQLite，与本技能不同源）。
- **上游更新时**：重读上表对应文档段落，不吞整仓；更新后须跑 `scripts/check_consistency.py`。
