#!/usr/bin/env python3
"""
House style for matplotlib figures.

Usage:
    from house_style import plot_style
    plot_style.setup()

Or import specific elements:
    from house_style.plot_style import COLORS, setup_style
    setup_style()
    fig, ax = plt.subplots()
    ax.plot(x, y, color=COLORS['primary'])
"""

import matplotlib.pyplot as plt

# =============================================================================
# COLOR PALETTE
# =============================================================================

# Muted, accessible, print-friendly
COLORS = {
    'primary': '#2E5077',      # Deep blue
    'secondary': '#E85D4C',    # Coral red
    'tertiary': '#4DA375',     # Sage green
    'quaternary': '#9B6B9E',   # Muted purple
    'quinary': '#D4A03E',      # Goldenrod
    'light': '#E8E8E8',        # Light gray
    'dark': '#2D2D2D',         # Near black
    'accent': '#6AADE4',       # Sky blue
}

# For cycling through multiple series
COLOR_CYCLE = [
    COLORS['primary'],
    COLORS['secondary'],
    COLORS['tertiary'],
    COLORS['quaternary'],
    COLORS['quinary'],
    COLORS['accent'],
]


# =============================================================================
# STYLE SETUP
# =============================================================================

def setup(font_size=10, title_size=11, tick_size=9, legend_size=9):
    """
    Set up matplotlib style for consistent, publication-quality figures.

    Characteristics:
    - Serif fonts (EB Garamond > Garamond > Georgia > Times)
    - White background
    - No grid by default
    - Top/right spines removed
    - Frameless legends
    - 300 DPI output

    Args:
        font_size: Base font size (default 10)
        title_size: Title font size (default 11)
        tick_size: Tick label font size (default 9)
        legend_size: Legend font size (default 9)
    """
    plt.rcParams.update({
        # Figure
        'figure.facecolor': 'white',
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,

        # Fonts
        'font.family': 'serif',
        'font.serif': ['EB Garamond', 'Garamond', 'Georgia', 'Times New Roman'],
        'font.size': font_size,
        'axes.titlesize': title_size,
        'axes.labelsize': font_size,
        'xtick.labelsize': tick_size,
        'ytick.labelsize': tick_size,
        'legend.fontsize': legend_size,

        # Axes
        'axes.facecolor': 'white',
        'axes.edgecolor': COLORS['dark'],
        'axes.linewidth': 0.8,
        'axes.grid': False,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.prop_cycle': plt.cycler('color', COLOR_CYCLE),

        # Ticks
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'xtick.major.width': 0.8,
        'ytick.major.width': 0.8,

        # Legend
        'legend.frameon': False,
        'legend.loc': 'best',

        # Lines
        'lines.linewidth': 1.5,
        'lines.markersize': 6,
    })


def setup_minimal():
    """
    Even more minimal style for simple plots.
    Smaller fonts, thinner lines.
    """
    setup(font_size=9, title_size=10, tick_size=8, legend_size=8)
    plt.rcParams.update({
        'axes.linewidth': 0.5,
        'xtick.major.width': 0.5,
        'ytick.major.width': 0.5,
        'lines.linewidth': 1.0,
        'lines.markersize': 4,
    })


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def remove_spines(ax, spines=('top', 'right')):
    """Remove specified spines from an axes object."""
    for spine in spines:
        ax.spines[spine].set_visible(False)


def add_grid(ax, axis='y', style=':', width=0.5, color=None):
    """Add a subtle grid to an axes object."""
    if color is None:
        color = COLORS['light']
    ax.grid(True, axis=axis, linestyle=style, linewidth=width, color=color)


def save_figure(fig, path, formats=('pdf', 'png')):
    """
    Save figure in multiple formats.

    Args:
        fig: matplotlib figure
        path: base path without extension (e.g., 'figures/fig_1')
        formats: tuple of formats to save (default: pdf and png)
    """
    from pathlib import Path
    path = Path(path)
    for fmt in formats:
        fig.savefig(path.with_suffix(f'.{fmt}'))
        print(f'Saved: {path.with_suffix(f".{fmt}")}')


# =============================================================================
# AUTO-SETUP ON IMPORT (optional)
# =============================================================================

# Uncomment to auto-apply style on import:
# setup()
