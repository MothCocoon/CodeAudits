---
name: align-override-access
description: Check that access levels (public/protected/private) of virtual overrides in an Unreal plugin's or project's Source match the base virtual declaration, then narrow or widen them, keeping overrides that outside code calls through the derived type. Use when asked to audit protection levels, access specifiers or public/protected/private of overrides.
---

# Override access levels

Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.
Keep each file's line endings. Edit files in place, so every change shows up as a diff.

An override declares the same access level as the nearest base declaration of that virtual.

## Discovery

Run the script, it parses the audited headers and walks base classes into the engine source:

```bash
python -I "<skill folder>/scripts/access_audit.py" "<source>" "<engine>/Engine"
```

`<source>` is the audited `Source` folder.
`<engine>` is the root of the engine the project builds with. `EngineAssociation` in the
`.uproject` names it: a version for a launcher install (`Epic Games/UE_<version>`), a GUID for a
source build registered under `HKEY_CURRENT_USER\Software\Epic Games\Unreal Engine\Builds`.
Ask the user when the engine can't be found.
The first run indexes engine headers into the temp folder, later runs reuse the index.
Header paths after `<engine>/Engine` limit the output to classes declared in them, e.g. the headers of a review.
Base classes are still resolved across the whole `<source>`.

Each row gives the override, its access, the base access and the base declaration with file:line.
Overrides whose base wasn't found go to stderr, usually a base under a disabled macro.

The script matches by name only. When the base access lists two values, the base has overloads
with different access (e.g. `UEdGraph::NotifyGraphChanged`): compare signatures by hand.
A `UFUNCTION(BlueprintNativeEvent)` in the base counts as a virtual `<Name>_Implementation`.
Destructors aren't compared, see Exceptions.

## Direction

- **Widening** (override less accessible than the base): raise it to the base level. Nothing
  outside can break.
- **Narrowing** (override more accessible than the base): lower it to the base level only when
  nothing outside the class hierarchy reaches it through the derived type. Grep the whole project,
  including the host project when auditing a plugin, for `->Method(`, `.Method(` and `&Class::Method` (delegate binds
  like `AddUObject`, `CreateSP`, `BindRaw`). Calls through a base pointer or reference aren't
  affected.
- `_Implementation` overrides are called by the generated thunk through the declaring base class.
  Narrowing them is safe.

## Exceptions

- **Called through the derived type by a base class template.** `TCommands<T>::Register` calls
  `RegisterCommands()` on `T`, so the override stays public although the base is protected.
  Such overrides carry the comment `// Public despite protected base, <reason>`. Keep every
  override marked this way, and mark new cases the same way.
- **Private overrides of engine virtuals called only by the engine** (`GetScriptStructImpl`,
  `EvaluateSwept` in MovieScene templates, `SGraphPaletteItem::GetItemTooltip`) stay private.
  The engine itself declares them this way. Check that every audited override of the same base
  virtual uses the same access.
- **Private override of a protected virtual declared in the audited code**: raise it to protected.
  Derived classes call these from their own code, and the base in the audited code is the reference.
- **Destructors** stay public. `SNew` and `MakeShareable` delete through the concrete type, even
  when the base (`SCompoundWidget`, `SPanel`) declares its destructor protected.

## Editing

- Insert access specifiers around the declaration, don't move it. Declaration order stays in
  sync with the definition order in cpp.
- A specifier inside `#if WITH_EDITOR` or `#if WITH_EDITORONLY_DATA` also changes the access of
  code after `#endif` in that configuration. Restore it with an explicit specifier after `#endif`
  when that code needs it.

## Report before editing

List mismatches as a table grouped by action: narrow, widen, keep (with the reason). Narrowing
rows name the callers checked.

## Change description

Narrowing and widening go to separate changes.

```
code audit: public overrides narrowed to protected, matching base virtuals
```

```
code audit: protected overrides widened to public, matching base virtuals
```
