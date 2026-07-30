#!/bin/bash
# create-paper.sh - Create new LaTeX paper from house style template
# Version: 1.0.0
# Usage: ./create-paper.sh "Paper Title" [--no-git]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory (where this script lives)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOUSE_STYLE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
TEMPLATE_DIR="$HOUSE_STYLE_DIR/templates/paper-template"
VERSION=$(cat "$HOUSE_STYLE_DIR/VERSION")

# Functions
error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Check arguments
if [ -z "$1" ]; then
    error "Usage: $0 \"Paper Title\" [--no-git]"
fi

PAPER_TITLE="$1"
NO_GIT=false

# Check for --no-git flag
if [ "$2" == "--no-git" ]; then
    NO_GIT=true
fi

# Sanitize paper title to create a lower-case kebab-case directory name.
# "New Paper Title" -> "new-paper-title"
PAPER_DIR=$(
    printf '%s' "$PAPER_TITLE" |
    tr '[:upper:]' '[:lower:]' |
    sed -E 's/[^[:alnum:]]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
)

if [ -z "$PAPER_DIR" ]; then
    error "Could not create valid directory name from title: $PAPER_TITLE"
fi

info "Creating paper: $PAPER_TITLE"
info "Directory: $PAPER_DIR"
info "House style version: $VERSION"

# Check if directory already exists
if [ -d "$PAPER_DIR" ]; then
    error "Directory '$PAPER_DIR' already exists"
fi

# Check if template exists
if [ ! -d "$TEMPLATE_DIR" ]; then
    error "Template directory not found: $TEMPLATE_DIR"
fi

# Copy template
info "Copying template..."
cp -r "$TEMPLATE_DIR" "$PAPER_DIR"
success "Template copied"

# Enter new directory
cd "$PAPER_DIR"

# Create .house-style directory and copy snapshot
info "Creating house style snapshot..."
mkdir -p .house-style
cp "$HOUSE_STYLE_DIR/preamble.tex" .house-style/
cp "$HOUSE_STYLE_DIR/style-rules.yaml" .house-style/
echo "$VERSION" > .house-style-version
success "House style snapshot created (v$VERSION)"

# Canon stamp. A paper created today has been written against today's
# commitments, so it starts reconciled -- unlike a pre-existing paper, where
# "reconciled" would be a claim nobody has checked.
info "Creating canon stamp..."
CANON_VERSION="unknown"
if [ -f "$HOUSE_STYLE_DIR/../canon/VERSION" ]; then
    CANON_VERSION=$(cat "$HOUSE_STYLE_DIR/../canon/VERSION")
fi
TODAY=$(date +%Y-%m-%d)
cat > .canon-stamp <<EOF
# Canon reconciliation stamp. See canon/README.md.
#
# last_reconciled: the date this project was brought up to the canon.
#   Set it with canon_drift.py --reconcile, not by hand.
# acknowledged: per-entry dismissals, permanent for this project.
# manuscript: optional globs limiting the scan to the live manuscript.
last_reconciled: $TODAY
acknowledged: []
EOF
success "Canon stamp created (canon $CANON_VERSION)"

# Customize main.tex title
info "Customizing files..."
if [ -f "main.tex" ]; then
    # Update title in main.tex
    # This is a simple approach - you may need to adjust based on template structure
    sed -i.bak "s/{{PAPER_TITLE}}/$PAPER_TITLE/g" main.tex
    rm -f main.tex.bak
fi

# Update AI documentation with paper name
for doc in CLAUDE.md AGENTS.md GEMINI.md; do
    if [ -f "$doc" ]; then
        sed -i.bak "s/{{PAPER_TITLE}}/$PAPER_TITLE/g" "$doc"
        sed -i.bak "s/{{PAPER_DIR}}/$PAPER_DIR/g" "$doc"
        rm -f "$doc.bak"
    fi
done

success "Files customized"

# Initialize git if not disabled
if [ "$NO_GIT" = false ]; then
    info "Initializing git repository..."
    git init > /dev/null 2>&1
    git add .
    git commit -m "Initial commit: $PAPER_TITLE from house-style v$VERSION" > /dev/null 2>&1
    success "Git initialized"
else
    info "Skipping git initialization (--no-git flag)"
fi

# Print success message
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
success "Paper created: $PAPER_TITLE"
success "Location: $(pwd)"
success "House style: v$VERSION"
if [ "$NO_GIT" = false ]; then
    success "Git: Initialized with initial commit"
fi
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Next steps:"
echo "  cd $PAPER_DIR"
echo "  replace abstract and keyword placeholders"
echo "  make          # Build main.pdf plus named upload PDF"
echo "  code .        # Open in editor"
echo ""
