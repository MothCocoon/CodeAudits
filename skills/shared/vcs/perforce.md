# Perforce

Detect: `p4 where <folder>` maps the audited folder to a depot path.

| Operation | Perforce |
|---|---|
| List tracked files | `p4 have <folder>/...` |
| Start a change | Create a pending changelist with the change description: `p4 --field "Description=<description>" change -o \| p4 change -i`. |
| Before editing a file | `p4 edit -c <changelist> <file>`. Files are read-only until opened, byte-level rewrites included. |
| Add a file | Create it, then `p4 add -c <changelist> <file>`. |
| Delete a file | `p4 delete -c <changelist> <file>`, not a delete on disk. |
| After editing | `p4 revert -a -c <changelist>` reverts files opened but left unchanged. |
| No pending changes | `p4 opened <folder>/...` prints nothing. |
| A change | A pending changelist. Submitting it is up to the user. |
