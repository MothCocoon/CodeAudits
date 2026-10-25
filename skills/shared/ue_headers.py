# Approximate parser of Unreal C++ headers, shared by the audit scripts.
# Reads class declarations, their bases and member function declarations.
# Doesn't evaluate the preprocessor, so declarations from every #if branch are seen.

import json
import os
import re
import tempfile


def strip_comments(t):
    t = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), t, flags=re.S)
    t = re.sub(r"//[^\n]*", "", t)
    t = re.sub(r'"(\\.|[^"\\\n])*"', '""', t)
    t = re.sub(r"'(\\.|[^'\\\n])'", "''", t)
    return t


def strip_preprocessor(t):
    out = []
    cont = False
    for line in t.split("\n"):
        s = line.strip()
        if cont or s.startswith("#"):
            cont = s.endswith("\\")
            out.append("")
        else:
            out.append(line)
    return "\n".join(out)


def replace_macro_call(t, name, replacement):
    out = []
    pos = 0
    for m in re.finditer(r"\b" + name + r"\s*\(", t):
        if m.start() < pos:
            continue
        j = m.end()
        depth = 1
        while j < len(t) and depth:
            if t[j] == "(":
                depth += 1
            elif t[j] == ")":
                depth -= 1
            j += 1
        out.append(t[pos:m.start()])
        out.append(replacement + "\n" * t[m.start():j].count("\n"))
        pos = j
    out.append(t[pos:])
    return "".join(out)


HEAD_RE = re.compile(r"\b(class|struct)\s+(?:alignas\([^)]*\)\s+)?(?:\w+_API\s+)?(?:UE_DEPRECATED\([^)]*\)\s+)?(\w+)\s*(?:final\s*)?(:[^{;]*)?\{")
ACC_RE = re.compile(r"\b(public|protected|private)\s*:(?!:)")
MACRO_ACC = [
    (re.compile(r"\bGENERATED_UCLASS_BODY\s*\(\s*\)"), "public"),
    (re.compile(r"\bGENERATED_UINTERFACE_BODY\s*\(\s*\)"), "public"),
    (re.compile(r"\bGENERATED_IINTERFACE_BODY\s*\(\s*\)"), "public"),
    # private for a class, unchanged for a struct
    (re.compile(r"\bGENERATED_BODY\s*\(\s*\)"), "generated"),
    (re.compile(r"\bSLATE_BEGIN_ARGS\s*\([^)]*\)"), "public"),
    (re.compile(r"\bSLATE_USER_ARGS\s*\([^)]*\)"), "public"),
]
# All-caps macros (UFUNCTION, FORCEINLINE, *_API, SLATE_ARGUMENT, ...) with their arguments
STRIP_MACROS = re.compile(r"\b[A-Z][A-Z0-9_]{3,}\b\s*(\([^()]*(\([^()]*(\([^()]*\)[^()]*)*\)[^()]*)*\))?")
NAME_RE = re.compile(r"(~?\w+|operator\s*[^\s(]+)\s*\(")
DESTRUCTOR = "~"


def split_top(s, open_chars="<([{", close_chars=">)]}"):
    depth = 0
    parts, cur = [], ""
    for ch in s:
        if ch in open_chars:
            depth += 1
        elif ch in close_chars:
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


def parse_bases(s):
    if not s:
        return []
    res = []
    for p in split_top(s[1:], "<", ">"):
        p = re.sub(r"<.*", "", p).strip()
        p = re.sub(r"\b(public|protected|private|virtual)\b", "", p).strip()
        p = p.split("::")[-1].strip()
        if p:
            res.append(p)
    return res


def normalize_param(p):
    p = p.split("=")[0]
    p = re.sub(r"\b(class|struct|enum|typename)\b", " ", p)
    # parameter annotation macros
    p = re.sub(r"\b(IN|OUT)\b", " ", p)
    p = re.sub(r"\s+", " ", p).strip()
    # drop the parameter name, also when glued to * or &
    m = re.match(r"^(.*?(?:[\w>\]] |[*&] ?))(\w+)$", p)
    if m and m.group(1).strip() not in ("const", "unsigned", "signed"):
        p = m.group(1)
    p = p.replace(" ", "")
    # top-level const on a by-value parameter is not part of the signature
    if not p.endswith("&") and not p.endswith("*") and p.startswith("const"):
        p = p[5:]
    return p


def signature(text_from_paren):
    depth = 0
    for j, ch in enumerate(text_from_paren):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                params = [normalize_param(x) for x in split_top(text_from_paren[1:j])]
                params = tuple(x for x in params if x not in ("", "void"))
                is_const = re.match(r"\s*const\b", text_from_paren[j + 1:]) is not None
                return params, is_const
    return None


