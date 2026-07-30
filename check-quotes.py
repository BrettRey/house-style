#!/usr/bin/env python3
"""
check-quotes.py -- verify that every direct quotation in a LaTeX manuscript
appears verbatim in the source it is attributed to.

Origin: a journal rejected a manuscript under a blanket citation-integrity
policy after the editors' own spot-check found quotations that were paraphrases
wrapped in quote marks with a page cite. A full audit then found that of the
nine quotations checkable against sources held locally, one was clean. Every
framing, style, terminology and legibility gate in the workflow had passed.
This defect is invisible to all of them, and it is the signature failure mode
of LLM-assisted drafting: the model reproduces the sense of a passage and
supplies plausible words for it. If you write with a model, assume every
quotation is a paraphrase until a machine has matched it character for
character against the source.

What this does NOT do: prove a quotation genuine. A PASS means the string was
found in a local copy of the source. Page numbers, editions and quotations
from sources not held locally still need a human with the book.

Two hard-won guards:

  * A degraded text extraction reports UNCHECKABLE, never MISSING. A
    mirror-reversed OCR file in literature/ (each word character-reversed)
    returns zero hits for ordinary English words, so a naive checker would
    accuse the author of fabricating a quotation that is really there. False
    accusations are as corrosive here as false quotations.

  * Matching is whitespace- and hyphenation-normalized. PDF text extraction
    breaks words across lines, so a raw substring test produces false
    negatives on perfectly good quotations.

Known limitation: a file can clear the prose-density floor and still be
scrambled word-by-word (boyd1999.md reads "kind may be natural somediscipline
or disciplinary matrix"). Such a file yields MISSING for a quotation that is
really in the source. So MISSING means "look at this", never "fabricated".
Confirm every MISSING against the page before drawing any conclusion.

Usage:
    python3 check-quotes.py main.tex [--lit literature] [--gate]

Exit codes: 0 all quotations pass or are only UNCHECKABLE; 1 with --gate if
any quotation is MISSING.
"""

import argparse
from collections import Counter
import re
import subprocess
import sys
from pathlib import Path

CITE_RE = re.compile(
    r'\\(?:cite[pt]?|textcite|parencite|citeyear|citealt)\s*'
    r'(?:\[(?P<pre>[^\]]*)\])?\s*(?:\[(?P<post>[^\]]*)\])?\s*\{(?P<keys>[^}]+)\}'
)
# Function words whose combined density tells prose from a broken extraction.
# "the " alone is too crude: Libert (2012) quotes Turkish, French and Latin at
# length and scores 48.6 on "the " alone, which a single-word floor read as a
# broken file and reported as UNCHECKABLE. The mirror-reversed Ameka file
# scores near zero on all of these, which is the case the floor exists for.
# Every marker must be multi-letter and non-palindromic. Including "a " let the
# mirror-reversed Ameka file score 158 and pass, because a one-letter word
# reversed is itself: the guard would have been silently disabled.
PROSE_MARKERS = ("the ", "of ", "and ", "to ", "in ", "is ", "that ", "for ", "with ")
PROSE_DENSITY_FLOOR = 90.0   # summed markers per 10k chars
CONTEXT = 260                # chars of surrounding text scanned for a citation


QUOTE_MAP = str.maketrans({
    '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
    '\u2032': "'", '\u2033': '"', '`': "'", '\u2013': '-', '\u2014': '-',
})


