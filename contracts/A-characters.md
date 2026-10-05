# A 类子契约 · 角色卡 / 人设（storyforge-writing）

> 归属：A 开发创作。对应 StoryForge `characters` / `characterRelations` / `characterDrivenPlans` / `knowledgeLedger`。
> 角色卡是 IP 设定资产；角色聊天（character chat）上层产品**只读引用冻结世界版本**。

## 1. 角色卡字段闭集

| 字段 | 含义 | 生成来源 |
|---|---|---|
| name | 角色名 | 项目角色图谱 |
| roleWeight | 主角/核心/配角权重 | p1-world-characters |
| moralAxis | 道德轴（正/邪/灰） | 人设 |
| orderAxis | 叙事顺序轴 | 出场序 |
| statusEvidenceChapterId | 状态证据章节 | 状态卡回指 |
| 能力/动机 | 人设核心 | 角色卡正文 |
| 登场章节 | 首次登场 | 细纲 |
| 状态: known/mistaken/candidate | 已登场/笔误待修/作者正典 | 前端状态机 |

## 2. 角色关系（characterRelations）

`fromCharacterId → toCharacterId` + 关系语义（夫妻/救命/仇敌/同僚/主从）。
生成时成对输出，带方向，避免双向重复。

## 3. 角色聊天（character chat）生成边界

- 生成**角色卡 + 说话风格 + 记忆约束 + 禁区（禁止事项）**，供聊天产品引用
- 该产品**只读引用**已封存 WorldRelease；**私域演化不回写**世界引擎
- 本 skill 出的是"人设语料"，不是活体聊天 runtime

## 4. 角色补全纪律（来自 LONGFORM 9.3）

- 角色补全必须**冻结明确角色和字段**；指定不存在的章节不得偷偷回退到其他章节
- 补全的**禁止字段**不进入冻结写入范围
- 世界设定里"用于说明规则的角色提及"**不等价于**创建/修改角色的授权
- 角色请求引用已有世界**不等价于**补齐/修改世界
- 过滤模型擅加任务时，同时清理其依赖与误导性计划摘要

## 5. 生命周期扩展（ADOPTION_EXTENSIONS）

- `character-merge-lifecycle`：角色合并
- `knowledge-ledger`：角色知识台账（characterId + knowledgeKey + factId + sourceChapterId）
- 角色状态卡（stateCards）随章节推进：`category / entityName / lastChapterId`
