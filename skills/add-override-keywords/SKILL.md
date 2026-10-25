---
name: add-override-keywords
description: Find method declarations in an Unreal plugin's or project's Source that override a base virtual but miss `virtual`, `override` or both, including silent overrides with neither keyword. Use when asked to check missing virtual/override keywords, implicit overrides, or override declarations.
---

# Missing virtual and override keywords

Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.
Keep each file's line endings. Edit files in place, so every change shows up as a diff.

Style: every override is declared `virtual ... override`.

## Discovery

Run the script, it parses the audited headers and walks base classes into the engine source:

```bash
python -I "<skill folder>/scripts/override_audit.py" "<source>" "<engine>/Engine"
```

`<source>` is the audited `Source` folder.
`<engine>` is the root of the engine the project builds with. `EngineAssociation` in the
`.uproject` names it: a version for a launcher install (`Epic Games/UE_<version>`), a GUID for a
source build registered under `HKEY_CURRENT_USER\Software\Epic Games\Unreal Engine\Builds`.
Ask the user when the engine can't be found.
The first run indexes engine headers into the temp folder, later runs reuse the index.

Output categories:
- **missing virtual and override**: same name and signature as a base virtual, no keyword at all.
  It overrides silently, and a signature change in the base leaves it as a separate function.
- **missing override**: `virtual` without `override` while a base declares the same virtual.
- **missing virtual**: `override` without `virtual`. Compiles, breaks the style only.
- **signature differs from base virtual**: same name as a base virtual, different parameters.
  Either an intended overload or an override that stopped matching the base. Read both
  declarations and decide.

Matching rules of the script:
- Signatures compare parameter types and the `const` qualifier. Parameter names, default
  values and top-level `const` on by-value parameters are ignored.
- A `UFUNCTION(BlueprintNativeEvent)` in the base counts as a virtual `<Name>_Implementation`.
- A destructor overrides when any base declares a virtual destructor. A non-virtual base
  destructor (`TSharedFromThis`) doesn't count.
- Operators are skipped.

Verify every hit by reading the base declaration before editing. The parser doesn't see
preprocessor branches, so a base virtual under a disabled macro (e.g. `ENABLE_JUMP_TO_INNER_OBJECT`)
can produce a false hit.

## Fix

- Add the missing keyword in the header declaration. The cpp definition doesn't change.
- `virtual` goes first, after any `*_API` macro: `MYMODULE_API virtual void Foo() override;`.
- Don't move the declaration and don't touch its access level. Access levels are a separate audit.

## Report before editing

List hits as a table: category, file:line, class, method, base class. Group by category so the
user can approve a subset.

## Change description

```
code audit: added missing virtual and override keywords
```
