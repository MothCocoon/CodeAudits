---
name: fix-source-headers
description: Audit and fix source file encoding (UTF-8 BOM), the project's copyright header line, and header/include spacing conventions across an Unreal plugin's or project's Source. Use when asked to check file encoding, copyright notices, or header formatting/spacing.
---

# Source header audit

There is a set of conventions for the top of every `.h`/`.cpp`/`.cs` file. This skill
finds and fixes deviations.
Detect the version control of the audited folder and follow its notes in `../shared/vcs/` for listing, editing, adding and deleting files.

Scan the tracked files under `Source` filtered to `.h`/`.hpp`/`.cpp`/`.cs`. That skips `Intermediate`,
`Binaries`, `Saved`, `DerivedDataCache`, `.git`, `.vs`, which hold UBT/UHT-generated files
(`*.gen.cpp`, `Module.*.cpp`, `Definitions.*.h`, ...), not real source.

Keep each file's line endings, never normalize them.

Header text and spacing fixes are in-place edits, so every change shows up as a diff. BOM
stripping is the only byte-level rewrite, because a text edit can't address the BOM bytes.

## 1. UTF-8 BOM check

Symptom: an editor/diff tool shows garbage characters (`ï»¿` or similar mojibake) right before the
first line of a file. That's a UTF-8 BOM (`EF BB BF`) being misrendered. The file is fine, it just
has a leading BOM most tools hide but some don't.

Detect: read the first 3 bytes of every `.h`/`.hpp`/`.cpp`/`.cs` file and check for `EF BB BF`.
`.Build.cs` files are included.

Fix: rewrite the file with those 3 bytes stripped (byte-level, not a text re-encode, everything
after the BOM is untouched).

```python
with open(path, "rb") as f:
    data = f.read()
if data.startswith(b"\xef\xbb\xbf"):
    with open(path, "wb") as f:
        f.write(data[3:])
```

## 2. Copyright header normalization

Find the canonical header line of the audited code: read the first line of each file (after
stripping any BOM) and take the dominant `// Copyright ...` line. Show it before editing.
When no line clearly dominates (two variants of similar count, or most files have none), ask the
user which line is canonical. Don't pick one yourself.

Deviations to fix are near-copies of the canonical line:
- Leading or trailing whitespace, e.g. ` // Copyright ...` with a leading space.
- A leading BOM in front of an otherwise correct line (handled by section 1).
- Files with no header line at all: add one only if asked.

**Do not touch other rightsholders' copyright lines.** Code derived from Unreal Engine may carry
`// Copyright Epic Games, Inc. All Rights Reserved.` on purpose.

When in doubt about a line that differs from the canonical one in more than whitespace, ask before
rewriting it. Copyright text has real licensing implications, don't guess.

Also watch for a stray `/*` accidentally prepended to the copyright line (e.g. `/*// Copyright...`).
That's not a header formatting issue. It silently opens a block comment that swallows the entire
rest of the file until the next literal `*/`, effectively commenting out all the code in that
translation unit. Flag this as a separate functional bug. Fixing the header text alone would
un-comment a block of code that hasn't compiled in who-knows-how-long, which needs its own build
verification, not a drive-by text fix.

## 3. Header/include spacing rules

For files whose first line is the canonical header:

**`.h` / `.hpp` files:**
- No blank line between the copyright line and `#pragma once` (they're adjacent).
- Exactly one blank line between `#pragma once` and the next non-blank line (usually the first
  `#include`, but `#if WITH_EDITOR`, a comment or a doc block are valid too).

Correct shape:
```cpp
// Copyright <canonical line>
#pragma once

#include "Something.h"
```

**`.cpp` files:**
- The include of the file's own header directly under the copyright line, no blank line between.
- Exactly one blank line after the own header include.

Correct shape:
```cpp
// Copyright <canonical line>
#include "MyActor.h"

#include "MyLogChannels.h"
#include "MySettings.h"
```

When the `.cpp` has no header of its own name but includes a header it primarily implements or
tests (e.g. `Foo.spec.cpp` with `Tests/FooTestTypes.h`), that header
takes the own-header slot.

Files with no such header (e.g. `*.spec.cpp` opening with `#include "Misc/AutomationTest.h"`
before an `#if WITH_DEV_AUTOMATION_TESTS` guard) keep copyright, blank line, first include.
Leave them as they are, this exception can occur in regular classes too.

**`.cs` files:** `.Build.cs` files put `using UnrealBuildTool;` directly under the copyright line.
Leave that as is.

Detect deviations with a byte-level regex anchored on the canonical header line (so you don't
accidentally touch other rightsholders' files), fix by inserting/collapsing the newline run, then
**re-scan from scratch after fixing**. Don't trust a stale "still broken" list, files can get
touched by other tooling (IDE, version control) between scan and fix.

## Change description

```
code audit: standardized formatting of top lines, stripped UTF BOM
```
