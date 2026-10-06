## Description: <br>
Distills the StoryForge writing framework (data contracts + writing SOP + governance discipline) into an agent-executable skill: routes a task to the right product contract, assembles context from local project materials, and produces **candidate** framework corpora and structured markdown. <br>

This skill produces candidate content only — nothing is written into StoryForge Canon without the author's adoption. <br>

## Publisher: <br>
[taosiuman](https://github.com/taosiuman) <br>

### License/Terms of Use: <br>
MIT — see [LICENSE](LICENSE). Contract content is distilled from [yuanbw2025/storyforge](https://github.com/yuanbw2025/storyforge) (MIT); attribution in [NOTICE.md](NOTICE.md). <br>

## Use Case: <br>
Authors, screenwriters and creators who work inside the StoryForge framework use this skill to turn local project materials (setting docs, research notes) into structured framework corpora and drafts for long-form fiction, short stories, novel-to-screenplay adaptation, world-engine packing, character cards, interactive fiction / TTRPG, comics and motion-drama pre-production. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill reads local project materials (markdown setting docs and research notes) to ground its output. <br>
Mitigation: Reads are limited to the project workspace the user points at; the skill does not write to the application's database and the user performs any import manually. <br>
Risk: Generated content is model output and may contain **fabricated** details that look factual. <br>
Mitigation: Every block must be labelled `OBSERVED` / `INFERRED` / `UNKNOWN`, carries provenance (source file + revision + contentHash) in a sidecar file, and enters Canon only after the author's explicit adoption. <br>
Risk: Real-person likeness, franchise or brand references can create rights issues, and uploading real-person media to external services is a data-protection concern. <br>
Mitigation: Use original names and generic visual descriptions; do **not** upload real-person media to any external service without the documented consent/retention gate; the skill contains no upload step of its own. <br>
Risk: The contracts are distilled from upstream documentation and can drift out of date. <br>
Mitigation: The baseline is recorded per document (with versions), `scripts/check_consistency.py` asserts internal consistency, and known gaps are marked `待实测` (to-be-measured) instead of being guessed. <br>

## Reference(s): <br>
- [Repository](https://github.com/taosiuman/storyforge-writing) <br>
- [Entry point](SKILL.md) · [Contracts](contracts) <br>
- [Consistency checker](scripts/check_consistency.py) · [Known limits](COMPAT.md) <br>

## Skill Output: <br>
**Output Type(s):** [text, markdown, json, guidance] <br>
**Output Format:** [Structured markdown contracts guidance plus candidate JSON framework corpora with a provenance sidecar] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Candidates only; the skill never writes to the application runtime, and the JSON it produces is deliberately NOT a backup package (no `version` field).] <br>

## Skill Version(s): <br>
0.2.1 <br>

## Ethical Considerations: <br>
Users should review generated candidates before adopting them, respect third-party rights when referencing real people, franchises or brands, and apply their own data-protection and compliance requirements before uploading any media to external services. <br>
