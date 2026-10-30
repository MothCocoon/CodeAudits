---
name: run-performance-audits
description: Run the performance code audit skills of the CodeAudits repo on an Unreal plugin or project in the recommended order, one skill per change. Use when asked to run performance audits, a performance code audit pass, or to audit a pull request or a changelist under review.
---

# Run performance audits

Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.
Keep each file's line endings. Edit files in place, so every change shows up as a diff.

Run it after `run-cosmetic-audits`, so its diffs stay small and land in the final layout.

Run the skills below one at a time, in this order. Each step:

1. Check that the audited folder has no pending changes, so the step's change holds only its own edits.
2. Load the skill and follow it: report, approval, fixes.
3. When the step can break compilation, stop for a build before the user records the change.
4. Hand over the change description from the skill and wait until the user records the change or skips the step.

A step with no findings is reported in one line and the run moves on.
The user may skip steps or stop the run, the order of the remaining steps stays.

| # | Skill | Why here | Build before recording |
|---|---|---|---|
| 1 | `fix-tobjectptr-usage` | Type fixes in declarations and their call sites. | yes |
| 2 | `resolve-weakptrs-once` | Functional change inside function bodies. | |

## Review mode

For a pull request or a changelist under review. Run it before reviewing the code, so the review reads audited code.

- Findings are limited to the files changed by the review, listed as the version control notes describe. Reading and searching the rest of the project stays allowed, e.g. for callers outside the review.
- All steps go to one change, with one build at the end when any build step changed something.
- The change description joins the subjects of the skills that changed something:

```
code audit: review fixes

* replaced raw object pointers in UPROPERTY members with TObjectPtr
* weak pointer resolves
```
