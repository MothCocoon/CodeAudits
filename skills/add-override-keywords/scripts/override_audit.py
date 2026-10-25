# Lists method declarations missing `virtual` or `override` in a source tree.
# Usage: python -I override_audit.py <SourceDir> <EngineDir>
# Output: TSV rows <category> <file:line> <class> <method> <base class>

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "shared"))
import ue_headers

index = ue_headers.HeaderIndex(sys.argv[1], sys.argv[2])

rows = []
for cls in index.source_classes.values():
    for method, decls in cls["methods"].items():
        for decl in decls:
            if decl["virtual"] and decl["override"]:
                continue
            if decl["override"]:
                rows.append(("missing virtual", cls, decl, method, ""))
                continue
            bases = index.base_virtuals(cls, method)
            if not bases:
                continue
            matching = [base for base, base_decl in bases if base_decl["sig"] == decl["sig"]]
            if matching:
                category = "missing override" if decl["virtual"] else "missing virtual and override"
                rows.append((category, cls, decl, method, matching[0]["name"]))
            else:
                rows.append(("signature differs from base virtual", cls, decl, method, bases[0][0]["name"]))

order = ["missing virtual and override", "missing override", "missing virtual", "signature differs from base virtual"]
rows.sort(key=lambda r: (order.index(r[0]), index.relpath(r[1]), r[2]["line"]))
for category, cls, decl, method, base in rows:
    name = "~" + cls["name"] if method == ue_headers.DESTRUCTOR else method
    print("\t".join([category, index.relpath(cls) + ":" + str(decl["line"]), cls["name"], name, base]))