def normalize(s):
    """
    Collapse whitespace, rejoin words broken by end-of-line hyphens, and fold
    quote marks and dashes to ASCII.

    The quote folding matters: LaTeX writes `expressions of feeling' where the
    source PDF has curly quotes, and without folding a perfectly good
    quotation containing an inner quote is reported MISSING.
    """
    s = s.translate(QUOTE_MAP)
    # LaTeX writes -- and --- where the source has en/em dashes; collapse runs so
    # a house-style dash inside a quotation still matches the printed source.
    s = re.sub(r'-{2,}', '-', s)
    s = s.replace('\u00ad', '')
    s = re.sub(r'-\s*\n\s*', '', s)
    s = re.sub(r'-\s{2,}', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def strip_markup(s):
    """Turn quoted LaTeX into the plain string a source would contain."""
    s = re.sub(r'\\(?:mention|term|textit|emph|textbf|textsc|mentionhead)\s*\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'\\dots\\?', '...', s)
    s = re.sub(r'\\[a-zA-Z]+\s*', '', s)
    s = s.replace('~', ' ').replace('\\', '')
    return normalize(s)


def extract_quotes(text):
    """Yield (line_no, quoted_text, start, end) for each \\enquote{...} span."""
    out = []
    i, n = 0, len(text)
    while i < n:
        j = text.find('\\enquote{', i)
        if j < 0:
            break
        k = j + len('\\enquote{')
        depth = 1
        while k < n and depth:
            if text[k] == '{' and text[k - 1] != '\\':
                depth += 1
            elif text[k] == '}' and text[k - 1] != '\\':
                depth -= 1
            k += 1
        body = text[j + 9:k - 1]
        out.append((text.count('\n', 0, j) + 1, body, j, k))
        i = k
    return out


def cites_for(text, q_start, q_end):
    """
    The citation that actually governs this quotation.

    House practice puts the cite immediately after the closing brace, so
    search forward first and take the nearest match; fall back to the nearest
    preceding one (integral "\\textcite[124]{wilkins1992} defines ..." form).
    Taking every citation within a fixed window instead attributes a quotation
    to whatever source the *next* sentence cites, which is how an early
    version of this script accused Bullokar's definition of being absent from
    Quirk.
    """
    ms = []
    after = list(CITE_RE.finditer(text, q_end, min(len(text), q_end + CONTEXT)))
    if after:
        ms.append(after[0])
    before = list(CITE_RE.finditer(text, max(0, q_start - CONTEXT), q_start))
    if before:
        ms.append(before[-1])
    out = []
    for m in ms:
        pages = (m.group('post') or m.group('pre') or '').strip()
        for k in m.group('keys').split(','):
            pair = (k.strip(), pages)
            if pair not in out:
                out.append(pair)
    return out


FOOTNOTE_TOKEN_RE = re.compile(r'\s\d{1,2}\s')


def _contains(src, quoted):
    """
    Substring test, retried with footnote markers removed from the source.

    pdftotext leaves superscript footnote markers inline, so Wilkins's
    definition extracts as "...with other word classes, 4 is (usually)
    monomorphemic...". A correct transcription of that sentence then fails an
    exact match. Digits are only stripped from the source on the retry, and
    only when standing alone, so numerals inside a quotation still have to
    match on the first pass.
    """
    low_src, low_q = src.lower(), quoted.lower()
    if low_q in low_src:
        return True
    return low_q in FOOTNOTE_TOKEN_RE.sub(' ', low_src)


FOLIO_RE = re.compile(r'(?<!\d)(\d{1,4})(?!\d)')


def build_page_map(raw):
    """
    Map printed page numbers to page text, so a cited page can be checked and
    not just the wording.

    Why this is needed: the wording check searches the whole document, so an
    exact quotation carrying the wrong page passes it. Two such errors shipped
    in one day (Cram cited to 62, actually 63; Boyd cited to 527, actually
    526), and a green run hid both.

    Method, from doing it by hand: printed folios appear in the running head or
    footer, so read the first and last ~80 characters of each page, collect
    every (pdf_index -> folio) observation, and take the most common
    difference. Real folios all agree on one offset; stray numbers scatter.
    Applying the winning offset then gives a folio for pages that print none
    (Poggi's do not), which hand-checking cannot do reliably.

    Returns {folio: normalized_text}, or None when the offset can't be trusted.
    """
    pages = raw.split('\f')
    if len(pages) < 3:
        return None
    votes = Counter()
    for i, p in enumerate(pages, 1):
        for m in FOLIO_RE.finditer(p[:80] + ' ' + p[-80:]):
            n = int(m.group(1))
            # A folio can't precede its own sheet, and 4-digit hits are years.
            if 1 <= n <= 4000 and n >= i - 1:
                votes[n - i] += 1
    if not votes:
        return None
    offset, support = votes.most_common(1)[0]
    # Demand real agreement: a handful of coincidences must not set the offset.
    if support < 3 or support < len(pages) * 0.10:
        return None
    return {i + offset: normalize(p) for i, p in enumerate(pages, 1)}


def parse_pages(spec):
    """Expand a cite's page field ('526', '63--69', '58, 92--97') to a set."""
    out = set()
    for part in re.split(r'[;,]', spec):
        part = part.strip().replace('--', '-').replace('–', '-')
        m = re.fullmatch(r'(\d{1,4})\s*-\s*(\d{1,4})', part)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if hi >= lo and hi - lo < 200:
                out.update(range(lo, hi + 1))
            continue
        m = re.fullmatch(r'(\d{1,4})', part)
        if m:
            out.add(int(m.group(1)))
    return out


def load_source(key, litdir):
    """
    Find a local copy of `key` and return (normalized_text, path, status).
    status is 'ok', 'degraded' or 'absent'.
    """
    stem = re.sub(r'[^a-z0-9]', '', key.lower())
    key_year = re.search(r'(1[6-9]\d\d|20\d\d)', key)
    key_year = key_year.group(1) if key_year else None
    # Surname-ish part of the key, for filename matching.
    key_name = re.sub(r'(1[6-9]\d\d|20\d\d).*$', '', stem) or stem
    cands = []
    for p in sorted(litdir.glob('*')):
        if p.suffix.lower() not in ('.md', '.txt', '.pdf'):
            continue
        norm = re.sub(r'[^a-z0-9]', '', p.stem.lower())
        if stem and stem in norm:
            cands.append(p)
            continue
        # Looser match, but the year must agree. Without this, keys sharing a
        # surname prefix collide: HuddlestonPullumReynolds2022 was matching
        # huddlestonpullum2002.pdf and the 2022 edition's quotations were
        # reported missing from the 2002 book.
        if len(key_name) >= 5 and key_name in norm:
            file_year = re.search(r'(1[6-9]\d\d|20\d\d)', norm)
            if key_year and file_year and file_year.group(1) != key_year:
                continue
            if key_year and not file_year:
                continue
            cands.append(p)
    if not cands:
        return [(None, None, 'absent', None)]
    # prefer a PDF: pdftotext keeps running heads and beats stale sidecar files
    cands.sort(key=lambda p: (p.suffix.lower() != '.pdf', len(p.name)))
    usable = []
    for p in cands:
        try:
            if p.suffix.lower() == '.pdf':
                raw = subprocess.run(['pdftotext', '-layout', str(p), '-'],
                                     capture_output=True, text=True, timeout=300).stdout
            else:
                raw = p.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        if len(raw) < 500:
            continue
        low = raw.lower()
        density = sum(low.count(w) for w in PROSE_MARKERS) / len(raw) * 10000
        if density < PROSE_DENSITY_FLOOR:
            continue          # unusable extraction; try the next candidate
        pages = build_page_map(raw) if p.suffix.lower() == '.pdf' else None
        usable.append((normalize(raw), p, 'ok', pages))
    if usable:
        return usable
    return [(None, cands[0], 'degraded', None)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('texfile')
    ap.add_argument('--lit', default='literature')
    ap.add_argument('--gate', action='store_true', help='exit 1 if any quotation is MISSING')
    args = ap.parse_args()

    tex = Path(args.texfile)
    litdir = Path(args.lit)
    if not tex.exists():
        print(f'not found: {tex}')
        return 2
    text = tex.read_text(encoding='utf-8')
    if not litdir.is_dir():
        print(f'no source directory at {litdir}; nothing can be checked')
        return 2

    rows, cache = [], {}
    for line_no, body, q_start, q_end in extract_quotes(text):
        quoted = strip_markup(body)
        pairs = [(k, p) for k, p in cites_for(text, q_start, q_end) if p]  # page-cited = a source claim
        if not pairs:
            rows.append(('SCAREQUOTE', line_no, quoted, '', ''))
            continue
        # Test every plausibly-cited source and pass on any hit. Attribution is
        # ambiguous when an integral cite precedes a quotation and the next
        # sentence's cite follows it, and a quotation is often legitimately
        # reproduced in a second source (Ameka block-quotes Coulmas; Gehweiler
        # block-quotes Wilkins). Reporting MISSING on attribution ambiguity
        # would manufacture the false accusations this script exists to avoid,
        # so the bar for MISSING is: absent from EVERY usable candidate.
        results = []
        # One key can match several files in literature/, and they are not always
        # the same work: potts2007 matched both "Potts - 2007 - The expressive
        # dimension.pdf" and "potts2007dimensions.pdf", which is a 2004 draft
        # titled "The dimensions of quotation". The shortest-name tie-break picked
        # the wrong one and reported two genuine quotations MISSING. So the
        # "absent from EVERY usable candidate" rule below applies per file too,
        # not just per cited key.
        for key, pages in pairs:
            if key not in cache:
                cache[key] = load_source(key, litdir)
            label = f'{key} p.{pages}'
            for src, path, status, pmap in cache[key]:
                if status == 'absent':
                    results.append(('NOSOURCE', label, 'no local copy'))
                elif status == 'degraded':
                    results.append(('UNCHECKABLE', label,
                                    f'{path.name} is not usable prose (re-extract it)'))
                elif quoted and _contains(src, quoted):
                    cited = parse_pages(pages)
                    if pmap and cited:
                        on = sorted(f for f, txt in pmap.items() if _contains(txt, quoted))
                        if on and not (set(on) & cited):
                            shown = ', '.join(str(f) for f in on[:4])
                            results.append(('PAGEOFF', label,
                                            f'wording is right but it is on p. {shown}, '
                                            f'not {pages} ({path.name})'))
                        else:
                            results.append(('PASS', label, path.name))
                    else:
                        results.append(('PASS', label, path.name))
                else:
                    results.append(('MISSING', label, f'not found in {path.name}'))
        # PAGEOFF ranks below UNCHECKABLE/NOSOURCE on purpose. A quotation often
        # carries two candidate cites (its own, and the next clause's), and is
        # often reproduced verbatim inside a second source. If the source that was
        # actually cited isn't held locally, a page disagreement with some other
        # book that happens to quote the same sentence says nothing about the
        # manuscript. Coulmas's definition, cited to Coulmas 2--3 and unheld, was
        # reported PAGEOFF against a neighbouring Ameka cite because Ameka
        # reproduces it at 108. Silence beats a false accusation.
        rank = {'PASS': 0, 'UNCHECKABLE': 1, 'NOSOURCE': 2, 'PAGEOFF': 3, 'MISSING': 4}
        results.sort(key=lambda r: rank[r[0]])
        best = results[0]
        note = best[2]
        if best[0] in ('MISSING', 'PAGEOFF') and len(results) > 1:
            note += ' (checked: ' + ', '.join(r[1] for r in results) + ')'
        rows.append((best[0], line_no, quoted, best[1], note))

    order = {'MISSING': 0, 'PAGEOFF': 1, 'UNCHECKABLE': 2, 'NOSOURCE': 3, 'PASS': 4, 'SCAREQUOTE': 5}
    rows.sort(key=lambda r: (order[r[0]], r[1]))
    counts = {}
    for r in rows:
        counts[r[0]] = counts.get(r[0], 0) + 1

    print(f'\nQuotation check: {tex}')
    print('  ' + '  '.join(f'{k}={v}' for k, v in sorted(counts.items(), key=lambda kv: order[kv[0]])))
    print()
    for status, line_no, quoted, cite, note in rows:
        if status == 'SCAREQUOTE':
            continue
        snippet = quoted if len(quoted) <= 88 else quoted[:85] + '...'
        print(f'  {status:<12} l.{line_no:<5} {cite:<26} {snippet}')
        if note and status != 'PASS':
            print(f'  {"":<12} {"":<7} -> {note}')
    if counts.get('SCAREQUOTE'):
        print(f'\n  ({counts["SCAREQUOTE"]} quoted spans carry no page cite; '
              'treated as scare quotes or mentions, not source claims)')
    if counts.get('PAGEOFF'):
        print('\n  PAGEOFF means the wording is genuinely in the source but not on the page')
        print('  cited. Usually an off-by-one from reading a page footer as the next page\'s')
        print('  head, or a quotation taken from a different edition. Fix the page, and')
        print('  check the edition before assuming it is only a typo.')
    if counts.get('MISSING'):
        print('\n  MISSING means the string is absent from a source that extracted cleanly.')
        print('  Read the page before concluding anything: check the edition, and check')
        print('  whether the source quotes it from somewhere else.')
    if counts.get('UNCHECKABLE') or counts.get('NOSOURCE'):
        print('\n  UNCHECKABLE/NOSOURCE are not clean bills of health. "Not held locally"')
        print('  is not "unverifiable": try a content index (mdfind), the quotation as')
        print('  reproduced inside a source you do hold, and open repositories (Oxford')
        print('  Text Archive, Internet Archive, institutional repositories) before')
        print('  filing a negative.')

    if args.gate and (counts.get('MISSING') or counts.get('PAGEOFF')):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
