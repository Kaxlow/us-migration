"""Shared classification contracts and exports; model fitting lives in the classification notebooks."""
from pathlib import Path
import hashlib
import json
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.model_selection import train_test_split
from .cohorts import FEATURES, LABELS, prepare_cross_section
from .unsupervised import configure_plots
from .snapshot_style import style_cell

SEED = 42
RATE_CLASSES = ['Low', 'Medium', 'High']
NET_CLASSES = ['Net outflow', 'Net inflow']
QUESTION = 'How accurately can county characteristics classify counties by migration outcome in terms of net migration, inflows, and outflows?'


def rate_labels(values, thresholds):
    values = np.asarray(values, dtype=float)
    thresholds = np.asarray(thresholds, dtype=float)
    if thresholds.shape != (2,) or not np.isfinite(thresholds).all() or thresholds[0] >= thresholds[1]:
        raise ValueError('Two distinct finite thresholds are required')
    if not np.isfinite(values).all():
        raise ValueError('Outcome values must be finite')
    return np.asarray(RATE_CLASSES)[np.searchsorted(thresholds, values, side='left')]


def prepare_classification(panel):
    counties, x, _ = prepare_cross_section(panel)
    train, test = train_test_split(np.arange(len(counties)), test_size=.2, random_state=SEED)
    counties['classification_split'] = 'train'
    counties.loc[test, 'classification_split'] = 'test'
    thresholds = {}
    for outcome in ['inflow', 'outflow']:
        field = outcome + '_individuals_per_1000'
        thresholds[outcome] = counties.iloc[train][field].quantile([1/3, 2/3], interpolation='linear').tolist()
        counties[outcome + '_class'] = rate_labels(counties[field], thresholds[outcome])
    net = counties.net_individuals_per_1000
    counties['net_class'] = np.where(net > 0, 'Net inflow', np.where(net < 0, 'Net outflow', 'Balanced'))
    assert set(train).isdisjoint(test)
    return counties, x, thresholds


def task_rows(counties, x, outcome):
    eligible = counties.net_class.ne('Balanced') if outcome == 'net' else pd.Series(True, index=counties.index)
    train = eligible & counties.classification_split.eq('train')
    test = eligible & counties.classification_split.eq('test')
    return x.loc[train], x.loc[test], counties.loc[train, outcome+'_class'], counties.loc[test, outcome+'_class']


def metrics(y, prediction, classes):
    matrix = confusion_matrix(y, prediction, labels=classes)
    totals = matrix.sum(axis=1, keepdims=True)
    return {'accuracy': float(accuracy_score(y, prediction)),
            'balanced_accuracy': float(balanced_accuracy_score(y, prediction)),
            'macro_f1': float(f1_score(y, prediction, labels=classes, average='macro', zero_division=0)),
            'classes': classes, 'confusion': matrix.tolist(),
            'confusion_normalized': np.divide(matrix, totals, out=np.zeros_like(matrix, dtype=float), where=totals!=0).tolist(),
            'classification_report': classification_report(y, prediction, labels=classes, output_dict=True, zero_division=0)}


def records(frame):
    return json.loads(frame.to_json(orient='records', double_precision=15))


from .exports import write_json


def export_context(root, source, counties, thresholds):
    import sklearn
    directory = root/'data'
    directory.mkdir(parents=True, exist_ok=True)
    fields = ['county_fips', 'county_name', 'year', 'classification_split', 'data_split',
              'inflow_class', 'outflow_class', 'net_class', 'socioeconomic_imputed', 'net_rate_iqr_flag']
    fields += [o+'_individuals'+suffix for o in ['inflow', 'outflow', 'net'] for suffix in ['', '_per_1000']]
    counties[fields].to_csv(directory/'county-profiles.csv', index=False)
    context = {'input': 'data/processed/analysis_county_year.parquet',
               'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'year': 2023, 'counties': len(counties), 'features': FEATURES, 'feature_labels': LABELS,
               'thresholds': thresholds, 'seed': SEED, 'test_size': .2, 'question': QUESTION,
               'split_counts': counties.classification_split.value_counts().to_dict(),
               'balanced_counties': int(counties.net_class.eq('Balanced').sum()),
               'imputed_counties': int(counties.socioeconomic_imputed.sum()),
               'outlier_flagged_counties': int(counties.net_rate_iqr_flag.sum()),
               'versions': {'numpy': np.__version__, 'pandas': pd.__version__, 'sklearn': sklearn.__version__},
               'class_counts': {o: records(counties.groupby(['classification_split', o+'_class']).size().rename('count').reset_index())
                                for o in ['inflow','outflow','net']}}
    write_json(directory/'context.json', context)
    return context


