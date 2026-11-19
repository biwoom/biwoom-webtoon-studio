import hashlib
import json
import re
from ..core import ROOT, safe

GATES = ['G0', 'G1', 'G2', 'G3', 'G3.5', 'G4']

def validate_bundle(b):
    errors = []
    def need(ok, code):
        if not ok: errors.append(code)
    try:
        project, sources, panels = b['project'], b['sources']['sources'], b['panels']['panels']
        pid = project['project_id']
        need(isinstance(pid,str) and re.fullmatch(r'ST-\d{3}',pid), 'PROJECT_ID')
        need(project['language']=='ko' and project['format']=='vertical_webtoon', 'PROJECT_FORMAT')
        need(project['rights_review']=='pending' and project['owner_approval_required'] is True, 'DRAFT_RIGHTS_GUARD')
        need(project['approval_gates']=={g:'pending' for g in GATES}, 'DRAFT_APPROVAL_GUARD')
        need(project['episodes']==['EP01'] and b['panels']['episode_id']=='EP01' and b['storyboard']['episode_id']=='EP01', 'EPISODE_ID')
        need(b['panels']['status']=='draft' and b['storyboard']['status']=='draft', 'DRAFT_STATUS')
        sm={s['id']:s for s in sources}
        need(len(sm)==len(sources) and len(sm)>0, 'SOURCE_IDS')
        for s in sources:
            need(s['type'] in ['canonical_text','commentary','translation','research','original_story'], 'SOURCE_TYPE')
            need(all(isinstance(s[k],str) and s[k].strip() for k in ['title','language','edition','locator','url']), 'SOURCE_FIELDS')
            need(s['usage_rights']=='unknown' and s['text_reuse_allowed'] is False, 'DRAFT_RIGHTS_GUARD')
            need(isinstance(s['locators'],list) and all(isinstance(x,str) and x for x in s['locators']), 'SOURCE_LOCATORS')
        chars=[x['id'] for x in b['characters']['characters']]
        locations=[x['id'] for x in b['locations']['locations']]
        need(len(chars)==len(set(chars)) and len(locations)==len(set(locations)), 'BIBLE_IDS')
        need(b['style']['status']=='draft' and b['style']['approved'] is False and project['art_style_id']==b['style']['id'], 'STYLE_DRAFT')
        expected=[f'{pid}-EP01-P{i:03}' for i in range(1,11)]
        need([p['id'] for p in panels]==expected,'PANEL_IDS_COUNT_ORDER')
        scenes=b['storyboard']['scenes']; scene_ids=[s['id'] for s in scenes]
        need(len(scene_ids)==len(set(scene_ids)), 'SCENE_IDS')
        need([x for s in scenes for x in s['panel_ids']]==expected, 'STORYBOARD_PANEL_LINKS')
        for p in panels:
            suffix=':'+str(p['id'])
            need(p['status']=='draft' and p['generate_without_text'] is True, 'PANEL_DRAFT_GUARD'+suffix)
            need(p['scene_id'] in scene_ids and any(p['id'] in s['panel_ids'] for s in scenes if s['id']==p['scene_id']), 'SCENE_REF'+suffix)
            need(isinstance(p['characters'],list) and all(c in chars for c in p['characters']) and p['location_id'] in locations, 'BIBLE_REF'+suffix)
            need(p['references']==[], 'NO_APPROVED_REFERENCE'+suffix)
            need(p['source_ids'] and all(s in sm for s in p['source_ids']), 'SOURCE_REF'+suffix)
            need(p['source_refs'] and set(r['source_id'] for r in p['source_refs'])==set(p['source_ids']), 'SOURCE_REF_LINK'+suffix)
            for r in p['source_refs']:
                need(r['source_id'] in sm and r['locator'] in sm[r['source_id']]['locators'], 'SOURCE_LOCATOR'+suffix)
            need(p['origin_type'] in ['canonical','traditional','interpretive','fictional'],'ORIGIN_TYPE'+suffix)
            if p['origin_type']=='canonical':
                need(all(sm.get(s,{}).get('type')=='canonical_text' and sm.get(s,{}).get('canonical_verified') is True for s in p['source_ids']), 'CANONICAL_UNVERIFIED'+suffix)
            need(all(isinstance(p[k],str) and p[k].strip() for k in ['composition','action','emotion','camera','source_supported_beat']), 'PANEL_FIELDS'+suffix)
            need(all(isinstance(p['adaptation'][k],str) and p['adaptation'][k].strip() for k in ['staging','text']), 'ADAPTATION_FIELDS'+suffix)
            for item in p['dialogue']:
                need(item['speaker'] in p['characters'] and item['kind'] in ['thought','speech'] and isinstance(item['text'],str) and bool(item['text'].strip()), 'DIALOGUE'+suffix)
                need(item['origin_type'] in ['interpretive','fictional'], 'TEXT_ADAPTATION'+suffix)
                if 'addressee' in item: need(item['addressee'] in p['characters'], 'ADDRESSEE'+suffix)
            for item in p['captions']:
                need(isinstance(item['text'],str) and bool(item['text'].strip()) and item['origin_type'] in ['interpretive','fictional'], 'CAPTION'+suffix)
            text_ids=[x['id'] for x in p['dialogue']+p['captions']]
            need(len(text_ids)==len(set(text_ids)), 'TEXT_IDS'+suffix)
        for name in ['script','style']:
            need(b['panels'][name+'_revision']==b['actual_hashes'][name], 'HASH_MISMATCH:'+name)
    except (KeyError,TypeError,AttributeError,ValueError):
        errors.append('SCHEMA_SHAPE')
    return {'schema_valid':not errors, 'errors':errors, 'approval_status':'pending',
            'generation_ready':False, 'rights_review':'pending',
            'notice':'Structure only; not source truth, rights clearance or owner approval.'}

def validate_story(story_id):
    if not re.fullmatch(r'ST-\d{3}',story_id): raise ValueError('INVALID_STORY_ID')
    base='stories/'+story_id+'/'
    paths={'project':'project.yaml','sources':'sources/source-index.yaml','characters':'bible/characters.yaml','locations':'bible/locations.yaml','style':'bible/style.yaml','storyboard':'episodes/EP01/storyboard.yaml','panels':'episodes/EP01/panels.yaml'}
    b={k:json.loads(safe(ROOT,base+v).read_text()) for k,v in paths.items()}
    b['actual_hashes']={name:'sha256:'+hashlib.sha256(safe(ROOT,base+path).read_bytes()).hexdigest() for name,path in [('script','episodes/EP01/screenplay.md'),('style','bible/style.yaml')]}
    return validate_bundle(b)
