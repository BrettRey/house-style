#!/usr/bin/env python3
"""
Cold-read extraction gate: does a hostile, half-blind reader find the PROBLEM?

The load-bearing failure behind Brett's recent rejections was not terminology,
it was that the reader could not find the problem the paper solves or the
contribution it makes. Referees and desk editors do not reconstruct a paper
from the whole text; they skim the opening, and if the problem isn't there,
they bounce. A charitable full-paper LLM review misses this every time,
because it reconstructs from everything it's given.

This tool forces the real reading condition:
  extract  -- pull ONLY what a desk editor sees (title + abstract + first ~2
              pages, de-macroed to plain text), and emit the hostile-editor
              extraction prompt. Feed that to N independent readers (ideally
              different models; use agent_review or fresh subagents).
  score    -- take the readers' JSON answers and report the scorecard: which
              of {problem, debate, gap, contribution} came back MISSING, the
              advance/reject tally, and the problem/contribution statements
              side by side so divergence is visible. PASS/FAIL.

A paper FAILS the gate if any reader marks the problem or contribution MISSING,
or a majority reject, or the readers' problem statements diverge (eyeball).
Convergent cold reads that all advance = the problem is legible.

Usage:
    python coldread.py extract main.tex [--follow-inputs] [--words 900]
    python coldread.py extract main.tex --prompt-only > coldread-prompt.txt
    python coldread.py score reader1.json reader2.json reader3.json

Reader JSON schema (what each cold reader returns):
    {"problem": "...|MISSING", "debate": "...|MISSING", "gap": "...|MISSING",
     "contribution": "...|MISSING", "decision": "advance|reject", "note": "..."}
"""

import argparse
import json
import re
import sys
from pathlib import Path

HOSTILE_PROMPT = """\
You are a desk editor at a selective journal with forty submissions this week \
and a 12% acceptance rate. You will read ONLY the opening below -- the title, \
abstract, and first pages. You will NOT be charitable, you will NOT reconstruct \
a generous version, and you will NOT give the benefit of the doubt. If something \
is not on the page, it is missing.

State each of the following in ONE sentence, or write exactly MISSING if the \
opening does not make it plain:
  problem      -- the specific problem this paper solves
  debate       -- the named debate or literature it enters
  gap          -- what is wrong or absent in existing approaches
  contribution -- what this paper adds

Then decide: advance to review, or reject at desk?

Return ONLY JSON, no prose:
{"problem": "...", "debate": "...", "gap": "...", "contribution": "...", \
"decision": "advance" or "reject", "note": "one blunt sentence to the author"}

=== OPENING ===
"""

UNWRAP = ["term", "mention", "emph", "textit", "textbf", "enquote", "olang",
          "textsc", "og", "cg", "textsubscript"]
DROP_WITH_ARG = ["footnote", "label", "cite", "citep", "citet", "textcite",
                 "parencite", "citealt", "citeauthor", "pageref", "ref",
                 "index", "marginpar"]
STRIP_ENVS = ["equation", "align", "align*", "gather", "gather*", "tabular",
              "tabular*", "tabularx", "array", "tikzpicture", "figure",
              "table", "verbatim"]


def read_source(path, follow, _seen=None):
    if _seen is None:
        _seen = set()
    rp = path.resolve()
    if rp in _seen:
        return ""
    _seen.add(rp)
    text = path.read_text(encoding="utf-8", errors="replace")
    if not follow:
        return text

    def _inline(m):
        cand = path.parent / m.group(1).strip()
        if cand.suffix != ".tex":
            cand = cand.with_suffix(".tex")
        return read_source(cand, True, _seen) if cand.exists() else ""

    return re.sub(r"\\(?:input|include)\{([^}]+)\}", _inline, text)


def strip_comments(t):
    return re.sub(r"(?<!\\)%.*", "", t)


def remove_macro_with_arg(text, macro):
    """Delete \\macro{...} including any optional [..] and balanced {..}."""
    out, i = [], 0
    pat = re.compile(r"\\" + macro + r"\b\s*")
    while i < len(text):
        m = pat.search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        j = m.end()
        if j < len(text) and text[j] == "[":          # optional arg
            depth = 1; j += 1
            while j < len(text) and depth:
                depth += text[j] == "["; depth -= text[j] == "]"; j += 1
        if j < len(text) and text[j] == "{":
            depth = 1; j += 1
            while j < len(text) and depth:
                depth += text[j] == "{"; depth -= text[j] == "}"; j += 1
        i = j
    return "".join(out)


def unwrap_macro(text, macro):
    """Replace \\macro{content} with content (keep the words)."""
    out, i = [], 0
    pat = re.compile(r"\\" + macro + r"\b\s*\{")
    while i < len(text):
        m = pat.search(text, i)
        if not m:
            out.append(text[i:]); break
        out.append(text[i:m.start()])
        j = m.end(); depth = 1; start = j
        while j < len(text) and depth:
            depth += text[j] == "{"; depth -= text[j] == "}"; j += 1
        out.append(text[start:j - 1]); i = j
    return "".join(out)


