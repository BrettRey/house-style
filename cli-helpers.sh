#!/bin/bash
# House style helpers for LLM CLIs
# Source this file in .zshrc: source ~/projects/LLM-CLI-projects/.house-style/cli-helpers.sh

# House style preamble for LaTeX work
# Usage: codex exec -C . --sandbox workspace-write "$(housestyle) Edit main.tex to..."
# Repo root, used to read the live house-style rules. Override with _HS_ROOT if the portfolio moves.
_HS_ROOT="${_HS_ROOT:-$HOME/projects/LLM-CLI-projects}"

housestyle() {
    cat << 'EOF'
HOUSE STYLE (MANDATORY):
Before editing ANY .tex file, follow these rules exactly.

LaTeX mechanics:
• \term{concept} for technical terms (small caps)
• \mention{word} for linguistic forms/examples (italics)
• \enquote{text} for quotations (not "" or ``)
• En-dash with spaces: text~-- parenthetical~-- text (NEVER em-dash ---)
• Brackets OUTSIDE italics: (\textit{text}) NOT \textit{(text)}
• \textsubscript{eng} not _eng in prose
• Citations: \textcite{} when the author is the sentence's agent
  ("Kane (2013) distinguishes ..."); \citep{} for parenthetical support.
  Never leave the author both named as subject and repeated in a trailing (Author, Year).
EOF
    # Append the full prose writing-style rules from the single source of truth,
    # so this preamble never drifts from .claude/rules/writing-style.md.
    local rules="$_HS_ROOT/.claude/rules/writing-style.md"
    if [ -f "$rules" ]; then
        printf '\nWriting style (house rules):\n'
        sed '1,/^-->/d' "$rules"
    else
        printf '\nAvoid LLM tics: contrastive negation, false ranges, weasel attribution,\ntrailing evaluative -ing tags, while-maintaining frames, throat-clearers,\nand hackneyed connectives (moreover, furthermore, however, thus).\n'
    fi
    cat << 'EOF'

Violations create rework. Follow scrupulously.

TASK:
EOF
}

# Short version for inline use
hs() {
    housestyle
}

# Wrapper functions that prepend house style automatically
# Usage: codex-tex "Edit main.tex to add a section on X"
codex-tex() {
    codex exec -C . --sandbox workspace-write "$(housestyle) $*"
}

agy-tex() {
    agy --print "$(housestyle) $*"
}

copilot-tex() {
    copilot -p "$(housestyle) $*"
}

# For piping file content with style rules
# Usage: cat main.tex | agy-tex-pipe "Check this for style violations"
agy-tex-pipe() {
    local input
    input="$(cat)"
    agy --print "$(housestyle) $*

INPUT:
$input"
}

# Print just the rules (for manual copy-paste)
housestyle-print() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "HOUSE STYLE RULES"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Semantic macros:"
    echo "  \\term{concept}     - technical terms (small caps)"
    echo "  \\mention{word}     - linguistic forms (italics)"
    echo "  \\enquote{text}     - quotations"
    echo ""
    echo "Typography:"
    echo "  • En-dash with spaces: text~-- parenthetical~-- text"
    echo "  • NEVER use em-dash (---)"
    echo "  • Brackets OUTSIDE italics: (\\textit{text})"
    echo "  • \\textsubscript{eng} not _eng"
    echo ""
    echo "Avoid:"
    echo "  • moreover, furthermore, nevertheless, however, thus, hence"
    echo "  • \"it is important to note\", \"it should be noted\", etc."
    echo "  • contrastive negation, false ranges, weasel attribution"
    echo "  • trailing evaluative -ing tags and while-maintaining frames"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

echo "[house-style] CLI helpers loaded. Commands: housestyle, hs, codex-tex, agy-tex, copilot-tex"
