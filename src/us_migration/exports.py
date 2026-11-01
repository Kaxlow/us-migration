"""Owned result bundles and static publication, independent of notebook execution."""
from pathlib import Path
import csv
import hashlib
import io
import json
import tempfile


def notebook_conclusions(root, notebook):
    """Read the reviewed prose from the notebook's conclusion Markdown cell.

    Authors review these paragraphs against saved results after changing a model.
    Exporting the same prose keeps the notebook and website in agreement.
    """
    cells = json.loads((Path(root)/'notebooks'/f'{notebook}.ipynb').read_text(encoding='utf-8'))['cells']
    cell = next(c for c in cells if c['cell_type'] == 'markdown'
                and any(line.startswith('## Conclusion') for line in ''.join(c['source']).splitlines()))
    sections = []
    for block in ''.join(cell['source']).strip().split('\n\n'):
        if block.startswith('<a ') or block.startswith('## '):
            continue
        if block.startswith('### '):
            sections.append({'title': block[4:].strip(), 'paragraphs': []})
        else:
            if not sections:
                sections.append({'title': '', 'paragraphs': []})
            sections[-1]['paragraphs'].append(block.replace('\n', ' '))
    if not sections or any(not s['paragraphs'] for s in sections):
        raise ValueError(f'{notebook}: conclusions need reviewed paragraphs')
    return sections


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def begin_analysis(root, topic):
    """Write a run in isolation; a failed notebook leaves the last result intact."""
    if topic not in {'exploration', 'clustering', 'pca', 'classification/naive-bayes', 'classification/decision-trees'}:
        raise ValueError('Unknown analysis topic')
    parent = Path(root)/'data/interim/analysis-runs'
    parent.mkdir(parents=True, exist_ok=True)
    bundle = Path(tempfile.mkdtemp(prefix=topic.replace('/', '-')+'-', dir=parent))
    for folder in ['data', 'figures']:
        (bundle/folder).mkdir()
    return bundle


def owned_path(directory, relative):
    directory = Path(directory).resolve()
    path = (directory/relative).resolve()
    if path == directory or directory not in path.parents:
        raise ValueError(f'Output escapes its owner: {relative}')
    return path


