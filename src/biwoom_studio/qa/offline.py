import json
import re
import xml.etree.ElementTree as ET
from ..core import ROOT, safe, read_json
from ..generation.mock import create_run, candidate, digest

IDS=[f'ST-999-EP01-P{i:03}' for i in range(1,4)]

def check_asset(run, record, expected_id):
    errors=[]
    if record.get('panel_id')!=expected_id:errors.append('PANEL_ID_MISMATCH')
    try:
        path=safe(run,record['image_path'])
        if not path.is_file():return errors+['ASSET_MISSING']
        content=path.read_bytes()
        if digest(content)!=record.get('image_sha256'):errors.append('HASH_MISMATCH')
        if path.suffix!='.svg' or len(content)>100000:errors.append('FORMAT_OR_SIZE')
        node=ET.fromstring(content)
        if node.tag!='{http://www.w3.org/2000/svg}svg':errors.append('SVG_FORMAT')
        if (node.get('width'),node.get('height'))!=('800','400'):errors.append('DIMENSIONS')
        if expected_id not in ''.join(node.itertext()):errors.append('LABEL_ID_MISMATCH')
    except (KeyError,ValueError,TypeError,OSError,ET.ParseError):errors.append('ASSET_INVALID')
    return errors

def checkpoint(run,state):
    # Append-only snapshots preserve earlier objective reports and reservations.
    path=safe(run,'p3-journal.jsonl')
    with path.open('a') as f:f.write(json.dumps(state,sort_keys=True)+'\n');f.flush()

def state_of(run):
    lines=safe(run,'p3-journal.jsonl').read_text().splitlines()
    state=json.loads(lines[-1])
    if state.get('kind')!='p3_offline_v1' or state.get('panel_ids')!=IDS or state.get('limit')!=2:
        raise ValueError('INVALID_OFFLINE_STATE')
    return state

def start():
    run=create_run()
    records={pid:candidate(run,{'id':pid,'status':'draft','dialogue':[]}) for pid in IDS}
    # Deliberate wrong expected hash in this isolated fixture, not real story data.
    records[IDS[1]]['image_sha256']='0'*64
    state={'kind':'p3_offline_v1','panel_ids':IDS,'records':records,'attempts':0,'limit':2,'phase':'paused','pending':None,'reports':[], 'approved':False,'live_calls':0}
    state['reports']=[{'panel_id':pid,'errors':check_asset(run,records[pid],pid)} for pid in IDS]
    checkpoint(run,state)
    return str(run.name)

def resume(run_name,fail=False):
    if not re.fullmatch(r'p2-[A-Za-z0-9_-]+',run_name):raise ValueError('INVALID_RUN_NAME')
    run=safe(ROOT,'output/p2-mock-runs/'+run_name)
    state=state_of(run)
    if state['phase'] in ('stalled','complete'):return state
    if state['pending']:
        # An interrupted provider attempt is ambiguous; never enqueue it again automatically.
        state['phase']='stalled';state['reason']='INTERRUPTED_ATTEMPT_REQUIRES_REVIEW';checkpoint(run,state);return state
    reports=[{'panel_id':pid,'errors':check_asset(run,state['records'][pid],pid)} for pid in IDS]
    state['reports']=reports
    bad=[r['panel_id'] for r in reports if r['errors']]
    if not bad:state['phase']='complete';checkpoint(run,state);return state
    if state['attempts']>=state['limit']:
        state['phase']='stalled';state['reason']='RETRY_LIMIT';checkpoint(run,state);return state
    pid=bad[0];state['attempts']+=1
    revision=state['attempts']+1
    state['pending']={'panel_id':pid,'revision':revision};state['phase']='running';checkpoint(run,state)
    try:
        record=candidate(run,{'id':pid,'status':'draft','dialogue':[]},revision,fail=fail)
    except (RuntimeError,ValueError,OSError) as exc:
        state['pending']=None;state['reason']=str(exc)
        state['phase']='stalled' if state['attempts']>=state['limit'] else 'paused'
        checkpoint(run,state);return state
    state['records'][pid]=record;state['pending']=None
    state['reports']=[{'panel_id':p,'errors':check_asset(run,state['records'][p],p)} for p in IDS]
    state['phase']='complete' if not any(r['errors'] for r in state['reports']) else 'paused'
    checkpoint(run,state);return state
