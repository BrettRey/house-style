#!/usr/bin/env python3
"""
House style linter for Brett Reynolds' LaTeX papers.
Checks for common style violations and AI voice signatures.

Passing this linter is not sufficient for house-style compatibility. It catches
common and automatable violations; house style still requires judgement about
argument, cadence, level discipline, terminology, and prose fit.

Usage:
    python check-style.py file.tex
    python check-style.py *.tex
    python check-style.py --strict file.tex  # Include advisory checks

AI voice check:
    Words are checked by co-occurrence density (Lady Bracknell principle:
    any one is unremarkable; a cluster is a tell). Phrases are flagged
    individually since each is already diagnostic.

    Source: Pangram AI Phrases dataset (Feb 2025), n-gram analysis of
    tens of millions of human vs AI-generated documents.

Sentence-length report:
    Models cluster sentence length in a narrow mid band, and the uniformity
    is more detectable than any individual word. The report gives the
    distribution and flags narrow spread; it does not rule on it. Advisory
    only: it never affects the exit code. Suppress with --no-lengths.
"""

import re
import sys
from collections import Counter
from pathlib import Path

VIOLATIONS = []
AI_FINDINGS = []
STRICT_MODE = False
AI_PHRASE_CLUSTER_THRESHOLD = 3

# Common contractions - apostrophe followed by these is NOT a quote
CONTRACTION_ENDINGS = {"t", "s", "re", "ve", "ll", "d", "m", "em", "cause", "til", "twas", "tis"}
STRUCTURED_LAYOUT_ENV_RE = re.compile(
    r'\\(begin|end)\{'
    r'(tabular|tabular\*|tabularx|array|align|align\*|aligned|alignedat|gather|gather\*)'
    r'\}'
)
GLOSS_QUOTE_RE = re.compile(r"`[^`']+?'")
LEADING_CONTRACTION_RE = re.compile(r"(?<!\w)'(?:cause|em|til|twas|tis)\b", re.IGNORECASE)
CATEGORY_CLASS_PATTERNS = [
    (re.compile(r"\bword class(?:es)?\b", re.IGNORECASE), "word class"),
    (re.compile(r"\blexical class(?:es)?\b", re.IGNORECASE), "lexical class"),
    (re.compile(r"\bsyntactic class(?:es)?\b", re.IGNORECASE), "syntactic class"),
    (re.compile(r"\bgrammatical class(?:es)?\b", re.IGNORECASE), "grammatical class"),
    (re.compile(r"\bmorphosyntactic class(?:es)?\b", re.IGNORECASE), "morphosyntactic class"),
    (re.compile(r"\bcategory class(?:es)?\b", re.IGNORECASE), "category class"),
    (
        re.compile(r"\bclasses? of (?:words|lexemes|lexical items|expressions|forms)\b", re.IGNORECASE),
        "class of words/forms",
    ),
    (
        re.compile(
            r"\b(?:noun|verb|adjective|adverb|determinative|article|preposition|postposition|"
            r"adposition|auxiliary|pronoun|subordinator|coordinator|interjection) class(?:es)?\b",
            re.IGNORECASE,
        ),
        "category label plus class",
    ),
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
RESTATEMENT_REVELATION_RE = re.compile(
    r"\b([a-z][a-z-]{3,})s?\b"
    r"[^.!?;]{0,90},\s+(?:and|but)\s+"
    r"(?:the|this|that|these|those)\s+\1s?\s+"
    r"(?:matters?|does\s+the\s+work|is\s+the\s+point|is\s+what\s+matters|"
    r"carries\s+the\s+argument|does\s+the\s+heavy\s+lifting)\b",
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

SKIP_PROSE_COMMANDS_RE = re.compile(
    r'\\(?:mention|mentionhead|olang|ipa|texttt|path|url|href|cite|citep|citet|'
    r'textcite|ref|label|enquote)\s*(?:\[[^\]]*\])*\{[^{}]*\}'
)

UNCONTRACTED_SUBJECT_AUX_PATTERNS = [
    # Personal pronouns with be/will/would
    (re.compile(r"\bI am\b"), "I am", "I'm"),
    (re.compile(r"\bI will\b"), "I will", "I'll"),
    (re.compile(r"\bI would\b"), "I would", "I'd"),
    (re.compile(r"\byou are\b", re.IGNORECASE), "you are", "you're"),
    (re.compile(r"\byou will\b", re.IGNORECASE), "you will", "you'll"),
    (re.compile(r"\byou would\b", re.IGNORECASE), "you would", "you'd"),
    (re.compile(r"\bhe is\b", re.IGNORECASE), "he is", "he's"),
    (re.compile(r"\bhe will\b", re.IGNORECASE), "he will", "he'll"),
    (re.compile(r"\bhe would\b", re.IGNORECASE), "he would", "he'd"),
    (re.compile(r"\bshe is\b", re.IGNORECASE), "she is", "she's"),
    (re.compile(r"\bshe will\b", re.IGNORECASE), "she will", "she'll"),
    (re.compile(r"\bshe would\b", re.IGNORECASE), "she would", "she'd"),
    (re.compile(r"\bit is\b", re.IGNORECASE), "it is", "it's"),
    (re.compile(r"\bit will\b", re.IGNORECASE), "it will", "REPHRASE_IT_WILL"),
    (re.compile(r"\bit would\b", re.IGNORECASE), "it would", "it'd"),
    (re.compile(r"\bwe are\b", re.IGNORECASE), "we are", "we're"),
    (re.compile(r"\bwe will\b", re.IGNORECASE), "we will", "we'll"),
    (re.compile(r"\bwe would\b", re.IGNORECASE), "we would", "we'd"),
    (re.compile(r"\bthey are\b", re.IGNORECASE), "they are", "they're"),
    (re.compile(r"\bthey will\b", re.IGNORECASE), "they will", "they'll"),
    (re.compile(r"\bthey would\b", re.IGNORECASE), "they would", "they'd"),
    # Demonstratives, existential there, and wh-pronouns where contraction is idiomatic.
    (re.compile(r"\bthis is\b", re.IGNORECASE), "this is", None),
    (re.compile(r"\bthis will\b", re.IGNORECASE), "this will", "this'll"),
    (re.compile(r"\bthat is\b", re.IGNORECASE), "that is", "that's"),
    (re.compile(r"\bthat will\b", re.IGNORECASE), "that will", "that'll"),
    (re.compile(r"\bthere is\b", re.IGNORECASE), "there is", "there's"),
    (re.compile(r"\bwhat is\b", re.IGNORECASE), "what is", "what's"),
    (re.compile(r"\bwho is\b", re.IGNORECASE), "who is", "who's"),
]

UNCONTRACTED_HAVE_AUX_RE = re.compile(
    r"\b(I|you|he|she|it|we|they|this|that|there|who|what)\s+(have|has)\s+"
    r"(been|being|had|done|gone|made|seen|known|found|shown|given|taken|come|"
    r"become|observed|reviewed|used|treated|linked|changed|declined|"
    r"[a-z]+ed|[a-z]+en)\b",
    re.IGNORECASE,
)

UNCONTRACTED_NEGATIVE_PATTERNS = [
    (re.compile(r"\bcannot\b", re.IGNORECASE), "cannot", "can't"),
    (re.compile(r"\bcan\s+not\b", re.IGNORECASE), "can not", "can't"),
    (re.compile(r"\bdo\s+not\b", re.IGNORECASE), "do not", "don't"),
    (re.compile(r"\bdoes\s+not\b", re.IGNORECASE), "does not", "doesn't"),
    (re.compile(r"\bdid\s+not\b", re.IGNORECASE), "did not", "didn't"),
    (re.compile(r"\bis\s+not\b", re.IGNORECASE), "is not", "isn't"),
    (re.compile(r"\bare\s+not\b", re.IGNORECASE), "are not", "aren't"),
    (re.compile(r"\bwas\s+not\b", re.IGNORECASE), "was not", "wasn't"),
    (re.compile(r"\bwere\s+not\b", re.IGNORECASE), "were not", "weren't"),
    (re.compile(r"\bhas\s+not\b", re.IGNORECASE), "has not", "hasn't"),
    (re.compile(r"\bhave\s+not\b", re.IGNORECASE), "have not", "haven't"),
    (re.compile(r"\bhad\s+not\b", re.IGNORECASE), "had not", "hadn't"),
    (re.compile(r"\bwill\s+not\b", re.IGNORECASE), "will not", "won't"),
    (re.compile(r"\bwould\s+not\b", re.IGNORECASE), "would not", "wouldn't"),
    (re.compile(r"\bshould\s+not\b", re.IGNORECASE), "should not", "shouldn't"),
    (re.compile(r"\bcould\s+not\b", re.IGNORECASE), "could not", "couldn't"),
]

CONTRACTION_SKIP_PHRASES = {
    "as it is",
    "i am responsible",
}

# ===========================
# AI VOICE SIGNATURE DATA
# ===========================
# Source: Pangram (Feb 2025). Words statistically overrepresented in
# AI-generated text vs human text. Individual words are unremarkable;
# co-occurrence density is the diagnostic signal.

AI_SIGNATURE_WORDS = {
    # High-signal words (distinctive AI markers)
    "delve", "delves", "delved", "delving",
    "tapestry", "tapestries",
    "testament", "testaments",
    "landscape", "landscapes",
    "realm", "realms",
    "vibrant", "vibrantly",
    "bustling",
    "kaleidoscope", "kaleidoscopes",
    "symphony",
    "tempest",
    "whimsy", "whimsical",
    "quirky",
    "roadmap",
    "toolkit",
    "beacon",
    "mosaic",
    # Verbs and their forms
    "illuminate", "illuminates", "illuminated", "illuminating", "illumination",
    "elucidate", "elucidates", "elucidated", "elucidating", "elucidative", "elucidatory",
    "underscore", "underscores", "underscoring", "underscored",
    "unravel", "unravels", "unraveling", "unraveled",
    "unleash", "unleashes", "unleashing", "unleashed",
    "unlock", "unlocks", "unlocking", "unlocked",
    "embark", "embarks", "embarked", "embarking",
    "navigate", "navigates", "navigated", "navigating",
    "grapple", "grapples", "grappled", "grappling",
    "foster", "fosters", "fostered", "fostering",
    "showcase", "showcases", "showcased", "showcasing",
    "reimagine", "reimagines", "reimagined", "reimagining",
    "revolutionize", "revolutionizes", "revolutionized", "revolutionizing",
    "elevate", "elevates", "elevated", "elevating",
    "empower", "empowered", "empowering",
    "entwine", "entwines", "entwined", "entwining",
    "intertwine", "intertwines", "intertwined", "intertwining",
    "reverberate", "reverberates", "reverberated", "reverberating",
    "resonate", "resonates", "resonating", "resonance",
    "transcend", "transcends", "transcended", "transcending", "transcendence", "transcendent",
    "harness", "harnessed", "harnessing",
    "espouse", "espouses", "espoused", "espousing",
    "evoke", "evokes", "evoked", "evoking",
    "exemplify", "exemplifies", "exemplifying",
    "revitalize", "revitalized",
    "vitalize",
    # Adjectives
    "pivotal", "pivotally",
    "paramount",
    "seamless", "seamlessly", "seamlessness",
    "groundbreaking",
    "transformative",
    "multifaceted",
    "meticulous", "meticulously", "meticulousness",
    "tireless", "tirelessly",
    "relentless", "relentlessly", "relentlessness",
    "timeless", "timelessly", "timelessness",
    "indelible", "indelibly",
    "unwavering",
    "unyielding",
    "poignant", "poignantly", "poignancy",
    "commendable",
    "invaluable", "invaluably",
    "exemplary",
    # Nouns
    "intricacies",
    "interplay", "interplays",
    "facet", "facets", "faceted",
    "embodiment", "embodiments",
    "endeavor", "endeavors", "endeavored", "endeavoring",
    "imperative", "imperatives",
    "groundwork",
    "underpinning", "underpinned", "underpin",
    "elusiveness",
    "versatility",
    # Adverbs
    "aptly",
    "profoundly",
    "intricately",
    "vividly",
    # Medium-signal words (common in academic text but AI-overrepresented)
    "crucial", "crucially",
    "nuance", "nuances", "nuanced",
    "robust",
    "compelling",
    "comprehensive",
    "innovative", "innovation", "innovate", "innovates", "innovated", "innovating",
    "insightful", "insightfully",
    "profound",
    "potent",
    "captivating",
    "intricate",
    "notable", "notably",
    "dynamic", "dynamically", "dynamics",
    "diverse",
    "sustainable", "sustainability",
    "authentic",
    "enigmatic",
    "crafted", "curated",
    "nestled",
    "newfound",
    "solace",
    "resilience",
    "perseverance",
    "enduring",
    "inspirational",
    "thought-provoking",
    "standout",
    "boast", "boasts", "boasted", "boasting",
    "garner", "garners", "garnered", "garnering",
    "leverage", "leverages", "leveraged", "leveraging",
    "holistic", "holistically",
    "noteworthy",
    "multifarious",
    "ever-evolving",
    "streamline", "streamlines", "streamlined", "streamlining",
    "utilize", "utilizes", "utilized", "utilizing",
}

AI_REPEAT_REVIEW_WORDS = {
    "delve", "delves", "delved", "delving",
    "underscore", "underscores", "underscoring", "underscored",
    "showcase", "showcases", "showcased", "showcasing",
    "tapestry", "tapestries",
    "realm", "realms",
    "foster", "fosters", "fostered", "fostering",
    "testament", "testaments",
    "vibrant", "pivotal", "groundbreaking", "transformative",
    "profound", "paramount", "seamless", "robust", "comprehensive",
    "curated", "crafted", "meticulous", "invaluable", "noteworthy",
    "ever-evolving", "multifaceted", "holistic", "nuanced",
    "leverage", "leverages", "leveraged", "leveraging",
    "utilize", "utilizes", "utilized", "utilizing",
}
AI_REPEAT_REVIEW_THRESHOLD = 2

# "load-bearing assumption" is a term of art from Assumption-Based Planning
# (Dewar et al. 1993), standard in the DMDU literature. Permitted in that exact
# collocation only, and capped, because the phrase is otherwise a very-high-
# signal LLM tell and correct usage at volume still reads as the tic.
LOAD_BEARING_CAP = 2

# Filler intensifiers: they raise the writer's commitment without changing the
# claim, and they usually delete cleanly ("this genuinely fails" = "this
# fails"). Ordinary enough that one use is no signal; a run of them is.
FILLER_INTENSIFIERS = {"genuinely", "really", "truly", "actually"}
FILLER_INTENSIFIER_THRESHOLD = 3

# Phrases individually diagnostic of AI voice.
# Each is a strong enough signal to flag on its own.
AI_SIGNATURE_PHRASES = [
    "a testament to",
    "stands as a testament to",
    "is a testament",
    "symbol of resilience",
    "watershed moment",
    "a complex tapestry",
    "complex tapestry",
    "rich tapestry",
    "rich cultural heritage",
    "rich history",
    "key turning point",
    "dynamic hub",
    "paving the way",
    "shed light on",
    "sheds light on",
    "shedding light on",
    "it's important to note",
    "it is important to note",
    "it's worth noting",
    "it is worth noting",
    "it's crucial to",
    "it is essential to",
    "in a world where",
    "in a world of",
    "in today's world",
    "in today's fast-paced world",
    "in the ever-evolving landscape",
    "at the intersection of",
    "a treasure trove of",
    "deep dive",
    "when it comes to",
    "at the end of the day",
    "overall",
    "in conclusion",
    "in summary",
    "not only but also",  # stripped version
    "highlights the importance",
    "highlight the importance",
    "underscores the importance",
    "underscore the importance",
    "the importance of",
    "crucial role in",
    "plays a crucial role",
    "significant role in",
    "plays a significant role",
    "significant impact on",
    "leaves a lasting impact",
    "deeper understanding",
    "deeper understanding of",
    "our understanding of",
    "their understanding of",
    "for understanding",
    "new insights into",
    "valuable insights into",
    "valuable insights",
    "provide valuable",
    "provides valuable",
    "important implications for",
    "important implications",
    "implications for",
    "the rise of",
    "the effects of",
    "interplay between",
    "the interplay between",
    "serves as a",
    "serve as a",
    "is a reminder",
    "stark reminder",
    "here are some",
    "several reasons",
    "despite these challenges",
    "these challenges",
    "navigate the complexities",
    "the complexities of",
    "step-by-step",
    "it remains to be seen",
    "further research is needed",
    "future generations",
    "personal growth",
    "well-being",
    "are committed to",
    "commitment to",
    "dedication to",
    "stumbled upon",
    "simple yet",
    "packs a punch",
    # Chat residue
    "i hope this message finds you well",
    "i hope this helps",
    "let me know if you need anything else",
    "of course!",
    "certainly!",
    "great question",
    # Faux-coaching / structural-spine tics
    "let me refine your claim",
    # "load-bearing X" is handled by the counting check in check_ai_voice(),
    # which permits the capped ABP term of art and flags every other use.
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
]

AI_CONSTRUCTION_PATTERNS = [
    (
        # Claim, comma, "and", then a clause that rates the claim instead of
        # advancing it: "and that's fair", "and it's worth seeing what it
        # costs", "and the hedges are the point", "and I don't claim it".
        # Identified 2026-07-25 as a heavy tic in LLM-drafted prose: sixteen
        # instances in one manuscript, nearly all from a single day's edits.
        # The second conjunct tells the reader how to take the first, which is
        # the faux-coaching failure wearing a coordinator. Cut it, promote it
        # to the main clause, or split it off; never convert it to a
        # gerund-participial adjunct, which trips the trailing -ing tic below.
        "coordinate evaluation tacked onto a claim",
        re.compile(
            r",\s+and\s+(?:"
            r"(?:it|that|this)(?:'s|\s+is)\s+(?:worth|fair|the\s+point|useful|"
            r"why|what|clear|striking|telling|significant|important|no\s+accident)"
            r"|the\s+\w+\s+(?:is|are)\s+the\s+point"
            r"|(?:that|this)(?:'s|\s+is)\s+(?:the|a)\s+\w+\b"
            r"|I\s+(?:don't|do\s+not)\s+claim"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        # The same tic in its metadiscursive form: the second conjunct doesn't
        # rate the claim, it announces that a point is coming. "and the reason
        # is worth stating", "and its status should be said plainly", "and the
        # borrowing needs stating precisely", "and the dispute is worth
        # resolving". The writer flags a move instead of making it, so the
        # sentence costs a clause and delivers nothing; the fix is always to
        # delete the conjunct and let the next sentence do its work.
        # Added 2026-08-10 after nine instances in one manuscript, eight of
        # them from two days' editing. Measured before adding: catches 4/4 of
        # the removed instances and fires once across 400 other .tex files in
        # the portfolio, on a genuine instance in another paper. Keep the verb
        # list closed; opening it to any verb makes this fire on ordinary
        # two-claim conjuncts.
        "announced move instead of the move",
        re.compile(
            r",\s+and\s+(?:the|this|that|its|his|her|their)\s+\w+(?:\s+\w+)?\s+"
            r"(?:needs?|deserves?|merits?|warrants?|is\s+worth|are\s+worth|"
            r"should\s+be)\s+"
            r"(?:stat|say|said|nam|separat|not|register|spell|mark|flagg?|"
            r"resolv)\w*\b",
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
    (
        # Corrective negation with no opponent: the claim is staged as a
        # correction of a position nobody in the argument holds. Same-sentence
        # forms only; the cross-sentence pronoun case is the correctio above.
        #   "the problem isn't the data, it's the inference"
        #   "this isn't a matter of taste but of evidence"
        #   "it's not that the category is wrong, it's that it does no work"
        # Advisory: a real rejection of a cited position looks the same. The
        # question the finding asks is whether anyone claimed the negated half.
        "corrective negation (did anyone claim the negated version?)",
        re.compile(
            r"\b(?:is|are|was|were)(?:\s+not|n[''’]t)\s+[^.!?;]{2,90}?,\s*"
            r"(?:it|this|that|they)(?:[''’]s|[''’]re|\s+(?:is|are|was|were))\b"
            r"|\b(?:is|are|was|were)(?:\s+not|n[''’]t)\s+(?:a|an|the)\s+"
            r"(?:matter|question|issue|case|failure|problem|function)\s+of\b"
            r"[^.!?;]{0,90}\bbut\b"
            r"|\bnot\s+that\b[^.!?;]{0,90},\s*(?:it|this|that)(?:[''’]s|\s+is)\s+that\b",
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

def strip_latex(text):
    """Strip LaTeX commands and environments to extract prose words.

    Used for AI voice detection where we need to match against plain
    English words, not LaTeX markup.
    """
    # Remove comments
    text = re.sub(r'(?<!\\)%.*', '', text)
    # Remove common environments we don't want to scan
    text = re.sub(r'\\begin\{(equation|align|verbatim|lstlisting|tikzpicture)\*?\}.*?\\end\{\1\*?\}', '', text, flags=re.DOTALL)
    # Remove \command{...} but keep the content inside braces
    # (so \term{definiteness} -> definiteness, \enquote{text} -> text)
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    # Remove remaining bare commands (\command)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    # Remove braces, tildes, backslashes
    text = re.sub(r'[{}~\\]', ' ', text)
    return text


def check_ai_voice(filepath):
    """Check a file for AI voice signatures.

    Words: counted by co-occurrence density. Any one AI-overrepresented
    word is unremarkable; a cluster is diagnostic (Lady Bracknell principle).

    Phrases: flagged individually, since each is already a strong signal.
    """
    path = Path(filepath)
    text = path.read_text(encoding='utf-8')
    prose = strip_latex(text)
    prose_lower = prose.lower()

    # --- Word co-occurrence density ---
    # Tokenize to words
    words = re.findall(r'\b[a-z]+(?:-[a-z]+)?\b', prose_lower)
    words_in_doc = set(words)
    word_counts = Counter(words)
    found_words = words_in_doc & AI_SIGNATURE_WORDS
    density = len(found_words)

    if density >= 3:
        sorted_words = sorted(found_words)
        AI_FINDINGS.append((
            filepath, 0,
            f"AI word co-occurrence: {density} signature words detected",
            ", ".join(sorted_words)
        ))

    # --- load-bearing: banned except the ABP term of art, capped ---
    # "load-bearing assumption" (Dewar et al. 1993) is permitted up to
    # LOAD_BEARING_CAP times per paper. Every other use is the praise-as-
    # structure tic. Enforced here because a cap nobody checks is not a cap.
    lb_all = re.findall(r'load[-\s]bearing\s+(\w+)', prose_lower)
    lb_technical = [w for w in lb_all if w == 'assumption' or w == 'assumptions']
    lb_other = [w for w in lb_all if w not in ('assumption', 'assumptions')]
    lb_bare = len(re.findall(r'load[-\s]bearing\b', prose_lower)) - len(lb_all)

    if lb_other or lb_bare:
        detail = ", ".join(f'"load-bearing {w}"' for w in sorted(set(lb_other)))
        if lb_bare:
            detail = (detail + ", " if detail else "") + f"bare 'load-bearing' x{lb_bare}"
        AI_FINDINGS.append((
            filepath, 0,
            "'load-bearing' outside the ABP term of art (praise-as-structure tic)",
            detail,
        ))
    if len(lb_technical) > LOAD_BEARING_CAP:
        AI_FINDINGS.append((
            filepath, 0,
            f"'load-bearing assumption' x{len(lb_technical)} exceeds the "
            f"cap of {LOAD_BEARING_CAP} per paper",
            "use 'critical assumption', or name the assumption",
        ))

    repeated_words = {
        word: count
        for word, count in word_counts.items()
        if word in AI_REPEAT_REVIEW_WORDS and count >= AI_REPEAT_REVIEW_THRESHOLD
    }
    if repeated_words:
        summary = ", ".join(
            f"{word} x{count}"
            for word, count in sorted(repeated_words.items(), key=lambda item: (-item[1], item[0]))
        )
        AI_FINDINGS.append((
            filepath, 0,
            "Repeated AI-associated word use (review incidence; one may be harmless)",
            summary,
        ))

    intensifiers = {
        word: count
        for word, count in word_counts.items()
        if word in FILLER_INTENSIFIERS
    }
    intensifier_total = sum(intensifiers.values())
    if intensifier_total >= FILLER_INTENSIFIER_THRESHOLD:
        summary = ", ".join(
            f"{word} x{count}"
            for word, count in sorted(intensifiers.items(), key=lambda item: (-item[1], item[0]))
        )
        AI_FINDINGS.append((
            filepath, 0,
            f"Filler intensifiers ({intensifier_total} uses) - most delete without loss",
            summary,
        ))

    # --- Phrase matching (line-level for line numbers) ---
    lines = text.split('\n')
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('%'):
            continue
        line_prose = strip_latex(line).lower()
        for phrase in AI_SIGNATURE_PHRASES:
            if phrase in line_prose:
                AI_FINDINGS.append((filepath, i, f"AI phrase: \"{phrase}\"", line.strip()))

    check_ai_construction_patterns(filepath, lines)


def check_ai_construction_patterns(filepath, lines):
    """Flag construction-level AI voice patterns as advisory findings."""
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('%'):
            continue
        line_no_comments = strip_comments(line)
        line_prose = strip_latex(line_no_comments)
        if not line_prose.strip():
            continue

        for label, pattern in AI_CONSTRUCTION_PATTERNS:
            if pattern.search(line_prose):
                AI_FINDINGS.append((filepath, i, f"AI pattern: {label}", line.strip()))

        if EVALUATIVE_PARTICIPLE_RE.search(line_prose):
            AI_FINDINGS.append((
                filepath,
                i,
                "AI pattern: trailing evaluative -ing supplement",
                line.strip(),
            ))

        if WHILE_MAINTAINING_RE.search(line_prose):
            AI_FINDINGS.append((
                filepath,
                i,
                "AI pattern: while maintaining/preserving trade-off frame",
                line.strip(),
            ))

        if WEASEL_ATTRIBUTION_RE.search(line_prose):
            AI_FINDINGS.append((
                filepath,
                i,
                "AI pattern: weasel attribution; name the source or delete",
                line.strip(),
            ))

        if AI_TRIAD_RE.search(line_prose):
            AI_FINDINGS.append((
                filepath,
                i,
                "AI pattern: prestige-adjective cluster or triad",
                line.strip(),
            ))

        if RESTATEMENT_REVELATION_RE.search(line_prose):
            AI_FINDINGS.append((
                filepath,
                i,
                "AI pattern: restatement-as-revelation; state the consequence directly",
                line.strip(),
            ))

        for match in FALSE_RANGE_RE.finditer(line_prose):
            span = match.group(0)
            if re.search(r"\d", span):
                continue
            if len(re.findall(r"\b[a-z]+\b", span.lower())) < 5:
                continue
            AI_FINDINGS.append((
                filepath,
                i,
                "AI pattern: possible false range; verify the endpoints form a real scale",
                line.strip(),
            ))


QUOTED_SPAN_COMMANDS = ('enquote', 'textquote', 'blockquote')

def blank_quoted_spans(text):
    """
    Blank the interior of every \\enquote{...} span, across line breaks and
    through nested braces, replacing characters with spaces so that line
    numbers and column offsets are preserved.

    House style checks describe how Brett should write. They must never fire
    on words he is quoting from a source: acting on such a warning silently
    edits someone else's sentence, which is how a quotation stops being one.
    The single-line SKIP_PROSE_COMMANDS_RE cannot do this job, because it
    matches \\enquote{...} only when the whole span sits on one line with no
    nested braces, and quotations of any length do neither.
    """
    chars = list(text)
    i = 0
    n = len(text)
    while i < n:
        if text[i] != '\\':
            i += 1
            continue
        matched = None
        for name in QUOTED_SPAN_COMMANDS:
            if text.startswith('\\' + name, i):
                after = i + 1 + len(name)
                # allow optional whitespace, then the opening brace
                j = after
                while j < n and text[j] in ' \t':
                    j += 1
                if j < n and text[j] == '{':
                    matched = j
                break
        if matched is None:
            i += 1
            continue
        depth = 0
        k = matched
        while k < n:
            if text[k] == '{' and (k == 0 or text[k-1] != '\\'):
                depth += 1
            elif text[k] == '}' and text[k-1] != '\\':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        if depth != 0:  # unbalanced; leave the text alone
            i += 1
            continue
        for pos in range(matched + 1, k):
            if chars[pos] != '\n':
                chars[pos] = ' '
        i = k + 1
    return ''.join(chars)

def strip_comments(line):
    """Remove LaTeX comments (% to end of line), preserving escaped \\%."""
    result = []
    i = 0
    while i < len(line):
        if line[i] == '%' and (i == 0 or line[i-1] != '\\'):
            break  # Rest is comment
        result.append(line[i])
        i += 1
    return ''.join(result)

def has_real_single_quotes(line):
    """
    Check for actual single-quoted strings, excluding contractions and possessives.
    Returns True only if there's a genuine 'quoted string' pattern.
    """
    # Remove contractions: word'ending where ending is known contraction
    cleaned = line
    cleaned = GLOSS_QUOTE_RE.sub('', cleaned)
    cleaned = LEADING_CONTRACTION_RE.sub('', cleaned)
    for ending in CONTRACTION_ENDINGS:
        cleaned = re.sub(rf"(\w)'{ending}\b", r"\1", cleaned, flags=re.IGNORECASE)

    # Remove possessives: word's or words'
    cleaned = re.sub(r"(\w)'s?\b", r"\1", cleaned)

    # Now check for remaining single quotes that look like quoted strings
    # Pattern: space/punctuation + ' + text + ' + space/punctuation
    if re.search(r"(?:^|[\s(])'[^']+?'(?:[\s,.\-:;?!)]|$)", cleaned):
        return True
    return False

def prose_for_contraction_check(line):
    """Remove LaTeX spans where contraction checks would hit object text."""
    return SKIP_PROSE_COMMANDS_RE.sub(' ', line)

def contraction_message(match_text, suggestion):
    """Format the contraction warning."""
    if suggestion == "REPHRASE_IT_WILL":
        return (
            f"Uncontracted pronoun + auxiliary '{match_text}' - "
            "rephrase rather than using the contracted form"
        )
    if suggestion is None:
        return (
            f"Uncontracted demonstrative + auxiliary '{match_text}' - "
            "contract if natural or rephrase"
        )
    return f"Uncontracted pronoun + auxiliary '{match_text}' - prefer '{suggestion}'"

def check_uncontracted_subject_aux(filepath, line_num, line_no_comments):
    """Flag uncontracted subject + auxiliary forms in prose."""
    prose = prose_for_contraction_check(line_no_comments)
    prose_lower = prose.lower()

    for pattern, _phrase, suggestion in UNCONTRACTED_SUBJECT_AUX_PATTERNS:
        for match in pattern.finditer(prose):
            start, end = match.span()
            window = prose_lower[max(0, start - 12):min(len(prose_lower), end + 12)]
            if any(skip_phrase in window for skip_phrase in CONTRACTION_SKIP_PHRASES):
                continue
            if re.match(r"\s+not\b", prose_lower[end:]):
                continue
            VIOLATIONS.append((
                filepath,
                line_num,
                contraction_message(match.group(0), suggestion),
                line_no_comments.strip(),
            ))

    have_contractions = {
        "i have": "I've",
        "you have": "you've",
        "he has": "he's",
        "she has": "she's",
        "it has": "it's",
        "we have": "we've",
        "they have": "they've",
        "this has": None,
        "that has": "that's",
        "there has": "there's",
        "who has": "who's",
        "what has": "what's",
    }

    for match in UNCONTRACTED_HAVE_AUX_RE.finditer(prose):
        subject_aux = f"{match.group(1).lower()} {match.group(2).lower()}"
        suggestion = have_contractions.get(subject_aux)
        VIOLATIONS.append((
            filepath,
            line_num,
            contraction_message(match.group(0), suggestion),
            line_no_comments.strip(),
        ))

    for pattern, _phrase, suggestion in UNCONTRACTED_NEGATIVE_PATTERNS:
        for match in pattern.finditer(prose):
            VIOLATIONS.append((
                filepath,
                line_num,
                f"Uncontracted negative auxiliary '{match.group(0)}' - prefer '{suggestion}' unless contrast/emphasis requires the full form",
                line_no_comments.strip(),
            ))

def iter_paragraphs_with_lines(text):
    """Yield prose-ish paragraphs with their starting line numbers."""
    current = []
    start_line = None

    def emit():
        if current and start_line is not None:
            return start_line, " ".join(current)
        return None

    for line_num, raw_line in enumerate(text.split('\n'), 1):
        line = strip_comments(raw_line).strip()
        if (
            not line
            or line.startswith('\\section')
            or line.startswith('\\subsection')
            or line.startswith('\\subsubsection')
            or line.startswith('\\begin')
            or line.startswith('\\end')
            or line.startswith('\\item')
        ):
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


def check_repeated_the_x_is_y_openers(filepath, text):
    """Warn when thesis-first copular paragraph openers become rhythmic."""
    the_x_is_y_matches = []
    object_matches = []
    for line_num, paragraph in iter_paragraphs_with_lines(text):
        opener = re.sub(r'\s+', ' ', strip_latex(paragraph)).strip()
        if THE_X_IS_Y_OPENER_RE.search(opener):
            the_x_is_y_matches.append((line_num, opener[:70]))
        if ARGUMENT_OBJECT_OPENER_RE.search(opener):
            object_matches.append((line_num, opener[:70]))

    the_x_line_nums = {line_num for line_num, _opener in the_x_is_y_matches}
    object_only_matches = [
        (line_num, opener)
        for line_num, opener in object_matches
        if line_num not in the_x_line_nums
    ]

    if len(the_x_is_y_matches) >= THE_X_IS_Y_OPENER_THRESHOLD:
        line_list = ", ".join(str(line_num) for line_num, _opener in the_x_is_y_matches[:5])
        if len(the_x_is_y_matches) > 5:
            line_list += ", ..."
        snippets = "; ".join(opener for _line_num, opener in the_x_is_y_matches[:3])
        VIOLATIONS.append((
            filepath,
            the_x_is_y_matches[THE_X_IS_Y_OPENER_THRESHOLD - 1][0],
            (
                f"[warning] Noticeable 'The X is Y' paragraph-opener cadence "
                f"({len(the_x_is_y_matches)}; lines {line_list}) - vary if not defining, contrasting, or pivoting"
            ),
            snippets,
        ))

    if (
        len(object_matches) >= ARGUMENT_OBJECT_OPENER_THRESHOLD
        and len(object_only_matches) >= 2
    ):
        line_list = ", ".join(str(line_num) for line_num, _opener in object_matches[:6])
        if len(object_matches) > 6:
            line_list += ", ..."
        snippets = "; ".join(opener for _line_num, opener in object_matches[:3])
        VIOLATIONS.append((
            filepath,
            object_matches[ARGUMENT_OBJECT_OPENER_THRESHOLD - 1][0],
            (
                f"[warning] Noticeable argumentative-object paragraph-opener cadence "
                f"({len(object_matches)}; lines {line_list}) - vary by making the move directly where possible"
            ),
            snippets,
        ))


# Verbatim-duplicated sentences. Revision, not drafting, creates these: a move is
# relocated (say, a concession pulled forward into the intro) and the original is
# left in place, so the paper makes the same move twice in the same words. No
# sectional review catches it, because each instance reads correctly where it sits.
#
# Measured 2026-08-10 over 865 distinct manuscripts under papers/ and books/:
# 26 files flagged (3.0%), 43 duplicate sentences, of which ~90% were genuine
# duplicated prose. Residual false positives come from manual bibliographies,
# repeated linguistic examples outside \ea...\z, and inline-math residue, which is
# why this is a [warning] and why the filters below exist.
DUPLICATE_SENTENCE_MIN_WORDS = 4
DUPLICATE_SENTENCE_MAX_WORDS = 25
# Bibliography-ish lines leak through when a document hand-rolls its references.
DUPLICATE_SENTENCE_BIBISH_RE = re.compile(
    r"\d+\s*:\s*\d+|\b(?:19|20)\d\d\b\s*\.?$|^and \w+, \w+\.|^\w+, [A-Z]\."
)


def check_duplicate_sentences(filepath, text):
    """Warn when the same sentence appears verbatim more than once."""
    body = re.sub(r'(?<!\\)%.*', '', text)
    body = re.sub(
        r'\\begin\{(equation|align|verbatim|lstlisting|tikzpicture|tabular|tabularx|'
        r'longtable|forest|exe|figure|table|quote|quotation|thebibliography)\*?\}'
        r'.*?\\end\{\1\*?\}',
        '', body, flags=re.DOTALL)
    body = re.sub(r'\\ea\b.*?\\z\b', '', body, flags=re.DOTALL)   # gb4e examples
    body = re.sub(r'\\\(.*?\\\)', '', body, flags=re.DOTALL)
    body = re.sub(r'\$[^$]*\$', '', body)
    prose = re.sub(r'\s+', ' ', strip_latex(body))

    seen = {}
    for sentence in re.split(r'(?<=[.!?])\s+', prose):
        sentence = sentence.strip()
        word_count = len(sentence.split())
        if not (DUPLICATE_SENTENCE_MIN_WORDS <= word_count <= DUPLICATE_SENTENCE_MAX_WORDS):
            continue
        if DUPLICATE_SENTENCE_BIBISH_RE.search(sentence):
            continue
        seen.setdefault(sentence.lower(), []).append(sentence)

    for occurrences in seen.values():
        if len(occurrences) < 2:
            continue
        snippet = occurrences[0][:70]
        line_num = 1
        for idx, line in enumerate(text.split('\n'), start=1):
            if occurrences[0][:30] in line:
                line_num = idx
                break
        VIOLATIONS.append((
            filepath,
            line_num,
            (
                f"[warning] Sentence appears verbatim {len(occurrences)}x - "
                f"usually a move duplicated by revision; cut one or make the second do new work"
            ),
            snippet,
        ))


# Integral-vs-parenthetical citation: author-as-agent immediately before \citep{}.
# Conservative/advisory: person-implying reporting verbs only, subject must be a
# capitalized non-stoplist token, and the \citep must sit in the same sentence
# (no intervening period) on the same source line. Misses multi-line sentences
# by design, to keep false positives low.
CITEP_REPORTING_VERB_RE = re.compile(
    r"\b([A-Z][A-Za-zÀ-ſ'’-]+(?:\s+(?:and|&)\s+[A-Z][A-Za-zÀ-ſ'’-]+|\s+et\s+al\.?)?)"
    r"\s+(argues?|argued|claims?|claimed|contends?|contended|maintains?|maintained|"
    r"proposes?|proposed|notes?|noted|observes?|observed|writes?|wrote|holds?|held|"
    r"distinguishes?|distinguished|emphasi[sz]es?|emphasi[sz]ed|posits?|posited|"
    r"insists?|insisted|remarks?|remarked|points?\s+out)\b"
    r"[^.]*?\\citep\{"
)
# Capitalized words that are not author surnames (avoid false positives).
CITEP_SUBJECT_STOPLIST = {
    "The", "This", "These", "That", "Those", "It", "We", "They", "He", "She",
    "One", "Here", "There", "Such", "His", "Her", "Their", "Our", "Its", "Some",
    "Many", "Most", "Each", "Both", "Recent", "Earlier", "Prior", "Previous",
    "Other", "Another", "A", "An", "In", "On", "As", "But", "And", "When",
    "While", "If", "Because", "Since", "Although", "However", "Thus", "Moreover",
    "Furthermore", "Nevertheless", "Table", "Figure", "Section", "Chapter",
    "Example", "Work", "Research", "Evidence", "Data", "Analysis", "Approach",
    "Account", "Model", "Framework", "Theory", "Study", "Paper", "Argument",
    "View", "Result", "Results", "Finding", "Findings", "Method", "Literature",
}


def check_file(filepath):
    """Check a single file for style violations."""
    path = Path(filepath)
    if not path.exists():
        print(f"File not found: {filepath}")
        return

    raw_text = path.read_text(encoding='utf-8')
    # Quoted material is the source's wording, not Brett's; never flag inside it.
    text = blank_quoted_spans(raw_text)
    lines = text.split('\n')
    layout_depth = 0
    check_repeated_the_x_is_y_openers(filepath, text)
    check_duplicate_sentences(filepath, text)

    for i, line in enumerate(lines, 1):
        # Skip pure comment lines
        if line.strip().startswith('%'):
            continue

        # Strip inline comments for checking
        line_no_comments = strip_comments(line)
        if not line_no_comments.strip():
            continue

        layout_matches = STRUCTURED_LAYOUT_ENV_RE.findall(line_no_comments)
        begins_layout = sum(1 for kind, _ in layout_matches if kind == 'begin')
        ends_layout = sum(1 for kind, _ in layout_matches if kind == 'end')
        inline_layout_row = '&' in line_no_comments and '\\\\' in line_no_comments
        in_structured_layout = layout_depth > 0 or begins_layout > 0 or inline_layout_row

        # 1. Brackets inside italics: \textit{(text)} or \emph{(text)}
        if re.search(r'\\(textit|emph)\{[^}]*[\(\)\[\]]', line_no_comments):
            match = re.search(r'\\(textit|emph)\{([^}]*)\}', line_no_comments)
            if match and re.search(r'[\(\)\[\]]', match.group(2)):
                VIOLATIONS.append((filepath, i, "Brackets inside italics", line.strip()))

        # 2. Em-dash (---) instead of en-dash (--)
        if '---' in line_no_comments:
            VIOLATIONS.append((filepath, i, "Em-dash (---) - use en-dash with spaces (~-- )", line.strip()))

        # 2b. Author-as-agent before \citep{} - integral citation candidate (advisory)
        cite_match = CITEP_REPORTING_VERB_RE.search(line_no_comments)
        if cite_match and cite_match.group(1).split()[0] not in CITEP_SUBJECT_STOPLIST:
            VIOLATIONS.append((filepath, i, "Author-as-agent before \\citep{} - consider integral \\textcite{} (\"Author (Year) argues ...\")", line.strip()))

        # 3. Raw \textit where semantic macro should be used
        if (
            not in_structured_layout
            and re.search(r'\\textit\{[a-z]+\}', line_no_comments)
            and not re.search(r'\\textit\{\\', line_no_comments)
        ):
            match = re.search(r'\\textit\{([a-z]+)\}', line_no_comments)
            if match:
                word = match.group(1)
                # Don't flag common non-term uses
                if word not in ['et', 'al', 'ibid', 'sic', 'passim', 'circa', 'inter', 'alia', 'per', 'se', 'de', 'facto', 'priori', 'posteriori']:
                    VIOLATIONS.append((filepath, i, f"Raw \\textit{{{word}}} - consider \\term{{}} or \\mention{{}}", line.strip()))

        # 4. Straight quotes or LaTeX quotes instead of \enquote
        # 4a. LaTeX-style backtick quotes
        if re.search(r"``[^']+''", line_no_comments):
            VIOLATIONS.append((filepath, i, "LaTeX quotes `` '' - use \\enquote{}", line.strip()))

        # 4b. Straight double quotes (but not in commands or as inch marks after numbers)
        if re.search(r'"[^"]+?"', line_no_comments):
            # Skip if inside a LaTeX command argument or after a number (inch marks)
            if not re.search(r'\\[a-z]+\{[^}]*"', line_no_comments) and not re.search(r'\d"', line_no_comments):
                VIOLATIONS.append((filepath, i, "Straight double quotes - use \\enquote{}", line.strip()))

        # 4c. Single quotes - only flag genuine quoted strings, not contractions/possessives
        if has_real_single_quotes(line_no_comments):
            VIOLATIONS.append((filepath, i, "Single quotes for quotation - use \\enquote{}", line.strip()))

        # 5. Underscore subscript in prose (not math mode)
        # More careful: check we're not in math mode, file paths, URLs, or command arguments
        if '$' not in line_no_comments and re.search(r'_[a-z]', line_no_comments):
            # Skip if it's:
            # - part of a command name like \text_something
            # - inside braces of common commands (file paths, citations, labels)
            # - looks like a filename (has extension)
            # - inside a URL
            skip_underscore = (
                re.search(r'\\[a-z]*_', line_no_comments) or
                re.search(r'\\(includegraphics|input|include|citep?|citet?|textcite|ref|label|cite)\s*(\[[^\]]*\])?\s*\{[^}]*_', line_no_comments) or
                re.search(r'_[a-z]+\.(pdf|png|jpg|tex|bib|csv|txt)', line_no_comments, re.IGNORECASE) or
                re.search(r'\\url\{[^}]*_', line_no_comments) or
                re.search(r'https?://[^\s}]*_', line_no_comments)
            )
            if not skip_underscore:
                VIOLATIONS.append((filepath, i, "Underscore subscript - use \\textsubscript{}", line.strip()))

        # 6. Hackneyed connectives/adverbs
        line_lower = line_no_comments.lower()
        hackneyed = [
            (r'\bmoreover\b', 'moreover'),
            (r'\bfurthermore\b', 'furthermore'),
            (r'\bnevertheless\b', 'nevertheless'),
            (r'(?:^|,\s*)however\b', 'however'),
            (r'(?:^|,\s*)thus\b', 'thus'),
            (r'(?:^|,\s*)hence\b', 'hence'),
            (r'\btherefore\b', 'therefore'),
            (r'\bconsequently\b', 'consequently'),
            (r'\baccordingly\b', 'accordingly'),
            (r'\badditionally\b', 'additionally'),
        ]
        for pattern, name in hackneyed:
            if re.search(pattern, line_lower):
                VIOLATIONS.append((filepath, i, f"Hackneyed connective/adverb '{name}' - prefer simple coordinators", line.strip()))

        # 7. Throat-clearers
        throat_clearers = [
            r'it is important to note',
            r'it should be (noted|mentioned)',
            r'it is worth (noting|mentioning)',
            r'it must be (noted|emphasized)',
            r'it bears (mentioning|noting)',
            r'needless to say',
        ]
        for pattern in throat_clearers:
            if re.search(pattern, line_lower):
                VIOLATIONS.append((filepath, i, "Throat-clearer - delete or rephrase", line.strip()))

        # 8. "crucially" - banned word
        if re.search(r'\bcrucially\b', line_lower):
            VIOLATIONS.append((filepath, i, "'crucially' - banned; rephrase", line.strip()))

        # 9. "wh-" terminology - banned prefix in prose
        # Skip if in a command or clearly code
        if re.search(r'\bwh-', line_lower) and not re.search(r'\\', line_no_comments[:20] if len(line_no_comments) > 20 else line_no_comments):
            VIOLATIONS.append((filepath, i, "'wh-' prefix - use 'interrogative' or specific term", line.strip()))

        # 10. "data" as plural (data are, data were, data have, these data, those data)
        if re.search(r'\bdata\s+(are|were|have|show|suggest|indicate)\b', line_lower):
            VIOLATIONS.append((filepath, i, "'data' as plural - house style uses singular", line.strip()))
        if re.search(r'\b(these|those)\s+data\b', line_lower):
            VIOLATIONS.append((filepath, i, "'these/those data' - house style uses singular", line.strip()))

        # 11. Contrastive "yet" - prefer "but"
        if re.search(r',\s*yet\b', line_lower):
            VIOLATIONS.append((filepath, i, "Contrastive 'yet' - prefer 'but'", line.strip()))

        # 12. "class" as synonym for category
        for pattern, label in CATEGORY_CLASS_PATTERNS:
            if pattern.search(line_no_comments):
                VIOLATIONS.append((filepath, i, f"'{label}' - use 'category' unless explicitly contrasting HPC class", line.strip()))

        # 13. "do real work" metaphor
        if REAL_WORK_METAPHOR_RE.search(line_no_comments):
            VIOLATIONS.append((
                filepath,
                i,
                "'do real work' metaphor - say what the expression, contrast, or argument does",
                line.strip(),
            ))

        # 14. "the present" self-reference
        if PRESENT_SELF_REFERENCE_RE.search(line_no_comments):
            VIOLATIONS.append((
                filepath,
                i,
                "'the present' self-reference - use 'I', 'this paper', 'the account', or the specific claim",
                line.strip(),
            ))

        # 15. Oxford spelling: -ise/-isation should be -ize/-ization
        # Exception list: words where -ise is part of the root (not Greek -izo)
        oxford_exceptions = {
            'advertise', 'advise', 'apprise', 'arise', 'chastise',
            'circumcise', 'comprise', 'compromise', 'demise', 'despise',
            'devise', 'disguise', 'enterprise', 'excise', 'exercise',
            'expertise', 'franchise', 'improvise', 'incise', 'merchandise',
            'otherwise', 'paradise', 'poise', 'praise', 'precise',
            'promise', 'premise', 'reprise', 'revise', 'supervise',
            'surmise', 'surprise', 'televise', 'treatise', 'wise',
            'noise', 'guise', 'bruise', 'cruise', 'raise', 'mise',
            # Not -ise/-ize alternations at all (different etymology)
            'rise', 'likewise', 'clockwise', 'counterclockwise',
            'lengthwise', 'stepwise', 'pairwise', 'crosswise',
        }
        # Match words ending in -ise, -ised, -ises, -ising, -isation, -isations
        for m in re.finditer(r'\b([a-z]+(?:ise[ds]?|ising|isations?))\b', line_lower):
            word = m.group(1)
            # Strip suffix to get the base for exception check
            base = re.sub(r'(isations?|ised|ises|ising)$', 'ise', word)
            if base not in oxford_exceptions:
                ize_form = word.replace('isation', 'ization').replace('ising', 'izing').replace('ised', 'ized').replace('ises', 'izes').replace('ise', 'ize')
                VIOLATIONS.append((filepath, i, f"Oxford spelling: '{word}' -> '{ize_form}'", line.strip()))

        # 16. Uncontracted subject + auxiliary/copula forms
        check_uncontracted_subject_aux(filepath, i, line_no_comments)

        # 17. Modal "must" - too strong for ordinary house-style prose
        if re.search(r'\bmust\b', line_lower):
            # Skip if in a quote or object-language mention.
            if not re.search(r'\\enquote|\\textit|\\mention', line_no_comments):
                VIOLATIONS.append((filepath, i, "Modal 'must' - prefer 'have to', 'should', or a more precise claim", line.strip()))

        # === STRICT MODE CHECKS (advisory) ===
        if STRICT_MODE:
            # 18. Sentence starting with "This" without clear referent
            if re.search(r'^\s*This\s+(is|was|has|does|shows|suggests|means)\b', line):
                VIOLATIONS.append((filepath, i, "[advisory] 'This [verb]' - consider adding noun for clarity", line.strip()))

        layout_depth = max(0, layout_depth + begins_layout - ends_layout)

# === Sentence-length distribution =========================================
# Models cluster sentence length in a narrow mid band, and the uniformity is
# more detectable than any individual word. This reports the distribution
# rather than ruling on it: no threshold can tell a well-judged run of
# similar-length sentences from a flattened one. Advisory only; never affects
# the exit code.

LENGTH_REPORTS = []

# Periods that do not end a sentence.
ABBREV_RE = re.compile(
    r"\b(?:e\.g|i\.e|cf|vs|etc|al|pp|p|ch|figs?|tbl|eds?|no|vol|ca|approx|"
    r"St|Dr|Prof|Mr|Ms|Mrs|Jr|Sr)\.",
    re.IGNORECASE,
)
INITIAL_RE = re.compile(r"\b([A-Z])\.(?=\s*[A-Z])")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’-]*")

# Bucket edges for the histogram (lower bound of each bucket).
LENGTH_BUCKETS = [(1, 9), (10, 14), (15, 19), (20, 24), (25, 29), (30, 34), (35, 39), (40, None)]
NARROW_BAND = (12, 26)
NARROW_BAND_SHARE = 0.60
MIN_SENTENCES_TO_REPORT = 15
MIN_SENTENCES_TO_JUDGE = 40
# Below this median the extraction is dominated by examples, glosses, box
# contents, and list scraps rather than running prose, and the spread says
# nothing about rhythm. Report the numbers, withhold the judgement.
MIN_MEDIAN_TO_JUDGE = 12
FLAT_IQR = 7
SHORT_SENTENCE_MAX = 9
SHORT_SENTENCE_SHARE = 0.05


# Math, citations, and cross-references are single tokens for length purposes:
# left alone, strip_latex turns them into stray words and their internal
# punctuation splits one sentence into several.
MATH_SPAN_RE = re.compile(r"\\\[.*?\\\]|\\\(.*?\\\)|\$\$.*?\$\$|\$[^$]*\$", re.DOTALL)
CITE_LIKE_RE = re.compile(
    r"\\(?:cite[a-z]*|textcite|parencite|footcite|ref|eqref|autoref|pageref|label|"
    r"url|href|includegraphics)\s*(?:\[[^\]]*\])*\s*(?:\{[^{}]*\})+",
    re.IGNORECASE,
)
TABLE_ROW_RE = re.compile(r"^(?=[^\n]*&)[^\n]*\\\\[^\n]*$", re.MULTILINE)
DOC_BODY_RE = re.compile(r"\\begin\{document\}(.*?)(?:\\end\{document\}|\Z)", re.DOTALL)
# Whole environments whose bodies are not prose. iter_paragraphs_with_lines
# drops the \begin and \end lines but keeps everything between them.
NON_PROSE_ENV_RE = re.compile(
    r"\\begin\{(equation|align|gather|multline|eqnarray|array|displaymath|"
    r"tikzpicture|tabular|tabularx|longtable|verbatim|lstlisting|forest)\*?\}"
    r".*?\\end\{\1\*?\}",
    re.DOTALL,
)


def prose_for_length_check(paragraph):
    """Reduce a paragraph to countable prose, math and citations as one token."""
    text = CITE_LIKE_RE.sub(" CITE ", paragraph)
    text = MATH_SPAN_RE.sub(" MATH ", text)
    return strip_latex(text)


def split_sentences(prose):
    """Split stripped prose into sentences, protecting abbreviation periods."""
    text = re.sub(r"\s+", " ", prose).strip()
    if not text:
        return []
    protected = ABBREV_RE.sub(lambda m: m.group(0).replace(".", "\x00"), text)
    protected = INITIAL_RE.sub(lambda m: m.group(1) + "\x00", protected)
    parts = re.split(r"(?<=[.!?])\s+", protected)
    return [part.replace("\x00", ".").strip() for part in parts if part.strip()]


def percentile(sorted_values, fraction):
    """Nearest-rank percentile; sorted_values must be non-empty."""
    index = int(round(fraction * (len(sorted_values) - 1)))
    return sorted_values[index]


def check_sentence_lengths(filepath):
    """Collect the sentence-length distribution for a file."""
    path = Path(filepath)
    text = blank_quoted_spans(path.read_text(encoding="utf-8"))
    # Preamble macros and \input lines are not prose. Body only, where there is one.
    body = DOC_BODY_RE.search(text)
    if body:
        text = body.group(1)
    # Equation and tabular bodies are data, not prose; iter_paragraphs_with_lines
    # only skips the surrounding \begin/\end lines.
    text = NON_PROSE_ENV_RE.sub("", text)
    text = TABLE_ROW_RE.sub("", text)

    lengths = []
    for _line_num, paragraph in iter_paragraphs_with_lines(text):
        for sentence in split_sentences(prose_for_length_check(paragraph)):
            count = len(WORD_RE.findall(sentence))
            # Sub-3-word fragments are captions, stray macros, and list scraps.
            if count >= 3:
                lengths.append(count)

    if len(lengths) < MIN_SENTENCES_TO_REPORT:
        return

    ordered = sorted(lengths)
    n = len(ordered)
    q1, median, q3 = (percentile(ordered, f) for f in (0.25, 0.5, 0.75))
    mean = sum(ordered) / n
    low, high = NARROW_BAND
    in_band = sum(1 for length in ordered if low <= length <= high)
    short = sum(1 for length in ordered if length <= SHORT_SENTENCE_MAX)

    notes = []
    if n < MIN_SENTENCES_TO_JUDGE:
        notes.append(("note", f"{n} sentences is too small a sample to judge rhythm; numbers only"))
    elif median < MIN_MEDIAN_TO_JUDGE:
        notes.append((
            "note",
            f"median {median} words suggests examples, glosses, or box and list content "
            "dominate the extraction; numbers only",
        ))
    else:
        if in_band / n >= NARROW_BAND_SHARE:
            notes.append((
                "advisory",
                f"{in_band / n:.0%} of sentences fall in {low}-{high} words; "
                "the band is narrow, so check whether the rhythm has flattened",
            ))
        if q3 - q1 <= FLAT_IQR:
            notes.append((
                "advisory",
                f"middle half spans only {q3 - q1} words ({q1}-{q3}); "
                "uniform length is more detectable than any single word choice",
            ))
        if short / n < SHORT_SENTENCE_SHARE:
            notes.append((
                "advisory",
                f"short sentences (<={SHORT_SENTENCE_MAX} words) are {short / n:.0%} of the total; "
                "house style allows occasional short sentences",
            ))

    LENGTH_REPORTS.append({
        "filepath": filepath,
        "n": n,
        "median": median,
        "mean": mean,
        "q1": q1,
        "q3": q3,
        "lengths": ordered,
        "notes": notes,
    })


def print_length_reports():
    """Print sentence-length distributions (advisory; no exit-code effect)."""
    if not LENGTH_REPORTS:
        return

    print(f"\n{'='*60}")
    print("SENTENCE LENGTH")
    print(f"{'='*60}")

    for report in LENGTH_REPORTS:
        n = report["n"]
        print(f"\n  --- {report['filepath']} ---")
        print(
            f"    {n} sentences | median {report['median']} | mean {report['mean']:.1f} | "
            f"middle half {report['q1']}-{report['q3']} ({report['q3'] - report['q1']} words)"
        )

        counts = []
        for low, high in LENGTH_BUCKETS:
            hits = sum(
                1 for length in report["lengths"]
                if length >= low and (high is None or length <= high)
            )
            label = f"{low}+" if high is None else f"{low}-{high}"
            counts.append((label, hits))

        widest = max(hits for _label, hits in counts) or 1
        for label, hits in counts:
            bar = "#" * int(round(24 * hits / widest))
            print(f"      {label:>6}  {bar:<24} {hits:>4}  {hits / n:>4.0%}")

        for level, note in report["notes"]:
            print(f"    [{level}] {note}")

    print()


def print_violations():
    """Print all violations found."""
    if not VIOLATIONS:
        print("No style violations found.")
        return

    print(f"\nFound {len(VIOLATIONS)} potential style violation(s):\n")

    current_file = None
    for filepath, line_num, issue, context in VIOLATIONS:
        if filepath != current_file:
            print(f"\n=== {filepath} ===")
            current_file = filepath
        print(f"  Line {line_num}: {issue}")
        # Truncate long lines
        if len(context) > 80:
            context = context[:77] + "..."
        print(f"    {context}")


def print_ai_findings():
    """Print AI voice detection results."""
    if not AI_FINDINGS:
        return

    print(f"\n{'='*60}")
    print("AI VOICE CHECK")
    print(f"{'='*60}")

    # Separate word-density findings (line 0), phrase clusters, and construction patterns.
    density_findings = [f for f in AI_FINDINGS if f[1] == 0]
    phrase_findings = [f for f in AI_FINDINGS if f[1] != 0 and f[2].startswith("AI phrase:")]
    pattern_findings = [f for f in AI_FINDINGS if f[1] != 0 and not f[2].startswith("AI phrase:")]

    for filepath, _, issue, words in density_findings:
        print(f"\n  {issue}")
        print(f"    Words found: {words}")

    if pattern_findings:
        grouped_patterns = {}
        for filepath, line_num, issue, context in pattern_findings:
            grouped_patterns.setdefault(filepath, []).append((line_num, issue, context))

        for filepath, items in grouped_patterns.items():
            print(f"\n  --- {filepath} ---")
            for line_num, issue, context in items:
                if len(context) > 100:
                    context = context[:97] + "..."
                print(f"    Line {line_num}: {issue}")
                print(f"      {context}")

    if phrase_findings:
        grouped = {}
        for filepath, line_num, issue, _context in phrase_findings:
            grouped.setdefault(filepath, []).append((line_num, issue))

        for filepath, items in grouped.items():
            if len(items) < AI_PHRASE_CLUSTER_THRESHOLD:
                continue

            phrase_counts = {}
            phrase_lines = {}
            for line_num, issue in items:
                match = re.search(r'"([^"]+)"', issue)
                phrase = match.group(1) if match else issue
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
                phrase_lines.setdefault(phrase, []).append(str(line_num))

            parts = []
            for phrase, count in sorted(phrase_counts.items(), key=lambda item: (-item[1], item[0])):
                line_list = ','.join(phrase_lines[phrase][:4])
                if len(phrase_lines[phrase]) > 4:
                    line_list += ',...'
                parts.append(f'"{phrase}" x{count} [lines {line_list}]')

            first_line = min(line_num for line_num, _issue in items)
            n_lines = len({line_num for line_num, _issue in items})
            summary = '; '.join(parts)
            if len(summary) > 220:
                summary = summary[:217] + '...'

            print(f"\n  --- {filepath} ---")
            print(
                f"    Line {first_line}: AI phrase cluster - {len(items)} signature phrase hits across {n_lines} lines"
            )
            print(f"      {summary}")

    print()

def main():
    global STRICT_MODE

    args = sys.argv[1:]

    if not args or '-h' in args or '--help' in args:
        print("Usage: python check-style.py [--strict] [--no-ai] [--no-lengths] file.tex [file2.tex ...]")
        print("")
        print("Options:")
        print("  --strict       Include advisory checks (vague 'This')")
        print("  --no-ai        Skip AI voice detection")
        print("  --no-lengths   Skip the sentence-length distribution report")
        print("")
        print("Style checks: em-dashes, raw \\textit, straight quotes, brackets in italics,")
        print("  hackneyed connectives/adverbs, modal 'must', throat-clearers, 'crucially', 'wh-' prefix,")
        print("  'data' as plural, contrastive 'yet',")
        print("  class-as-category terminology, underscore subscripts, Oxford spelling (-ize not -ise),")
        print("  uncontracted subject + auxiliary and negative auxiliary forms")
        print("")
        print("AI voice check:")
        print("  Words:   co-occurrence density, repeated high-signal word incidence, filler intensifiers")
        print("  Phrases: clustered advisory when 3+ generic framing phrases recur in a file")
        print("  Patterns: advisory line items for contrastive and corrective negation, trailing")
        print("    evaluative -ing, false ranges, while-maintaining frames, weasel attribution, triads")
        print("")
        print("Sentence length:")
        print("  Distribution report (median, middle half, histogram) with advisories when the")
        print("  spread is narrow, the middle half is flat, or short sentences are nearly absent")
        sys.exit(0)

    if '--strict' in args:
        STRICT_MODE = True
        args.remove('--strict')

    skip_ai = '--no-ai' in args
    if skip_ai:
        args.remove('--no-ai')

    skip_lengths = '--no-lengths' in args
    if skip_lengths:
        args.remove('--no-lengths')

    if not args:
        print("Error: No files specified")
        sys.exit(1)

    for filepath in args:
        check_file(filepath)
        if not skip_ai:
            check_ai_voice(filepath)
        if not skip_lengths:
            check_sentence_lengths(filepath)

    print_violations()
    print_ai_findings()
    print_length_reports()

    # Exit with error code if violations found (AI findings are advisory, don't affect exit code)
    sys.exit(1 if VIOLATIONS else 0)

if __name__ == '__main__':
    main()
