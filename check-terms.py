#!/usr/bin/env python3
"""
Terminology-legibility audit for Brett Reynolds' LaTeX papers.

Catches the specific failure that shipped to JSO (and that recurs across
Claude and Codex drafts): a specialized term used in reader-facing prose --
especially in the abstract -- before, or without, any reader-facing gloss.

It reports, for every marked concept (\\term{...}) and every word on a standing
watchlist of terms that escape the macro (projectible, profile, anchoring,
cascade, uptake, ...):
  - the region of FIRST use (title / abstract / body), abstract counted as
    position zero;
  - whether a gloss-shape accompanies that first use (a parenthetical, a
    definitional cue, or a nearby citation);
  - the total occurrence count.

It cannot judge whether a gloss is any *good* -- that's the paraphrase test and
a human. It reliably catches "used in the abstract, defined in section 2."

Audience calibration: a term the target reader OWNS is not jargon. Pass
--free term1,term2 (or a planning/terms.md ledger) to exempt terms the venue's
readers own. A phil-of-science venue owns 'projectible'; a corpus venue does
not. That list is set once, at venue-selection time.

Usage:
    python check-terms.py main.tex
    python check-terms.py main.tex --follow-inputs        # inline \\input/\\include
    python check-terms.py main.tex --free projectible,projectibility,homeostatic
    python check-terms.py main.tex --ledger planning/terms.md
    python check-terms.py main.tex --gate                 # exit 1 on any flag

Exit status: 0 = clean (or report mode); 1 = flags found under --gate; 2 = error.

This is a linter, not a judge. Passing it is necessary, not sufficient.
"""

import argparse
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# WATCHLIST -- terms that escape the \term{} macro and recur unglossed.
# THIS IS WHERE PUSHBACKS BECOME PERMANENT. When Brett (or a reviewer) flags a
# term for being dropped in bare, add it here once; it is then checked forever.
# Entries are matched case-insensitively on word boundaries; multiword phrases
# are matched as phrases. Audience-owned terms are exempted per-paper via
# --free / --ledger, so this list is the union across all audiences.
# --------------------------------------------------------------------------
WATCHLIST = [
    "projectible", "projectibility", "projection",
    "profile", "anchoring", "cascade", "uptake", "conferral",
    "homeostatic", "homeostasis", "stabilizer", "stabiliser",
    "life-cycle", "lifecycle",
    "causal-normative network", "social cascade",
]

# Gloss cues near a first use that count as "reader is given help here."
GLOSS_CUE_RE = re.compile(
    r"(\([^)]{3,}\)"                                   # a parenthetical
    r"|\\citep?\{|\\textcite\{|\\parencite\{"          # a citation
    r"|\b(?:that is|i\.e\.|namely|by which (?:i|we) mean"
    r"|defined as|we call|call this|refers? to|is the|is a|are the|are)\b)",
    re.IGNORECASE,
)

# Environments whose contents are not reader-facing argument prose.
STRIP_ENVS = ["equation", "align", "align*", "gather", "gather*", "tabular",
              "tabular*", "tabularx", "array", "tikzpicture", "verbatim"]


def read_source(path: Path, follow_inputs: bool, _seen=None):
    """Return the .tex source, optionally inlining \\input/\\include."""
    if _seen is None:
        _seen = set()
    rp = path.resolve()
    if rp in _seen:
        return ""
    _seen.add(rp)
    text = path.read_text(encoding="utf-8", errors="replace")
    if not follow_inputs:
        return text

    def _inline(m):
        target = m.group(1).strip()
        cand = path.parent / target
        if cand.suffix != ".tex":
            cand = cand.with_suffix(".tex")
        if cand.exists():
            return read_source(cand, True, _seen)
        return ""

    return re.sub(r"\\(?:input|include)\{([^}]+)\}", _inline, text)


def strip_comments(text: str) -> str:
    # Remove from an unescaped % to end of line.
    return re.sub(r"(?<!\\)%.*", "", text)


def strip_heavy_envs(text: str) -> str:
    for env in STRIP_ENVS:
        text = re.sub(r"\\begin\{" + re.escape(env) + r"\}.*?\\end\{"
                      + re.escape(env) + r"\}", " ", text, flags=re.DOTALL)
    return text


def blank_preamble(text: str) -> str:
    """Blank everything before \\begin{document} (pdfkeywords, hypersetup, etc.)
    while preserving line numbers, so metadata never counts as a reader-facing
    first use. The title is captured separately, from the un-blanked source."""
    m = re.search(r"\\begin\{document\}", text)
    if not m:
        return text
    head = text[:m.start()]
    return ("\n" * head.count("\n")) + text[m.start():]


def brace_contents(text: str, macro: str):
    """Yield the brace-balanced argument of every \\macro{...}."""
    out = []
    for m in re.finditer(r"\\" + macro + r"\s*\{", text):
        i = m.end()
        depth, start = 1, i
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        out.append((start, text[start:i - 1]))
    return out


def line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def snippet(text: str, idx: int, width: int = 70) -> str:
    s = max(0, idx - 10)
    frag = re.sub(r"\s+", " ", text[s:idx + width]).strip()
    return frag[:width + 20]


def find_regions(text: str):
    """Return (title_span, abstract_span, body_start_idx)."""
    title = brace_contents(text, "title")
    title_text = title[0][1] if title else ""
    ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.DOTALL)
    abstract_text = ab.group(1) if ab else ""
    if ab:
        body_start = ab.end()
    else:
        doc = re.search(r"\\begin\{document\}", text)
        body_start = doc.end() if doc else 0
    return title_text, abstract_text, body_start


