import hashlib
import html
import json
import re
import tempfile
from datetime import datetime, timezone
from ..core import ROOT, safe, write_json, read_json
from ..models.p1 import validate_story

PROVIDER = 'offline-placeholder-v1'
REFERENCE = b'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="120"><rect width="400" height="120" fill="#dddddd"/><text x="10" y="50">TEST REFERENCE - NOT ART APPROVED</text></svg>'

def digest(value):
    return hashlib.sha256(value).hexdigest()

class MockProvider:
    def render(self, panel_id, revision, reference, fail=False):
        if fail: raise RuntimeError('SIMULATED_PROVIDER_FAILURE')
        if reference != REFERENCE: raise ValueError('REFERENCE_CHANGED')
        label=html.escape(f'TEST ONLY | {panel_id} | revision {revision}')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400"><rect width="800" height="400" fill="#eeeeee"/><rect x="20" y="20" width="760" height="360" fill="none" stroke="#555"/><text x="40" y="100">{label}</text><text x="40" y="160">OFFLINE PLACEHOLDER - NOT GENERATED ART</text><text x="40" y="220">NO USER APPROVAL / NO LIVE CALL</text></svg>').encode()

def create_run():
    base=safe(ROOT,'output/p2-mock-runs');base.mkdir(parents=True,exist_ok=True)
    run=__import__('pathlib').Path(tempfile.mkdtemp(prefix='p2-',dir=base))
    safe(run,'reference.svg').write_bytes(REFERENCE)
    write_json(run,'run.json',{'mock_only':True,'provider':PROVIDER,'reference_sha256':digest(REFERENCE),'art_approved':False})
    return run

def candidate(run,panel,revision=1,*,live=False,provider=PROVIDER,fail=False):
    # Block external/live requests before filesystem reads or provider execution.
    if live or provider != PROVIDER: raise ValueError('LIVE_PROVIDER_DISABLED')
    pid=panel.get('id','')
    if not re.fullmatch(r'ST-\d{3}-EP\d{2}-P\d{3}',pid): raise ValueError('INVALID_PANEL_ID')
    if type(revision) is not int or revision < 1: raise ValueError('INVALID_REVISION')
    if panel.get('status')!='draft': raise ValueError('DRAFT_TEST_ONLY')
    state=read_json(run,'run.json')
    if state.get('mock_only') is not True or state.get('provider')!=PROVIDER: raise ValueError('NOT_MOCK_RUN')
    reference=safe(run,'reference.svg').read_bytes()
    if digest(reference)!=state['reference_sha256'] or reference!=REFERENCE: raise ValueError('REFERENCE_CHANGED')
    stem=f'candidates/{pid}/r{revision:03}'
    for ext in ('.svg','.json','.failure.json'):
        if safe(run,stem+ext).exists(): raise FileExistsError('REVISION_EXISTS')
    request={'panel_id':pid,'revision':revision,'provider':provider,'mock_only':True,'live_calls':0,'api_cost':0,'reference_sha256':digest(reference),'dialogue_sha256':digest(json.dumps(panel.get('dialogue',[]),ensure_ascii=False,sort_keys=True).encode()),'approval':'not_approved','created_at':datetime.now(timezone.utc).isoformat()}
    try:
        content=MockProvider().render(pid,revision,reference,fail)
    except RuntimeError as exc:
        write_json(run,stem+'.failure.json',{**request,'status':'failed','error':str(exc),'candidate_created':False})
        raise
    image=safe(run,stem+'.svg');image.parent.mkdir(parents=True,exist_ok=True)
    with image.open('xb') as f:f.write(content)
    record={**request,'status':'test_candidate','image_path':stem+'.svg','image_sha256':digest(content),'kind':'offline_svg_placeholder_not_ai_image'}
    write_json(run,stem+'.json',record)
    return record

def demo(story_id):
    validation=validate_story(story_id)
    if not validation['schema_valid']: raise ValueError('P1_INVALID')
    # Validation success is not G0/rights/budget approval; this isolated test never calls live APIs.
    source=read_json(ROOT,'stories/'+story_id+'/episodes/EP01/panels.yaml')
    wanted=[story_id+'-EP01-P006',story_id+'-EP01-P007']
    panels=[next(p for p in source['panels'] if p['id']==pid) for pid in wanted]
    run=create_run()
    first=[candidate(run,p) for p in panels]
    sibling=safe(run,first[0]['image_path']).read_bytes()
    revision=candidate(run,panels[1],2)
    assert safe(run,first[0]['image_path']).read_bytes()==sibling
    summary={'run':str(run),'mock_only':True,'panel_ids':wanted,'initial_candidates':first,'targeted_revision':revision,'unchanged_sibling':wanted[0],'gates':'pending','rights':'pending','budget':'unset','live_calls':0,'p3_verified':False}
    write_json(run,'summary.json',summary)
    return summary
