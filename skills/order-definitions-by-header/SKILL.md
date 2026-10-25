---
name: order-definitions-by-header
description: Reorder function definitions in .cpp files to follow the declaration order of their own header. Use when asked to check or fix method order in cpp vs header.
---

# Definition order follows the header

Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.
Scan the tracked files under `Source` filtered to `.cpp`.
Keep each file's line endings. Edit files in place, so every change shows up as a diff.

Function definitions in a `.cpp` follow the declaration order of its own header, so a diff on a
header maps to the same place in the cpp.

- Order key: position of the declaration in the header, across access sections and nested types.
  Members of several classes declared in one header follow the header's class order.
- Left in place: includes, `LOCTEXT_NAMESPACE` define and undef, log categories, static member
  and file-scope variable definitions, anonymous namespaces, file-local helpers used by the
  definitions below them. They stay above the first member definition.
- Definitions whose declaration lives in another header, and declarations whose definition lives
  in another cpp (a class split across several cpp files), are out of scope.
- A definition keeps the preprocessor guard of its declaration (`#if WITH_EDITOR`,
  `#if WITH_EDITORONLY_DATA`, ...). Neighbors under the same guard share one `#if` block.
  A guard tag like `// WITH_EDITOR` after `#endif` stays if the file used it.
- Comments directly above a definition move with it.
  Group markers mirror the header when the cpp already uses them (`// UObject` ... `// --`).
- Bodies are never touched. One blank line between definitions.
- A move is two in-place edits: cut the block with one, paste it with another.

Verify after reordering:
- Content: sorted non-blank lines of the file before and after differ only in guard and group
  marker lines.
- Order: list definitions (`Class::Name(` at column 0) and compare with the header declaration
  order.

`BEGIN_SLATE_FUNCTION_BUILD_OPTIMIZATION` is not a guard to preserve while reordering, see the
`remove-redundant-directives` skill.

## Change description

```
code audit: order methods in cpp the same as in header

Makes work easier for everyone who relies on a consistent class layout.
```
