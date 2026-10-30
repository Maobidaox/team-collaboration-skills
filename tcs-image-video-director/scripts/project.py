#!/usr/bin/env python3
"""Local project ledger. Never submits remote work or claims server-side idempotency."""
import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path


def identifier(value):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,159}', value):
        raise ValueError('Use an ASCII identifier without path separators')
    return value


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


@contextmanager
def transaction(root, create=False):
    root = Path(root).resolve()
    os.makedirs(root, exist_ok=True)
    lock = root / '.project.lock'
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ValueError('Project is locked; verify the other writer before recovering the lock')
    os.close(fd)
    temp = None
    try:
        p = root / 'project.json'
        if create:
            if p.exists():
                raise ValueError('Project already exists; use show to resume')
            state = {'workflow_id': str(uuid.uuid4()), 'state_version': 0, 'status': 'draft',
                     'artifacts': {}, 'submissions': {}, 'pending_actions': [], 'delivery': None}
        else:
            state = json.loads(p.read_text())
        before = json.dumps(state, ensure_ascii=False, sort_keys=True)
        yield root, state
        if create or json.dumps(state, ensure_ascii=False, sort_keys=True) != before:
            history = root / 'history'
            os.makedirs(history, exist_ok=True)
            if p.exists():
                snapshot = history / f'{state["state_version"]:06}.json'
                if not snapshot.exists():
                    shutil.copyfile(p, snapshot)
            state['state_version'] += 1
            fd, name = tempfile.mkstemp(prefix='.state-', dir=root)
            temp = Path(name)
            with os.fdopen(fd, 'w') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
                f.write('\n'); f.flush(); os.fsync(f.fileno())
            os.replace(temp, p)
    finally:
        if temp and temp.exists():
            temp.unlink()
        lock.unlink()


def descendants(state, changed):
    affected = {changed}
    while True:
        more = {k for k, a in state['artifacts'].items() if set(a['depends_on']) & affected}
        if more <= affected:
            return affected - {changed}
        affected |= more


def add_artifact(root, state, key, file, kind, dependencies):
    identifier(key)
    source = Path(file).resolve(strict=True)
    if not source.is_file():
        raise ValueError('Artifact must be a readable local file')
    deps = list(dict.fromkeys(dependencies))
    if key in deps or any(d not in state['artifacts'] for d in deps):
        raise ValueError('Dependencies must exist and must not reference this artifact')
    if set(deps) & descendants(state, key):
        raise ValueError('Dependency cycle')
    if any(state['artifacts'][d]['status'] in ('invalidated', 'failed') for d in deps):
        raise ValueError('Cannot build from an invalidated input')
    dependency_hashes = {d: state['artifacts'][d]['sha256'] for d in deps}
    sha = digest(source)
    suffix = source.suffix.lower() if re.fullmatch(r'\.[a-zA-Z0-9]{1,8}', source.suffix) else '.bin'
    dest = root / 'assets' / (sha + suffix)
    os.makedirs(dest.parent, exist_ok=True)
    if not dest.exists():
        shutil.copyfile(source, dest)
    old = state['artifacts'].get(key)
    if old and old['sha256'] == sha and old['depends_on'] == deps and old['kind'] == kind and old.get('dependency_hashes') == dependency_hashes and old['status'] != 'invalidated':
        return
    for dependent in descendants(state, key):
        state['artifacts'][dependent]['status'] = 'invalidated'
        state['artifacts'][dependent]['review'] = None
    state['artifacts'][key] = {'path': str(dest.relative_to(root)), 'sha256': sha, 'kind': kind,
                              'depends_on': deps, 'dependency_hashes': dependency_hashes, 'status': 'ready', 'review': None}
    state['status'] = 'draft'
    state['delivery'] = None


def reserve(state, key, tool, inputs, authorization):
    identifier(key)
    if not authorization.strip():
        raise ValueError('Record the user-authorized scope before reserving a submission')
    if key in state['submissions']:
        raise ValueError('Submission already reserved; query the recorded task, never submit this key again')
    for name in inputs:
        if name not in state['artifacts'] or state['artifacts'][name]['status'] not in ('ready', 'accepted'):
            raise ValueError('Submission input missing or invalidated')
    state['submissions'][key] = {'tool': tool, 'inputs': inputs, 'authorization': authorization,
                                'input_hashes': {k: state['artifacts'][k]['sha256'] for k in inputs},
                                'status': 'unknown', 'generationId': None}