def figure(fig, root, name, svg=False):
    directory = root/'figures'
    directory.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(directory/(name+'.png'), dpi=130, bbox_inches='tight', facecolor='white')
    if svg:
        fig.savefig(directory/(name+'.svg'), bbox_inches='tight', facecolor='white')
    plt.show()
    plt.close(fig)


def sample(frame, root, name):
    """20-row CSV plus legible five-row images covering every column."""
    frame = frame.sort_index().head(20)
    frame.to_csv(root/'data'/f'{name}.csv', index=False)
    images = []
    for start in range(0, len(frame.columns), 6):
        part = frame.iloc[:5, start:start+6]
        fig, ax = plt.subplots(figsize=(12, 2.6))
        ax.axis('off')
        values = [[f'{v:.3f}' if isinstance(v, (float, np.floating)) else str(v) for v in row] for row in part.to_numpy()]
        table = ax.table(cellText=values, colLabels=[textwrap.fill(c.replace('_', ' '), 21) for c in part.columns],
                         cellLoc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        for (r, c), cell in table.get_celld().items():
            style_cell(cell, r)
            if r == 0:
                cell.set_height(cell.get_height()*1.6)
        filename = f'{name}-{start//6+1}'
        figure(fig, root, filename)
        images.append(filename+'.png')
    return {'name': name, 'columns': frame.columns.tolist(), 'images': images}


def evaluate(model, baseline, x_test, y_test, classes, counties, root, outcome):
    predicted, base = model.predict(x_test), baseline.predict(x_test)
    rows = counties.loc[x_test.index, ['county_fips','county_name','year','classification_split']].copy()
    rows['actual'], rows['predicted'], rows['baseline'] = y_test, predicted, base
    for i, label in enumerate(model.classes_):
        rows['probability_'+label.lower().replace(' ', '_')] = model.predict_proba(x_test)[:, i]
    rows.to_csv(root/'data'/f'{outcome}-predictions.csv', index=False)
    result = {'model': metrics(y_test, predicted, classes), 'baseline': metrics(y_test, base, classes)}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, key, title in zip(axes, ['confusion', 'confusion_normalized'], ['County counts', 'Share of actual class']):
        matrix = np.asarray(result['model'][key])
        ax.imshow(matrix, cmap='migration_sequential', vmin=0,
                  vmax=1 if key == 'confusion_normalized' else matrix.max())
        ax.set(xticks=range(len(classes)), yticks=range(len(classes)), xticklabels=classes,
               yticklabels=classes, xlabel='Predicted', ylabel='Actual', title=title)
        for i in range(len(classes)):
            for j in range(len(classes)):
                ax.text(j, i, str(matrix[i,j]) if key=='confusion' else f'{matrix[i,j]:.1%}',
                        ha='center', va='center', color='white' if matrix[i,j]>(1 if key == 'confusion_normalized' else matrix.max())*.6 else '#293d36')
    figure(fig, root, outcome+'-confusion')
    return result


def comparison_plot(table, root, name):
    fig, ax = plt.subplots(figsize=(11, 4))
    positions = np.arange(len(table))
    ax.plot(positions, table.mean_train_score, 'o-', label='Training macro-F1')
    ax.errorbar(positions, table.mean_test_score, yerr=table.std_test_score, fmt='o-', label='Validation macro-F1 ± fold SD')
    ax.set(xlabel='Candidate (see tuning table)', ylabel='Macro-F1', ylim=(0, 1))
    ax.set_xticks(positions[::2])
    ax.legend()
    figure(fig, root, name)


def tree_structure(estimator):
    tree = estimator.tree_
    def visit(i):
        weights = tree.value[i][0]
        node = {'id': int(i), 'samples': int(tree.n_node_samples[i]), 'impurity': float(tree.impurity[i]),
                'prediction': str(estimator.classes_[weights.argmax()]),
                'proportions': {str(c): float(v/weights.sum()) for c,v in zip(estimator.classes_, weights)}}
        if tree.children_left[i] != -1:
            node.update(feature=FEATURES[tree.feature[i]], threshold=float(tree.threshold[i]),
                        children=[visit(tree.children_left[i]), visit(tree.children_right[i])])
        return node
    return visit(0)
