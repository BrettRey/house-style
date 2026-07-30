#!/bin/bash
# Create symlinks to the consolidated references.bib.
# Run from the portfolio root.
#
# STALE PATHS. The project list below predates the 2026-06/07 folder
# reorganizations, so the paths no longer resolve. The convention it implements
# is still current: a project's references.bib should be a symlink to the
# central bibliography, with project-specific additions in references-local.bib.
# Rebuild the list from papers/INDEX.md before running this.

set -e

CENTRAL_BIB="../../.house-style/references.bib"

# Projects using refs.bib
refs_projects=(
    "papers/Constructions_as_causal_mesoscales_in_CE_2_0"
    "papers/Definiteness_and_deitality"
    "papers/Grammar_and_emergence"
    "papers/Grammaticality_as_Kind_Miller"
    "papers/Grammaticality_de_idealized"
    "papers/How_to_Study_Boundary_Phenomena_English_Reciprocals_and_the_Limits_of_Categorization"
    "papers/Independent_relative_whose"
    "papers/Language_as_a_Stack_of_Homeostatic_Property_Cluster_HPC_Kinds"
    "papers/linguistics-mereology"
    "papers/Transparent_free_relatives"
    "papers/echolocation"
    "papers/grammatical-variation-metastudy"
)

# Projects using references.bib
references_projects=(
    "papers/Functions_as_Comparanda__Categories_as_Kinds__A_Homeostatic_Approach_to_Typology"
    "papers/linguistics-metrology"
    "papers/countability"
    "papers/English_kinship_terms"
    "papers/Labels_to_Stabilisers"
    "papers/Focus_modifiers_interrogative_heads"
    "papers/Alternations-Bayesian"
    "papers/HPC book"
)

# Special cases
# papers/English_LBC_functionalist uses 11_bibliography.bib
# papers/CxG_chunking_feature_selection uses literature/bib.bib
# personal/dillard-kimmerer uses references.bib

echo "Creating symlinks to consolidated references.bib..."

for proj in "${refs_projects[@]}"; do
    if [ -d "$proj" ]; then
        cd "$proj"
        if [ -f refs.bib ] && [ ! -L refs.bib ]; then
            mv refs.bib refs.bib.bak
            echo "  Backed up: $proj/refs.bib"
        fi
        if [ ! -L refs.bib ]; then
            ln -sf "$CENTRAL_BIB" refs.bib
            echo "  Linked: $proj/refs.bib"
        else
            echo "  Already linked: $proj/refs.bib"
        fi
        cd - > /dev/null
    else
        echo "  Skipping (not found): $proj"
    fi
done

for proj in "${references_projects[@]}"; do
    if [ -d "$proj" ]; then
        cd "$proj"
        if [ -f references.bib ] && [ ! -L references.bib ]; then
            mv references.bib references.bib.bak
            echo "  Backed up: $proj/references.bib"
        fi
        if [ ! -L references.bib ]; then
            ln -sf "$CENTRAL_BIB" references.bib
            echo "  Linked: $proj/references.bib"
        else
            echo "  Already linked: $proj/references.bib"
        fi
        cd - > /dev/null
    else
        echo "  Skipping (not found): $proj"
    fi
done

# Special: English_LBC_functionalist
if [ -d "papers/English_LBC_functionalist" ]; then
    cd "papers/English_LBC_functionalist"
    if [ -f 11_bibliography.bib ] && [ ! -L 11_bibliography.bib ]; then
        mv 11_bibliography.bib 11_bibliography.bib.bak
        echo "  Backed up: papers/English_LBC_functionalist/11_bibliography.bib"
    fi
    if [ ! -L 11_bibliography.bib ]; then
        ln -sf "$CENTRAL_BIB" 11_bibliography.bib
        echo "  Linked: papers/English_LBC_functionalist/11_bibliography.bib"
    fi
    cd - > /dev/null
fi

# Special: CxG_chunking_feature_selection
if [ -d "papers/CxG_chunking_feature_selection/literature" ]; then
    cd "papers/CxG_chunking_feature_selection/literature"
    if [ -f bib.bib ] && [ ! -L bib.bib ]; then
        mv bib.bib bib.bib.bak
        echo "  Backed up: papers/CxG_chunking_feature_selection/literature/bib.bib"
    fi
    if [ ! -L bib.bib ]; then
        ln -sf "../../../.house-style/references.bib" bib.bib
        echo "  Linked: papers/CxG_chunking_feature_selection/literature/bib.bib"
    fi
    cd - > /dev/null
fi

# Special: dillard-kimmerer
if [ -d "personal/dillard-kimmerer" ]; then
    cd "personal/dillard-kimmerer"
    if [ -f references.bib ] && [ ! -L references.bib ]; then
        mv references.bib references.bib.bak
        echo "  Backed up: personal/dillard-kimmerer/references.bib"
    fi
    if [ ! -L references.bib ]; then
        ln -sf "$CENTRAL_BIB" references.bib
        echo "  Linked: personal/dillard-kimmerer/references.bib"
    fi
    cd - > /dev/null
fi

echo ""
echo "Done. Backups saved as *.bib.bak"
echo "To restore: mv file.bib.bak file.bib"