def gloss_near(text: str, idx: int, window: int = 240) -> bool:
    return bool(GLOSS_CUE_RE.search(text[idx: idx + window]))


def norm(term: str) -> str:
    return re.sub(r"\s+", " ", term).strip().lower()


def collect_terms(raw_body: str, title_text: str, abstract_text: str):
    """Build {display_term: {'variants': set, 'is_marked': bool}}."""
    terms = {}

    def add(display, marked):
        key = norm(display)
        entry = terms.setdefault(key, {"display": display, "marked": marked})
        if marked:
            entry["marked"] = True

    for _, content in brace_contents(raw_body, "term"):
        # \term can wrap markup; take its plain text.
        plain = re.sub(r"\\[a-zA-Z]+\*?|\{|\}", "", content).strip()
        if plain:
            add(plain, marked=True)
    for w in WATCHLIST:
        add(w, marked=False)
    return terms


def first_use(term_key, marked, full_stripped, title_text, abstract_text, body_start):
    """Return (region, char_idx_in_full, glossed_bool, count)."""
    # Build a word/phrase regex for the term (allow trailing plural s / ies).
    esc = re.escape(term_key).replace(r"\ ", r"\s+")
    if marked:
        pat = re.compile(r"\\term\s*\{[^}]*" + esc + r"[^}]*\}", re.IGNORECASE)
        word = re.compile(esc, re.IGNORECASE)
    else:
        word = re.compile(r"(?<![\w-])" + esc + r"(?:s|es|ity|ility)?(?![\w-])",
                          re.IGNORECASE)
        pat = word

    count = len(word.findall(full_stripped))
    # Region of first use: title (-2) < abstract (0) < body.
    if word.search(title_text):
        region = "title"
    elif word.search(abstract_text):
        region = "abstract"
    else:
        region = "body"
    m = word.search(full_stripped, 0)
    if not m:
        return None
    idx = m.start()
    # If first body-region use, prefer the first occurrence at/after body_start
    # only when it is not present in front matter.
    glossed = gloss_near(full_stripped, m.end())
    return region, idx, glossed, count


def main():
    ap = argparse.ArgumentParser(description="Terminology-legibility audit.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--follow-inputs", action="store_true",
                    help="inline \\input/\\include before auditing")
    ap.add_argument("--free", default="",
                    help="comma-separated terms the target reader OWNS (exempt)")
    ap.add_argument("--ledger", default="",
                    help="planning/terms.md; rows marked free are exempted")
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if any term is flagged")
    args = ap.parse_args()

    free = {norm(t) for t in args.free.split(",") if t.strip()}
    if args.ledger:
        lp = Path(args.ledger)
        if lp.exists():
            for line in lp.read_text(encoding="utf-8", errors="replace").splitlines():
                if "|" in line and re.search(r"\bfree\b", line, re.IGNORECASE):
                    cell = line.split("|")[1].strip() if line.split("|") else ""
                    cell = re.sub(r"[`*]", "", cell)
                    if cell:
                        free.add(norm(cell))

    any_flag = False
    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"error: {f} not found", file=sys.stderr)
            return 2
        raw = strip_comments(read_source(p, args.follow_inputs))
        full = strip_heavy_envs(raw)
        # Title comes from the preamble; capture it before blanking. Everything
        # else (abstract, body) is searched with the preamble blanked so PDF
        # metadata never registers as a first use.
        title_text, _, _ = find_regions(full)
        stripped = blank_preamble(full)
        _, abstract_text, body_start = find_regions(stripped)

        terms = collect_terms(stripped, title_text, abstract_text)
        rows = []
        for key, meta in terms.items():
            fu = first_use(key, meta["marked"], stripped,
                           title_text, abstract_text, body_start)
            if not fu:
                continue
            region, idx, glossed, count = fu
            if count == 0:
                continue
            exempt = key in free
            # Flag: first use in front matter (title/abstract) without a gloss,
            # or a watchlist term never glossed at first use anywhere.
            front = region in ("title", "abstract")
            flagged = (not exempt) and (not glossed) and (front or not meta["marked"])
            rows.append({
                "term": meta["display"], "region": region, "line": line_of(stripped, idx),
                "glossed": glossed, "count": count, "exempt": exempt,
                "flagged": flagged, "snippet": snippet(stripped, idx),
            })

        rows.sort(key=lambda r: (not r["flagged"],
                                 {"title": 0, "abstract": 1, "body": 2}[r["region"]],
                                 -r["count"]))
        print(f"\n=== terminology audit: {f} ===")
        print(f"{'flag':<5}{'term':<32}{'first use':<12}{'gloss':<7}{'n':<4}")
        for r in rows:
            flag = "FLAG" if r["flagged"] else ("free" if r["exempt"] else "")
            fu = f"{r['region']}:{r['line']}"
            g = "yes" if r["glossed"] else "NO"
            print(f"{flag:<5}{r['term'][:31]:<32}{fu:<12}{g:<7}{r['count']:<4}")
            if r["flagged"]:
                print(f"       ^ {r['snippet']}")
                any_flag = True

        flags = [r for r in rows if r["flagged"]]
        print(f"\n{len(flags)} flag(s): term used unglossed in front matter, "
              f"or watchlist term never glossed at first use.")

    if args.gate and any_flag:
        print("\nGATE: terminology audit failed. Gloss flagged terms at first "
              "use, or mark them free for this venue in planning/terms.md.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
