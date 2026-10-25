# Lists overrides whose access level differs from the nearest base declaration of the same virtual.
# Usage: python -I access_audit.py <SourceDir> <EngineDir>
# Output: TSV rows <file:line> <class> <method> <access> <base access> <base class> <base file:line>

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "shared"))
import ue_headers

index = ue_headers.HeaderIndex(sys.argv[1], sys.argv[2])

rows = []
for cls in index.source_classes.values():
    for method, decls in cls["methods"].items():
        if method == ue_headers.DESTRUCTOR:
            continue
        for decl in decls:
            matching = [(base, base_decl) for base, base_decl in index.base_virtuals(cls, method) if base_decl["sig"] == decl["sig"]]
            if not matching:
                continue
            nearest = matching[0][0]
            base_access = sorted({base_decl["access"] for base, base_decl in matching if base is nearest})
            if base_access == [decl["access"]]:
                continue
            base_lines = ",".join(str(base_decl["line"]) for base, base_decl in matching if base is nearest)
            rows.append((index.relpath(cls), decl["line"], cls["name"], method, decl["access"], "/".join(base_access), nearest["name"], nearest["file"] + ":" + base_lines))

rows.sort()
for file, line, cls_name, method, access, base_access, base_name, base_location in rows:
    print("\t".join([file + ":" + str(line), cls_name, method, access, base_access, base_name, base_location]))