def record(top, stmt, line):
    native_event = re.search(r"\bUFUNCTION\s*\([^;]*\bBlueprintNativeEvent\b", stmt) is not None
    s = STRIP_MACROS.sub(" ", stmt)
    if "(" not in s or re.match(r"\s*(typedef|using|friend|static)\b", s):
        return
    m = NAME_RE.search(s)
    if not m:
        return
    name = m.group(1)
    if name.startswith("operator") or name == top["class"]["name"]:
        return
    if re.search(r"\b(decltype|template)\b", s[:m.start()]):
        return
    sig = signature(s[m.end() - 1:])
    if sig is None:
        return
    # destructors of all classes share one key, so a base virtual destructor matches by name
    if name.startswith("~"):
        name = DESTRUCTOR
    tail = s[m.end() - 1:]
    decl = {
        "access": top["access"],
        "virtual": re.search(r"\bvirtual\b", s[:m.start()]) is not None,
        "override": re.search(r"\)\s*(const\s*)?(&{1,2}\s*)?(noexcept\s*)?(override|final)\b", tail) is not None,
        "line": line,
        "sig": sig,
    }
    methods = top["class"]["methods"]
    methods.setdefault(name, []).append(decl)
    if native_event:
        methods.setdefault(name + "_Implementation", []).append(dict(decl, virtual=True, override=False))


def parse_file(path):
    try:
        raw = open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return {}
    t = strip_preprocessor(strip_comments(raw))
    t = replace_macro_call(t, "PURE_VIRTUAL", ";")
    line_of = []
    ln = 1
    for ch in t:
        line_of.append(ln)
        if ch == "\n":
            ln += 1
    classes = {}
    stack = []
    depth = 0
    i = 0
    stmt_start = 0
    while i < len(t):
        boundary = i == 0 or not (t[i - 1].isalnum() or t[i - 1] == "_")
        m = HEAD_RE.match(t, i) if boundary else None
        if m:
            kind, name, bases = m.group(1), m.group(2), m.group(3)
            depth += 1
            cls = {"name": name, "bases": parse_bases(bases), "methods": {}, "file": path}
            classes.setdefault(name, cls)
            stack.append({"class": cls, "depth": depth, "kind": kind, "access": "public" if kind == "struct" else "private"})
            i = m.end()
            stmt_start = i
            continue
        top = stack[-1] if stack else None
        if top and depth == top["depth"] and boundary:
            am = ACC_RE.match(t, i)
            if am:
                top["access"] = am.group(1)
                i = am.end()
                stmt_start = i
                continue
            hit = None
            for rx, acc in MACRO_ACC:
                hit = rx.match(t, i)
                if hit:
                    if acc != "generated":
                        top["access"] = acc
                    elif top["kind"] == "class":
                        top["access"] = "private"
                    break
            if hit:
                i = hit.end()
                stmt_start = i
                continue
        ch = t[i]
        if ch in "{;":
            if top and depth == top["depth"]:
                record(top, t[stmt_start:i], line_of[i])
            if ch == "{":
                depth += 1
            else:
                stmt_start = i + 1
            i += 1
            continue
        if ch == "}":
            depth -= 1
            if stack and depth < stack[-1]["depth"]:
                stack.pop()
            i += 1
            stmt_start = i
            continue
        i += 1
    return classes


def build_engine_index(engine_dir):
    path = os.path.join(tempfile.gettempdir(), "ue_headers_index_" + re.sub(r"\W", "_", os.path.abspath(engine_dir)) + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    index = {}
    rx = re.compile(r"^\s*(?:class|struct)\s+(?:alignas\([^)]*\)\s+)?(?:\w+_API\s+)?(\w+)\s*(?:final\s*)?(?::|\{|$)")
    # class name on its own line, followed by the base list
    rx_split = re.compile(r"^\s*(\w+)\s*:\s*public\b")
    for sub in ("Source", "Plugins"):
        for root, _, files in os.walk(os.path.join(engine_dir, sub)):
            if "ThirdParty" in root or "Intermediate" in root:
                continue
            for f in files:
                if not f.endswith(".h"):
                    continue
                p = os.path.join(root, f)
                try:
                    for line in open(p, encoding="utf-8", errors="replace"):
                        m = rx.match(line) or rx_split.match(line)
                        if m:
                            index.setdefault(m.group(1), []).append(p)
                except OSError:
                    pass
    json.dump(index, open(path, "w"))
    return index


class HeaderIndex:
    def __init__(self, source_dir, engine_dir):
        self.source_dir = source_dir
        self.source_classes = {}
        for root, _, files in os.walk(source_dir):
            for f in files:
                if f.endswith(".h"):
                    for name, cls in parse_file(os.path.join(root, f)).items():
                        self.source_classes.setdefault(name, cls)
        self.engine_index = build_engine_index(engine_dir)
        self.engine_classes = {}

    def get_class(self, name):
        if name in self.source_classes:
            return self.source_classes[name]
        if name not in self.engine_classes:
            self.engine_classes[name] = None
            for p in self.engine_index.get(name, []):
                parsed = parse_file(p)
                if name in parsed:
                    self.engine_classes[name] = parsed[name]
                    break
        return self.engine_classes[name]

    def ancestors(self, cls):
        # breadth-first, so nearer bases come first
        seen = set()
        queue = list(cls["bases"])
        while queue:
            name = queue.pop(0)
            if name in seen:
                continue
            seen.add(name)
            base = self.get_class(name)
            if base is None:
                continue
            yield base
            queue.extend(base["bases"])

    def base_virtuals(self, cls, method):
        # (base class, decl) for every ancestor declaration of the method that is virtual
        res = []
        for base in self.ancestors(cls):
            for decl in base["methods"].get(method, []):
                if decl["virtual"] or decl["override"]:
                    res.append((base, decl))
        return res

    def relpath(self, cls):
        return os.path.relpath(cls["file"], self.source_dir)
