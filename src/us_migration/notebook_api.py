"""Expose notebook-defined transforms to tests without executing its data workflow.

Only cells explicitly tagged cleaning-definitions are evaluated. The notebook is
the single implementation; importing this module does not download or clean data.
"""
from functools import lru_cache
import ast
import io
import json
import re
import unicodedata
import zipfile
from datetime import datetime
import numpy as np
import pandas as pd
from .acquisition import ROOT, ACS_VARIABLES
from .eda import FEATURES, OUTCOMES


@lru_cache(maxsize=1)
def definitions():
    path=ROOT/'notebooks/01_data_cleaning.ipynb'
    notebook=json.loads(path.read_text(encoding='utf-8'))
    namespace={'np':np,'pd':pd,'io':io,'json':json,'re':re,'zipfile':zipfile,
               'unicodedata':unicodedata,'datetime':datetime,'ROOT':ROOT,
               'ACS_VARIABLES':ACS_VARIABLES,'FEATURES':FEATURES,'OUTCOMES':OUTCOMES,
               '__name__':'us_migration.notebook_definitions'}
    for number,cell in enumerate(notebook['cells']):
        if 'cleaning-definitions' not in cell.get('metadata',{}).get('tags',[]):continue
        source=''.join(cell['source'])
        tree=ast.parse(source)
        if any(not isinstance(node,(ast.FunctionDef,ast.ClassDef,ast.Assign)) for node in tree.body):
            raise ValueError(f'Definition cell {number} contains a workflow statement')
        exec(compile(tree,f'{path}#cell-{number}','exec'),namespace)
    return namespace
