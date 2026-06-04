"""
plotting.py — Funções de visualização padronizadas.

Todas as funções:
    - Usam a paleta de cores de config.py
    - Salvam automaticamente em output/figures/ (300 dpi)
    - Retornam (fig, ax) para ajustes posteriores nos notebooks
"""

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import pandas as pd

from .config import (
    PALETTE_HD, PALETTE_HD_LIST, PALETTE_QUAL,
    FIGSIZE_SINGLE, FIGSIZE_WIDE, FIGSIZE_COMPARE,
    DPI, OUTPUT_FIGURES, MPL_STYLE, VAR_LABELS, CAT_LABELS,
)


def _apply_style():
    """Aplica estilo global aos gráficos."""
    plt.rcParams.update(MPL_STYLE)


def _save(fig, filename: str):
    """Salva figura em output/figures/ com 300 dpi."""
    OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FIGURES / filename, dpi=DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")


def _get_label(var: str) -> str:
    """Retorna rótulo legível para a variável."""
    return VAR_LABELS.get(var, var)


# =========================================================================
# GRÁFICOS PARA VARIÁVEIS QUALITATIVAS (Bloco 1)
# =========================================================================

def bar_chart(
    series: pd.Series,
    var_name: str,
    filename: str | None = None,
    figsize: tuple = FIGSIZE_SINGLE,
) -> tuple:
    """Gráfico de barras simples para variável qualitativa."""
    _apply_style()
    fig, ax = plt.subplots(figsize=figsize)

    counts = series.value_counts()
    colors = PALETTE_QUAL[:len(counts)]

    bars = ax.bar(range(len(counts)), counts.values, color=colors,
                  edgecolor="white", linewidth=0.8)

    # Rótulos legíveis nas barras
    cat_map = CAT_LABELS.get(var_name, {})
    tick_labels = [cat_map.get(c, str(c)) for c in counts.index]
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(tick_labels, rotation=0 if len(tick_labels) <= 4 else 30,
                        ha="center" if len(tick_labels) <= 4 else "right")

    # Valores sobre as barras
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                str(val), ha="center", va="bottom", fontweight="bold",
                fontsize=10)

    ax.set_xlabel("")
    ax.set_ylabel("Frequência absoluta (fi)")
    ax.set_title(f"Distribuição — {_get_label(var_name)}")
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    if filename:
        _save(fig, filename)
    return fig, ax


def bar_chart_grouped(
    df: pd.DataFrame,
    var_name: str,
    group: str = "HeartDisease",
    filename: str | None = None,
    figsize: tuple = FIGSIZE_WIDE,
) -> tuple:
    """Gráfico de barras agrupadas: qualitativa × HeartDisease."""
    _apply_style()
    fig, ax = plt.subplots(figsize=figsize)

    cat_map = CAT_LABELS.get(var_name, {})
    group_map = CAT_LABELS.get(group, {})

    ct = pd.crosstab(df[var_name], df[group])
    categories = ct.index.tolist()
    x = np.arange(len(categories))
    width = 0.35

    for i, col in enumerate(ct.columns):
        offset = -width / 2 + i * width
        label = group_map.get(col, str(col))
        color = PALETTE_HD.get(col, PALETTE_QUAL[i])
        bars = ax.bar(x + offset, ct[col], width, label=label,
                       color=color, edgecolor="white", linewidth=0.8)
        # Valores sobre as barras
        for bar, val in zip(bars, ct[col]):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 1, str(val),
                        ha="center", va="bottom", fontsize=9)

    tick_labels = [cat_map.get(c, str(c)) for c in categories]
    ax.set_xticks(x)
    ax.set_xticklabels(tick_labels, rotation=0 if len(tick_labels) <= 4 else 30,
                        ha="center" if len(tick_labels) <= 4 else "right")

    ax.set_xlabel("")
    ax.set_ylabel("Frequência absoluta (fi)")
    ax.set_title(f"{_get_label(var_name)} × {_get_label(group)}")
    ax.legend(title=_get_label(group), frameon=True, fancybox=True)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    if filename:
        _save(fig, filename)
    return fig, ax


# =========================================================================
# HISTOGRAMA (Blocos 2 e 3)
# =========================================================================

