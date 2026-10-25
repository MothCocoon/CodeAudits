---
name: remove-redundant-directives
description: Remove pointless preprocessor guards and macros in an Unreal plugin's or project's Source - WITH_EDITOR guards in editor-only modules and BEGIN/END_SLATE_FUNCTION_BUILD_OPTIMIZATION blocks. Use when asked to clean up redundant WITH_EDITOR guards in editor modules or Slate optimization macros.
---

# Redundant preprocessor guards and macros

Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.
Scan the tracked files under `Source` filtered to `.h`/`.cpp`.
Keep each file's line endings. Edit files in place, so every change shows up as a diff.

## No `WITH_EDITOR` guards in editor modules

Modules of type `Editor` in the `.uplugin` or `.uproject` only build with the editor, so
`#if WITH_EDITOR` is always true there.
Remove the `#if WITH_EDITOR` and its `#endif` in headers and cpps of such modules, keeping the
guarded code. An `#else` branch goes away with them.
Guards in `Runtime` and `DeveloperTool` modules stay.

## Slate build optimization blocks

`BEGIN_SLATE_FUNCTION_BUILD_OPTIMIZATION` expands to `UE_DISABLE_OPTIMIZATION_SHIP`, so it turns
optimization off despite the name. It exists to keep compile times sane for huge declarative
widget trees.
Typical widget builders (a `Construct` with a dozen or so `SNew`) compile fine without it.
Remove `BEGIN/END_SLATE_FUNCTION_BUILD_OPTIMIZATION` pairs and the `#include "SlateOptMacros.h"`
that only served them.

## Change description

Each kind of fix goes to its own change.

```
code audit: removed pointless WITH_EDITOR guards from the editor module
```

```
code audit: removed redundant Slate optimization macros

Optimizations were disabled in a few Slate classes for no reason. This might have been useful with older MSVC versions.
```
