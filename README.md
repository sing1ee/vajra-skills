# zc-skills

Personal Claude Code skills collection. Each skill lives in `skills/<name>/SKILL.md` and is symlinked to `~/.claude/skills/` for use.

## Skills

| Skill | Description |
|-------|-------------|
| [cc-search](skills/cc-search/) | Search Claude Code conversation history using ripgrep |

## Installation

```bash
# Symlink a skill to make it available in Claude Code
ln -s "$(pwd)/skills/<skill-name>" ~/.claude/skills/<skill-name>
```
