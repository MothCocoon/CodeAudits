---
name: fix-tobjectptr-usage
description: Fix TObjectPtr usage in an Unreal plugin's or project's Source - replace raw object pointers in UPROPERTY members with TObjectPtr, so the code compiles in targets setting NativePointerMemberBehaviorOverride = PointerMemberBehavior.Disallow, and remove redundant nullptr initializers of TObjectPtr. Use when asked to check raw UObject pointer members, native pointer UHT errors, TObjectPtr conversion, or nullptr assigned to TObjectPtr.
---

# TObjectPtr usage

Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.
Scan the tracked files under `Source` filtered to `.h`/`.cpp`.
Keep each file's line endings. Edit files in place, so every change shows up as a diff.

## 1. Raw object pointers in UPROPERTY members

A target setting `NativePointerMemberBehaviorOverride = PointerMemberBehavior.Disallow` in its `.Target.cs` makes UHT fail on every raw object pointer in a UPROPERTY member.
Code relying on raw pointers compiles in projects allowing them and breaks in the others.

UHT checks:
- UPROPERTY members of UCLASS and USTRUCT types pointing to any UObject type, `UClass*` and `const` pointers included.
- Container elements, map keys and values: `TArray<UFoo*>`, `TSet<UFoo*>`, `TMap<FName, UFoo*>`.

UHT doesn't check function parameters and return values, members without UPROPERTY, local variables and `TNonNullPtr`. Leave them.

Replace:
- `UFoo* Name` with `TObjectPtr<UFoo> Name`
- `const UFoo* Name` with `TObjectPtr<const UFoo> Name`
- `TArray<UFoo*>` with `TArray<TObjectPtr<UFoo>>`, same for other containers

Keep the UPROPERTY specifiers and the default value. A `= nullptr` initializer goes away with the conversion.

Grep the whole host project (the folder with the `.uproject`) for each converted member, not only the plugin.
`TObjectPtr` converts to a raw pointer implicitly, most call sites compile unchanged. Fix the ones that don't at the call site:
- `auto*` deduced from the member: write the raw type.
- `UFoo*&` or `UFoo**` taking the member: change the signature to `TObjectPtr<UFoo>&` in the audited code, use `static_cast<UFoo*&>(MutableView(Member))` outside it.
- Raw pointer containers taken by reference: change the signature to the `TObjectPtr` container in the audited code. Outside it, use `MutableView(Member)` for a mutable reference and `ToRawPtrTArrayUnsafe(Member)` for a const one.
- Template deduction or a conditional operator expecting `T*`: add `.Get()`.

UHT reports the remaining raw pointers only in a target setting `Disallow`. Elsewhere this scan is the only check.

## 2. Redundant nullptr on TObjectPtr

`TObjectPtr` default-constructs to null.
Declarations of `TObjectPtr` assigning `nullptr` lose the initializer, members and local variables alike: `= nullptr`, `{nullptr}`, `{ nullptr }`.

Keep:
- Default arguments of `TObjectPtr` parameters. Removing them changes the function signature.
- Assignments in statements, which reset a pointer set before.

## Report before editing

List the findings as a table per section, then wait for approval.

| File:line | Member or variable | Before | After | Call sites changed |
|---|---|---|---|---|
| Foo.h:42 | `UFoo::Target` | `AActor*` | `TObjectPtr<AActor>` | Bar.cpp:120 |

## Change description

Each section goes to a separate change.

```
code audit: replaced raw object pointers in UPROPERTY members with TObjectPtr

The code now compiles in projects that disallow native pointer members with NativePointerMemberBehaviorOverride = PointerMemberBehavior.Disallow.
```

```
code audit: remove redundant nullptr assigned on TObjectPtr
```
