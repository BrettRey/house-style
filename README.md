# House Style System

**Version:** 2.2.0

This directory contains the house style framework for LaTeX academic papers by Brett Reynolds.

> ## This repository is public
>
> Anything committed here is world-readable. Two habits keep it safe to leave that way.
>
> **Bibliography notes must not name the venue a manuscript is under review with.**
> Use the preprint identifier instead: `note = {Preprint, LingBuzz/009537}`, never
> `note = {Manuscript submitted to <venue>}`. Two reasons. It discloses a pending
> submission, which is a decision to make deliberately on a publications page
> rather than as a side effect of a `.bib` file. And it goes stale on every
> decision letter: an audit in July 2026 found several entries still claiming a
> manuscript was under review somewhere it had already been rejected. A preprint
> ID never goes stale.
>
> **Don't put case detail in the tooling.** The linters exist because specific
> things went wrong, and the lesson belongs in the docstring, but manuscript
> numbers and journal names do not.
>
> Check before pushing:
>
> ```bash
> grep -nE "submitted to|under review at|/Users/" references.bib *.py
> ```

## Contents

- `VERSION` - Current version (semantic versioning)
- `preamble.tex` - LaTeX preamble with packages and macros
- `style-rules.yaml` - Machine-readable style conventions
- `style-guide.md` - **Canonical** human-readable style guide; also the single source for the agent-facing rule files generated into `.claude/rules/`
- `scripts/generate-claude-rules.py` - Extracts `<!-- claude-rule: NAME -->` blocks from `style-guide.md` into `.claude/rules/NAME.md`
- `Makefile` - `make claude-rules` (regenerate), `make check-claude-rules` (fail if stale)
- `templates/` - Project templates and tools

## Style-rule single source

`style-guide.md` is the canonical source for *all* style guidance. The four agent-facing rule files in `.claude/rules/` are generated from it:

- `.claude/rules/writing-style.md` (generated)
- `.claude/rules/latex-house-style.md` (generated)
- `.claude/rules/quarto-house-style.md` (generated)
- `.claude/rules/cgel-conventions.md` (generated)

These generated files start with a `GENERATED FILE. DO NOT EDIT.` header. To change a rule, edit the matching `<!-- claude-rule: NAME -->` block in `style-guide.md` and run `make claude-rules`.

The other rule files in `.claude/rules/` (`source-grounding.md`, `bibliography-workflow.md`, `multi-model-dispatch.md`, `package-verification.md`, `agent-output-management.md`, `decisions-log.md`) are hand-authored canonical files and not touched by the generator.

## Creating a New Paper

```bash
cd <portfolio root>
.house-style/templates/agents/create-paper.sh "Your Paper Title"
```

This creates a new paper directory with:
- Complete LaTeX structure
- House style snapshot (frozen at creation)
- Build automation (Makefile)
- Git repository with pre-commit hooks
- AI documentation for Claude/Kimi/Gemini

## Structure

```
.house-style/
├── VERSION                      # 2.2.0
├── preamble.tex                 # LaTeX setup
├── style-rules.yaml             # Machine-readable rules
├── style-guide.md               # Human-readable guide
├── README.md                    # This file
└── templates/
    ├── paper-template/          # Template for new papers
    │   ├── main.tex
    │   ├── references.bib
    │   ├── Makefile
    │   ├── .gitignore
    │   ├── CLAUDE.md
    │   ├── AGENTS.md
    │   ├── GEMINI.md
    │   └── .git/hooks/pre-commit
    └── agents/
        └── create-paper.sh      # Project creation script
```

## Updating Existing Papers

Papers get a **snapshot** of the house style at creation time. To update:

```bash
cd your-paper-directory/
cp ../.house-style/preamble.tex .house-style/
cp ../.house-style/style-rules.yaml .house-style/
# Update .house-style-version if desired
```

**Note:** Papers under review or published should generally NOT be updated.

## Modifying the House Style

1. Edit files in `.house-style/`
2. Increment `VERSION` following semantic versioning:
   - **Major** (X.0.0): Breaking changes to conventions
   - **Minor** (0.X.0): New conventions added
   - **Patch** (0.0.X): Corrections, clarifications
3. New papers will use the updated version
4. Existing papers can opt-in to updates manually

## Key Features

### Three-Agent System

1. **Creation Agent** (`create-paper.sh`) - Generates new papers
2. **AI Guidance** - Claude/Kimi/Gemini read rules during writing
3. **Enforcement** (future) - Pre-commit checks for violations

### Synchronized AI Documentation

All three AI doc files (CLAUDE.md, AGENTS.md, GEMINI.md) are kept in sync via pre-commit hook. Edit any one, and changes propagate to the others automatically.

### House Style Conventions

See `style-guide.md` for full documentation. Key points:

- **LaTeX**: `\term{}` for mention, `\enquote{}` for quotes
- **Notation**: `\crossmark` for cross-linguistic concepts
- **Writing**: Contractions preferred, ~60 word paragraphs
- **Structure**: Avoid `\paragraph{}`, use prose with markers
- **Citations**: `\citep{}` and `\textcite{}`

## Files Created by Template

When you create a new paper, you get:

```
New_Paper_Name/
├── .house-style-version         # Version tracking
├── .house-style/                # Local snapshot
│   ├── preamble.tex
│   └── style-rules.yaml
├── main.tex                     # Paper source
├── references.bib               # Bibliography
├── Makefile                     # Build commands
├── .gitignore                   # LaTeX artifacts
├── CLAUDE.md                    # AI documentation
├── AGENTS.md                    # (synced)
├── GEMINI.md                    # (synced)
└── .git/hooks/pre-commit        # Auto-sync hook
```

## Documentation

- **Human users**: Read `style-guide.md`
- **AI assistants**: Read `style-rules.yaml` (machine-readable)

## Version History

### 2.2.0 (2026-07-30)
- Three writing-style rules added to `style-guide.md`: corrective negation without an
  opponent, paragraph closers (the opener rules had no counterpart at the other end),
  and stacked noun phrases
- Filler intensifiers (genuinely, really, truly, actually) added to the AI vocabulary list
- `check-style.py`: corrective-negation pattern, filler-intensifier incidence count, and a
  sentence-length distribution report (median, middle half, histogram) with advisories for
  narrow bands, flat spread, and absent short sentences. Advisory only; no exit-code effect

### 1.0.0 (2025-11-07)
- Initial release
- LaTeX preamble with standard packages
- Style rules from house-style-and-preamble.tex
- Project creation agent
- Template with Makefile and AI docs
- Pre-commit hook for AI doc syncing
