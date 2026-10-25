---
name: clean-up-constructors
description: Three-step cleanup in an Unreal plugin's or project's Source - move default member values from constructors to declarations, remove constructors left redundant (respecting the FObjectInitializer parent-chain rule and USTRUCT default constructor needs), then delete .cpp files left as empty stubs. Use when asked to move defaults to declarations, remove redundant member initializers, empty/trivial constructors, or dead/empty implementation files.
---

# Constructor cleanup

Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.
Scan the tracked files under `Source` filtered to `.h`/`.cpp`.
Keep each file's line endings. Edit files in place, so every change shows up as a diff.

The steps run in order: moving defaults empties constructors, removing constructors empties cpp
files.

## 1. Default member values at declaration

A member's default value assigned in a constructor (initializer list entry or plain assignment
in the body) moves to the member's declaration, written as `Type Name = Value;`.
Remove the constructor entry afterwards.
If the declaration already has the same value, only remove the constructor entry.
If the value is plain default construction of a class type (`FGuid()`, `FString()`, `Widget()`),
only remove the constructor entry, the declaration gets no initializer.
The same applies to `nullptr` for `TObjectPtr` members, which default to null.
Existing `TObjectPtr<...> Name = nullptr;` declarations lose the initializer too, members and
local variables alike.

Move only when all of these hold, otherwise leave the code and report the case:
- The member is declared in the class itself. Inherited members set in a subclass constructor
  stay in the constructor.
- The value doesn't depend on constructor parameters, `this`, `ObjectInitializer`, other members
  or runtime calls (`CreateDefaultSubobject`, `GetDefault`, `StaticClass`, ...).
- The value compiles in the header: literals, enum values, `TEXT`/`FName`/`FString` literals,
  math type constructors, constants visible from the header. `LOCTEXT` doesn't qualify since
  `LOCTEXT_NAMESPACE` lives in the cpp.
- The assignment is unconditional: no `if`, loop or lambda around it. An `#if` around it is fine
  only when the declaration sits under a guard implying it (`WITH_EDITOR` assignment with a
  `WITH_EDITORONLY_DATA` member).
- No other constructor of the class would change behavior. Other constructors that set the member
  explicitly keep doing so. If one leaves it unset, skip.
- The member isn't a bitfield (`uint8 bFoo : 1`).
- It's a direct assignment or initializer entry, not `Add`/`Append` or other container calls.

Constructors left empty by the move are handled by section 2.
When an initializer list drops to `: Super(...)` only, keep it well-formed (colon, commas).

## 2. Redundant constructors

A constructor doing nothing the compiler/UHT-generated one wouldn't do gets removed: both the
header declaration and the cpp definition (or the inline body in the header).

Removable:
- Empty body, no initializer list: `UFoo::UFoo() {}`.
- Empty body, pure forward only: `: Super(ObjectInitializer)`, `: Super()`.
- Initializer entries that only restate the default (`: Ptr(nullptr)` on `TObjectPtr`/raw pointer
  members with a null default, `: Widget()`) count as empty.

Not removable:
- Any non-empty body (`CreateDefaultSubobject`, inherited defaults like `Category = ...`,
  `static_assert`, container appends, ...).
- Any initializer entry setting a member or base to a real value.

Special cases:
- **Struct default constructor with a sibling user constructor.** The sibling suppresses the
  implicit default constructor, and USTRUCT reflection needs one. Replace the empty body with
  `FFoo() = default;` in the header and drop any cpp definition.
- **`(const FObjectInitializer&)` signature.** Without a user constructor UHT generates
  `UFoo(const FObjectInitializer& ObjectInitializer = FObjectInitializer::Get())` only if the
  parent's constructor type is ObjectInitializer. Otherwise it generates `UFoo()`, and subclasses
  calling `Super(ObjectInitializer)`, including game-side subclasses of a public plugin, stop
  compiling. Remove an OI constructor only when the parent chain has the OI constructor type: a
  parent declaring `(const FObjectInitializer&)`, or one without a user constructor whose own
  parent has the OI type. Parents declaring only `UParent()` (e.g. `UWorldSubsystem`) block removal.
  The UHT logic is in `GetConstructorType` (`EpicGames.UHT/Exporters/CodeGen/UhtHeaderCodeGenerator.cs`).
- **`: Super(FObjectInitializer::Get())` inside an OI constructor** discards the caller's
  initializer, likely a bug. Report, don't remove.
- **`GENERATED_UCLASS_BODY()`** declares a `(const FObjectInitializer&)` constructor the class must
  define. When removing that definition, switch the macro to `GENERATED_BODY()`.

Discovery covers cpp definitions (`^[UAFS]\w+::~?[UAFS]\w+\(` with enough context for the whole
initializer list and body) and inline constructors in headers. Never classify a constructor
without seeing its full body.

Applying:
- Delete the cpp definition with its trailing blank line, so spacing between neighbors stays one
  blank line.
- Delete the header declaration line.
- A cpp left with only includes and `UE_INLINE_GENERATED_CPP_BY_NAME` becomes a section 3
  candidate. Report it, don't delete in this pass.

Report after the pass as a table grouped by action: removed, converted to `= default`, kept
with reason.

| Class | File:line | Initializer | Action |
|---|---|---|---|
| `UFoo` | Foo.cpp:13 | none | removed decl and def |
| `FBar` | Bar.h:20 | none, sibling ctor | `= default` |

## 3. Empty stub .cpp files

Some `.cpp` files are pure boilerplate left over from the "Add C++ Class" wizard: their entire
content is the copyright header, a blank line, and a single `#include` of their own header, no
actual code. Example: a file at `X/Y/Foo.cpp` whose only non-blank line is `#include "X/Y/Foo.h"`.

Detect: after the copyright line, count non-blank lines. If there's exactly one, and it's
`#include "<path matching the .cpp's own basename>"`, it's a candidate.
A file holding only the own include and `#include UE_INLINE_GENERATED_CPP_BY_NAME(<Name>)` is a
candidate too: without the inlining include UBT compiles `<Name>.gen.cpp` on its own.

**Before deleting, verify it's actually safe. Don't assume from memory:**
- UnrealBuildTool auto-generates a `<HeaderName>.gen.cpp` per reflected header (UCLASS/USTRUCT/
  UENUM/UINTERFACE) under `Intermediate/Build/.../UHT/`, **independent of whether a hand-written
  .cpp exists**. This means even a stub `.cpp` for a header with `UCLASS()`/`UINTERFACE()` in it is
  not needed for reflection registration. Confirm by finding the corresponding `.gen.cpp` in
  Intermediate for one of the candidates.
- Slate widget headers aren't reflected. Check the header has no inline-less
  declarations (constructors, `Construct`, overrides) whose bodies are expected in that `.cpp`.
- BlueprintNativeEvent interface functions (declared in an `I`-prefixed interface class, no body)
  look like they'd need a `_Implementation` body somewhere, but the actual overrides live in the
  concrete classes that implement the interface (grep for `Execute_<FunctionName>` callers and
  `<FunctionName>_Implementation` definitions to confirm), not in the interface's own stub `.cpp`.
- **The only real proof is a build.** Don't report the deletions as safe until a clean build
  confirms them.

## Change description

```
code audit: set default property values at declarations

* Moved initializations from constructors, everywhere where this was practical.
* TObjectPtr doesn't need nullptr assigned.
* Removed now empty constructors.
* Removed now empty cpp files.
```
