#!/usr/bin/env python3
"""
Markdown house-style linter.

Flags violations of writing-style.md rules in markdown prose:
- em-dashes
- paragraphs over 100 words
- AI high-signal vocabulary
- AI adverbs and hackneyed adverbs
- AI tic phrases
- overuse of watch-list words

Usage: check-style-md.py <file.md>
"""
import sys
import re
from pathlib import Path
from collections import Counter

CUT_HIGH_SIGNAL = {
    "delve", "delves", "delving", "underscores", "underscore", "underscoring",
    "showcase", "showcasing", "testament", "tapestry", "realm", "vibrant",
    "pivotal", "groundbreaking", "transformative", "profound", "paramount",
    "seamless", "robust", "comprehensive", "curated", "crafted",
    "whimsical", "quirky", "elegant", "meticulous", "invaluable",
    "noteworthy", "ever-evolving", "multifaceted", "holistic", "nuanced",
    "leverage", "leveraging", "utilize", "utilizing",
}
HIGH_SIGNAL_REPEAT_THRESHOLD = 2

WATCH_OVERUSE = {
    "essential", "significant", "key", "valuable", "meaningful", "diverse",
    "complex", "creative", "critical", "potential", "findings", "crucial",
    "landscape", "enhance", "navigate", "journey", "streamline", "dynamic",
}

AI_ADVERBS = {
    "additionally", "aptly", "creatively", "moreover", "successfully", "overall",
}

HACKNEYED_ADVERBS = {
    "moreover", "furthermore",
}

AI_TIC_PHRASES = [
    "load-bearing",
    "load-bearing claim",
    "let me refine your claim",
    "let me refine your load-bearing claim",
    "the one place i'd still push",
    "because i think it matters",
    "you're doing zero moves",
    "the gap is what's interesting",
    "the tell is",
    "content-clothes",
    "the content isn't actually there",
    "structural spine",
    "pull one, and the other goes inert",
    "doing the heavy lifting",
    "deserves the weight",
    "it is important to note",
    "it's important to note",
    "it should be noted",
    "it's worth noting",
    "it is worth noting",
    "complex and multifaceted",
    "challenging traditional paradigms",
    "in conclusion",
    "in summary",
    "in a world where",
    "in today's fast-paced world",
    "in the ever-evolving landscape",
    "at the intersection of",
    "a treasure trove of",
    "deep dive",
    "the rise of",
    "step-by-step",
    "stands as a testament to",
    "symbol of resilience",
    "watershed moment",
    "rich cultural heritage",
    "rich history",
    "key turning point",
    "dynamic hub",
    "plays a crucial role",
    "plays a significant role",
    "plays a vital role",
    "underscores the importance",
    "leaves a lasting impact",
    "i hope this message finds you well",
    "i hope this helps",
    "let me know if you need anything else",
    "of course!",
    "certainly!",
    "great question",
]

PRESENT_SELF_REFERENCE_RE = re.compile(
    r"\bthe present\s+"
    r"(author|paper|study|article|work|analysis|account|argument|proposal|chapter|section)\b",
    re.IGNORECASE,
)
REAL_WORK_METAPHOR_RE = re.compile(
    r"\b(?:do|does|did|doing)\s+real\s+work\b",
    re.IGNORECASE,
)
THE_X_IS_Y_OPENER_RE = re.compile(
    r"^The\s+.{1,80}?\s+(?:is|are|was|were)\b"
)
THE_X_IS_Y_OPENER_THRESHOLD = 3
ARGUMENT_OBJECT_OPENER_RE = re.compile(
    r"^(?:The|This|That)\s+(?:[a-z][a-z-]*\s+){0,3}"
    r"(?:claim|argument|account|proposal|analysis|problem|issue|point|"
    r"question|objection|reply|response|contrast|distinction|move|"
    r"framework|view|thesis|diagnosis|answer|result|evidence|lesson|"
    r"implication|worry|target|section|paper|profile)\b"
)
ARGUMENT_OBJECT_OPENER_THRESHOLD = 4

