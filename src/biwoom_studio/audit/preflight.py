import hashlib
import json
import re
from ..core import ROOT, safe
from ..models.p1 import validate_story


def approval_binding_issues(panel_id, image_bytes, dialogue, record):
    """Compare immutable content bindings only. Caller must independently verify human authority."""
    issues=[]
    if not isinstance(record,dict): return ['APPROVAL_MISSING']
    if record.get('panel_id')!=panel_id:issues.append('PANEL_ID_MISMATCH')
    if record.get('gate')!='G3.5' or record.get('decision')!='approved':issues.append('NOT_G35_APPROVAL')
    if record.get('approval_scope')!='image_and_dialogue':issues.append('IMAGE_ONLY_OR_UNSPECIFIED_SCOPE')
    if record.get('mock_only') is not False:issues.append('NONPRODUCTION_RECORD')
    for field in ('image_revision','dialogue_revision','approved_by','approved_at'):
        if not isinstance(record.get(field),str) or not record[field].strip():issues.append('MISSING_'+field.upper())
    expected_image=hashlib.sha256(image_bytes).hexdigest()
    # P5 comparison protocol: UTF-8 JSON sorted keys, compact separators, whole dialogue/caption bundle.
    expected_text=hashlib.sha256(json.dumps(dialogue,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if record.get('image_sha256')!=expected_image:issues.append('IMAGE_CHANGED')
    if record.get('dialogue_sha256')!=expected_text:issues.append('DIALOGUE_CHANGED')
    return issues

def affected_panels(continuity, rule_id):
    rules=[r for r in continuity['rules'] if r['id']==rule_id]
    if len(rules)!=1:raise ValueError('UNKNOWN_OR_DUPLICATE_RULE')
    return sorted(set(rules[0]['affected_panel_ids']))

def preflight(story_id):
    if not re.fullmatch(r'ST-\d{3}',story_id):raise ValueError('INVALID_STORY_ID')
    validation=validate_story(story_id)
    base='stories/'+story_id+'/'
    p=json.loads(safe(ROOT,base+'project.yaml').read_text())
    gates=p.get('approval_gates',{})
    blockers=['NO_LIVE_PROVIDER','NO_AUTHENTICATED_APPROVAL_IMPORT','NO_RELEASE_COORDINATOR']
    if not validation['schema_valid']:blockers.append('P1_SCHEMA_INVALID')
    for gate in ('G0','G1','G2','G3','G3.5','G4'):
        if gates.get(gate)!='approved':blockers.append('LOCAL_RECORD_PENDING:'+gate)
    if p.get('rights_review')!='verified':blockers.append('RIGHTS_PENDING')
    # Private project configuration stays local; no pilot-specific path/hash in code.
    reference=p.get('archive_reference')
    archive={'state':'not_configured'}
    if reference is not None:
        if not isinstance(reference,dict) or not re.fullmatch(r'[0-9a-f]{64}',reference.get('sha256','')):
            raise ValueError('INVALID_ARCHIVE_REFERENCE')
        path=safe(ROOT,reference['path'])
        archive={'state':'missing','expected_sha256':reference['sha256']}
        if path.is_file():
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            archive={'state':'hash_match' if actual==reference['sha256'] else 'hash_mismatch','sha256':actual}
    if archive['state']!='hash_match':blockers.append('LOCAL_ARCHIVE_UNVERIFIED')
    return {'story_id':story_id,'read_only':True,'local_gate_records':gates,'p1':validation,
            'blockers':blockers,'archive':archive,'live_allowed':False,'release_allowed':False,
            'dot_codex_integration_verified':False,
            'pilot_state':'not_inferred_from_local_records',
            'final_output_allowed':False,'preview_policy':'review_only_clearly_label_unapproved',
            'next_actions':[
                {'action':'Reconcile conversation approvals with exact files','reason':'Local gate records are pending; image-only approval is not image+dialogue approval.'},
                {'action':'Import immutable revision/hash evidence without overwriting originals','reason':'Missing record, changed image/dialogue and matching binding must remain distinct; matching hashes alone do not authenticate user approval.'},
                {'action':'Resolve source/rights and budget separately','reason':'Source verification is not automatic G0 rights clearance.'},
                {'action':'Verify local private archive transfer','reason':archive['state']},
                {'action':'Plan a three-panel phone storyboard comparison before full rendering','reason':'Action, reaction, reveal and alternative gutters need actual visual G3 review; no retroactive approval.'}],
            'note':'Local evidence only. Conversation image approval is not imported or denied by this report; pending means local records are unreconciled. No G4 or public release inferred.'}