def histogram(
    series: pd.Series,
    var_name: str,
    bins: list | np.ndarray | None = None,
    labels: list[str] | None = None,
    density_curve: bool = True,
    filename: str | None = None,
    figsize: tuple = FIGSIZE_SINGLE,
) -> tuple:
    """
    Histograma com curva de densidade opcional.

    Para Age (variável discreta): usar bins/labels das faixas etárias.
    Para contínuas: bins calculados por Sturges.
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=figsize)

    color = PALETTE_QUAL[0]

    if labels is not None and bins is not None:
        # Histograma categórico (faixas etárias)
        cuts = pd.cut(series, bins=bins, labels=labels,
                       include_lowest=True, right=False)
        counts = cuts.value_counts(sort=False)
        bar_positions = range(len(counts))
        bars = ax.bar(bar_positions, counts.values, color=color,
                       edgecolor="white", linewidth=0.8)
        ax.set_xticks(bar_positions)
        ax.set_xticklabels(labels)
        # Valores sobre as barras
        for bar, val in zip(bars, counts.values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1, str(val),
                    ha="center", va="bottom", fontweight="bold", fontsize=10)
    else:
        # Histograma numérico com bins
        if bins is None:
            from .frequency_tables import sturges_bins
            bins = sturges_bins(series)
        ax.hist(series, bins=bins, color=color, edgecolor="white",
                linewidth=0.8, alpha=0.85, density=density_curve)

        if density_curve:
            # Curva de densidade (KDE)
            from scipy.stats import gaussian_kde
            x_range = np.linspace(series.min(), series.max(), 300)
            kde = gaussian_kde(series, bw_method="silverman")
            ax.plot(x_range, kde(x_range), color="#E05263", linewidth=2,
                    label="Curva de densidade")
            ax.legend(frameon=True, fancybox=True)
            ax.set_ylabel("Densidade")
        else:
            ax.set_ylabel("Frequência absoluta (fi)")

    ax.set_xlabel(_get_label(var_name))
    ax.set_title(f"Histograma — {_get_label(var_name)}")
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    if filename:
        _save(fig, filename)
    return fig, ax


# =========================================================================
# BOXPLOTS (Blocos 2 e 3)
# =========================================================================

def boxplot_single(
    series: pd.Series,
    var_name: str,
    filename: str | None = None,
    figsize: tuple = FIGSIZE_SINGLE,
) -> tuple:
    """Boxplot simples para uma variável numérica."""
    _apply_style()
    fig, ax = plt.subplots(figsize=figsize)

    bp = ax.boxplot(series.dropna(), vert=True, patch_artist=True,
                     widths=0.5,
                     boxprops=dict(facecolor=PALETTE_QUAL[0], alpha=0.7),
                     medianprops=dict(color="#E05263", linewidth=2),
                     whiskerprops=dict(color="#555555"),
                     capprops=dict(color="#555555"),
                     flierprops=dict(marker="o", markerfacecolor="#E05263",
                                     markersize=5, alpha=0.6))

    ax.set_ylabel(_get_label(var_name))
    ax.set_title(f"Boxplot — {_get_label(var_name)}")
    ax.set_xticklabels([""])
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    if filename:
        _save(fig, filename)
    return fig, ax


def boxplot_comparison(
    df: pd.DataFrame,
    var_name: str,
    group: str = "HeartDisease",
    filename: str | None = None,
    figsize: tuple = FIGSIZE_COMPARE,
) -> tuple:
    """Boxplot comparativo por grupo HeartDisease."""
    _apply_style()
    fig, ax = plt.subplots(figsize=figsize)

    group_map = CAT_LABELS.get(group, {})
    groups = sorted(df[group].unique())
    data_list = [df[df[group] == g][var_name].dropna() for g in groups]

    bp = ax.boxplot(data_list, vert=True, patch_artist=True,
                     widths=0.5,
                     medianprops=dict(color="white", linewidth=2),
                     whiskerprops=dict(color="#555555"),
                     capprops=dict(color="#555555"),
                     flierprops=dict(marker="o", markersize=5, alpha=0.6))

    # Colorir cada caixa
    colors = [PALETTE_HD.get(g, PALETTE_QUAL[i]) for i, g in enumerate(groups)]
    for patch, color, flier_color in zip(bp["boxes"], colors, colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    for i, flier in enumerate(bp["fliers"]):
        flier.set(markerfacecolor=colors[i])

    tick_labels = [group_map.get(g, str(g)) for g in groups]
    ax.set_xticklabels(tick_labels)
    ax.set_ylabel(_get_label(var_name))
    ax.set_title(f"{_get_label(var_name)} × {_get_label(group)}")
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    if filename:
        _save(fig, filename)
    return fig, ax
