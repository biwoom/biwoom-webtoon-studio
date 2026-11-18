import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {'P01': {'S01': 'commentary'}, 'P02': {'S02': 'canon'}}
MARKERS = {pid: ('SYNTHETIC_IMAGE_MARKER:' + pid).encode() for pid in EXPECTED}
DIALOGUE = {'P01': '합성 해설 예시', 'P02': '합성 경전 역할 예시: 실제 경전 인용 아님'}

def safe(root, relative):
    raw_root = Path(root).absolute()
    try:
        root_parts = raw_root.relative_to(ROOT).parts
    except ValueError:
        raise ValueError('ROOT_OUTSIDE_STUDIO') from None
    cursor = ROOT
    for part in root_parts:
        if part == '..':
            raise ValueError('ROOT_OUTSIDE_STUDIO')
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError('SYMLINK_REJECTED')
    root = raw_root.resolve()
    if root != ROOT and ROOT not in root.parents:
        raise ValueError('ROOT_OUTSIDE_STUDIO')
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('PATH_ESCAPE')
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError('SYMLINK_REJECTED')
    result = cursor.resolve()
    if result != root and root not in result.parents:
        raise ValueError('PATH_ESCAPE')
    return result

def write_json(run, name, value):
    path = safe(run, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def read_json(run, name):
    return json.loads(safe(run, name).read_text(encoding='utf-8'))

def create_fixture():
    base = safe(ROOT, 'output/mock-runs')
    base.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='mock-', dir=base))
    for role in ('source', 'candidates', 'approvals', 'preview', 'export'):
        safe(run, role).mkdir()
    panels = []
    for pid, roles in EXPECTED.items():
        image = 'candidates/' + pid + '.marker'
        safe(run, image).write_bytes(MARKERS[pid])
        panels.append({'id':pid, 'image':image, 'dialogue':DIALOGUE[pid], 'source_roles':roles.copy()})
    write_json(run, 'source/storyboard.json', {'mock_only':True, 'panels':panels})
    write_json(run, 'source/expected.json', {'panel_ids':list(EXPECTED), 'source_role_ledger':EXPECTED})
    return run

def binding(run, panel):
    return {'panel_id':panel['id'],
            'image_sha256':hashlib.sha256(safe(run, panel['image']).read_bytes()).hexdigest(),
            'dialogue_sha256':hashlib.sha256(json.dumps(panel['dialogue'], ensure_ascii=False).encode()).hexdigest()}

def approve_fixture_only(run):
    # No generic approve command: auto approval is restricted to these exact synthetic fixtures.
    story = read_json(run, 'source/storyboard.json')
    panels = story['panels']
    if story.get('mock_only') is not True or [p['id'] for p in panels] != list(EXPECTED):
        raise ValueError('NOT_SYNTHETIC_FIXTURE')
    for panel in panels:
        pid = panel['id']
        if (panel['dialogue'] != DIALOGUE[pid] or panel['source_roles'] != EXPECTED[pid]
                or panel['image'] != 'candidates/' + pid + '.marker'
                or safe(run, panel['image']).read_bytes() != MARKERS[pid]):
            raise ValueError('NOT_SYNTHETIC_FIXTURE')
    for panel in panels:
        write_json(run, 'approvals/' + panel['id'] + '.json', {
            **binding(run, panel), 'mock_only':True, 'decision':'mock_approved',
            'approved_by':'SYNTHETIC_TEST_NOT_USER',
            'approved_at':datetime.now(timezone.utc).isoformat()})

def validate(run):
    story = read_json(run, 'source/storyboard.json')
    if story.get('mock_only') is not True:
        raise ValueError('MOCK_ONLY')
    panels = story['panels']
    ids = [p['id'] for p in panels]
    errors = []
    for pid in EXPECTED:
        if pid not in ids: errors.append({'code':'MISSING_PANEL','panel_id':pid})
    for panel in panels:
        pid = panel['id']
        if pid not in EXPECTED or ids.count(pid) != 1:
            errors.append({'code':'INVALID_PANEL_ID','panel_id':pid})
            continue
        if panel['source_roles'] != EXPECTED[pid]:
            errors.append({'code':'SOURCE_ROLE_MISMATCH','panel_id':pid})
        current = binding(run, panel)  # Re-read actual current bytes, not cached approval data.
        approval_path = safe(run, 'approvals/' + pid + '.json')
        if not approval_path.exists():
            errors.append({'code':'APPROVAL_MISSING','panel_id':pid})
            continue
        approval = json.loads(approval_path.read_text())
        if (approval.get('mock_only') is not True or approval.get('decision') != 'mock_approved'
                or approval.get('approved_by') != 'SYNTHETIC_TEST_NOT_USER'
                or not approval.get('approved_at')):
            errors.append({'code':'INVALID_APPROVAL','panel_id':pid})
        elif any(approval.get(k) != v for k,v in current.items()):
            errors.append({'code':'APPROVAL_STALE','panel_id':pid})
    return panels, errors

def preview(run):
    panels, errors = validate(run)
    write_json(run, 'preview/review.json', {'mock_only':True, 'final':False,
        'label':'SYNTHETIC REVIEW ONLY — NOT FINAL', 'panels':panels, 'approval_issues':errors})
    return errors

def layout(run):
    panels, errors = validate(run)
    if not errors:
        write_json(run, 'export/mock-layout.json', {'mock_only':True, 'production_release':False,
            'label':'SYNTHETIC MOCK LAYOUT — NO G4 OR REAL USER APPROVAL', 'panels':panels})
    return errors
