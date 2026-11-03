"""frozen u numerical inputs, separate from fitted annual execution artifacts."""

from dataclasses import asdict
import hashlib
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from .artifacts import json_values, require, write_json
from .captures import strict_json
from .execution_design import ExecutionPredictor, SetterCandidate, origin_law

_ARRAYS = ('target', 'rows', 'weight', 'map_indices', 'native_neighbors',
           'circumstance_indices', 'age_indices', 'setter_mean_indices', 'setter_mean_weights')
_METADATA = ('head', 'size', 'keys', 'design', 'actors', 'age_indices_by_block_role', 'setup_index')
_BATCH = ('row', 'weight', 'origin_cell')
_ORIGIN = ('origin_centers', 'origin_neighbors', 'origin_weights')


def _sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def _write_arrays(root, name, arrays):
    path = root / name
    require(all(value.dtype.kind in 'iuf' and np.isfinite(value).all() for value in arrays.values()),
            'u input arrays must be finite numerical data')
    with path.open('xb') as stream:
        np.savez(stream, **arrays)
    return dict(path=name, sha256=_sha(path), bytes=path.stat().st_size,
                arrays=[dict(name=key, dtype=value.dtype.str, shape=list(value.shape)) for key, value in arrays.items()])


def _read_arrays(root, reference):
    path = (root / reference['path']).resolve()
    require(path.is_relative_to(root) and path.is_file(), 'u input member is missing or outside bundle')
    require(path.stat().st_size == reference['bytes'] and _sha(path) == reference['sha256'], 'u input member digest differs')
    contract = reference['arrays']
    with np.load(path, allow_pickle=False) as arrays:
        require(arrays.files == [row['name'] for row in contract], 'u input array names/order differ')
        result = {name: arrays[name] for name in arrays.files}
    require(all(value.dtype.str == row['dtype'] and list(value.shape) == row['shape']
                and value.dtype.kind in 'iuf' and np.isfinite(value).all()
                for row, value in zip(contract, result.values(), strict=True)), 'u input dtype/shape/value differs')
    return result


def _csr_arrays(matrix):
    require(isinstance(matrix, csr_matrix), 'u input matrix must be csr')
    return dict(data=matrix.data, indices=matrix.indices, indptr=matrix.indptr)


def _csr(arrays, shape):
    require(arrays['data'].dtype == np.float64 and arrays['data'].ndim == 1
            and arrays['indices'].dtype.kind == 'i' and arrays['indptr'].dtype.kind == 'i'
            and arrays['indices'].ndim == arrays['indptr'].ndim == 1,
            'u input csr arrays have wrong types')
    # scipy may choose narrower indices in its constructor; retain captured widths.
    matrix = csr_matrix(tuple(shape), dtype=np.float64)
    matrix.data, matrix.indices, matrix.indptr = (arrays[name] for name in ('data', 'indices', 'indptr'))
    matrix.check_format(full_check=True)
    require(matrix.has_sorted_indices and matrix.has_canonical_format, 'u input csr is not canonical')
    return matrix


def write_u_bundle(output, design, *, actors, initial, metadata, selector, probes):
    """write existing physical rows and unchanged dynamic batches; manifest last."""
    require(design['head'] == 'u' and initial.dtype == np.float64 and initial.shape == (design['size'],),
            'u input capture requires u and a float64 baseline of canonical dimension')
    require('incoming_ledger' in metadata, 'u input capture needs incoming ledger')
    root = Path(output).resolve()
    root.mkdir()
    (root / 'batches').mkdir()
    head = {name: design[name] for name in _METADATA}
    document = dict(schema_version=1, kind='execution-u-inputs', metadata=metadata,
                    design=head, actors=actors, selector=selector,
                    probes=[asdict(predictor) for predictor in probes])
    write_json(root / 'inputs.json', json_values(document), compact=True)
    info = dict(path='inputs.json', sha256=_sha(root / 'inputs.json'), bytes=(root / 'inputs.json').stat().st_size)
    arrays = _write_arrays(root, 'head.npz', {name: design[name] for name in _ARRAYS}
                           | dict(initial=initial) | dict(zip(_ORIGIN, origin_law(), strict=True)))
    fixed = _write_arrays(root, 'fixed.npz', _csr_arrays(design['fixed_matrix']))
    fixed['shape'] = list(design['fixed_matrix'].shape)
    batches = []
    for number, batch in enumerate(design['batches']()):
        reference = _write_arrays(root, f'batches/{number:05d}.npz',
                                  _csr_arrays(batch['dynamic_matrix']) | {name: batch[name] for name in _BATCH})
        reference.update(shape=list(batch['dynamic_matrix'].shape),
                         base_matrix_nonzeros=batch['base_matrix_nonzeros'])
        batches.append(reference)
    manifest = dict(schema_version=1, kind='execution-u-input-bundle', inputs=info,
                    arrays=arrays, fixed=fixed, batches=batches)
    manifest['payload_bytes'] = info['bytes'] + arrays['bytes'] + fixed['bytes'] + sum(row['bytes'] for row in batches)
    write_json(root / 'manifest.json', manifest)
    return root / 'manifest.json'


