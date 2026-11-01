"""Shared input contract and figure exports; estimators live in the clustering and PCA notebooks."""
from pathlib import Path
import hashlib
import json
import textwrap
from .snapshot_style import PAPER, INK, style_cell

import matplotlib.pyplot as plt
from matplotlib import colormaps
from matplotlib.colors import LinearSegmentedColormap
from cycler import cycler
import numpy as np
import pandas as pd

from .cohorts import FEATURES, LABELS, MIGRATION, STANDARDIZED_FEATURES, STANDARDIZED_MIGRATION, prepare_cross_section
COLORS = ['#965030', '#3d7067', '#8a9272', '#b77f5a', '#665f50', '#749b8e', '#c3a875', '#293d36']


def configure_plots():
    for name, colors in [('migration_sequential', ['#f8f3e8', '#8eafa0', '#293d36']),
                         ('migration_diverging', ['#965030', '#f8f3e8', '#3d7067'])]:
        if name not in colormaps:
            colormaps.register(LinearSegmentedColormap.from_list(name, colors))
    plt.rcParams.update({'figure.facecolor': '#ffffff', 'axes.facecolor': '#ffffff',
                         'text.color': '#293d36', 'axes.labelcolor': '#293d36',
                         'axes.prop_cycle': cycler(color=COLORS),
                         'axes.edgecolor': '#bbae90', 'xtick.color': '#665a43',
                         'ytick.color': '#665a43', 'font.family': 'DejaVu Sans',
                         'axes.titlesize': 15, 'axes.labelsize': 11,
                         'font.size': 10, 'figure.dpi': 110})


def save_figure(fig, directory, name):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(directory / name, dpi=160, bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close(fig)


def sample_image(frame, directory, name, title):
    """Render precisely the numeric DataFrame displayed in the notebook."""
    fig, ax = plt.subplots(figsize=(12, 2.8), facecolor=PAPER)
    ax.axis('off')
    ax.set_title(title, fontsize=15, color=INK, loc='left', pad=12)
    values = [[f'{v:.3f}' for v in row] for row in frame.to_numpy()]
    table = ax.table(cellText=values, colLabels=[textwrap.fill(c.replace('_', ' '), 17)
                     for c in frame.columns], cellLoc='center', bbox=[0, 0, 1, .95])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (r, c), cell in table.get_celld().items():
        style_cell(cell, r)
        if r == 0:
            cell.set_height(cell.get_height() * 1.6)
    save_figure(fig, directory, name)


from .exports import write_json


def provenance(path, counties, features):
    import sklearn
    return {'input': 'data/processed/analysis_county_year.parquet',
            'input_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'year': int(counties.year.iloc[0]), 'counties': len(counties),
            'imputed_counties': int(counties.socioeconomic_imputed.sum()),
            'outlier_flagged_counties': int(counties.net_rate_iqr_flag.sum()),
            'features': list(features), 'feature_labels': LABELS,
            'versions': {'numpy': np.__version__, 'pandas': pd.__version__, 'sklearn': sklearn.__version__}}
