"""Contract tests: the schemas only widen, real generations validate, examples pass or fail as written.

Run from the repository root: `python3 -m unittest discover -s tests -v` (needs `jsonschema`, see
tests/requirements.txt). Generations are read from DEVOS_GENERATIONS (default `../_generations` next to this
repository's checkout, the workspace layout); extra system generations from DEVOS_SYSTEM_GENERATIONS (paths separated by
`os.pathsep`). Without them only the committed examples run, and the skipped tests say so.
"""
import copy
import json
import os
import re
import sqlite3
import subprocess
import unittest

from jsonschema import Draft202012Validator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(ROOT, "schema")
EXAMPLES = os.path.join(ROOT, "tests", "examples")
QUERY_EXAMPLES = os.path.join(ROOT, "tests", "query-examples")
# v1.1 as drafted (schema/v1 unchanged since): every v1.2 schema must accept whatever this accepted.
BASELINE_COMMIT = "ea4975a"


def _workspace_default():
    # The contract lives at <workspace>/devos-intelligence-contract or in <workspace>/devos-intelligence-contract.worktrees/<name>.
    parent = os.path.dirname(ROOT)
    if parent.endswith(".worktrees"):
        parent = os.path.dirname(parent)
    return os.path.join(parent, "_generations")


GENERATIONS = os.environ.get("DEVOS_GENERATIONS", _workspace_default())
SYSTEM_GENERATIONS = [p for p in os.environ.get("DEVOS_SYSTEM_GENERATIONS", "").split(os.pathsep) if p]

GRAPH_SCHEMA = {
    "entities.ndjson": "entity",
    "declarations.ndjson": "declaration",
    "relations.ndjson": "relation",
    "evidence.ndjson": "evidence",
    "observations.ndjson": "observation",
    "links.ndjson": "link",
    "diagnostics.ndjson": "diagnostic",
}
SUBSET_KEYWORDS = {"$schema", "$id", "title", "description", "type", "required", "properties", "additionalProperties",
                   "enum", "const", "pattern", "items", "minItems", "minimum"}
INPUT_PREFIX = "(?:[a-z0-9][a-z0-9-]*/)?"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def schema(group, name):
    return load_json(os.path.join(SCHEMA, group, f"{name}.schema.json"))


def kind_names():
    return sorted(f[: -len(".schema.json")] for f in os.listdir(os.path.join(SCHEMA, "v1", "kinds")) if f.endswith(".schema.json"))


def prefixed(s):
    """System generations: every anchored id pattern accepts an optional `{input}/` prefix (docs/CONTRACT-v1.2.md)."""
    if isinstance(s, list):
        return [prefixed(x) for x in s]
    if isinstance(s, dict):
        return {k: ("^" + INPUT_PREFIX + v[1:] if k == "pattern" and isinstance(v, str) and v.startswith("^") else prefixed(v)) for k, v in s.items()}
    return s


class Validators:
    def __init__(self, system=False):
        self.system = system
        self.cache = {}

    def get(self, group, name):
        key = (group, name)
        if key not in self.cache:
            s = schema(group, name)
            if self.system and group in ("v1", "v1/kinds"):
                s = prefixed(s)
            self.cache[key] = Draft202012Validator(s)
        return self.cache[key]

    def errors(self, group, name, record):
        return [f"{name}: {'/'.join(map(str, e.absolute_path)) or '$'}: {e.message}" for e in self.get(group, name).iter_errors(record)]


KINDS = set()


def record_errors(v, base, record):
    """Errors of one graph record: its base schema, its kind schema (observations) and the `site` rule."""
    if not KINDS:
        KINDS.update(kind_names())
    errors = v.errors("v1", base, record)
    if base == "observation":
        if record.get("kind") in KINDS:
            errors += v.errors("v1/kinds", record["kind"], record)
        if "site" in record and record["site"] not in record.get("evidence", []):
            errors.append("observation: site is not one of the record's evidence ids")
    if base == "link" and v.system and record.get("scope") == "system":
        errors += v.errors("system/v1", "system-link", record)
    return errors