def receipt(state, key, task_id, status):
    entry = state['submissions'][key]
    if entry['generationId'] and entry['generationId'] != task_id:
        raise ValueError('Cannot change the remote task associated with a submission')
    if not task_id.strip():
        raise ValueError('Only record the actual remote task identifier')
    if entry['status'] in ('ready', 'failed') and entry['status'] != status:
        raise ValueError('Terminal task status cannot be reversed locally')
    entry.update(generationId=task_id, status=status)


def review(root, state, key, evidence, passed):
    item = state['artifacts'][key]
    if item['status'] == 'invalidated':
        raise ValueError('Replace the invalidated artifact before reviewing')
    if digest(root / item['path']) != item['sha256']:
        raise ValueError('Artifact changed outside the project ledger')
    if not evidence.strip():
        raise ValueError('Review must identify observed evidence and checks')
    item['review'] = {'passed': passed, 'evidence': evidence}
    item['status'] = 'accepted' if passed else 'failed'
    state['status'] = 'draft'; state['delivery'] = None


def deliver(root, state, key):
    if state['pending_actions']:
        raise ValueError('Pending user decisions remain')
    if any(s['status'] in ('unknown', 'submitted') for s in state['submissions'].values()):
        raise ValueError('Unresolved remote task remains; recover its status before delivery')
    seen = set()
    def check(k):
        if k in seen:
            return
        seen.add(k); a = state['artifacts'][k]
        if a['status'] != 'accepted' or not a['review'] or not a['review']['passed']:
            raise ValueError('Every delivery dependency needs an actual passing review: ' + k)
        if digest(root / a['path']) != a['sha256']:
            raise ValueError('Artifact hash mismatch: ' + k)
        for dep in a['depends_on']:
            check(dep)
    if state['artifacts'][key]['kind'] != 'assembly':
        raise ValueError('Complete video delivery requires an assembly artifact')
    check(key)
    state['status'] = 'delivered'; state['delivery'] = key


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('init'); sub.add_parser('show')
    a = sub.add_parser('add'); a.add_argument('id'); a.add_argument('file'); a.add_argument('--kind', required=True)
    a.add_argument('--depends-on', nargs='*', default=[])
    a = sub.add_parser('reserve'); a.add_argument('key'); a.add_argument('--tool', required=True)
    a.add_argument('--inputs', nargs='*', default=[]); a.add_argument('--authorization', required=True)
    a = sub.add_parser('receipt'); a.add_argument('key'); a.add_argument('--task-id', required=True)
    a.add_argument('--status', choices=['submitted', 'ready', 'failed'], required=True)
    a = sub.add_parser('review'); a.add_argument('id'); a.add_argument('--evidence', required=True)
    a.add_argument('--result', choices=['passed', 'failed'], required=True)
    a = sub.add_parser('deliver'); a.add_argument('id')
    a = sub.add_parser('pending'); a.add_argument('decision')
    a = sub.add_parser('resolve'); a.add_argument('decision'); a.add_argument('--evidence', required=True)
    a = p.parse_args()
    try:
        if a.command == 'show':
            print((Path(a.project) / 'project.json').read_text()); return
        with transaction(a.project, create=a.command == 'init') as (root, state):
            if a.command == 'add': add_artifact(root, state, a.id, a.file, a.kind, a.depends_on)
            elif a.command == 'reserve': reserve(state, a.key, a.tool, a.inputs, a.authorization)
            elif a.command == 'receipt': receipt(state, a.key, a.task_id, a.status)
            elif a.command == 'review': review(root, state, a.id, a.evidence, a.result == 'passed')
            elif a.command == 'deliver': deliver(root, state, a.id)
            elif a.command == 'pending':
                if not a.decision.strip(): raise ValueError('Decision cannot be empty')
                if a.decision not in state['pending_actions']: state['pending_actions'].append(a.decision)
                state['status'] = 'draft'; state['delivery'] = None
            elif a.command == 'resolve':
                if not a.evidence.strip(): raise ValueError('Decision evidence is required')
                state['pending_actions'].remove(a.decision)
                state.setdefault('decisions', []).append({'decision': a.decision, 'evidence': a.evidence})
        print(json.dumps({'project': str(root), 'state_version': state['state_version'], 'status': state['status']}))
    except (ValueError, KeyError, OSError) as e:
        p.exit(1, str(e) + '\n')

if __name__ == '__main__':
    main()