def demacro(text):
    for env in STRIP_ENVS:
        text = re.sub(r"\\begin\{" + re.escape(env) + r"\*?\}.*?\\end\{"
                      + re.escape(env) + r"\*?\}", " ", text, flags=re.DOTALL)
    for m in DROP_WITH_ARG:
        text = remove_macro_with_arg(text, m)
    for _ in range(3):                       # nested \term{\emph{..}}
        for m in UNWRAP:
            text = unwrap_macro(text, m)
    text = re.sub(r"\\(sub)*section\*?\s*\{([^}]*)\}", r"\n\n\2. ", text)
    text = re.sub(r"\\[a-zA-Z]+\*?", " ", text)   # remaining bare commands
    text = text.replace("{", " ").replace("}", " ").replace("~", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_opening(path, follow, words):
    raw = strip_comments(read_source(path, follow))
    title_m = re.search(r"\\title\s*\{", raw)
    title = ""
    if title_m:
        j = title_m.end(); depth = 1; s = j
        while j < len(raw) and depth:
            depth += raw[j] == "{"; depth -= raw[j] == "}"; j += 1
        title = demacro(raw[s:j - 1])
    ab = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", raw, re.DOTALL)
    abstract = demacro(ab.group(1)) if ab else ""
    after = raw[ab.end():] if ab else raw[re.search(r"\\begin\{document\}", raw).end():] \
        if re.search(r"\\begin\{document\}", raw) else raw
    body = demacro(after)
    body_words = body.split()
    body = " ".join(body_words[:words])
    truncated = len(body_words) > words
    return title, abstract, body, truncated


def cmd_extract(a):
    p = Path(a.file)
    if not p.exists():
        print(f"error: {a.file} not found", file=sys.stderr); return 2
    title, abstract, body, trunc = extract_opening(p, a.follow_inputs, a.words)
    opening = (f"TITLE: {title or '(none found)'}\n\n"
               f"ABSTRACT:\n{abstract or '(none found)'}\n\n"
               f"BODY (first ~{a.words} words{'; truncated' if trunc else ''}):\n{body}")
    if a.prompt_only:
        print(HOSTILE_PROMPT + opening)
    else:
        print("=== reader-facing opening (what a desk editor sees) ===\n")
        print(opening)
        print("\n=== to run the gate ===")
        print("Feed the hostile-editor prompt (coldread.py extract <f> --prompt-only) to")
        print("3+ independent readers, ideally different models (agent_review or fresh")
        print("subagents). Collect each reader's JSON, then: coldread.py score r1 r2 r3")
    return 0


def cmd_score(a):
    readers = []
    for f in a.readers:
        try:
            readers.append(json.loads(Path(f).read_text()))
        except Exception as e:
            print(f"error reading {f}: {e}", file=sys.stderr); return 2
    if not readers:
        print("no readers", file=sys.stderr); return 2
    elems = ["problem", "debate", "gap", "contribution"]
    print(f"=== cold-read scorecard ({len(readers)} readers) ===\n")
    missing = {e: 0 for e in elems}
    for e in elems:
        for r in readers:
            if str(r.get(e, "MISSING")).strip().upper() == "MISSING":
                missing[e] += 1
    for e in elems:
        mark = "FAIL" if (e in ("problem", "contribution") and missing[e]) else ""
        print(f"  {e:<13} MISSING for {missing[e]}/{len(readers)} readers   {mark}")
    advances = sum(1 for r in readers if str(r.get("decision", "")).lower() == "advance")
    print(f"\n  decision: {advances}/{len(readers)} advance, "
          f"{len(readers) - advances} reject")
    print("\n  problem statements (eyeball for divergence):")
    for i, r in enumerate(readers, 1):
        print(f"    R{i}: {str(r.get('problem', 'MISSING'))[:100]}")
    print("  contribution statements:")
    for i, r in enumerate(readers, 1):
        print(f"    R{i}: {str(r.get('contribution', 'MISSING'))[:100]}")
    fail = (missing["problem"] or missing["contribution"]
            or advances <= len(readers) / 2)
    print(f"\n  GATE: {'FAIL' if fail else 'PASS'}"
          + ("  -- problem/contribution not legible to a cold reader, or majority reject."
             if fail else "  -- cold readers found the problem and advanced."))
    print("  (Divergent problem statements above are also a FAIL even if nothing is MISSING.)")
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser(description="Cold-read extraction gate.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("extract")
    ex.add_argument("file")
    ex.add_argument("--follow-inputs", action="store_true")
    ex.add_argument("--words", type=int, default=900)
    ex.add_argument("--prompt-only", action="store_true")
    sc = sub.add_parser("score")
    sc.add_argument("readers", nargs="+")
    a = ap.parse_args()
    return cmd_extract(a) if a.cmd == "extract" else cmd_score(a)


if __name__ == "__main__":
    sys.exit(main())