def read_ndjson(path):
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                yield n, json.loads(line)


def validate_generation(directory, system=False, limit=20):
    """All records of a generation; returns at most `limit` errors and the number of records checked."""
    v = Validators(system)
    errors, count = [], 0

    def check(rel, n, errs):
        for e in errs:
            if len(errors) < limit:
                errors.append(f"{rel}:{n}: {e}")

    manifest = load_json(os.path.join(directory, "manifest.json"))
    check("manifest.json", 1, v.errors("v1", "manifest", manifest))
    if system:
        check("manifest.json", 1, v.errors("system/v1", "system-manifest", manifest))
    files = [("graph/projects.ndjson", None), ("snippets.ndjson", "snippet")] + [(f"graph/{f}", s) for f, s in GRAPH_SCHEMA.items()]
    if system:
        files += [("inputs.ndjson", "system/input"), ("graph/packages.ndjson", "system/package-resolution"), ("graph/traces.ndjson", "system/trace")]
    for rel, name in files:
        path = os.path.join(directory, rel)
        if not os.path.exists(path):
            continue
        for n, record in read_ndjson(path):
            count += 1
            if name is None:
                base = "analysis-context" if record.get("recordType") == "analysisContext" else "project"
                check(rel, n, record_errors(v, base, record))
            elif name.startswith("system/"):
                check(rel, n, v.errors("system/v1", name.split("/", 1)[1], record))
            else:
                check(rel, n, record_errors(v, name, record))
    return errors, count


def generation_dirs():
    if not os.path.isdir(GENERATIONS):
        return []
    out = []
    for name in sorted(os.listdir(GENERATIONS)):
        d = os.path.join(GENERATIONS, name)
        if os.path.isfile(os.path.join(d, "manifest.json")):
            out.append(d)
    return out


def is_system(d):
    return load_json(os.path.join(d, "manifest.json")).get("generationType") == "system"


