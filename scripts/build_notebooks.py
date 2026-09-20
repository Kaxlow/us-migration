"""Generate the raw-data cleaning walkthrough and ten cleaned-data EDA charts."""
from pathlib import Path
import nbformat as nbf
from notebook_chart_cells import CHARTS

ROOT=Path(__file__).resolve().parents[1]
def md(s): return nbf.v4.new_markdown_cell(s)
def py(s): return nbf.v4.new_code_cell(s)

SETUP = """from pathlib import Path
import sys, json, hashlib, subprocess, inspect
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from IPython.display import display, Markdown, Code
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'src/us_migration').is_dir())
sys.path.insert(0, str(ROOT/'src'))
from us_migration.cleaning import api_frame, clean_acs, normalize_irs, canonical_irs_pairs, clean_acs_flows, clean_fema, clean_noaa
from us_migration.notebook_helpers import raw_snapshot, comparison_image, finish_chart, build_analysis_cohort, cohort_reasons, assert_clean_cohort, MEASURES, FEATURES, OUTCOMES
from us_migration.eda import profile, correlation_bundle, coverage
DATA = ROOT/'data/processed'
TABLES = ROOT/'reports/tables'
TABLES.mkdir(parents=True, exist_ok=True)
sns.set_theme(style='whitegrid', context='notebook', palette='colorblind')
plt.rcParams.update({'axes.titlesize':15, 'axes.labelsize':11, 'xtick.labelsize':10, 'ytick.labelsize':10})
pd.set_option('display.max_columns', 14)
"""

CLEANING_STYLE = """
# Output images have their own theme; they do not inherit the editor background.
plt.style.use('dark_background')
plt.rcParams.update({'figure.facecolor':'#1e1e1e', 'axes.facecolor':'#252526',
                     'savefig.facecolor':'#1e1e1e', 'grid.color':'#454545'})
"""

def write(name,cells):
    notebook=nbf.v4.new_notebook(cells=cells,metadata={
        'kernelspec':{'display_name':'Python 3 (us-migration)','language':'python','name':'python3'},
        'language_info':{'name':'python','version':'3.13'}})
    for i,cell in enumerate(notebook.cells): cell['id']=f'cell-{i:03d}'
    nbf.write(notebook,ROOT/'notebooks'/name)

def cleaning_notebook():
    # The cleaning notebook is hand-authored and authoritative; never regenerate it.
    notebook=nbf.read(ROOT/'notebooks/01_data_cleaning.ipynb',as_version=4)
    nbf.validate(notebook)
    return notebook.cells


def eda_notebook():
    cells=[md('''# Ten exploratory findings from validated cleaned data

Run notebook 01 first. Every chart uses its missing-free, rule-validated cohort, and no chart silently fills missing observations. Most comparisons use the latest common year; titles/captions identify years and sample restrictions. Ten captioned PNGs are saved under `reports/figures/eda/`.

These are descriptive associations, not causal effects. Predictor imputation, overlapping ACS windows, published dollar bases, geography changes, and IRS series breaks limit interpretation.'''),py(SETUP),py("""all_units=pd.read_parquet(DATA/'analysis_county_year.parquet')
assert_clean_cohort(all_units)
display(all_units.loc[all_units.geography_level.eq('state'),['county_name','year','inflow_individuals','outflow_individuals','net_individuals_per_1000']].tail(6))
# County comparisons use one geographic level; state observations remain in the analysis file.
clean=all_units.loc[all_units.geography_level.eq('county')].copy()
latest=int(clean.year.max())
cross=clean.loc[clean.year.eq(latest)].copy()
print(f'Validated cohort: {len(clean):,} county-years, {clean.year.min()}–{latest}; latest-year sample: {len(cross):,} counties')
display(clean[MEASURES].describe().T.round(2))
charts=[]
blue,teal,orange,red='#326c9d','#208b85','#d28b28','#b74e50'
money=FuncFormatter(lambda value,pos:f'${value/1000:,.0f}k')""")]
    for number,(heading,code) in enumerate(CHARTS,1):
        cells.extend([md(f'## Visualization {number}: {heading}'),py(code)])
    cells.extend([md('## Saved chart catalog and interpretation limits'),py("""assert len(charts)==10
assert all((ROOT/entry['image']).is_file() for entry in charts)
pd.DataFrame(charts).to_csv(TABLES/'eda_chart_catalog.csv',index=False)
nl=chr(10)
(ROOT/'reports/eda_visualizations.md').write_text('# Ten findings from cleaned analysis data'+nl+nl+
    (nl+nl).join(f'## {i+1}. {Path(item["image"]).stem}'+nl+nl+f'![Chart](../{item["image"]})'+nl+nl+item['caption'] for i,item in enumerate(charts))+nl,encoding='utf-8')
print('Saved ten captioned PNGs and reports/eda_visualizations.md')
display(pd.DataFrame(charts))"""),md('The cohort includes imputed predictors and does not restore suppressed migration outcomes. Retention tables, source uncertainty, geography flags, and denominator-review exclusions in notebook 01 should accompany these findings; modeling also requires temporal/geographic validation and release-date-aware predictors.')])
    return cells

def main():
    cleaning_notebook() # validate without changing source or saved outputs
    write('02_eda_findings.ipynb',eda_notebook())

if __name__=='__main__': main()