# Contrastive sentence-initial connectives (use "but" instead)
SENTENCE_START_CONTRASTIVE = re.compile(
    r"(?:^|[.!?]\s+)(Yet|However|Nevertheless|Nonetheless)\b"
)
CONTRASTIVE_NEGATION_PATTERNS = [
    (
        # Claim, comma, "and", then a clause that rates the claim instead of
        # advancing it: "and that's fair", "and it's worth seeing what it
        # costs", "and the hedges are the point", "and I don't claim it".
        # The second conjunct tells the reader how to take the first, which is
        # the faux-coaching failure wearing a coordinator. Cut it, promote it,
        # or split it off; never convert it to a gerund-participial adjunct,
        # which trips the trailing -ing check below.
        "coordinate evaluation tacked onto a claim",
        re.compile(
            r",\s+and\s+(?:"
            r"(?:it|that|this)(?:\u2019s|'s|\s+is)\s+(?:worth|fair|the\s+point|useful|"
            r"why|what|clear|striking|telling|significant|important|no\s+accident)"
            r"|the\s+\w+\s+(?:is|are)\s+the\s+point"
            r"|(?:that|this)(?:\u2019s|'s|\s+is)\s+(?:the|a)\s+\w+\b"
            r"|I\s+(?:don\u2019t|don't|do\s+not)\s+claim"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "contrastive negation",
        re.compile(
            r"\bnot\s+(?:only|just|merely|simply)\b[^.!?;]{0,140}\bbut(?:\s+also)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "not-because-but-because frame",
        re.compile(r"\bnot\s+because\b[^.!?;]{0,140}\bbut\s+because\b", re.IGNORECASE),
    ),
    (
        "two-sentence correctio",
        re.compile(
            r"\b(?:it|this|that)\s+(?:is|was)(?:\s+not|n't)\b[^.!?]{1,100}\.\s+"
            r"(?:it|this|that)\s+(?:is|was)\b",
            re.IGNORECASE,
        ),
    ),
]
EVALUATIVE_PARTICIPLE_RE = re.compile(
    r",\s+(highlighting|underscoring|reflecting|cementing|solidifying|"
    r"signali[sz]ing|showcasing|emphasizing|reinforcing|illustrating|"
    r"demonstrating|revealing|suggesting|indicating|paving|leading|allowing|"
    r"resulting)\b",
    re.IGNORECASE,
)
WHILE_MAINTAINING_RE = re.compile(
    r"\bwhile\s+(?:also\s+)?(?:maintaining|preserving|ensuring|retaining|"
    r"safeguarding|protecting)\b",
    re.IGNORECASE,
)
WEASEL_ATTRIBUTION_RE = re.compile(
    r"\b(?:some|many)\s+(?:critics|scholars|researchers|observers|"
    r"commentators|analysts)\s+(?:argue|claim|suggest|note|contend|have\s+noted)\b"
    r"|\b(?:industry|media|market|policy|research)\s+reports\s+suggest\b"
    r"|\bresearch\s+suggests\b"
    r"|\bit\s+is\s+widely\s+(?:believed|argued|recognized|acknowledged)\b",
    re.IGNORECASE,
)
FALSE_RANGE_RE = re.compile(
    r"\bfrom\s+[a-z][^,.;:!?]{3,80}?\s+to\s+[a-z][^,.;:!?]{3,80}?(?=,|\.|;|:|$)",
    re.IGNORECASE,
)
AI_TRIAD_RE = re.compile(
    r"\b(?:innovative|transformative|groundbreaking|robust|comprehensive|"
    r"holistic|nuanced|meticulous|seamless|dynamic|vibrant|pivotal)"
    r"\b[^.!?;]{0,80},\s+(?:and\s+)?"
    r"(?:innovative|transformative|groundbreaking|robust|comprehensive|"
    r"holistic|nuanced|meticulous|seamless|dynamic|vibrant|pivotal)\b",
    re.IGNORECASE,
)
RESTATEMENT_REVELATION_RE = re.compile(
    r"\b([a-z][a-z-]{3,})s?\b"
    r"[^.!?;]{0,90},\s+(?:and|but)\s+"
    r"(?:the|this|that|these|those)\s+\1s?\s+"
    r"(?:matters?|does\s+the\s+work|is\s+the\s+point|is\s+what\s+matters|"
    r"carries\s+the\s+argument|does\s+the\s+heavy\s+lifting)\b",
    re.IGNORECASE,
)


def is_skip_line(line):
    s = line.strip()
    return (
        not s
        or s.startswith("#")
        or s.startswith("```")
        or re.match(r"^\[[\w\d]+\]:", s)
        or s == "---"
    )


def is_skip_paragraph(stripped):
    return (
        not stripped
        or stripped.startswith("#")
        or stripped.startswith("```")
        or re.match(r"^\[[\w\d]+\]:", stripped)
    )


def iter_paragraphs_with_lines(text):
    current = []
    start_line = None

    def emit():
        if current and start_line is not None:
            return start_line, "\n".join(current)
        return None

    for line_num, line in enumerate(text.split("\n"), start=1):
        if not line.strip():
            paragraph = emit()
            if paragraph:
                yield paragraph
            current = []
            start_line = None
            continue

        if start_line is None:
            start_line = line_num
        current.append(line)

    paragraph = emit()
    if paragraph:
        yield paragraph


def lint_file(path):
    text = Path(path).read_text()
    lines = text.split("\n")
    issues = []

    # Em-dash detection (excluding md horizontal rules and reference links)
    for i, line in enumerate(lines, start=1):
        if is_skip_line(line):
            continue
        if "—" in line:  # U+2014 EM DASH
            issues.append((i, "em-dash", "use commas, parens, or en-dash with spaces"))
        if "---" in line and line.strip() != "---":
            issues.append((i, "ascii em-dash (---)", line.strip()[:60]))

    # Paragraph length (>100 words)
    the_x_is_y_openers = []
    object_openers = []
    for line_offset, para in iter_paragraphs_with_lines(text):
        stripped = para.strip()
        if is_skip_paragraph(stripped):
            continue
        opener = re.sub(r"\s+", " ", stripped).strip()
        if THE_X_IS_Y_OPENER_RE.search(opener):
            the_x_is_y_openers.append((line_offset, opener[:70]))
        if ARGUMENT_OBJECT_OPENER_RE.search(opener):
            object_openers.append((line_offset, opener[:70]))
        words = re.findall(r"\b\w+\b", stripped)
        wc = len(words)
        if wc > 100:
            issues.append((line_offset, "long paragraph", f"{wc} words (max 100)"))

    the_x_line_nums = {line for line, _opener in the_x_is_y_openers}
    object_only_openers = [
        (line, opener)
        for line, opener in object_openers
        if line not in the_x_line_nums
    ]

    if len(the_x_is_y_openers) >= THE_X_IS_Y_OPENER_THRESHOLD:
        lines = ", ".join(str(line) for line, _opener in the_x_is_y_openers[:5])
        if len(the_x_is_y_openers) > 5:
            lines += ", ..."
        issues.append((
            the_x_is_y_openers[THE_X_IS_Y_OPENER_THRESHOLD - 1][0],
            "cadence warning",
            (
                f"noticeable 'The X is Y' paragraph-opener pattern "
                f"({len(the_x_is_y_openers)}; lines {lines}); vary if not defining, contrasting, or pivoting"
            ),
        ))
    if (
        len(object_openers) >= ARGUMENT_OBJECT_OPENER_THRESHOLD
        and len(object_only_openers) >= 2
    ):
        lines = ", ".join(str(line) for line, _opener in object_openers[:6])
        if len(object_openers) > 6:
            lines += ", ..."
        issues.append((
            object_openers[ARGUMENT_OBJECT_OPENER_THRESHOLD - 1][0],
            "cadence warning",
            (
                f"noticeable argumentative-object paragraph-opener pattern "
                f"({len(object_openers)}; lines {lines}); vary by making the move directly where possible"
            ),
        ))

    # Vocabulary checks
    word_counter = Counter()
    high_signal_counter = Counter()
    high_signal_lines = {}
    for i, line in enumerate(lines, start=1):
        if is_skip_line(line):
            continue
        line_lower = line.lower()
        words_in_line = re.findall(r"\b[a-z]+\b", line_lower)
        for w in words_in_line:
            if w in WATCH_OVERUSE:
                word_counter[w] += 1
            if w in CUT_HIGH_SIGNAL:
                high_signal_counter[w] += 1
                high_signal_lines.setdefault(w, []).append(i)
        words_set = set(words_in_line)
        for w in AI_ADVERBS & words_set:
            issues.append((i, "AI adverb", w))
        for w in HACKNEYED_ADVERBS & words_set:
            issues.append((i, "hackneyed adverb", w))
        for phrase in AI_TIC_PHRASES:
            if phrase in line_lower:
                issues.append((i, "AI tic phrase", phrase))
        for label, pattern in CONTRASTIVE_NEGATION_PATTERNS:
            if pattern.search(line):
                issues.append((i, "AI construction", label))
        if EVALUATIVE_PARTICIPLE_RE.search(line):
            issues.append((i, "AI construction", "trailing evaluative -ing supplement"))
        if WHILE_MAINTAINING_RE.search(line):
            issues.append((i, "AI construction", "while maintaining/preserving trade-off frame"))
        if WEASEL_ATTRIBUTION_RE.search(line):
            issues.append((i, "AI construction", "weasel attribution; name the source or delete"))
        if AI_TRIAD_RE.search(line):
            issues.append((i, "AI construction", "prestige-adjective cluster or triad"))
        if RESTATEMENT_REVELATION_RE.search(line):
            issues.append((i, "AI construction", "restatement-as-revelation; state the consequence directly"))
        for match in FALSE_RANGE_RE.finditer(line):
            span = match.group(0)
            if re.search(r"\d", span):
                continue
            if len(re.findall(r"\b[a-z]+\b", span.lower())) < 5:
                continue
            issues.append((i, "AI construction", "possible false range; verify real scale"))
        if REAL_WORK_METAPHOR_RE.search(line):
            issues.append((i, "real-work metaphor", "say what the expression, contrast, or argument does"))
        if PRESENT_SELF_REFERENCE_RE.search(line):
            issues.append((i, "present self-reference", "use 'I', 'this paper', 'the account', or the specific claim"))
        for m in SENTENCE_START_CONTRASTIVE.finditer(line):
            issues.append((i, "contrastive starter", f"'{m.group(1)}' — use 'But' instead"))

    if len(high_signal_counter) >= 3:
        found = ", ".join(sorted(high_signal_counter))
        issues.append((0, "AI word cluster", f"{len(high_signal_counter)} high-signal words: {found}"))
    for word, count in high_signal_counter.items():
        if count >= HIGH_SIGNAL_REPEAT_THRESHOLD:
            lines = ",".join(str(line) for line in high_signal_lines[word][:4])
            if len(high_signal_lines[word]) > 4:
                lines += ",..."
            issues.append((
                high_signal_lines[word][0],
                "AI high-signal repeated",
                f"'{word}' used {count} times (lines {lines}); prune unless technical",
            ))

    # Overuse summary (>2 occurrences)
    for word, count in word_counter.items():
        if count > 2:
            issues.append((0, "overuse", f"'{word}' used {count} times"))

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: check-style-md.py <file.md>")
        sys.exit(1)
    path = sys.argv[1]
    if not Path(path).exists():
        print(f"File not found: {path}")
        sys.exit(1)
    issues = lint_file(path)
    if not issues:
        print("No house-style issues detected.")
        return
    issues.sort(key=lambda x: (x[0], x[1]))
    for line, category, detail in issues:
        loc = f"{path}:{line}" if line > 0 else f"{path}"
        print(f"  {loc}  [{category}]  {detail}")
    print(f"\n{len(issues)} issue(s). See .claude/rules/writing-style.md")


if __name__ == "__main__":
    main()
