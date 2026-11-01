"""Finalize notebook result bundles without exposing packaging code in the narrative.

Notebooks call ``export_analysis(name, globals())`` after their final result.
The namespace is read through explicit per-analysis contracts below; estimator
fitting and scientific choices remain in the notebooks. A failed export leaves
its previous canonical bundle intact because finish_analysis runs last.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd

from .exports import finish_analysis, notebook_conclusions, write_json


def _inputs(namespace, names):
    missing = [name for name in names if name not in namespace]
    if missing:
        raise ValueError('Run the notebook analysis cells before exporting; missing: ' + ', '.join(missing))
    return [namespace[name] for name in names]


def export_analysis(name, namespace):
    """Finalize one completed analysis using its live notebook variables."""
    exporters = {
        'clustering': _clustering,
        'pca': _pca,
        'naive_bayes': _naive_bayes,
        'decision_trees': _decision_trees,
    }
    if name not in exporters:
        raise ValueError(f'Unknown notebook analysis: {name}')
    exporters[name](namespace)


def _clustering(namespace):
    from scipy.cluster.hierarchy import dendrogram, linkage

    (ROOT, BUNDLE, summary, selected, fits, views, LABELS, counties, OUTCOME_DEFINITIONS, metrics, assignments, migration, scores, trees, toy, toy_fit, toy_z) = _inputs(
        namespace, ['ROOT', 'BUNDLE', 'summary', 'selected', 'fits', 'views', 'LABELS', 'counties', 'OUTCOME_DEFINITIONS', 'metrics', 'assignments', 'migration', 'scores', 'trees', 'toy', 'toy_fit', 'toy_z'])
    ROOT, BUNDLE = Path(ROOT), Path(BUNDLE)
    DOWNLOAD = OUT = BUNDLE/'data'
    # One row per selected method and cluster; all outcomes use rates per 1,000 ACS residents.
    summary_rows = []
    for view in ['characteristics', 'migration']:
        result = summary['views'][view]
        for method, label in [('kmeans', 'K-means'), ('hierarchical', 'Hierarchical')]:
            k = selected[view, method]
            labels = fits[view, method, k] + 1
            matrix = views[view]
            names = LABELS if view == 'characteristics' else ['Inflow rate', 'Outflow rate']
            for cluster in range(1, k+1):
                subset = counties.loc[labels == cluster]
                means = matrix[labels == cluster].mean(axis=0)
                strongest = np.argsort(np.abs(means))[-3:][::-1]
                reading = '; '.join(f'{names[j]} {means[j]:+.2f} SD relative to the cohort mean' for j in strongest)
                if method == 'kmeans':
                    reading = next(r['title'] for r in summary['interpretations'][view] if r['cluster'] == cluster) + '. ' + reading
                row = {'View': view.title(), 'Method': label, 'Selected k': k,
                       'Silhouette': result['silhouette' if method == 'kmeans' else 'hierarchical_silhouette'],
                       'Cluster': f'C{cluster}', 'Counties': len(subset), 'Interpretation': reading}
                for o in OUTCOME_DEFINITIONS:
                    for name, q in [('Median', .5), ('Q1', .25), ('Q3', .75)]:
                        row[o['label']+' '+name] = float(subset[o['rate']].quantile(q))
                summary_rows.append(row)
    conclusion_table = pd.DataFrame(summary_rows)
    conclusion_table.to_csv(DOWNLOAD/'clustering-conclusion-summary.csv', index=False)
    summary['conclusion_table'] = summary_rows
    summary['outcomes'] = OUTCOME_DEFINITIONS
    summary['metrics'] = json.loads(metrics.to_json(orient='records'))
    conclusion_sections = notebook_conclusions(ROOT, 'clustering')
    summary['conclusion_sections'] = conclusion_sections
    summary['conclusions'] = [p for section in conclusion_sections for p in section['paragraphs']]
    write_json(DOWNLOAD/'clustering.json', summary)

    # Browser figures use the same fitted arrays and hierarchy as the notebook.
    chart_data = {'profiles': {}, 'trees': {}}
    for view, matrix in views.items():
        labels = assignments[view + '_kmeans'].to_numpy()
        chart_data['profiles'][view] = {'labels': LABELS if view == 'characteristics' else ['Inflow rate', 'Outflow rate'],
            'values': pd.DataFrame(matrix).groupby(labels).mean().to_numpy().tolist()}
        tree = dendrogram(trees[view], truncate_mode='lastp', p=30, no_plot=True)
        chart_data['trees'][view] = {key: tree[key] for key in ['icoord', 'dcoord', 'ivl']}
    chart_data['counties'] = assignments.assign(inflow=migration.iloc[:,0], outflow=migration.iloc[:,1],
        PC1=scores[:,0], PC2=scores[:,1]).to_dict(orient='records')
    chart_data['toy'] = {'points': toy.tolist(), 'labels': toy_fit.labels_.tolist(), 'centers': toy_fit.cluster_centers_.tolist()}
    tree = dendrogram(linkage(toy_z, method='average', metric='cosine'), labels=list('ABCDEF'), no_plot=True)
    chart_data['trees']['toy'] = {key: tree[key] for key in ['icoord', 'dcoord', 'ivl']}
    write_json(DOWNLOAD/'clustering-charts.json', chart_data)


    finish_analysis(ROOT, 'clustering', BUNDLE)


def _pca(namespace):
    from .unsupervised import provenance

    (ROOT, BUNDLE, INPUT, counties, FEATURES, retained, retained90, cumulative, variance, interpretations, associations, limits, OUTCOME_DEFINITIONS, coefficients, loadings, toy, demo) = _inputs(
        namespace, ['ROOT', 'BUNDLE', 'INPUT', 'counties', 'FEATURES', 'retained', 'retained90', 'cumulative', 'variance', 'interpretations', 'associations', 'limits', 'OUTCOME_DEFINITIONS', 'coefficients', 'loadings', 'toy', 'demo'])
    ROOT, BUNDLE = Path(ROOT), Path(BUNDLE)
    DOWNLOAD = OUT = BUNDLE/'data'
    write_json(DOWNLOAD/'pca-toy.json', {'points': toy.tolist(),
        'vectors': (demo.components_ * np.sqrt(demo.explained_variance_)[:,None] * 2).tolist()})

    summary = provenance(INPUT, counties, FEATURES)
    summary.update(retained=retained,retained90=retained90,retained_variance=float(cumulative[retained-1]),
        two_component_variance=float(cumulative[1]),variance=variance.to_dict(orient='records'),
        interpretations=interpretations,associations=associations.to_dict(orient='records'),color_limits=limits,outcomes=OUTCOME_DEFINITIONS)
    summary['strongest_associations']={}
    conclusion_sections = notebook_conclusions(ROOT, 'pca')
    conclusions = [p for section in conclusion_sections for p in section['paragraphs']]
    summary['conclusion_sections'] = conclusion_sections
    for o in OUTCOME_DEFINITIONS:
        a=associations.loc[associations.outcome.eq(o['id'])]
        strongest=a.loc[a.spearman_rho.abs().idxmax()]
        summary['strongest_associations'][o['id']]={'component':strongest.component,'spearman_rho':float(strongest.spearman_rho)}
    summary['coefficients']=coefficients.iloc[:,:retained].to_dict(orient='index')
    summary['variable_correlations']=loadings.iloc[:,:retained].to_dict(orient='index')
    summary['conclusions']=conclusions
    write_json(DOWNLOAD/'pca.json',summary)

    finish_analysis(ROOT, 'pca', BUNDLE)


def _naive_bayes(namespace):
    (ROOT, BUNDLE, result, context) = _inputs(
        namespace, ['ROOT', 'BUNDLE', 'result', 'context'])
    ROOT, BUNDLE = Path(ROOT), Path(BUNDLE)
    DOWNLOAD = OUT = BUNDLE/'data'
    conclusion_sections = notebook_conclusions(ROOT, 'naive_bayes')
    result['conclusions'] = conclusion_sections[0]['paragraphs']
    write_json(OUT/'naive-bayes.json', {'context': context, 'tasks': {'inflow': result}})
    finish_analysis(ROOT, 'classification/naive-bayes', BUNDLE)


def _decision_trees(namespace):
    (ROOT, BUNDLE, tasks, context, worked_example) = _inputs(
        namespace, ['ROOT', 'BUNDLE', 'tasks', 'context', 'worked_example'])
    ROOT, BUNDLE = Path(ROOT), Path(BUNDLE)
    DOWNLOAD = OUT = BUNDLE/'data'
    conclusion_sections = notebook_conclusions(ROOT, 'decision_trees')
    for outcome, section in zip(['outflow', 'net'], conclusion_sections):
        tasks[outcome]['conclusions'] = section['paragraphs']
    write_json(OUT/'decision-trees.json',{'context':context,'tasks':tasks,'worked_example':worked_example})

    finish_analysis(ROOT, 'classification/decision-trees', BUNDLE)
