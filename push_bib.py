#!/usr/bin/env python3
"""Merge a project's references-local.bib into the central bibliography.

The check that matters is NOT the citation key. Across 2,177 entries the central
bib accumulated 40 groups sharing a DOI and 60 sharing a title and year, all
under different keys: `craver2009`, `craver_2009` and
`craver_2009_mechanisms_natural_kinds` were three copies of one paper. A
key-based duplicate check waves every one of those through, which is how they
got there. So this matches on DOI first, then on normalized title plus year,
and treats the key as the weakest signal.

Default behaviour on any kind of collision is refuse and report. Silently
overwriting a central entry from a project-local file propagates whatever that
project happened to have (an abbreviated journal name for one venue, a
truncated author list) to every paper in the portfolio. Corrections are still
possible, but they have to be asked for by name:

    push_bib.py --update slater2015

Usage:
    push_bib.py                          # from inside a project directory
    push_bib.py --project papers/countability
    push_bib.py --local path/to/refs.bib --dry-run
    push_bib.py --update KEY [--update KEY ...]
    push_bib.py --json

Exit status: 0 = everything merged or nothing to do; 1 = something was refused;
2 = configuration or safety error.

The central bib is protected against the Edit and Write tools by
protect-files.sh. This script writes with ordinary file I/O, which is the
sanctioned route, and refuses to run if the central bib has uncommitted
changes, so every write is recoverable with `git checkout`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HOUSE_STYLE = Path(__file__).resolve().parent
CENTRAL = HOUSE_STYLE / "references.bib"
ROOT = HOUSE_STYLE.parent

ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.M)
LOCAL_HEADER = (
    "% Local bibliography entries -- merged into the central bib via /push-bib\n"
    "% Add new entries here during editing sessions.\n"
)


@dataclass
class Entry:
    key: str
    entrytype: str
    text: str
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def doi(self) -> str | None:
        d = self.fields.get("doi")
        if not d:
            url = self.fields.get("url", "")
            m = re.search(r"doi\.org/(.+)$", url)
            d = m.group(1) if m else None
        if not d:
            return None
        return re.sub(r"^https?://(dx\.)?doi\.org/", "", d.strip()).lower().rstrip(".")

    @property
    def title_year(self) -> tuple[str, str] | None:
        t = self.fields.get("title")
        if not t:
            return None
        norm = re.sub(r"[{}\\]", "", t.lower())
        norm = re.sub(r"\\?\$[^$]*\$", " ", norm)
        norm = re.sub(r"[^a-z0-9 ]", " ", norm)
        norm = re.sub(r"\s+", " ", norm).strip()
        if not norm:
            return None
        year = (self.fields.get("year") or self.fields.get("date") or "")[:4]
        return (norm, year)

    @property
    def aliases(self) -> set[str]:
        return {a.strip() for a in re.split(r"[,\s]+", self.fields.get("ids", "")) if a.strip()}


def parse_fields(text: str) -> dict[str, str]:
    """Field values, brace-balanced. A naive regex stops at the first '}' and
    mangles any title containing braces, which is most of them."""
    out: dict[str, str] = {}
    body = text[text.index(",") + 1:]
    i = 0
    while i < len(body):
        m = re.compile(r"(\w+)\s*=\s*").search(body, i)
        if not m:
            break
        name = m.group(1).lower()
        j = m.end()
        while j < len(body) and body[j].isspace():
            j += 1
        if j >= len(body):
            break
        if body[j] in "{\"":
            closer = "}" if body[j] == "{" else '"'
            depth, k = 1, j + 1
            while k < len(body) and depth:
                if body[k] == "\\":
                    k += 2
                    continue
                if body[k] == body[j] and closer == "}":
                    depth += 1
                elif body[k] == closer:
                    depth -= 1
                k += 1
            out[name] = body[j + 1:k - 1].strip()
            i = k
        else:
            k = j
            while k < len(body) and body[k] not in ",\n":
                k += 1
            out[name] = body[j:k].strip()
            i = k
    return out


def mask_comments(text: str) -> str:
    """Replace each comment line with spaces of the SAME length, so every
    character offset still lines up with the original.

    Entries get retired by commenting them out, and a parser that ignores this
    sees phantom entries: `% @book{spelke2007,` is a deliberately disabled
    duplicate that biber correctly skips. Blanking the lines outright would
    shift offsets, and callers slice the original text by offset to rewrite
    entries, so the slices have to stay exact. A '%' inside a field value is
    left alone."""
    return "\n".join(" " * len(line) if line.lstrip().startswith("%") else line
                     for line in text.splitlines())


def parse_bib(text: str) -> list[Entry]:
    masked = mask_comments(text)
    entries: list[Entry] = []
    for m in ENTRY_RE.finditer(masked):
        if m.group(1).lower() in ("comment", "preamble", "string"):
            continue
        start = m.start()
        depth, j = 0, masked.index("{", start)
        while j < len(masked):
            if masked[j] == "\\":
                j += 2
                continue
            if masked[j] == "{":
                depth += 1
            elif masked[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        entries.append(Entry(
            key=m.group(2), entrytype=m.group(1).lower(),
            text=text[start:j + 1],                  # exact original slice
            fields=parse_fields(masked[start:j + 1]),  # comments ignored
        ))
    return entries


def git_clean(path: Path) -> tuple[bool, str]:
    try:
        out = subprocess.run(
            ["git", "-C", str(path.parent), "status", "--porcelain", "--", path.name],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"could not run git: {exc}"
    if out.returncode != 0:
        return False, "central bib is not in a git repository"
    return (not out.stdout.strip()), out.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", help="project directory holding references-local.bib")
    ap.add_argument("--local", help="explicit path to the local bib")
    ap.add_argument("--central", default=str(CENTRAL), help="central bib (default: house style)")
    ap.add_argument("--update", action="append", default=[], metavar="KEY",
                    help="deliberately replace this central entry with the local version")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="write even if the central bib has uncommitted changes")
    args = ap.parse_args()

    central_path = Path(args.central).resolve()
    if args.local:
        local_path = Path(args.local).resolve()
    else:
        base = Path(args.project).resolve() if args.project else Path.cwd()
        local_path = base / "references-local.bib"
    if not local_path.is_file():
        print(f"[push-bib] no local bib at {local_path}")
        return 0
    if not central_path.is_file():
        sys.exit(f"[push-bib] no central bib at {central_path}")

    central_text = central_path.read_text(encoding="utf-8")
    central = parse_bib(central_text)
    local = parse_bib(local_path.read_text(encoding="utf-8"))
    if not local:
        print(f"[push-bib] {local_path.name} holds no entries")
        return 0

    by_key = {e.key.lower(): e for e in central}
    for e in central:
        for a in e.aliases:
            by_key.setdefault(a.lower(), e)
    by_doi: dict[str, Entry] = {}
    by_title: dict[tuple[str, str], Entry] = {}
    for e in central:
        if e.doi:
            by_doi.setdefault(e.doi, e)
        if e.title_year:
            by_title.setdefault(e.title_year, e)

    updates = {k.lower() for k in args.update}
    appended, refused, updated = [], [], []

    for e in local:
        hit_key = by_key.get(e.key.lower())
        hit_doi = by_doi.get(e.doi) if e.doi else None
        hit_title = by_title.get(e.title_year) if e.title_year else None

        if e.key.lower() in updates:
            if not hit_key:
                refused.append((e, "no central entry with this key to update", None))
            else:
                updated.append((e, hit_key))
            continue
        if hit_key:
            refused.append((e, "key already in the central bib", hit_key.key))
        elif hit_doi:
            refused.append((e, f"same DOI ({e.doi}) under a different key", hit_doi.key))
        elif hit_title:
            refused.append((e, "same title and year under a different key", hit_title.key))
        else:
            appended.append(e)

    if args.json:
        print(json.dumps({
            "local": str(local_path), "central": str(central_path),
            "append": [e.key for e in appended],
            "update": [[e.key, c.key] for e, c in updated],
            "refuse": [{"key": e.key, "reason": r, "central": c} for e, r, c in refused],
        }, indent=2))
        return 1 if refused else 0

    print(f"[push-bib] {local_path}")
    print(f"           -> {central_path}  ({len(central)} entries)\n")
    for e in appended:
        print(f"  NEW      {e.key}")
    for e, c in updated:
        print(f"  UPDATE   {e.key}  (replaces central entry {c.key})")
    for e, reason, c in refused:
        print(f"  REFUSED  {e.key}: {reason}")
        if c:
            print(f"           cite {c} instead, or re-run with --update {c}")
    if not (appended or updated or refused):
        print("  (nothing to do)")

    if appended or updated:
        if not args.dry_run:
            clean, detail = git_clean(central_path)
            if not clean and not args.allow_dirty:
                print(f"\n[push-bib] refusing to write: central bib has uncommitted changes")
                print(f"           {detail or 'not in a git repository'}")
                print("           commit or stash first so this write is recoverable,")
                print("           or pass --allow-dirty")
                return 2
            new_text = central_text
            for e, c in updated:
                new_text = new_text.replace(c.text, e.text, 1)
            if appended:
                if not new_text.endswith("\n"):
                    new_text += "\n"
                new_text += "\n" + "\n\n".join(e.text for e in appended) + "\n"
            central_path.write_text(new_text, encoding="utf-8")
            local_path.write_text(LOCAL_HEADER, encoding="utf-8")
            print(f"\n[push-bib] wrote {len(appended)} new, {len(updated)} updated; "
                  f"cleared {local_path.name}")
        else:
            print("\n[push-bib] dry run, nothing written")

    if refused:
        print(f"\n[push-bib] {len(refused)} entr{'y' if len(refused)==1 else 'ies'} refused. "
              "Nothing about them was changed centrally.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