def load_u_bundle(path):
    """restore the canonical objective inputs without any source or feature pass."""
    path = Path(path).resolve(strict=True)
    root = path.parent
    manifest = strict_json(path.read_bytes())
    require(manifest['schema_version'] == 1 and manifest['kind'] == 'execution-u-input-bundle', 'wrong u input bundle kind/version')
    info = manifest['inputs']
    member = (root / info['path']).resolve()
    require(member.is_relative_to(root) and member.is_file(), 'u metadata member is missing or outside bundle')
    require(member.stat().st_size == info['bytes'] and _sha(member) == info['sha256'], 'u metadata digest differs')
    document = strict_json(member.read_bytes())
    require(document['schema_version'] == 1 and document['kind'] == 'execution-u-inputs', 'wrong u inputs kind/version')
    design = document['design']
    require(set(design) == set(_METADATA) and design['head'] == 'u'
            and type(design['size']) is int and design['size'] > 0, 'u input head metadata differs')
    arrays = _read_arrays(root, manifest['arrays'])
    require(list(arrays) == [*_ARRAYS, 'initial', *_ORIGIN], 'u head array contract differs')
    for name, current in zip(_ORIGIN, origin_law(), strict=True):
        value = arrays.pop(name)
        require(value.dtype == current.dtype and value.shape == current.shape
                and value.tobytes() == current.tobytes(), 'u captured origin law differs: ' + name)
    for name, value in arrays.items():
        require(value.dtype == (np.int64 if name in ('rows', 'map_indices', 'native_neighbors', 'circumstance_indices', 'age_indices', 'setter_mean_indices') else np.float64),
                'u head array has wrong type: ' + name)
    initial = arrays.pop('initial')
    design.update(arrays)
    physical = len(design['keys']); size = design['size']
    require(initial.shape == (size,) and design['target'].shape == design['rows'].shape == design['weight'].shape == (physical,)
            and len(set(design['keys'])) == physical and np.all(np.isin(design['target'], (0.,1.)))
            and np.all(design['weight'] > 0), 'u physical rows/targets differ')
    require(design['design']['size'] == size and len(design['design']['coefficient_names']) == size,
            'u coefficient layout differs')
    design['fixed_matrix'] = _csr(_read_arrays(root, manifest['fixed']), manifest['fixed']['shape'])
    require(design['fixed_matrix'].shape == (physical,size), 'u fixed matrix dimensions differ')
    batches = []
    fixed_nonzeros = np.diff(design['fixed_matrix'].indptr)
    for reference in manifest['batches']:
        arrays = _read_arrays(root, reference)
        require(list(arrays) == ['data', 'indices', 'indptr', *_BATCH], 'u batch array contract differs')
        dynamic = _csr(arrays, reference['shape'])
        row, weight, cell = (arrays[name] for name in _BATCH)
        require(row.dtype == cell.dtype == np.int64 and weight.dtype == np.float64
                and row.ndim == weight.ndim == cell.ndim == 1 and len(row) == len(weight) == len(cell)
                and 0 < len(row) <= 4096 and dynamic.shape == (len(row),size)
                and np.all((row >= 0) & (row < physical)) and np.all((cell >= 0) & (cell < 656))
                and np.all(weight > 0), 'u batch row/origin/weight contract differs')
        require(reference['base_matrix_nonzeros'] == int(fixed_nonzeros[row].sum()+dynamic.nnz),
                'u batch nonzero count differs')
        batches.append(dict(dynamic_matrix=dynamic, row=row, weight=weight,
                            base_matrix_nonzeros=reference['base_matrix_nonzeros'], origin_cell=cell))
    require(bool(batches), 'u input bundle has no batches')
    design['batches'] = lambda: iter(batches)
    probes = []
    for record in document['probes']:
        record['setter_prior'] = tuple(SetterCandidate(**candidate) for candidate in record['setter_prior'])
        record['context']['strength'] = tuple(record['context']['strength'])
        probes.append(ExecutionPredictor(**record))
    return dict(design=design, actors=document['actors'], initial=initial,
                metadata=document['metadata'], selector=document['selector'], probes=tuple(probes))
