# zc-skills

Personal Claude Code skills collection. Each skill lives in `skills/<name>/SKILL.md` and is symlinked to `~/.claude/skills/` for use.

## Skills

| Skill | Description |
|-------|-------------|
| [cc-search](skills/cc-search/) | Search Claude Code conversation history using ripgrep |
| [company-value-analysis](skills/company-value-analysis/) | 公司价值深度分析，覆盖商业模式、护城河、财务指标、管理层、估值 |

## Installation

```bash
# Symlink a skill to make it available in Claude Code
ln -s "$(pwd)/skills/<skill-name>" ~/.claude/skills/<skill-name>
```
