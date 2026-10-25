---
name: replace-tsubclassof
description: Audit TSubclassOf usage in an Unreal plugin's or project's Source and switch serialized class references to TSoftClassPtr where it removes a hard load without regression. Use when asked to check TSubclassOf, hard class references, or replace them with soft refs.
---

# TSubclassOf to TSoftClassPtr

Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.
Keep each file's line endings. Edit files in place, so every change shows up as a diff.

## Data compatibility

`FClassProperty` inherits `FObjectPropertyBase::GetID()`, so a `TSubclassOf` UPROPERTY is saved with the tag `ObjectProperty`.
`FSoftObjectProperty::ConvertFromType` (shared by `FSoftClassProperty`) converts that tag into the soft path on load.
Existing assets, blueprint CDOs and config values load without a resave.

## Switch to soft

A UPROPERTY member in a runtime module, outside `WITH_EDITORONLY_DATA`, which is read only by editor code or only for display.
The hard ref there makes the cooked asset load the referenced class (a blueprint package) for nothing.

- Change the getter signature to return `const TSoftClassPtr<T>&`. Don't keep a `UClass*` getter next to it.
- Editor callers that need the class call `.LoadSynchronous()`.
- Display-only callers use `IsNull()` and `GetAssetName()` without loading.
- Grep the whole host project (the folder with the `.uproject`) for the getter and member names, not only the plugin.

## Keep as TSubclassOf

- **Runtime-used classes** (`NewObject`, `FindComponentByClass`, spawning). Soft would mean a sync load during gameplay.
- **`WITH_EDITORONLY_DATA` members**. They aren't cooked.
- **Non-UPROPERTY members**. Nothing is serialized.
- **Editor module members**, including factories.
- **Function parameters, static maps, engine overrides** (`SupportsType`), and `DeterminesOutputType` BlueprintPure params. These receive an already loaded class.

## Report before editing

List each `TSubclassOf` UPROPERTY member as a table: member, readers (runtime or editor), gain, risk (public API change, null without load).
Leave function signatures, which aren't data, out of the table and summarize them in one line.

## Change description

```
code audit: replaced usages of TSubclassOf with TSoftClassPtr

Serialized class references are now TSoftClassPtr, so cooked assets no longer load the referenced classes. As a general rule, runtime properties shouldn't use TSubclassOf, which is a hard reference.
```
