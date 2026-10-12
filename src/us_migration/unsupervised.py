"""Shared input contract and figure exports; estimators live in notebooks 03 and 04."""
from pathlib import Path
import hashlib
import json
import textwrap
from .snapshot_style import PAPER, INK, style_cell

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FEATURES = [
    'log10_population', 'median_age', 'log10_income', 'log10_home_value',
    'log10_rent', 'poverty_pct', 'unemployment_pct', 'vacancy_pct',
    'homeownership_pct', 'bachelors_plus_pct', 'log1p_incidents',
    'precipitation_inches', 'temperature_f',
]
LABELS = ['Log population', 'Median age', 'Log income', 'Log home value',
          'Log rent', 'Poverty %', 'Unemployment %', 'Vacancy %',
          'Homeownership %', "Bachelor’s+ %", 'Log1p incidents',
          'Precipitation', 'Temperature']
MIGRATION = ['inflow_individuals_per_1000', 'outflow_individuals_per_1000']
STANDARDIZED_FEATURES = [c.removesuffix('_pct').removesuffix('_inches').removesuffix('_f') for c in FEATURES]
STANDARDIZED_MIGRATION = ['inflow', 'outflow']
COLORS = ['#80600d', '#697787', '#36847c', '#b56043', '#8c6eaa', '#466b9c', '#bb903b', '#626957']


def prepare_cross_section(panel, year=2023):
    """One eligible county per row. No new imputation or outcome-driven filtering."""
    counties = panel.loc[panel.year.eq(year) & panel.geography_level.eq('county')].copy()
    counties = counties.sort_values('county_fips').reset_index(drop=True)
    if counties.empty or counties.county_fips.duplicated().any():
        raise ValueError('Expected a nonempty, unique county cross-section')
    for source, target in [('population', 'log10_population'),
                           ('median_household_income', 'log10_income'),
                           ('median_home_value', 'log10_home_value'),
                           ('median_gross_rent', 'log10_rent')]:
        if not (counties[source] > 0).all():
            raise ValueError(f'{source} must be positive before log10')
        counties[target] = np.log10(counties[source])
    if not (counties.declarations >= 0).all():
        raise ValueError('Incident counts must be nonnegative')
    counties['log1p_incidents'] = np.log1p(counties.declarations)
    characteristics = counties[FEATURES].copy()
    migration = counties[MIGRATION].copy()
    for frame in [characteristics, migration]:
        if not np.isfinite(frame.to_numpy(dtype=float)).all():
            raise ValueError('Nonfinite model input; rerun the cleaning audit')
        if (frame.std(ddof=0) == 0).any():
            raise ValueError('Constant feature; revise the feature specification')
    if not np.allclose(counties.net_individuals_per_1000,
                       migration.iloc[:, 0] - migration.iloc[:, 1]):
        raise ValueError('Migration arithmetic mismatch')
    return counties, characteristics, migration


def configure_plots():
    plt.rcParams.update({'figure.facecolor': '#ffffff', 'axes.facecolor': '#ffffff',
                         'text.color': '#443313', 'axes.labelcolor': '#443313',
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


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def provenance(path, counties, features):
    import sklearn
    return {'input': 'data/processed/analysis_county_year.parquet',
            'input_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'year': int(counties.year.iloc[0]), 'counties': len(counties),
            'imputed_counties': int(counties.socioeconomic_imputed.sum()),
            'outlier_flagged_counties': int(counties.net_rate_iqr_flag.sum()),
            'features': list(features), 'feature_labels': LABELS,
            'versions': {'numpy': np.__version__, 'pandas': pd.__version__, 'sklearn': sklearn.__version__}}
