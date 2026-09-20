"""Execute notebook analyses offline using this Python environment."""
import os
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager
import json

ROOT=Path(__file__).resolve().parents[1]

def execute_notebook(path, parameters=None):
    # Keep kernel registration local to the repo; do not modify the user's global kernels.
    runtime=ROOT/'data/interim/jupyter'
    kernel=runtime/'kernels/us-migration'
    kernel.mkdir(parents=True,exist_ok=True)
    (kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
        'display_name':'US Migration','language':'python'}))
    os.environ['JUPYTER_PATH']=str(runtime)
    os.environ['IPYTHONDIR']=str(runtime/'ipython')
    os.environ['JUPYTER_RUNTIME_DIR']=str(runtime/'runtime')
    os.environ['MPLCONFIGDIR']=str(runtime/'matplotlib')
    notebook=nbformat.read(path,as_version=4)
    if parameters:
        cell=next(c for c in notebook.cells if c.cell_type=='code' and c.source.startswith('START_YEAR='))
        import re
        for name,value in parameters.items():
            cell.source=re.sub(rf'(?m)^{name}=.*$',f'{name}={int(value)}',cell.source)
    client=NotebookClient(notebook,timeout=900,kernel_name='us-migration',resources={'metadata':{'path':str(ROOT)}})
    try:
        client.execute()
    finally:
        nbformat.write(notebook,path)
    print('Executed',path.name,flush=True)


def main():
    for path in sorted((ROOT/'notebooks').glob('0*.ipynb')):
        execute_notebook(path)

if __name__=='__main__': main()
