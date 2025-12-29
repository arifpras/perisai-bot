"""Shared Economist-style chart helpers for PerisAI plots."""
import matplotlib
from matplotlib import rcParams
from datetime import date
from typing import Optional

# Economist color palette (includes both gray/grey keys for compatibility)
ECONOMIST_COLORS = {
    "red": "#E3120B",
    "blue": "#1DB4D0",
    "teal": "#00847E",
    "grey": "#7A7A7A",
    "gray": "#8C8C8C",
    "yellow": "#F4C20D",
    "green": "#60BD68",
    "bg_gray": "#F0F0F0",
    "black": "#1A1A1A",
    "grid": "#FFFFFF",
}

ECONOMIST_PALETTE = [
    ECONOMIST_COLORS["red"],
    ECONOMIST_COLORS["blue"],
    ECONOMIST_COLORS["grey"],
    ECONOMIST_COLORS["yellow"],
    ECONOMIST_COLORS["green"],
]


def apply_economist_style(fig, ax, *, tick_labelsize: int = 12, grid_linewidth: float = 1.8) -> None:
    """Apply The Economist styling to a matplotlib figure/axes."""
    # Harden default sizes so later calls without explicit fontsize do not override styling
    rcParams["axes.titlesize"] = 13
    rcParams["axes.labelsize"] = max(10, tick_labelsize)
    ax.set_facecolor(ECONOMIST_COLORS["bg_gray"])
    fig.patch.set_facecolor("white")

    # Remove top/right/left spines; style bottom spine
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(ECONOMIST_COLORS["black"])
    ax.spines["bottom"].set_linewidth(0.5)

    # Grid: horizontal only, visible
    ax.grid(
        axis="y",
        color=ECONOMIST_COLORS.get("grid", "white"),
        linewidth=grid_linewidth,
        linestyle="-",
        alpha=1.0,
    )
    ax.grid(axis="x", visible=False)

    # Tick styling
    tick_color = ECONOMIST_COLORS.get("gray", ECONOMIST_COLORS["grey"])
    ax.tick_params(axis="both", which="both", length=0, labelsize=tick_labelsize, colors=tick_color)
    ax.xaxis.label.set_color(tick_color)
    ax.yaxis.label.set_color(tick_color)


def add_economist_caption(fig, *, as_of: Optional[date] = None, text: Optional[str] = None, tick_color: Optional[str] = None) -> None:
    """Add unified caption and margins for Economist-style plots."""
    fig.subplots_adjust(left=0.08, right=0.98, top=0.90, bottom=0.15)
    caption_color = tick_color or ECONOMIST_COLORS.get("gray", ECONOMIST_COLORS["grey"])
    as_of_date = as_of or date.today()
    caption = text or f"Source: PerisAI analytics | as of {as_of_date.strftime('%d %b %Y')}"
    fig.text(0.08, 0.005, caption, fontsize=11, color=caption_color, ha="left", va="bottom", weight="normal")
