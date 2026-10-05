# A 类子契约 · 长篇 / 短篇（storyforge-writing）

> 归属：A 开发创作。字段闭集来自 storyforge schema v10 + LONGFORM-AND-NODE v1.6.0。
> 生成时遵守总入口的"数据契约 + 写作 SOP + 治理红线"，本文件只补长篇专属规则。

## 1. 完整长篇覆盖范围（9 块，全部要能生成）

1. 项目：名称、创作目标、题材、规模、作者约束
2. 世界观：起源/自然/人文/种族/势力/地点/历史/规则/多世界关系
3. 故事：主题、核心冲突、叙事策略、主线和支线
4. 角色：角色卡、关系、物品、状态、知识和生命周期
5. 大纲：全书 / 卷 / 章
6. 细纲：场景、目标、节拍、视角、承接、伏笔
7. 正文：生成、续写、选择编辑、扩写、重写、润色、审校、采纳、版本
8. 长程工程：事实、事件、关系、时间线、主支线进度、伏笔、原文、摘要、索引、影响分析
9. durable 运行：候选、刷新恢复、stale、拒绝/采纳、post-state、下游生效

## 2. 字段 → 语料映射（长铗传为例）

| StoryForge 表 | 长铗传来源 md | 生成内容 |
|---|---|---|
| works | project-baseline.md | code=长铗传、status、创作目标、规模（**90 集**，原 70 集扩展）×1 分钟、文风 |
| worldviews | p1-world-characters.md + knowledge/*.md | 唐代长安/天宝/安史之乱世界观、势力（保皇/太子党/杨国忠/叛军）、地点 |
| storyCores | p2-story-structure.md | 主题（理想主义幻灭）、核心冲突、主支线（复仇线/灭门真相线/游侠信念线） |
| characters | p1-world-characters.md | 裴行/游侠/裴守义/阿鸾/王怀远/卢征… 各卡（roleWeight/moralAxis） |
| characterRelations | p1-world-characters.md | 裴行↔阿鸾(夫妻)、裴行↔游侠(救命)、裴行↔卢征(仇) |
| outlineNodes | p3-scene-breakdown.md | 全书→幕→卷→章 树（第一幕长安落日 3-20…） |
| chapters | scripts/**episode-01..04** | 逐章状态（v0.1 曾写 act1-4，实际路径已变） |
| detailedOutlines | p3-scene-breakdown.md | 场景/目标/节拍/视角/承接/伏笔 |
| foreshadows | 各幕剧本 | 伏笔卡（阿鸾存活/灭门幕后/游侠身份） |
| storyTimelineEvents | 剧本时间线 | 天宝十四载末→至德二载 事件序 |
| stateCards | 角色状态 | 裴行(巡吏→游侠→远走敦煌) 等 |
| codexEntries | knowledge/*.md | 考据条目（官制/刑狱/游侠/市坊） |
| temporalFacts / knowledgeLedger | knowledge/*.md | 带来源章节的结构化事实 |
| narrativeSummaryNodes | 各幕 | 章/卷/全书摘要（可重建） |

## 3. 长篇写作 SOP 细化

- **创作顺序自由**：作者可先写世界/角色/故事；生成时按当前已确认内容联动，留白允许自主创造。
- **单任务单 Skill 单写入目标**：以作者原话确定 Skill 和写入字段；规划解读不得覆盖人物/时间/数量/禁止事项。
- **每阶段至多推进一份正文候选**：后续任务留会谈，终验后恢复为待确认计划。
- **跨章节前**：检查上一章章后运行状态。
- **全书进度**：来自实际设定/人物/卷章/细纲/正文，不能由"某次运行完成"推算。
- **完稿检查**：章纲覆盖、空正文、结构异常、待处理运行；作者核对目标/结局后确认完成并备份。

## 4. 百万字 / 长程一致性

- 原文永久可回查；事实/实体/关系/事件/主支线结构化
- 章节/卷/全局摘要可重建；Context Gateway 先目录后详情
- 伏笔、锁定约束高优先级但仍留原文来源
- 规模/召回/时间/预算/真实文学一致性分开验收

## 5. 显式派生世界（可选）

长篇保持独立 owner；作者可"基于当前作品创建世界草稿"或"封存为世界版本"。
派生保存来源作品/revision/选取范围/contentHash；原长篇后续修改不自动改写旧世界。

## 6. 节点模式合同（同源，不复制）

节点 = 同一长篇能力的 DAG 表达。可拆解/替换/连接中间产物，但**不复制第二套生成/记忆/数据体系**。
官方分步骤流程可**导出为官方节点模板**；节点调用领域 action/Skill，**不复制 UI 组件内部逻辑**；节点产物走同一候选/采纳链。

**每个节点至少声明**（字段闭集，源：LONGFORM-AND-NODE §7）：

```
type / version      节点类型与版本
owner               责任 owner
输入/输出类型       I/O 的显式类型
required sources    必读来源（对应 CONTEXT_SOURCES key）
allowed writes      允许写入的目标（对应 FIELD_REGISTRY）
作用域              scope（项目/世界/作品/实例）
依赖                dependsOn
资源预算            budget
运行证据            run evidence（可回查）
```

**图执行前必须检查**：① 循环 ② 缺输入 ③ 类型不匹配 ④ 作用域越界 ⑤ **未登记权限**。
运行图与 checkpoint 可独立保存。

**跨模式验收（5 条，缺一不可）**：

1. 分步骤创建的数据可被节点读取；
2. 节点生成并采纳的数据在分步骤 UI 显示；
3. 版本、stale、导入导出与删除一致；
4. 同一动作**无第二套** Prompt、AI 请求、DB 表清单或字段映射；
5. 非法连线在**调用模型之前**被阻断。

> 验收证据（引用，不代跑）：`R-LONGFORM-*` 系列 + `tests/e2e/longform-integration.spec.ts`、
> `longform-agent-experience.spec.ts`。注意：模拟模型回归**只证明工程流程**，
> 不证明真实模型的文学质量、整书无人值守生产或在线社区可用性。

## 7. 短篇（子集）

短篇独立创作（INDEPENDENT-CREATION）：故事核 / 角色 / 单线大纲 / 正文；**可显式派生世界草稿或封存世界版本**。
（v0.1.0 曾写「不提供『封装为世界』完整路径」，与源文档矛盾 —— 「不提供封装为世界」指的是**剧本 / 漫画**等改造类产品，见 `INDEPENDENT-CREATION.md:11`。）