def index_sql():
    """Statements of schema/index/v1/index.sql by section, whitespace collapsed."""
    sections, current = {}, None
    with open(os.path.join(SCHEMA, "index", "v1", "index.sql"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            m = re.match(r"^-- (base|evidence|system)$", line)
            if m:
                current = m.group(1)
                sections[current] = []
            elif line and not line.startswith("--"):
                sections[current].append(normalize_sql(line))
    return sections


def normalize_sql(s):
    return re.sub(r"\s+", " ", s.strip().rstrip(";")).strip().lower()


def object_name(stmt):
    return re.match(r"create (?:virtual )?(?:table|index) (\w+)", stmt).group(1)


class SchemasOnlyWiden(unittest.TestCase):
    """Compatibility rule 5: a minor only adds. Every keyword of the v1.1 schemas is kept or relaxed."""

    def baseline(self, rel):
        try:
            text = subprocess.run(["git", "-C", ROOT, "show", f"{BASELINE_COMMIT}:{rel}"], check=True, capture_output=True, text=True).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest(f"git history with {BASELINE_COMMIT} is not available")
        return json.loads(text)

    def compare(self, old, new, path, problems):
        if isinstance(old, dict):
            if not isinstance(new, dict):
                problems.append(f"{path}: object replaced")
                return
            for k, ov in old.items():
                nv = new.get(k)
                p = f"{path}/{k}"
                if k == "required":
                    if not set(nv or []) <= set(ov):
                        problems.append(f"{p}: new required {sorted(set(nv or []) - set(ov))}")
                elif k == "enum":
                    if nv is not None and not set(ov) <= set(nv):
                        problems.append(f"{p}: removed {sorted(set(ov) - set(nv))}")
                elif k == "type":
                    ot = ov if isinstance(ov, list) else [ov]
                    nt = nv if isinstance(nv, list) else [nv]
                    if nv is not None and not set(ot) <= set(nt):
                        problems.append(f"{p}: narrowed {ot} -> {nt}")
                elif k in ("pattern", "const", "minItems", "minimum"):
                    if nv != ov:
                        problems.append(f"{p}: changed {ov!r} -> {nv!r}")
                elif k == "additionalProperties":
                    if nv is False and ov is not False:
                        problems.append(f"{p}: closed")
                elif k in ("description", "$id", "title", "$schema"):
                    continue
                elif nv is None:
                    continue
                else:
                    self.compare(ov, nv, p, problems)

    def test_v1_schemas_accept_everything_v1_1_accepted(self):
        problems = []
        for f in sorted(os.listdir(os.path.join(SCHEMA, "v1"))):
            if f.endswith(".schema.json"):
                rel = f"schema/v1/{f}"
                self.compare(self.baseline(rel), load_json(os.path.join(ROOT, rel)), f, problems)
        self.assertEqual(problems, [])

    def test_no_new_required_capability(self):
        self.assertNotIn("enum", schema("v1", "manifest")["properties"]["requiredCapabilities"]["items"])


class SchemaFiles(unittest.TestCase):
    def all_schema_files(self):
        for group in ("v1", "v1/kinds", "system/v1", "query/v1"):
            for f in sorted(os.listdir(os.path.join(SCHEMA, group))):
                if f.endswith(".schema.json"):
                    yield group, f

    def test_every_schema_is_valid_draft_2020_12(self):
        for group, f in self.all_schema_files():
            with self.subTest(file=f"{group}/{f}"):
                Draft202012Validator.check_schema(load_json(os.path.join(SCHEMA, group, f)))

    def test_record_schemas_use_only_the_engine_validator_subset(self):
        def walk(s, path, bad):
            if isinstance(s, dict):
                for k, v in s.items():
                    if k not in SUBSET_KEYWORDS:
                        bad.append(f"{path}/{k}")
                    if k == "properties":
                        for pk, pv in v.items():
                            walk(pv, f"{path}/properties/{pk}", bad)
                    elif k == "items":
                        walk(v, f"{path}/items", bad)
        for group, f in self.all_schema_files():
            if group == "query/v1":
                continue
            with self.subTest(file=f"{group}/{f}"):
                bad = []
                walk(load_json(os.path.join(SCHEMA, group, f)), "", bad)
                self.assertEqual(bad, [])

    def test_kind_schema_names_match_their_const(self):
        for name in kind_names():
            self.assertEqual(schema("v1/kinds", name)["properties"]["kind"]["const"], name)


class Examples(unittest.TestCase):
    def records(self, name):
        return list(read_ndjson(os.path.join(EXAMPLES, name)))

    def base_of(self, record):
        return "link" if str(record.get("id", "")).startswith("lnk:") else "observation"

    def test_engine_and_constructed_examples_validate(self):
        v = Validators()
        for name in ("angular-fixtures.ndjson", "v1.2-constructed.ndjson"):
            for n, record in self.records(name):
                with self.subTest(file=name, line=n, kind=record.get("kind")):
                    self.assertEqual(record_errors(v, self.base_of(record), record), [])

    def test_examples_cover_every_kind_schema(self):
        seen = {r.get("kind") for name in ("angular-fixtures.ndjson", "v1.2-constructed.ndjson") for _, r in self.records(name)}
        self.assertEqual(sorted(set(kind_names()) - seen), [])

    def test_invalid_examples_fail(self):
        v = Validators()
        for n, record in self.records("v1.2-invalid.ndjson"):
            with self.subTest(line=n, kind=record.get("kind")):
                self.assertNotEqual(record_errors(v, self.base_of(record), record), [])

    def test_query_examples_match_their_row_schemas(self):
        names = sorted((f[: -len(".schema.json")] for f in os.listdir(os.path.join(SCHEMA, "query", "v1"))), key=len, reverse=True)
        checked = 0
        for engine in sorted(os.listdir(QUERY_EXAMPLES)):
            for f in sorted(os.listdir(os.path.join(QUERY_EXAMPLES, engine))):
                name = next(n for n in names if f == f"{n}.json" or f.startswith(f"{n}-"))
                with self.subTest(file=f"{engine}/{f}"):
                    data = load_json(os.path.join(QUERY_EXAMPLES, engine, f))
                    errors = [e.message for e in Draft202012Validator(schema("query/v1", name)).iter_errors(data)]
                    self.assertEqual(errors, [])
                    checked += 1
        self.assertGreater(checked, 0)


class RealGenerations(unittest.TestCase):
    """Every v1.0 and v1.1 generation of the workspace validates against the v1.2 schemas."""

    def setUp(self):
        self.dirs = [d for d in generation_dirs() if not is_system(d)]
        if not self.dirs:
            self.skipTest(f"no generations in {GENERATIONS}")

    def test_generations_validate(self):
        versions = set()
        for d in self.dirs:
            versions.add(load_json(os.path.join(d, "manifest.json"))["schemaVersion"])
            with self.subTest(generation=os.path.basename(d)):
                errors, count = validate_generation(d)
                self.assertGreater(count, 0)
                self.assertEqual(errors, [])
        print(f"\n  generations: {len(self.dirs)} ({', '.join(os.path.basename(d) for d in self.dirs)}); schema versions {sorted(versions)}")

    def test_index_tables_match_index_sql(self):
        sections = index_sql()
        allowed = {object_name(s): s for section in ("base", "evidence") for s in sections[section]}
        checked = 0
        for d in self.dirs:
            path = os.path.join(d, "index.sqlite")
            if not os.path.exists(path):
                continue
            checked += 1
            with self.subTest(generation=os.path.basename(d)):
                self.assertEqual(index_problems(path, sections["base"], allowed), [])
                meta = read_meta(path)
                for key in ("schemaVersion", "commit", "engine"):
                    self.assertIn(key, meta)
        if checked == 0:
            self.skipTest("no generation with index.sqlite")


class SystemGenerations(unittest.TestCase):
    def setUp(self):
        self.dirs = [d for d in generation_dirs() if is_system(d)] + SYSTEM_GENERATIONS
        if not self.dirs:
            self.skipTest("no system generation (set DEVOS_SYSTEM_GENERATIONS)")

    def test_system_generations_validate(self):
        for d in self.dirs:
            with self.subTest(generation=d):
                errors, count = validate_generation(d, system=True)
                self.assertGreater(count, 0)
                self.assertEqual(errors, [])

    def test_system_index_tables_match_index_sql(self):
        sections = index_sql()
        allowed = {object_name(s): s for section in sections for s in sections[section]}
        for d in self.dirs:
            path = os.path.join(d, "index.sqlite")
            if not os.path.exists(path):
                continue
            with self.subTest(generation=d):
                self.assertEqual(index_problems(path, sections["base"] + sections["system"], allowed), [])


def read_meta(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return dict(con.execute("select key, value from meta").fetchall())
    finally:
        con.close()


def index_problems(path, required, allowed):
    """Tables and indexes of an index.sqlite against index.sql: required ones present and identical, others known."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = con.execute("select name, sql from sqlite_master where sql is not null and type in ('table', 'index')").fetchall()
    finally:
        con.close()
    present = {name: normalize_sql(sql) for name, sql in rows if not name.startswith("search_") and not name.startswith("sqlite_")}
    problems = []
    for stmt in required:
        name = object_name(stmt)
        if name not in present:
            problems.append(f"missing {name}")
        elif present[name] != stmt:
            problems.append(f"{name}: {present[name]!r} differs from {stmt!r}")
    for name, stmt in present.items():
        if name not in allowed:
            problems.append(f"unknown {name}")
        elif allowed[name] != stmt:
            problems.append(f"{name}: {stmt!r} differs from {allowed[name]!r}")
    return sorted(set(problems))


if __name__ == "__main__":
    unittest.main()
