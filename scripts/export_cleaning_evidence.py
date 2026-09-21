"""Publish selected saved notebook outputs without executing the notebook."""
import hashlib
import html
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def main():
    path = ROOT / 'notebooks/01_data_cleaning.ipynb'
    notebook = json.loads(path.read_text(encoding='utf-8'))
    selected = {'2.7.', '3.8.', '4.4.', '5.5.', '6.4.', '7.2.', '7.3.',
                '8.5.', '9.3.', '9.4.', '9.5.'}
    sections = {}
    section = None
    for index, cell in enumerate(notebook['cells']):
        source = ''.join(cell['source'])
        if cell['cell_type'] == 'markdown':
            match = re.match(r'### (\d+\.\d+\.) (.+)', source)
            if match:
                section = match[1]
                if section in selected:
                    sections[section] = {'title': match[2], 'outputs': []}
        elif section in selected:
            for output in cell.get('outputs', []):
                data = output.get('data', {})
                table = re.search(r'<table\b.*?</table>', ''.join(data.get('text/html', [])), re.S)
                if table:
                    # Saved pandas tables only; remove notebook inline presentation.
                    content = re.sub(r'\s(?:style|border)="[^"]*"', '', table[0])
                    sections[section]['outputs'].append({'cell': index + 1, 'html': content})
                elif output.get('output_type') == 'stream':
                    sections[section]['outputs'].append({'cell': index + 1, 'html': '<pre>'+html.escape(''.join(output['text']))+'</pre>'})
    # The full variable profile is repetitive; keep the final quality table only.
    sections['9.5.']['outputs'] = sections['9.5.']['outputs'][:1]
    # Paired snapshots from the exports produced by the notebook. Keep these
    # explicitly distinct from captured cell outputs; no pipeline is rerun.
    panel_path = ROOT / 'data/processed/county_year_panel.parquet'
    prepared_path = ROOT / 'data/processed/prepared_geography_year.parquet'
    panel = pd.read_parquet(panel_path)
    prepared = pd.read_parquet(prepared_path)
    keys = ['county_fips', 'year']
    original = panel.set_index(keys)
    comparisons = []
    for variable in ['median_household_income', 'median_home_value', 'median_gross_rent']:
        for _, row in prepared.loc[prepared[variable + '_imputed']].head(2).iterrows():
            comparisons.append({'county': row['county_name'], 'year': row['year'],
                                'variable': variable,
                                'before': original.loc[(row['county_fips'], row['year']), variable],
                                'after': row[variable], 'imputed': True})
    export_snapshots = {
        'joined': panel[['county_fips', 'year', 'population', 'inflow_individuals',
                         'outflow_individuals', 'net_individuals_per_1000',
                         'declarations', 'temperature_f']].head(5).to_html(index=False, border=0),
        'imputed': pd.DataFrame(comparisons).to_html(index=False, border=0, na_rep='Missing')
    }
    result = {'notebook': str(path.relative_to(ROOT)).replace('\\', '/'),
              'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'sections': sections,
              'exportSnapshots': export_snapshots,
              'exportHashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [panel_path, prepared_path]}}
    target = ROOT / 'website/data/cleaning-evidence.json'
    target.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    print('Exported', sum(len(s['outputs']) for s in sections.values()), 'saved notebook outputs')

if __name__ == '__main__':
    main()
