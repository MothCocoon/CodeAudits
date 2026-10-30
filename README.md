# CodeAudits

Agent skills auditing Unreal Engine C++ code, written in the [Agent Skills](https://agentskills.io) format (`SKILL.md` with `name` and `description` frontmatter).
Each skill looks for one kind of issue, lists the findings for approval, then edits files in place, so every change shows up as a reviewable diff.

## Skills

### Cosmetic

| Skill | What it does |
|---|---|
| `fix-source-headers` | Strips UTF-8 BOM, normalizes the copyright line and the spacing around `#pragma once` and the first includes. |
| `remove-redundant-directives` | Removes `WITH_EDITOR` guards in editor modules and Slate build optimization macros. |
| `clean-up-constructors` | Moves default member values to declarations, removes redundant constructors and empty stub `.cpp` files. |
| `add-override-keywords` | Adds missing `virtual` and `override`, including overrides declared with neither. |
| `align-override-access` | Aligns access levels of overrides with the base virtual, keeping overrides that outside code calls through the derived type. |
| `order-definitions-by-header` | Orders function definitions in `.cpp` like declarations in the header. |

### Performance

| Skill | What it does |
|---|---|
| `fix-tobjectptr-usage` | Replaces raw object pointers in UPROPERTY members with `TObjectPtr` and removes redundant `nullptr` initializers of `TObjectPtr`. |
| `resolve-weakptrs-once` | Resolves each weak pointer once into a local and adds missing null checks. |

Every skill ends with a change description. One skill makes one change: a git commit, a Perforce changelist or a Lore commit.
Version control specifics live in `skills/shared/vcs/`, one file per system.
To run each group in the order above, use `run-cosmetic-audits`, then `run-performance-audits`. Their review mode audits only the files of a pull request or changelist and puts each group's fixes into one change.

## Install

Clone the repo and link each folder of `skills/`, `shared` included, into the skills folder of your agent.
Link, don't copy: skills read the version control notes and the scripts import the header parser from `shared`, which has to sit next to the skill folders.

Claude Code reads skills from `~/.claude/skills` (all projects) or `<project>/.claude/skills` (one project).
For other agents supporting Agent Skills, use the folder named in their docs.

Windows, a junction needs no admin rights:

```powershell
Get-ChildItem <repo>\skills -Directory | ForEach-Object { New-Item -ItemType Junction -Path "<agent skills folder>\$($_.Name)" -Target $_.FullName }
```

macOS and Linux:

```bash
for s in <repo>/skills/*/; do ln -s "${s%/}" "<agent skills folder>/"; done
```

A variant for an agent that doesn't read `SKILL.md` belongs in a thin adapter pointing at these skills, not in a copy of them.

## Requirements

- Python 3 for `add-override-keywords` and `align-override-access`. The engine ships one in `Engine/Binaries/ThirdParty/Python3/Win64/python.exe`.
- Engine headers of the engine the project builds with, a launcher install is enough. The scripts walk base classes into them. The first run indexes engine headers into the temp folder, later runs reuse the index.