def publish_files(directory, files):
    """Replace only this owner's recorded files; preserve unowned local files."""
    directory = Path(directory)
    manifest = directory/'manifest.json'
    old = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {'files': {}}
    # Validate the complete operation before writing or removing anything.
    for name in set(files) | set(old['files']):
        owned_path(directory, name)
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in sorted(files.items())}
    for name, content in files.items():
        target = owned_path(directory, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != content:
            target.write_bytes(content)
    for name in set(old['files']) - set(files):
        target = owned_path(directory, name)
        if target.is_file():
            target.unlink()
    write_json(manifest, {'files': hashes})


def finish_analysis(root, topic, bundle):
    files = {p.relative_to(bundle).as_posix(): p.read_bytes() for p in Path(bundle).rglob('*') if p.is_file() and p.name != 'manifest.json'}
    publish_files(Path(root)/'reports/analyses'/topic, files)


def read_bundle(root, topic):
    directory = Path(root)/'reports/analyses'/topic
    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    files = {}
    for name, expected in manifest['files'].items():
        content = owned_path(directory, name).read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError(f'{topic}: changed artifact {name}; rerun or finalize its analysis')
        files[name] = content
    return files


def classification_files(root):
    """Combine independent analyses only when their input and split evidence agree."""
    bundles = [read_bundle(root, 'classification/'+name) for name in ['naive-bayes', 'decision-trees']]
    nb, dt = [json.loads(files['data/'+name+'.json']) for files, name in zip(bundles, ['naive-bayes', 'decision-trees'])]
    if nb['context'] != dt['context']:
        raise ValueError('Classification provenance differs; refresh both analyses on the same input and specification')
    merged = {}
    for files in bundles:
        for name, content in files.items():
            if name in merged and merged[name] != content:
                raise ValueError(f'Classification shared artifact differs: {name}')
            merged[name] = content
    rows = []
    for outcome, task in {**nb['tasks'], **dt['tasks']}.items():
        rows.append({'outcome': outcome, 'model': 'Multinomial NB' if outcome == 'inflow' else 'Decision tree',
                     'test_count': task['test_count'], **{key: task['model'][key] for key in ['accuracy', 'balanced_accuracy', 'macro_f1']},
                     'baseline_accuracy': task['baseline']['accuracy'], 'baseline_macro_f1': task['baseline']['macro_f1']})
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    merged['data/question-9-results.csv'] = stream.getvalue().encode()
    # Each image shows a six-column slice. Compare all sample rows in that slice
    # and their row keys, so differently labeled tasks can share identical inputs.
    sample_images = {}
    for bundle in [nb, dt]:
        for task in bundle['tasks'].values():
            for sample in task['samples']:
                name = sample['name']
                if '-characteristics-' not in name: continue
                prefix, split = name.split('-characteristics-')
                keys = merged[f'data/{prefix}-{split}-sample-keys.csv']
                rows = list(csv.DictReader(io.StringIO(merged[f'data/{name}.csv'].decode())))
                for index, image in enumerate(sample['images']):
                    columns = tuple(sample['columns'][index*6:(index+1)*6])
                    signature = (columns, tuple(tuple(row[c] for c in columns) for row in rows), keys)
                    prior = sample_images.get(signature)
                    if prior and merged['figures/'+image] == merged['figures/'+prior]:
                        sample['images'][index] = prior
                    else:
                        sample_images[signature] = image
    referenced = {image for b in [nb,dt] for t in b['tasks'].values() for s in t['samples'] for image in s['images']}
    for name in list(merged):
        if name.startswith('figures/') and '-characteristics-' in name and Path(name).name not in referenced:
            del merged[name]
    for name, bundle in [('naive-bayes',nb),('decision-trees',dt)]:
        merged['data/'+name+'.json'] = (json.dumps(bundle, indent=2)+'\n').encode()
    return merged


def website_bundle(root, topic, files):
    for source, destination in [('data','data'), ('figures','assets')]:
        selected = {name[len(source)+1:]: content for name,content in files.items() if name.startswith(source+'/')}
        publish_files(Path(root)/'website'/destination/topic, selected)


def export_topics(root, topics=None):
    root = Path(root)
    available = [t for t in ['cleaning','exploration','clustering','pca'] if (root/'reports/analyses'/t/'manifest.json').exists()]
    if all((root/'reports/analyses/classification'/t/'manifest.json').exists() for t in ['naive-bayes','decision-trees']):
        available.append('classification')
    selected = available if topics is None else list(dict.fromkeys(topics))
    # Assemble and validate every requested bundle before modifying public artifacts.
    bundles = {t: classification_files(root) if t == 'classification' else read_bundle(root,t) for t in selected}
    for topic, files in bundles.items():
        website_bundle(root, topic, files)
    from .outcomes import OUTCOME_DEFINITIONS
    (root/'website/outcome-definitions.js').write_text('// Generated from the Python outcome contract.\nexport default '+json.dumps(OUTCOME_DEFINITIONS,ensure_ascii=False)+';\n',encoding='utf-8')
    refresh_findings(root)
    return selected


def refresh_findings(root):
    """Small findings payload keeps the overview independent of large chart datasets."""
    data = Path(root)/'website/data'
    sources = {'exploration':'exploration/analysis.json','clustering':'clustering/clustering.json',
               'pca':'pca/pca.json','naive-bayes':'classification/naive-bayes.json','decision-trees':'classification/decision-trees.json'}
    result = {}
    hashes = {}
    for topic, relative in sources.items():
        path = data/relative
        if not path.exists(): continue
        value = json.loads(path.read_text(encoding='utf-8'))
        context = value.get('context', value)
        hashes[topic] = context.get('input_sha256',context.get('sourceSha256'))
        if topic == 'exploration':
            result[topic] = {'year':value['latest'], 'counties':value['counties'], 'captions':value['captions'], 'associations':value['associations']}
        elif topic in ['clustering','pca']:
            result[topic] = {key:value[key] for key in ['year','counties','conclusions']}
        else:
            for outcome, task in value['tasks'].items():
                result.setdefault('classification',{})[outcome] = {'model':task['model'], 'baseline':task['baseline'], 'test_count':task['test_count'], 'conclusions':task['conclusions']}
    result['inputHashes'] = hashes
    result['consistentInput'] = len(set(hashes.values())) <= 1
    write_json(data/'findings.json',result)
