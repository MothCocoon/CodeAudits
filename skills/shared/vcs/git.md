# Git

Detect: `git rev-parse --show-toplevel` succeeds in the audited folder.

| Operation | Git |
|---|---|
| List tracked files | `git ls-files <folder>` |
| List files changed by a review | `git diff --name-only <base>...HEAD`, with the pull request's target branch as `<base>`. |
| Before editing a file | Nothing, files are writable. |
| Add a file | Create it. |
| Delete a file | Delete it from disk. |
| No pending changes | `git status --porcelain <folder>` prints nothing. |
| A change | A commit. The change description is the commit message. |

Never push, submit or otherwise publish a change. Record it only when the user asks.
