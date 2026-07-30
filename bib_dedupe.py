#!/usr/bin/env python3
"""Find and merge duplicate entries in the central bibliography.

Duplicates here do not share a citation key. `craver2009`, `craver_2009` and
`craver_2009_mechanisms_natural_kinds` are three keys for one paper, which is
why nothing caught them. This clusters by DOI and by normalized title plus
year, then proposes a merge per cluster.

The merge keeps one entry and records the other keys in its `ids` field, so
**no manuscript needs editing**: an existing \\citep{} of a retired key still
resolves. Doing only half of that -- aliasing without deleting -- is what
produced the six "citekey alias is also a real entry key" collisions, where
biber silently drops the alias.

Clusters whose entries disagree on a material field (author, journal,
publisher, volume, pages, entry type) are NOT proposed for merge. Two entries
can share a title and year and still be different works or different editions:
`cavell1969avoidance` is the Cambridge printing and `Cavell1969AvoidanceOfLove`
the Scribner's, so their pagination differs.

Usage:
    bib_dedupe.py                        # report clusters, propose merges
    bib_dedupe.py --report merge.md      # write the proposal for review
    bib_dedupe.py --apply merge.md       # perform the approved merges
    bib_dedupe.py --show craver2009      # every entry in one cluster, in full

Exit status: 0 = clean or report written; 1 = clusters found; 2 = error.

Nothing is written without --apply, and --apply refuses if the central bib has
uncommitted changes.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HOUSE_STYLE = Path(__file__).resolve().parent
CENTRAL = HOUSE_STYLE / "references.bib"
ROOT = HOUSE_STYLE.parent

sys.path.insert(0, str(HOUSE_STYLE))
from push_bib import Entry, parse_bib, git_clean  # noqa: E402

# Fields whose disagreement means these are probably not the same object.
MATERIAL = ("author", "editor", "journal", "booktitle", "publisher",
            "volume", "number", "pages", "edition", "year")
# Fields where a difference is cosmetic or an enrichment.
COSMETIC = ("doi", "url", "note", "abstract", "keywords", "ids", "file",
            "address", "location", "series", "issn", "isbn", "month")

CITE_RE = re.compile(r"\\(?:cite[a-zA-Z]*|textcite|parencite|autocite|footcite)"
                     r"\s*(?:\[[^\]]*\])*\s*\{([^}]*)\}")


def norm(v: str) -> str:
    v = re.sub(r"[{}\\]", "", v.lower())
    v = re.sub(r"[^a-z0-9 ]", " ", v)
    return re.sub(r"\s+", " ", v).strip()


def norm_names(v: str) -> str:
    """Compare author and editor lists by surname set. `Craver, Carl F.` and
    `Carl F. Craver` are the same person in two BibTeX name orders, and
    comparing the raw strings reports a conflict that isn't one. Braced
    compound surnames (`Dimitri {Coelho Mollo}`) are kept whole."""
    surnames = []
    for name in re.split(r"\s+and\s+", v.strip()):
        name = name.strip()
        if not name:
            continue
        if "," in name:
            surname = name.split(",")[0]
        else:
            braced = re.search(r"\{([^}]+)\}\s*$", name)
            surname = braced.group(1) if braced else name.split()[-1] if name.split() else name
        surnames.append(norm(surname))
    return " | ".join(sorted(s for s in surnames if s))


def citation_counts() -> dict[str, int]:
    """How often each key is cited across the portfolio."""
    counts: dict[str, int] = defaultdict(int)
    for pattern in ("**/*.tex", "**/*.qmd"):
        for path in ROOT.glob(pattern):
            if any(p in {".git", "_build", "build", "node_modules"} for p in path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in CITE_RE.finditer(text):
                for key in m.group(1).split(","):
                    key = key.strip()
                    if key:
                        counts[key] += 1
    return counts


def cluster(entries: list[Entry]) -> list[list[Entry]]:
    """Union entries that share a DOI or a normalized title+year."""
    parent: dict[str, str] = {e.key: e.key for e in entries}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for index in (defaultdict(list), defaultdict(list)):
        pass
    by_doi, by_title = defaultdict(list), defaultdict(list)
    for e in entries:
        if e.doi:
            by_doi[e.doi].append(e.key)
        if e.title_year and e.title_year[0]:
            by_title[e.title_year].append(e.key)
    for group in list(by_doi.values()) + list(by_title.values()):
        for k in group[1:]:
            union(group[0], k)

    out: dict[str, list[Entry]] = defaultdict(list)
    lookup = {e.key: e for e in entries}
    for e in entries:
        out[find(e.key)].append(e)
    return [v for v in out.values() if len(v) > 1]


def conflicts(group: list[Entry]) -> list[str]:
    bad = []
    if len({e.entrytype for e in group}) > 1:
        bad.append("entrytype: " + ", ".join(sorted({e.entrytype for e in group})))
    for f in MATERIAL:
        fn = norm_names if f in ("author", "editor") else norm
        vals = {fn(e.fields[f]) for e in group if e.fields.get(f)}
        if len(vals) > 1:
            bad.append(f)
    return bad


def choose_winner(group: list[Entry], cites: dict[str, int]) -> tuple[Entry, Entry]:
    """(key_source, data_source). The surviving key is the most-cited one; the
    surviving fields come from the most complete entry. They are often not the
    same entry."""
    key_src = max(group, key=lambda e: (cites.get(e.key, 0), len(e.fields), -len(e.key)))
    data_src = max(group, key=lambda e: (len(e.fields), len(e.text)))
    return key_src, data_src


FIELD_ORDER = ("author", "editor", "title", "booktitle", "journal", "series",
               "publisher", "address", "location", "institution", "school",
               "edition", "volume", "number", "pages", "year", "date", "month",
               "doi", "url", "urldate", "isbn", "issn", "eprint", "note",
               "abstract", "keywords", "ids")


def merge_fields(group: list[Entry], data_src: Entry) -> dict[str, str]:
    """Union of every entry's fields. Picking one entry wholesale drops data:
    HuddlestonPullum2005 carries an ISBN and huddleston2005 a DOI, and taking
    either alone loses the other. On disagreement the more complete entry wins,
    which only ever applies to cosmetic fields since material conflicts are
    excluded from the merge set upstream."""
    merged: dict[str, str] = {}
    for e in sorted(group, key=lambda x: (x is data_src, len(x.fields))):
        for k, v in e.fields.items():
            if k == "ids":
                continue
            if v.strip():
                merged[k] = v
    return merged


def render(group: list[Entry], key: str, data_src: Entry, aliases: set[str]) -> str:
    fields = merge_fields(group, data_src)
    if aliases:
        fields["ids"] = ", ".join(sorted(aliases))
    ordered = [f for f in FIELD_ORDER if f in fields]
    ordered += [f for f in sorted(fields) if f not in FIELD_ORDER]
    width = max(len(f) for f in ordered)
    body = "".join(f"  {f.ljust(width)} = {{{fields[f]}}},\n" for f in ordered)
    return f"@{data_src.entrytype}{{{key},\n{body}}}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--central", default=str(CENTRAL))
    ap.add_argument("--report", metavar="FILE", help="write the proposal for review")
    ap.add_argument("--apply", metavar="FILE", help="perform the merges approved in FILE")
    ap.add_argument("--show", metavar="KEY", help="print every entry in one cluster")
    ap.add_argument("--allow-dirty", action="store_true")
    args = ap.parse_args()

    path = Path(args.central).resolve()
    text = path.read_text(encoding="utf-8")
    entries = parse_bib(text)
    groups = sorted(cluster(entries), key=lambda g: -len(g))
    cites = citation_counts()

    if args.show:
        for g in groups:
            if any(e.key == args.show for e in g):
                for e in g:
                    print(f"--- {e.key}  (cited {cites.get(e.key,0)}x)\n{e.text}\n")
                print("conflicts:", conflicts(g) or "none")
                return 0
        print(f"[dedupe] {args.show} is not in any duplicate cluster")
        return 0

    clean, dirty = [], []
    for g in groups:
        (dirty if conflicts(g) else clean).append(g)

    if args.apply:
        approved = set()
        for line in Path(args.apply).read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*-\s*\[[xX]\]\s*(\S+)", line)
            if m:
                approved.add(m.group(1))
        if not approved:
            sys.exit("[dedupe] no lines checked off in the report; nothing to apply")
        if not args.allow_dirty:
            ok, detail = git_clean(path)
            if not ok:
                sys.exit(f"[dedupe] central bib has uncommitted changes ({detail}); "
                         "commit or stash first")
        new_text, merged = text, 0
        for g in clean:
            key_src, data_src = choose_winner(g, cites)
            if key_src.key not in approved:
                continue
            aliases = {e.key for e in g if e.key != key_src.key}
            for e in g:
                aliases |= e.aliases
            aliases.discard(key_src.key)
            replacement = render(g, key_src.key, data_src, aliases)
            for e in g:
                if e is data_src:
                    new_text = new_text.replace(e.text, replacement, 1)
                else:
                    new_text = new_text.replace(e.text + "\n", "", 1)
            merged += 1
        path.write_text(new_text, encoding="utf-8")
        print(f"[dedupe] merged {merged} cluster(s); "
              f"{len(parse_bib(new_text))} entries remain (was {len(entries)})")
        return 0

    lines = [
        "# Bibliography duplicate merge proposal",
        "",
        f"{len(entries)} entries. {len(groups)} duplicate clusters "
        f"({len(clean)} field-compatible, {len(dirty)} needing a decision).",
        "",
        "Check off `- [x]` any cluster you want merged, then:",
        "",
        "    python3 .house-style/bib_dedupe.py --apply <this-file>",
        "",
        "Merging keeps the most-cited key and the most complete entry's fields,",
        "and records the retired keys in `ids`. No manuscript needs editing:",
        "an existing citation of a retired key still resolves.",
        "",
        "## Field-compatible (safe to merge)",
        "",
    ]
    for g in clean:
        key_src, data_src = choose_winner(g, cites)
        losers = [e for e in g if e.key != key_src.key]
        title = (data_src.fields.get("title") or "")[:70].replace("\n", " ")
        lines.append(f"- [ ] {key_src.key}  — {title}")
        lines.append(f"      keep key `{key_src.key}` (cited {cites.get(key_src.key,0)}x), "
                     f"fields from `{data_src.key}` ({len(data_src.fields)} fields)")
        for e in losers:
            lines.append(f"      retire `{e.key}` (cited {cites.get(e.key,0)}x) -> becomes an alias")
    if not clean:
        lines.append("(none)")

    lines += ["", "## Needs a decision (entries disagree on a material field)", ""]
    for g in dirty:
        title = (g[0].fields.get("title") or "")[:70].replace("\n", " ")
        lines.append(f"- {' / '.join(e.key for e in g)} — {title}")
        lines.append(f"      conflicting: {', '.join(conflicts(g))}")
        lines.append(f"      inspect: bib_dedupe.py --show {g[0].key}")
    if not dirty:
        lines.append("(none)")

    out = "\n".join(lines) + "\n"
    if args.report:
        Path(args.report).write_text(out, encoding="utf-8")
        print(f"[dedupe] wrote {args.report}: {len(clean)} safe, {len(dirty)} needing a decision")
    else:
        print(out)
    return 1 if groups else 0


if __name__ == "__main__":
    sys.exit(main())
