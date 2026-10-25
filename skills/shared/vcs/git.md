# Git

Detect: `git rev-parse --show-toplevel` succeeds in the audited folder.

| Operation | Git |
|---|---|
| List tracked files | `git ls-files <folder>` |
| Before editing a file | Nothing, files are writable. |
| Add a file | Create it. |
| Delete a file | Delete it from disk. |
| No pending changes | `git status --porcelain <folder>` prints nothing. |
| A change | A commit. The change description is the commit message. |
