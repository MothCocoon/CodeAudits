---
name: run-all-audits
description: Run every code audit skill of the CodeAudits repo on an Unreal plugin or project in the recommended order, one skill per change. Use when asked to run all audits, a full code audit pass, the audits in order, or to audit a pull request or a changelist under review.
---

# Run all audits

Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.
Keep each file's line endings. Edit files in place, so every change shows up as a diff.

Run the skills below one at a time, in this order. Each step:

1. Check that the audited folder has no pending changes, so the step's change holds only its own edits.
2. Load the skill and follow it: report, approval, fixes.
3. When the step can break compilation, stop for a build before the user records the change.
4. Hand over the change description from the skill and wait until the user records the change or skips the step.

A step with no findings is reported in one line and the run moves on.
The user may skip steps or stop the run, the order of the remaining steps stays.

### Cosmetic

| # | Skill | Why here | Build before recording |
|---|---|---|---|
| 1 | `fix-source-headers` | Touches the top of every file. Without BOM, later parsers and diffs work cleanly. | |
| 2 | `remove-redundant-directives` | Fewer `#if` blocks and macros to carry through later steps. | |
| 3 | `clean-up-constructors` | Removes code: constructors, stub cpp files and definitions that would be moved later. | yes |
| 4 | `add-override-keywords` | The compiler confirms the set of overrides. | |
| 5 | `align-override-access` | Works on the confirmed set of overrides. Inserts specifiers without moving declarations. | yes |
| 6 | `order-definitions-by-header` | Pure moves, a large diff on the first run. Done before functional changes, so their diffs stay small and land in the final layout. | |

### Functional

| # | Skill | Why here | Build before recording |
|---|---|---|---|
| 7 | `fix-tobjectptr-usage` | Type fixes in declarations and their call sites. | yes |
| 8 | `resolve-weakptrs-once` | Functional change inside function bodies. | |
| 9 | `replace-tsubclassof` | Functional change: getter API and its callers. | yes |

## Review mode

For a pull request or a changelist under review. Run it before reviewing the code, so the review reads audited code.

- Findings are limited to the files changed by the review, listed as the version control notes describe. Reading and searching the rest of the project stays allowed, e.g. for callers outside the review.
- `order-definitions-by-header` only places definitions the review added. The rest of each file keeps its order.
- All steps go to one change, with one build at the end when any build step changed something.
- The change description joins the subjects of the skills that changed something:

```
code audit: review fixes

* added missing virtual and override keywords
* public overrides narrowed to protected, matching base virtuals
```
