# Brett Reynolds House Style Guide

**Version:** 2.2.0 (LLM tic-and-shadow update)
**For:** LaTeX academic papers in linguistic typology

This guide documents LaTeX conventions and writing style for academic papers. See `preamble.tex` for the corresponding LaTeX macros, `style-rules.yaml` for machine-readable rules, and `docs/plans/typography-design.md` for the full typography specification.

## Typography Overview

- **Font:** EB Garamond with old-style numerals; Charis SIL for IPA
- **Layout:** Letter paper with book-like asymmetric margins
- **Headings:** Small caps sections, italic subsections (Bringhurst-inspired)
- **Links:** Dark maroon (#800020)

## LaTeX Quick Reference (Agent Brief)

The condensed directive for `.tex` edits. Full per-rule detail in the sections below.

<!-- claude-rule: latex-house-style -->
# LaTeX House Style

**Every edit to a .tex file must follow these rules. No exceptions.**

| Rule | Wrong | Right |
|------|-------|-------|
| Brackets upright | `\textit{(text)}` | `(\textit{text})` |
| En-dash, not em | `text---more` | `text~-- more` |
| Semantic macros | `\textit{definiteness}` | `\term{definiteness}` (concepts) |
| | `\textit{the}` | `\mention{the}` (forms) |
| Mentions in headings | `\subsection{The \mention{the}}` | `\subsection{The \mentionhead{the}}` |
| Quotations | `"text"` or `` ``text'' `` | `\enquote{text}` |
| Subscripts | `_eng` | `\textsubscript{eng}` |
| Category terminology | `word class` | `category` |

## Critical LaTeX Conventions

- **References**: Always `\clearpage` before `\printbibliography`
- **Keywords**: Papers should include keywords by default; keep the visible keyword line after the abstract and `pdfkeywords` metadata in sync
- **Terms, mentions, quotations**: `\term{}` for concepts (small caps), `\mention{}` for forms (italics), `\enquote{}` for quotations
- **Cross-linguistic notation**: `\textsc{subject}\crossmark` for comparative concepts, `\textsc{subject}\textsubscript{eng}` for language-specific
- **Dashes**: en-dash with spaces for parenthetical (`~-- text~--`), en-dash no spaces for ranges (`2001--2025`)
- **Examples**: `langsci-gb4e` package, use `\ea ... \z` (no `exe` environment)
- **Citations**: `\citep{}` parenthetical, `\textcite{}` narrative, `\citealp{}` when the citation sits inside a parenthesis you already opened (a gloss, an aside), since `\citep{}` would double the brackets. `\parencite{}`/`\textcite{}` are the biblatex-native equivalents and render identically under the house `apa`+`natbib=true` setup, but `\citep{}` is the house standard; don't introduce `\parencite{}`. (Known deviation as of 2026-07-24: the AI-evaluation papers `delegation-assurance` and `adversarial-pragmatics` carry many `\parencite{}` calls, `evidentiary-assurance` uses `\citep{}`; normalize toward `\citep{}` at polish.) <!--asof:2026-07 verify:grep -rqI parencite --include=*.tex papers/-->

## Tools

- `/check-style` - Slash command to audit a file for violations
- `.house-style/check-style.py main.tex` - Linter script
<!-- /claude-rule -->

## Quarto Quick Reference (Agent Brief)

The condensed directive for `.qmd` edits.

<!-- claude-rule: quarto-house-style -->
# Quarto House Style

**Every edit to a .qmd file must follow these rules. No exceptions.**

| Rule | Wrong | Right |
|------|-------|-------|
| Semantic spans | `*definiteness*` | `[definiteness]{.term}` (concepts) |
| | `*the*` | `[the]{.mention}` (forms) |
| Quotations | `'text'` | `"text"` (Pandoc smart-quotes) |
| En-dash, not em | `text---more` | `text -- more` |
| Citations | `(Author 2020)` | `[@key]` or `@key` |

Import the shared theme: `theme: [default, path/to/quarto-theme.scss]`
Full mapping: `.house-style/style-rules.yaml` (quarto section)
Quarto theme: `.house-style/quarto-theme.scss`
<!-- /claude-rule -->

## Table of Contents

1. [Brackets](#brackets)
2. [Terms, Mentions, and Quotations](#terms-mentions-and-quotations)
3. [Dashes, Ranges, Hyphens](#dashes-ranges-hyphens)
4. [Contractions and Plain Style](#contractions-and-plain-style)
5. [Numbered Examples](#numbered-examples)
6. [Category vs. Function](#category-vs-function)
7. [Citations](#citations)
8. [Journal Article Formatting](#journal-article-formatting)
9. [Dual-Audience Accessibility](#dual-audience-accessibility)
10. [BibTeX Conventions](#bibtex-conventions)
11. [Python Plot Style](#python-plot-style)
12. [Figure Design](#figure-design)
13. [Slide Presentations (Quarto)](#slide-presentations-quarto)

---

## Brackets

**Rule:** Brackets (parentheses, square brackets, braces) should always be upright (roman), never italicized - even when the text inside is italic.

```latex
% Correct
(\textit{the dog})
[\textit{NP}]

% Wrong - brackets inherit italic
\textit{(the dog)}
```

---

## Terms, Mentions, and Quotations

**Rule:** Distinguish between terms (concepts being defined), mentions (forms under discussion), and quotations.

### Three Semantic Macros

| Purpose | Macro | Rendering | Example |
|---------|-------|-----------|---------|
| Terms (concepts) | `\term{definiteness}` | small caps | The notion of \term{definiteness} is complex. |
| Mentions (forms) | `\mention{the}` | italics | The word \mention{the} is a determinative. |
| Mentions in headings | `\mentionhead{the}` | normal lowercase italics | `\section{The word \mentionhead{the}}` |
| Object language | `\olang{der Hund}` | italics | German \olang{der Hund} 'the dog' |
| Quotations | `\enquote{text}` | curly quotes | As \enquote{going forward} spread... |

**Important:** In headings (section, subsection, etc.), use `\mentionhead{}` instead of `\mention{}`. It renders as ordinary lowercase italic mention text, not slanted small caps, and is robust in moving arguments such as section headings and table-of-contents entries.

### Examples

- **Term:** `\term{definiteness}` involves identifiability and uniqueness.
- **Mention:** The determinative `\mention{the}` is not always definite.
- **Object language:** German `\olang{der Hund}` 'the dog'
- **Quotation:** `\enquote{Outer with an \enquote{inner} quote}`
- **Semantic meanings:** use single 'quote'

**Note:** `\term{}` is now small caps (was italics in v1). Use `\mention{}` for the old italics behavior.

---

## Dashes, Ranges, Hyphens

### Parenthetical Asides
Use an en dash (`--`) with surrounding spaces:

```latex
the category is stable~-- within limits~-- across registers
```

### Ranges and Relations
Use an en dash (no spaces):

```latex
2001--2025
pp.\ 113--127
the form--function distinction
```

### Compounds
Use hyphens only:

```latex
corpus-based study
task-specific rubric
```

---

## Contractions and Plain Style

**Contractions are preferred:**

> We don't gain anything by multiplying categories.

### Delete Throat-Clearers

❌ **Avoid:** "It is important to note that the results clearly show that..."
✅ **Prefer:** "The results show..."

❌ **Avoid:** Meta-commentary labels like "A note on X:...", "A caveat on the 'payoff' idiom:...", "An aside on..."
✅ **Prefer:** Just say the thing directly, or integrate it into the prose.

### No Metacommentary Frames

Never announce an observation, objection, or point before making it. Metacommentary frames perform thoroughness rather than being thorough. They add words and subtract confidence.

❌ **Avoid:** "A potential worry:" / "A related concern is that" / "One might object that" / "It's worth noting that" / "An important point here is"
✅ **Prefer:** Just state the fact. "A potential worry: X is fragile" means "X is fragile." Say "X is fragile."

The test: if deleting the frame leaves the sentence intact and more direct, the frame was metacommentary. Delete it.

❌ **Avoid:** "A potential worry: identification shapes production, and production signals identification."
✅ **Prefer:** "Identification shapes production, and production signals identification."

### No Corrective Framing by Default

The "it isn't X; it's Y" construction (*correctio*) is massively overused by LLMs. It defines by negation, privileges the misconception by putting it first, and creates a combative rhythm. State what something is. Don't define by what it isn't unless the misconception is so prevalent that readers will actively misunderstand without the correction.

❌ **Avoid:** "It isn't a taxonomy; it's a conditioning structure."
✅ **Prefer:** "It's a conditioning structure."

❌ **Avoid:** "The contribution isn't empirical; it's conceptual."
✅ **Prefer:** "The contribution is conceptual."

The test: does the reader actually hold the misconception? If yes, the negation earns its place. If you're correcting a position nobody holds, you're shadow-boxing. One *correctio* per paper is plenty. More than that and the paper sounds like it's arguing with an imaginary opponent in every paragraph.

### Banned Modals

❌ **Avoid:** The modal "must" (e.g., "The features must cluster reliably")
✅ **Prefer:** "have to" or softer phrasing (e.g., "The features have to cluster" or just "cluster reliably")

### Simple Coordinators

Prefer simple coordinators (and, but) to hackneyed "academic" connectives (moreover, furthermore, nevertheless, however).

❌ **Avoid:** Contrastive "yet" (e.g., "The pattern is clear, yet exceptions remain")
✅ **Prefer:** Simple "but" (e.g., "The pattern is clear, but exceptions remain")

Sentence-initial coordinators are fine where they improve flow. Avoid overuse.

### Banned Sentence Adverbs

❌ **Crucially** – Find a better way to signal importance, or let the content speak for itself.

### Data is Singular

Treat *data* as a mass noun taking singular agreement:

✅ **Correct:** "The data shows a clear pattern."
✅ **Correct:** "This data is consistent with the hypothesis."
❌ **Avoid:** "The data show..." / "These data are..."

### Avoid "wh-" Terminology

Don't use *wh-words*, *wh-fronting*, *wh-movement*, etc. Use precise functional or categorial terms instead.

| ❌ Avoid | ✅ Prefer |
|----------|-----------|
| wh-words | interrogative words, relative words, or specify: *who*, *what*, *which* |
| wh-fronting | interrogative fronting, or describe the construction |
| wh-movement | interrogative displacement, relative clause formation |
| wh-clause | interrogative clause, relative clause, exclamative clause |

**Rationale:** "Wh-" conflates interrogatives, relatives, and exclamatives, which have distinct syntax. It also fails for *how* (interrogative but not wh-). Be precise about which construction or category you mean.

### AI Tics

Phrase- and frame-level tics that mark text as AI-generated. Avoid in production prose; flag in editing.

<!-- claude-rule: writing-style -->
- Contractions preferred
- ~60 word paragraphs (max 100)
- Avoid: throat-clearers, `\paragraph{}` headings, hackneyed adverbs (moreover, furthermore)
- Avoid AI tics. The phrase- and frame-level ones: "It is important to note that," "complex and multifaceted," "not merely X but Y" as a repeated frame, "not only X but Y," "not because X but because Y," "challenging traditional paradigms," "in conclusion," "in summary," "overall," "in a world where...," "in today's fast-paced world," "in the ever-evolving landscape of X," "at the intersection of X and Y," "the rise of," "deep dive," "treasure trove," "step-by-step," "it's not about X, it's about Y."
- **Praise-as-structure cluster (very high signal):** treating a sentence, phrase, post, or tweet as if it were structural engineering. "load-bearing" (as analytical metaphor), "X is doing the heavy lifting," "do/does/did/doing real work," "the post/sentence deserves the weight," "I keep coming back to this [tweet/post/line]." These almost always identify the writer as Claude. Just say what the thing does.
- **Faux-coaching / structural-spine cluster (very high signal):** don't let the prose perform an expert giving live feedback to the writer. Avoid "Let me refine your claim," "the one place I'd still push," "because I think it matters," "you're doing zero moves there," "the gap is what's interesting," "the tell is," "content-clothes," "the content isn't actually there," "structural spine," "pull one, and the other goes inert." These are LLM-coaching tics: intimate, overconfident, metaphor-heavy, and analytically hollow. Replace them with the actual claim, evidence, and consequence.
- **No profundity from emptiness.** Don't turn absence into an aphorism unless the argument has earned it. Sentences like "the emptiness of the string IS its lack of content" or "the gap is what matters" often convert a missing argument into a stylized revelation. State the relation plainly: the expression has no content; therefore it cannot support the inference, contrast, or test being proposed.
- **Colon reveals.** Don't use a colon (or an em-dash) to stage a drumroll and then drop a payload: "The best part: it learns," "And the result: silence," "One catch: it's slow." The punctuation promises a reveal the content rarely earns, and the withheld-then-delivered rhythm is a very common AI tic. State it in one clause ("it learns, which is the useful part") or just say the thing ("it learns"). Keep the colon for genuine apposition, lists, ratios, and quotation.
- **Faux-insight setups.** Don't preface a claim with a frame that promises suppressed or insider knowledge: "What nobody tells you is…," "Here's what most people miss," "The dirty secret is…," "What they don't want you to know." The setup borrows authority the claim hasn't earned and implies a hidden truth where there's usually just a claim. Make the claim directly; if it really is under-appreciated, show why with evidence rather than announcing that it is.
- **Restatement-as-revelation cluster (high signal):** don't fake an insight by repeating and rearranging a couple of key words across a clause and landing on a tidy abstraction. "The direction you noticed is real, but it's the direction of projection, and a causal effect is one kind of projection" rotates *direction* and *projection* to sound like an arrival while only re-saying "a causal effect is a special case," a point already made one sentence earlier. "But the projections split into two grades, and the split matters" has the same problem: it repeats *split* and lands on *matters* instead of saying what follows. Tells: a sentence whose payload is a word lifted from the previous sentence; a rule-of-three crescendo that ends on an abstraction; a clause that re-poses the prior sentence as though advancing. Fix: if the point is already made, cut the sentence; if it isn't, make the new point once, plainly.
- **Corrective negation without an opponent (high signal).** Don't set up a claim by denying something nobody asserted: "the problem isn't the data, it's the inference," "this isn't a matter of taste but of evidence," "it's not that the category is wrong, it's that it does no work." The negation manufactures an interlocutor so the assertion can arrive as a correction, borrowing the authority of a disagreement that never happened. It also costs a clause: the reader processes the false version before getting the real one. Assert the claim once ("the inference is what fails"). Keep the negation only when a position is actually being rejected, and then say whose it is and cite it. This is the general case of the contrastive negation banned in the revision rule below, where the phantom opponent is the draft's own earlier wording.
- **Don't affirm the reader's perception as set-up.** In replies, reviews, and correspondence, cut the tokens that credit the interlocutor's observation in order to stage your own reframing: "the X you noticed is real," "you've put your finger on," "you're right to sense," "good question," "that's exactly the tension." A plain concession is fine and often right ("you're right that it's directed, but the direction runs from what you observe to what you expect"): it grants a flat point and goes straight to the distinction. The tic is the ornament around the concession, not the concession itself.
- **Revise for the end-reader, not the conversation (very high signal).** When feedback corrects a draft (a misattribution, an overstatement, a wrong emphasis), rewrite the passage as if drafting it fresh with the corrected fact. The reader never saw the faulty version, so nothing in the revision may exist to answer it. The failure mode is writing the revision to be legible *as a fix* to the person who complained. Tells: contrastive negation of the old wording ("glossematic drift is not Mortensen's theory; it is Ahlqvist's" replacing "Mortensen's theory of glossematic drift"); the correction promoted to the front of the sentence or paragraph, displacing the argument; the feedback's justification imported as new content (the author's aside that the theory "was common currency by then" surfacing in the text as "by which time it was standard in the field"); a clause engineered so the old reading "can't arise," defending against a misreading only the corrector could make. Salience in the conversation is not salience in the document. The right fix is usually smaller than the discussion, and often a deletion: "Mortensen's theory of glossematic drift" becomes "glossematic drift" with the citation carrying attribution, not a sentence relitigating who originated what. Test each revised sentence: does it serve the paragraph's argument, or does it prove the correction was heard?
- Avoid AI vocabulary, identified empirically by expert human detectors of AI-generated text (Russell, Karpinska, Iyyer 2025, arXiv:2501.15654):
  - **High-signal words to cut or justify:** delve, underscore, showcase/showcasing, tapestry, realm, foster, testament, vibrant, pivotal, groundbreaking, transformative, profound, paramount, seamless, comprehensive, curated, crafted, whimsical, quirky, elegant, meticulous, invaluable, noteworthy, ever-evolving, multifaceted, holistic, nuanced, leverage, utilize.
  - **`robust` is a term of art here, not a tic.** 670 uses across 231 of Brett's `.tex` files, nearly all technical: robustness check, robustness test, robustness under perturbation, a robustness criterion for mechanistic categories. Keep those. Cut it only in the appraisal slot, where it modifies an abstraction instead of naming something that was tested ("robust framework", "robust evidence"). It sits outside the high-signal list because it doesn't belong in a run of words like *tapestry* and *whimsical*, which have no technical use here at all.
  - **Watch for overuse:** potential, findings, crucial, essential, significant, key, valuable, meaningful, diverse, complex, creative, critical, landscape, enhance, navigate, journey, streamline, dynamic.
  - **AI adverbs:** additionally, aptly, creatively, moreover, successfully. Most are removable without loss.
  - **Filler intensifiers:** genuinely, really, truly, actually. These raise the writer's commitment without changing the claim, and they usually delete cleanly ("this genuinely fails" is "this fails"). Keep one only where it marks a real contrast with something stated (an apparent case against an actual one).
  - The principle is incidence and distribution, not blanket prohibition. One use of a word may be harmless; repeated use in one article usually needs pruning unless the word has a technical reason to be there. As a working threshold, a high-signal non-technical word appearing more than once in an article should be reviewed, and recurrence across Brett's papers should be watched as a house-style drift. The discriminator is the slot the word sits in: inside a technical collocation naming something measured or tested, it's usually earning its place ("robustness check"); modifying an abstraction, it usually isn't ("robust framework"). When unsure, count it in the corpus. `profound`, `nuanced`, and `foster` all run high in Brett's papers and all turn out to be evaluative filler, so frequency alone doesn't settle it.
- Avoid AI structural patterns: formulaic openings that scene-set, immediately quote an authority, or front-load historical context; optimistically vague conclusions; quotes followed by narrative gloss ("she said, gesturing at the city"); generic openers and closers that don't carry information; false ranges ("from intimate gatherings to global movements") where the endpoints don't form a real scale; triadic adjective strings that simulate coverage ("innovative, transformative, and groundbreaking").
- **Avoid unsupported evaluative participial tags.** Final supplements such as "... , highlighting the pattern's importance", "... , underscoring the need for", "... , reflecting broader tensions", "... , cementing its role", or "... , paving the way for" often smuggle appraisal in without evidence. Keep gerund-participial supplements when they supply genuine event structure or share an explicit subject; rewrite when the participle merely evaluates the previous clause.
- **Avoid the `while maintaining/preserving` trade-off frame** unless there is a real trade-off. "The method increases coverage while preserving accuracy" is fine if both quantities are measured; "streamlines the process while maintaining quality" is usually managerial fog.
- **Name sources instead of weasel attribution.** "Some critics argue", "observers have noted", "industry reports suggest", and "research suggests" need a named source, citation, corpus result, or deletion.
- **Integral citation when the author is the agent (a frequent model tic).** When a clause attributes an act to a specific author with a reporting verb (*argues, shows, distinguishes, proposes, notes, finds*), name the author as the grammatical subject and fold the year into it: "Kane (2013, pp. 22–25) distinguishes two moves ...". Models default instead to deferring the citation to an end-of-sentence parenthetical ("... distinguishes two moves ... (Kane, 2013, pp. 22–25)"), which splits the agent from the subject and, when the author is already named in the clause, repeats the name (the clearest tell is a doubled "Kane ... (Kane, 2013)"). Use `\textcite{}` for this, not `\citep{}`. Keep the parenthetical `\citep{}` form where you cite a proposition or finding rather than attribute an act, where several sources back one claim at once, or where a run of integral citations would read like a lit-review march ("X argues ..., Y argues ...").
- Avoid "the present" self-reference for Brett, his arguments, or his papers. Don't write "the present author", "the present paper", "the present study", "the present article", "the present work", "the present analysis", "the present account", "the present argument", "the present proposal", or similar phrases such as "the present chapter" or "the present section". Use "I", "this paper", "this article", "the account", or the specific claim.
- Treat repeated paragraph openers that name the argumentative object rather than making the move as a cadence warning, not a ban: "The claim...", "The account...", "The problem...", "This objection...", and the special case "The X is Y". These openers can be useful when they define a term, protect a needed contrast, or mark a section-level pivot. The issue is distributional: avoid letting the pattern become noticeable, where too many paragraphs begin by placing an object on the table rather than advancing the argument.
- **Paragraph closers need the same scrutiny as openers.** The commoner tic sits at the end: a short sentence that restates the paragraph as though concluding it ("The distinction matters," "So the category does no work here," "That's the whole argument"). It reads as a landing and adds nothing, and a run of them turns a section into a series of beats. A paragraph can stop on its last piece of evidence or its last move; it doesn't have to be sealed. Cut the closer when it only re-says what precedes it; keep it when it states a consequence the reader can't get from the paragraph alone. Distributional again: two or three sealed paragraphs in a row is the signal, not any one of them.
- **Don't stack nouns before the head.** Two or more nouns premodifying a head ("cross-linguistic category boundary stability effects", "corpus-distributional evidence base", "benchmark performance generalization claims") compress relations the reader then has to reconstruct, and they hide which noun is an argument of which. Linguistics prose breeds these because each element is a real technical term. Unpack with prepositions or a finite clause: "how stable category boundaries are across languages", "what the corpus distribution shows". Adjective-plus-noun-plus-noun counts too ("robust evaluation framework"). One premodifying noun is usually fine ("category boundary"); trouble starts at two and worsens with each addition.
- Prefer: direct verbs, simple coordinators (and, but), concrete examples before abstractions, finite agentive clauses when nominalizations have started to carry the argument
- **Punctuation hierarchy for asides:** commas (neutral), parentheses (supplementary, de-emphasized), dashes (emphatic, interruptive). LLMs overuse dashes. Most asides are parenthetical, not dramatic. Use parentheses more, dashes less.
- **Clause-initial PP commas:** prefer a comma after a clause-initial preposition phrase, especially when the PP sets the frame for the clause. Write "For HPC-style work in linguistics, this implies a division of labour", not "For HPC-style work in linguistics this implies a division of labour."
- **Participial adjunct discipline:** gerund-participial adjuncts can repair flat "X, and it/they Y" coordination when the second clause shares a subject and supplies real event structure. But don't overcorrect into the trailing evaluative "-ing" tic ("..., highlighting", "..., underscoring", "..., reflecting", "..., leading to", "..., allowing"). Keep the coordinate when the second conjunct has a different subject, when the verb is copular and an appositive fits better ("a scale, a modelling choice"), when the participle would dangle onto a nearer wrong nominal, or when the repetition is deliberate emphasis.
- **Write the shadow back in where the genre allows it.** LLM-assisted prose often loses interaction, repair, risk, idiolect, punctuation variety, local genre habits, and uneven rhythm. For Brett's papers, that doesn't mean adding fake chumminess or errors. It means allowing warranted stance ("I take this to show..."), live qualification ("or, more carefully..."), direct criticism ("this inference is too quick"), concrete verbs, occasional short sentences, and the ordinary local habits of academic prose. Don't launder every sentence into polished expository neutrality.
- **Concreteness is observables, not nouns (very high signal).** Grounding an abstract passage means adding observables, contrasts, procedures, and failure conditions, not attaching a running example's proper nouns to the framework. A sentence that names the example's characters (a firm, a score, a benchmark, a "matter") while leaving the claim unspecified is still abstract: mentioning them "sounds concrete" but constrains nothing. Attaching abstract nouns (*link*, *facet*, *standing*, *carries to X*) to parts of the architecture only redescribes the inference. A grounded passage tells the reader what was measured or tested, what use or claim is proposed, which specific differences between the two might matter, what evidence would bridge them, and what result would defeat or restrict the inference. Tells of the cosmetic version: abstract nouns doing the work; one token concrete sentence dropped into an otherwise floating paragraph; the running example's name sprinkled through sentences that would read identically without it. Fix: replace each abstract label with a specific observable, a named contrast (a supported vs. an unsupported use), or a procedure, and state the stop condition. Corollary for source--target reasoning: a link isn't assessed in the abstract; it's assessed by describing two settings and investigating the specific sources of non-transfer between them. Until the two settings and the possible non-transfers are named, the link is a box in a diagram.
- **Projectibility first mentions:** projectibility is central to Brett's work but unfamiliar to most audiences. At first mention, usually add a brief gloss and a Goodman citation, calibrated to the audience. A compact default is "projectibility (what observing some features licenses us to predict about others; Goodman 1955)" using `\citealp{Goodman1955}` in LaTeX. **Not `\citep{}`**: the gloss is already inside parentheses, and `\citep{}` adds its own, rendering "...predict about others; ((Goodman, 1955))". Found 2026-08-09 in `adversarial-pragmatics`, which had followed this line literally; the line has said `\citep{}` since it was written. Specialist philosophy-of-science audiences may need less; linguistics, education, AI, or public audiences usually need more.
- **Explanation-level discipline:** Define the target behavior, judgment, category, model output, or social fact before proposing mechanisms. Mark the explanatory level: behavioral, algorithmic, social-practical, corpus-distributional, model-internal, neural/biological, institutional, or normative.
- **Avoid filler verbs:** `underlies`, `involves`, `regulates`, `drives`, `encodes`, and `represents` often add explanatory sound to correlation. Use them only when the mechanism, test, or level-specific meaning is explicit.
- **Avoid mereological slippage:** Parts do not do what wholes do. Neurons do not understand, embeddings do not mean, fields do not decide, grammars do not judge. Attribute whole-agent, whole-community, or whole-practice predicates to the right bearer.
- **Treat internal maps as evidence stores, not explanations:** connectomes, model activations, vector spaces, and corpus inventories can guide hypotheses and tests; they do not explain a behavior or category by being detailed.
- **Use LLM critique as sparring, not evidence:** model suggestions can sharpen hypotheses, expose weak links, and find missing contrasts. They do not count as source-grounded support.
<!-- /claude-rule -->

### Rapoport's Rules (Dennett 2013)

<!-- claude-rule: writing-style -->
## Rapoport's Rules (Dennett 2013)

When engaging critically with another scholar's work, follow Rapoport's Rules with reasonable flexibility:

1. Re-express the target's position so clearly and fairly that they'd say, "Thanks, I wish I'd put it that way."
2. List points of agreement, especially non-obvious ones.
3. Mention anything you've learned from the target.
4. Only then may you rebut or criticize.

This applies to all critical commentary, whether in papers, reviews, or email. The goal is charitable engagement, not strawmanning. Flexibility is fine (you don't need a numbered list in every paragraph), but the spirit is mandatory: understand and acknowledge before you criticize.
<!-- /claude-rule -->

---

## Numbered Examples

Uses `langsci-gb4e` package. **Note:** No `exe` environment.

### Simple Example

```latex
\ea\label{ex:simple}
\textit{The committee have decided to adjourn.}
\z
```

### Judgement Markers and Subexamples

```latex
\ea\label{ex:sub}
    \ea \textit{She has already left.}
    \ex[*]{\ungram{\textit{She have already left.}}}
    \ex[\#]{\odd{\textit{The square triangle laughed.}}}
    \z
\z
```

Cross-reference: `see (\ref{ex:sub})`

### Paragraph Continuation After Examples

**Rule:** If the text following an example should continue the same paragraph (no indentation), leave **no blank line** between `\z` and the subsequent text. A blank line triggers a new paragraph with indentation.

```latex
% Same paragraph continues (no indent)
\ea\label{ex:cont}
\textit{The committee have decided.}
\z
This shows that collective nouns can trigger plural agreement.

% New paragraph starts (indented)
\ea\label{ex:new}
\textit{The committee has decided.}
\z

A different pattern emerges with singular agreement.
```

### Interlinear Gloss

Abbreviations in small caps using `\abbr{}`:

```latex
\ea\label{ex:gloss}
\gll Ich sehe den Hund. \\
     I see the.\abbr{acc} dog \\
\glt `I see the dog.'
\z
```

---

## Category vs. Function

**Distinguish lexical categories from functions:**

- Categories: `\term{determinative}`, `\term{adjective}`
- Functions: `\term{head}`, `\term{modifier}`, `\term{subject}`

**Example:** In `\enquote{\mention{those} books}`, `\mention{those}` is a `\term{determinative}` (category) functioning as `\term{determiner}` in the NP.

### Class vs. Category

Do not use **class** as a synonym for **category**. In the HPC vocabulary, a class is a descriptive grouping collected for analytical convenience, pedagogy, or local generalization; no shared maintenance mechanism is presupposed. A category is a mechanism-maintained property cluster that supports scoped induction.

Use **category** for lexical categories and their phrasal projections: `\term{noun}`, `\term{verb}`, `\term{adjective}`, `\term{determinative}`, `\term{NP}`, `\term{VP}`. Avoid **word class**, **lexical class**, **adjective class**, and similar phrasing when the intended meaning is category.

Reserve **class** for the weaker HPC sense (a grouping whose mechanism-backed unity is unknown, mixed, or absent), fixed technical compounds such as **classifier**, **class-averaged F1**, and **multi-class prediction**, or quoted/source terminology that is being discussed rather than adopted.

### CGEL Terminology Conventions

<!-- claude-rule: cgel-conventions -->
# Linguistic Terminology (CGEL Style)

This workspace follows CGEL conventions. Critical distinctions:

## Category vs Function
- **Determinative** = lexical category
- **Determiner** = syntactic function
- "the dog" is an NP with a DP in determiner function (reject Abney's DP hypothesis)
- **Article** is not a CGEL lexical category. *The* and *a* are determinatives.
- **Possessive** cross-cuts too many CGEL analyses to use without disambiguation: genitive NPs, genitive pronouns, determinatives, and semantic possession are distinct.

## Syntactic Functions
- **Predicator**, not *predicate*, is the clause-level syntactic function. Do not list *predicate* alongside subject, object, complement, adjunct as though it were a parallel function.
- **Attributive** and **predicative** are functions (uses) of adjectives, not subcategories of adjective.

## Count vs non-count
- **Non-count**, not *mass*, is CGEL's term. CGEL explicitly prefers *non-count* "in part because it reflects clearly the test we use for determining whether a noun is count or non-count, in part because 'mass' is not suitable for the full range of non-count nouns. The term 'mass' is readily applicable with nouns like *water* or *coal* that denote substances but it is less evident that it applies transparently to abstract non-count nouns such as *knowledge*, *spelling*, *work*."
- Use *count/non-count* throughout. Do not write *mass*, *mass-singular*, *mass/count*, etc.

## Tense, Aspect, Mood
- **Perfect**: CGEL analyses as secondary tense, not aspect. Do not default to calling it "aspectual" or grouping it with the progressive as a "viewpoint operator." But note: whether the perfect is genuinely tense rather than aspect is an open HPC boundary question — it may sit in the overlap zone between the two clusters.
- **Progressive** is aspectual.
- **Irrealis**, not *subjunctive*, for *were* in counterfactuals (*if I were*).

## General Principle
- Keep syntax and semantics distinct; they interact but shouldn't be confounded.
- CGEL grounds categoryhood in distribution and syntactic behaviour, not meaning. Semantic correlations exist but do not define categories.
<!-- /claude-rule -->

### Cross-Linguistic Notation

Use the cross symbol to mark comparative concepts:

```latex
\textsc{subject}\crossmark
\textsc{topic}\crossmark
\textsc{noun}\crossmark
```

**Language-specific:**
```latex
\textsc{subject}\textsubscript{eng}
\textsc{topic}\textsubscript{jpn}
```

**Language-internal (generic):**
```latex
\textsc{subject}\textsubscript{$L$}
```

**Important:** Always use `\textsubscript{}` for these labels; do not use the underscore character (`\_`) directly in text mode.

---

## Citations

Using `biblatex` with `natbib=true`:

### Basic Citations

- **Parenthetical:** `\citep{HuddlestonPullum2002}`
- **Inside an existing parenthesis:** `\citealp{HuddlestonPullum2002}` (no added brackets)
- **Textual:** `\textcite{Pullum2018}`
- **Multiple:** `\citep{HuddlestonPullum2002,Pullum2018}`
- **With page:** `\citep[113--127]{HuddlestonPullum2002}`

---

## Journal Article Formatting

Scholarly journals use structural apparatus sparingly. Avoid textbook-style formatting.

### Abstract and Keywords

Papers should include keywords by default from the seed template. Put a visible keyword line immediately after the abstract and keep the PDF metadata `pdfkeywords` in sync.

```latex
\hypersetup{
  pdftitle={Title},
  pdfkeywords={keyword one, keyword two, keyword three}
}

\begin{abstract}
...
\end{abstract}

\noindent\textbf{Keywords:} keyword one; keyword two; keyword three
```

Use semicolons in the visible line and commas in PDF metadata. Replace the seed placeholders before submission; don't leave `TODO` or generic `keywords` in a share-ready manuscript.

### Document Structure and Headings

A typical journal article has a focused structure with 5-7 major sections (e.g., Introduction, Background, Analysis, Discussion, Conclusion). Avoid creating an excessive number of top-level sections.

✅ **Use:** `\section{}` and `\subsection{}` for the main divisions of the paper. These two levels are usually sufficient.

❌ **Avoid:** An overly granular structure. If you have more than 7-8 `\section`s, consider merging related topics.

❌ **Avoid:** Deeper nesting with `\subsubsection{}` or `\paragraph{}`. A topic that seems to require a third-level heading should be restructured, perhaps as a new `\subsection{}` or integrated into the main prose.

### Bold, Bullets, Enumeration

**Avoid bold labels in prose.** Taxonomies and argument sequences should flow as narrative, not as itemized lists.

- ❌ **Wrong:** **(i) Cross-linguistic property covariation.** The diagnostic features must cluster...
- ✅ **Right:** First, the diagnostic features must cluster...

**Enumerated lists are acceptable for:**
- Hypothesis or prediction lists
- Linguistic examples (`\ex` from langsci-gb4e)
- Illustrative codebook entries

**Avoid lists for:**
- Argumentative sequences (use prose with transitions: "first," "second," "finally")
- Objection-reply pairs (use discourse markers: "A first objection," "A related worry")
- Before/after pedagogical contrasts (use narrative)

### Transitions and Discourse Markers

Use ordinal markers and discourse connectives for flow:

**Sequence:** first, second, third; one [concern], another, a final [point]

**Objections:** A first objection concerns...; A second question asks...; A related worry...; Finally, does...

**Illustrations:** Consider first...; A second illustration...; The clearest case...

---

## Dual-Audience Accessibility

When writing for readers from multiple disciplines (e.g., linguists and philosophers), make cross-disciplinary terminology accessible without sacrificing rigor.

### Paragraph Length

Keep paragraphs under 100 words on average. Dense 200+ word paragraphs should be broken into 2--4 shorter units with clear topic sentences. **Aim for ~60 words per paragraph** in body text.

### Parenthetical Glosses

When introducing technical terms, add brief functional explanations:

- Latent variables (quantities representing unobserved category strength)
- Spearman's ρ (a rank correlation measure)
- Differential object marking (where only some objects trigger case or agreement)

### Concrete Before Abstract

Introduce technical apparatus with concrete examples or plain-language motivation:

❌ **Wrong:** Define a vector of observable diagnostics: **n**_L = ⟨ArgHead, ...⟩

✅ **Right:** Traditional typology trades in binary tallies: language X "has" adjectives or it doesn't. The comparanda × categories matrix provides something better: explicit measurement models. For nominality, define a vector...

### Comparanda Notation and Terminology

Maintain a strict distinction between comparative concepts and language-specific categories:

- Use **\textsc{Term}\textsubscript{cross}** for cross-linguistic comparanda (syntactic functions, semantic targets, discourse roles, comparative categories)
- Use **\textsc{Term}\textsubscript{eng}** (or other language tag) for language-specific realisations
- Use **\textsc{Term}\textsubscript{int}** for language-internal discussion without naming a language
- Reserve **function** (without modifier) for syntactic functions only
- Use **target** for semantic targets
- Use **role** for discourse/pragmatic roles
- Use **category** for lexical categories or their phrasal projections
- Do not use **class** as a synonym for **category**. Reserve **class** for descriptive groupings whose mechanism-backed unity is unknown, mixed, or absent, for fixed compounds such as **classifier**, **class-averaged F1**, and **multi-class prediction**, or for quoted/source terminology.
- Remind readers that mappings between axes are rarely one-to-one: a single expression can realise multiple functions, targets, and roles simultaneously

---

## BibTeX Conventions

Protect capitals in proper nouns and first words after colons using braces:

```bibtex
title = {The {Cambridge} Grammar of the {English} Language}
title = {Radical Construction Grammar: {Syntactic} Theory...}
title = {Character identity mechanisms: {A} conceptual model...}
```

### What to Protect

- Proper nouns: `{Cambridge}`, `{English}`, `{American}`
- First word after colon: `{Syntactic}`, `{A}`, `{An}`
- Acronyms: `{HPC}`, `{DOM}`

### What NOT to Protect

- Common nouns, adjectives, verbs (unless part of proper noun)
- Title-initial words (BibTeX handles these automatically)

---

## Quick Reference

### LaTeX Macros (from preamble.tex)

```latex
% Semantic typography
\term{text}           % Terms/concepts (small caps)
\mention{text}        % Mentions/forms (italics)
\mentionhead{text}    % Mentions/forms in headings (ordinary lowercase italics)
\olang{text}          % Object language (italics)
\abbr{text}           % Small-caps abbreviations for glosses
\ipa{text}            % IPA in Charis SIL font

% Cross-linguistic
\crossmark            % Cross-linguistic subscript marker

% Judgements
\ungram{*sentence}    % Ungrammatical (*)
\marg{?sentence}      % Marginal (?)
\odd{#sentence}       % Odd (#)

% Abbreviations
\eg                   % e.g., with spacing
\ie                   % i.e., with spacing
\etc                  % etc. with spacing

% Numbers
\liningnums{2025}     % Lining figures (for tables, isolated years)
```

### Citation Commands

```latex
\citep{key}           % (Author Year)
\citealp{key}         % Author Year -- inside a parenthesis you already opened
\textcite{key}        % Author (Year)
\citep[page]{key}     % (Author Year:page)
```

### Example Commands

```latex
\ea ... \z            % Single example
\ea \ea ... \ex ... \z \z   % Subexamples
\gll ... \\ ... \\ \glt ... % Interlinear gloss
```

---

## Quarto Conventions

When creating Quarto documents (.qmd) -- slides, HTML papers, or notebooks -- use these Pandoc markdown equivalents of the LaTeX macros above.

### Semantic Spans

Use Pandoc bracketed spans with CSS classes. **Do not** use bare `*italic*` for mentions or terms.

| Purpose | Quarto syntax | LaTeX equivalent | Rendering |
|---------|--------------|-----------------|-----------|
| Terms (concepts) | `[definiteness]{.term}` | `\term{definiteness}` | small caps |
| Mentions (forms) | `[the]{.mention}` | `\mention{the}` | italics |
| Object language | `[der Hund]{.olang}` | `\olang{der Hund}` | italics |
| Thesis (slides) | `[Key point.]{.thesis}` | n/a | highlight box |

These require CSS classes in the project's SCSS theme. Use `.house-style/quarto-theme.scss` as the base and import it in your YAML frontmatter:

```yaml
format:
  revealjs:
    theme: [default, path/to/quarto-theme.scss]
```

### Quotations

Standard double quotes. Pandoc smart-quotes handle curly rendering automatically -- no special macro needed.

```markdown
"Outer quote with an 'inner' quote"
```

### Dashes

Pandoc converts `--` to en-dash and `---` to em-dash. We use en-dash only.

```markdown
the category is stable -- within limits -- across registers   # parenthetical
2001--2025                                                     # range
pp. 113--127                                                   # page range
```

### Citations

Requires `bibliography: references.bib` in the YAML frontmatter.

| Purpose | Quarto syntax | LaTeX equivalent |
|---------|--------------|-----------------|
| Parenthetical | `[@HuddlestonPullum2002]` | `\citep{HuddlestonPullum2002}` |
| Textual | `@Pullum2018` | `\textcite{Pullum2018}` |
| With page | `[@HuddlestonPullum2002, p. 113]` | `\citep[113]{HuddlestonPullum2002}` |
| Multiple | `[@key1; @key2]` | `\citep{key1,key2}` |

### Small Caps (General)

For small caps outside semantic spans, use Pandoc's built-in class:

```markdown
[subject]{.smallcaps}
```

### Things to Avoid in .qmd Files

- Bare `*italic*` for metalinguistic mentions (use `[text]{.mention}`)
- Inline `style=` attributes for semantic typography (use CSS classes)
- Em-dashes (`---`) -- use en-dashes (`--`) with spaces for parentheticals
- Raw HTML `<em>` or `<i>` tags for semantic content

---

## Python Plot Style

For matplotlib figures, use `plot_style.py` to ensure consistency with house typography.

### Setup

```python
import sys
sys.path.insert(0, '/path/to/.house-style')  # or symlink
from plot_style import setup, COLORS

setup()  # applies all rcParams
```

### Colour Palette (Dual: Vibrant + Text)

The palette has two tiers. **Vibrant** colours are for plot fills, backgrounds, and decorative elements. **Text** variants are darkened to meet WCAG AA contrast (≥4.5:1 on white) and must be used for text, labels, thin lines, and any element conveying information through colour alone.

| Name | Vibrant | Text | Ratio (vibrant) | Ratio (text) |
|------|---------|------|-----------------|--------------|
| primary | `#2E5077` | (same) | 8.30:1 AAA | -- |
| secondary | `#E85D4C` | `#C74F41` | 3.44:1 | 4.54:1 AA |
| tertiary | `#4DA375` | `#3D825D` | 3.08:1 | 4.62:1 AA |
| quaternary | `#9B6B9E` | `#946697` | 4.21:1 | 4.56:1 AA |
| quinary | `#D4A03E` | `#94702B` | 2.36:1 | 4.55:1 AA |
| light | `#E8E8E8` | -- | (background) | -- |
| dark | `#2D2D2D` | (same) | 13.77:1 AAA | -- |
| accent | `#6AADE4` | `#4B7AA1` | 2.41:1 | 4.57:1 AA |
| link | `#800020` | (same) | 10.83:1 AAA | -- |

**Rule:** Never use vibrant secondary, tertiary, quaternary, quinary, or accent as text colour. Use the `-text` variant. Primary, dark, and link are safe for text as-is.

### Style Characteristics

- **Fonts:** Serif (EB Garamond > Georgia > Times)
- **Spines:** Top/right removed by default
- **Grid:** Off by default (add with `add_grid(ax)`)
- **Legend:** Frameless
- **Output:** 300 DPI PDF + PNG

### Quick Reference

```python
from plot_style import COLORS, setup, save_figure, add_grid

setup()
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(x, y, color=COLORS['primary'])
add_grid(ax, axis='y')
save_figure(fig, 'figures/fig_1')  # saves .pdf and .png
```

---

## Figure Design

The Python Plot Style section above fixes the mechanics (fonts, spines, grid, palette, DPI). These principles govern the design itself, and apply to any tool (matplotlib, ggplot2, TikZ/pgfplots). Audit a figure against them with `/check-chart-style`.

### Show the comparison, not the clutter

- **Small multiples over overplotting.** More than about five series, or a rainbow legend, means splitting into panels that share one identical scale, not one crowded multi-line chart.
- **Direct labels over legends.** Where there's room, label each series at its endpoint instead of forcing a legend round-trip.
- **Range-frame.** Let axes span the actual data extent; don't pad to arbitrary round numbers. Marking min and max is good.
- **Colour earns its ink.** It encodes a variable or marks emphasis, never decoration. Sequential data gets an ordered palette, not a categorical rainbow. Give a redundant channel (shape, label, position) so the figure survives greyscale.

### Tell the truth (lie factor near 1)

- Bar and area baselines at zero. No truncated y-axis that exaggerates change. No dual y-axes implying a coupling that isn't there.
- No 3D, and no area or volume encoding of a single linear quantity.
- Identical scales across compared panels. Normalise or deflate when comparing across time or unequal bases.

### Keep it self-contained

- Keep axis labels with units. Don't offload the whole scale to the caption: journal figures get pulled into reviews and slides, out of context.
- The caption documents the evidence: source, N, and any scale shared across panels. It answers "compared to what?"

---

## Slide Presentations (Quarto)

All slide presentations use **Quarto revealjs** with the house theme. This is the default format for talks, workshops, and conference presentations.

### Default YAML

```yaml
---
title: "Title"
subtitle: "Subtitle"
author: "Brett Reynolds"
date: "YYYY-MM-DD"
format:
  revealjs:
    theme: [default, ../../.house-style/quarto-theme.scss]
    width: 1600
    height: 900
    center: false
    slideNumber: true
    embed-resources: true
    hash-type: number
    navigation-mode: linear
---
```

Adjust the relative path to `quarto-theme.scss` based on project depth.

### Semantic Spans

Same as Quarto papers: `[text]{.term}` for concepts (small-caps), `[text]{.mention}` for forms (italic), `[text]{.olang}` for object language (italic), `[text]{.thesis}` for highlighted propositions (blue box).

### Accessibility (WCAG 2.1)

The theme enforces these automatically:
- **Contrast:** Text colours meet WCAG AA (≥4.5:1). Use `-text` palette variants for coloured text.
- **Reduced motion:** Transitions are suppressed for users with `prefers-reduced-motion`.
- **Focus indicators:** Visible outlines for keyboard navigation.
- **Font size:** Root 36px with 1.4 line height ensures readability at projection distance.

When writing slides, also:
- Add `alt` text to all images: `![Description](image.png)`
- Don't convey information through colour alone (use shape, pattern, or label as redundant channel)
- Keep slide text to key points (don't use slides as a teleprompter)

### Project-Specific Customisation

If a presentation needs extra styles (diagram layouts, custom panels), create a `custom.scss` in the project folder and chain it:

```yaml
theme: [default, ../../.house-style/quarto-theme.scss, custom.scss]
```

Don't duplicate the house theme variables in project-local files.

---

**For AI assistants:** This style guide should be followed when writing or editing LaTeX academic papers, Quarto documents (.qmd), Python figures, and Quarto revealjs slides. For LaTeX, consult `style-rules.yaml` (latex section) and `plot_style.py` for matplotlib styling. For Quarto, consult `style-rules.yaml` (quarto section) and use `quarto-theme.scss` as the base theme. For slides, use the default YAML above and chain `quarto-theme.scss`. Use semantic span classes (`[text]{.term}`, `[text]{.mention}`) instead of bare italic for metalinguistic content in .qmd files. Use `-text` colour variants for any coloured text to meet WCAG AA contrast ratios.
