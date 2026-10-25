# Lore

Detect: a `.lore/` folder at the root of the working tree.

Files are writable. Lore doesn't watch the disk: an edited file shows up in `lore status` only after it's marked dirty or found by a scan.

| Operation | Lore |
|---|---|
| List tracked files | No listing command. Walk the folder on disk and drop the files `lore status --scan <folder>` reports as added (`A`). |
| List files changed by a review | `lore revision diff <branch point>` on the reviewed branch. The branch point is the last revision listed by `lore revision history --only-branch`. |
| Before editing a file | Nothing. |
| After editing a file | `lore dirty <file>`, or one `lore status --scan <folder>` after the whole pass. |
| Add a file | Create it, then `lore dirty <file>`. |
| Delete a file | Delete it from disk, then `lore dirty <file>`. |
| Move a file | `lore stage move <from> <to>`, so the file keeps its history. |
| No pending changes | `lore status --scan <folder>` reports no dirty or staged files. |
| A change | A commit, which creates a new revision. Recorded with `lore stage <folder>` followed by `lore commit "<description>"`. |

Never push, submit or otherwise publish a change. Record it only when the user asks.
