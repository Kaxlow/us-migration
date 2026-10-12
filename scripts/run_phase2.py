"""Execute just the two Phase 2 notebooks; never rerun acquisition or cleaning."""
from run_notebooks import ROOT, execute_notebook

if __name__ == '__main__':
    for filename in ['03_clustering.ipynb', '04_pca.ipynb']:
        execute_notebook(ROOT / 'notebooks' / filename)
