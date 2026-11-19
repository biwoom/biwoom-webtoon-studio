"""Offline synthetic Composer. No authenticated production ingress exists."""
import base64
import hashlib
import html
import io
import json
import tempfile
from pathlib import Path
from ..core import ROOT, safe, write_json, read_json
from ..qa.raster import inspect_raster, text_hash, admission

IDS = ('ST-999-EP01-P001', 'ST-999-EP01-P002')
TEXT = ('Synthetic action: five circles.', 'Synthetic reaction: pause.')

def fixture_bytes(index):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (480, 260), ('#e4d7c5', '#d1e2df')[index])
    draw = ImageDraw.Draw(im)
    draw.text((20, 20), 'SYNTHETIC TEST ONLY / ' + IDS[index], fill='black')
    for n in range(5):
        x = 50 + n * 75
        draw.ellipse((x, 80, x+35, 115), fill='#93617d')
    draw.text((20, 180), TEXT[index], fill='black')
    buf = io.BytesIO(); im.save(buf, format='PNG'); return buf.getvalue()

def create_fixture():
    base = safe(ROOT, 'output/p4-mock-runs'); base.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix='p4-', dir=base))
    panels = []
    for i, pid in enumerate(IDS):
        raw = fixture_bytes(i)
        safe(run, pid+'.png').write_bytes(raw)
        panels.append({'panel_id':pid, 'path':str((run/(pid+'.png')).relative_to(ROOT)),
            'dialogue':{'dialogue':[TEXT[i]], 'captions':[]},
            'expected':{'panel_id':pid, 'image_sha256':hashlib.sha256(raw).hexdigest(),
                'format':'PNG', 'width':480, 'height':260}})
    write_json(run, 'panels.json', panels)
    return run

def current_binding(panel):
    qa = inspect_raster(panel['path'], panel['panel_id'], panel['expected'])
    if not qa['technical_pass']: raise ValueError('TECHNICAL_QA_BLOCKED:'+str(qa['errors']))
    return {'panel_id':panel['panel_id'], 'image_sha256':qa['image_sha256'],
            'dialogue_sha256':text_hash(panel['dialogue'])}

def fixture_event(panel):
    # An exact fixture allowlist, not caller mock_only/authenticated flags.
    pid = panel['panel_id']
    if pid not in IDS: raise ValueError('NOT_SYNTHETIC_FIXTURE')
    index = IDS.index(pid)
    if (safe(ROOT, panel['path']).read_bytes() != fixture_bytes(index) or
        panel['dialogue'] != {'dialogue':[TEXT[index]], 'captions':[]}):
        raise ValueError('NOT_SYNTHETIC_FIXTURE')
    return {'schema':'synthetic_receipt_v1', 'event_id':'fixture-'+pid,
            **current_binding(panel), 'decision':'mock_approved',
            'principal':'SYNTHETIC_TEST_NOT_OWNER', 'production_authority':False}

def import_owner_approval(*args, **kwargs):
    # Adapter boundary. No JSON field, name, historic chat closeout or signature
    # supplied by the caller authenticates owner identity. Future trusted ingress
    # must verify provenance and bind an immutable candidate/episode digest.
    raise ValueError('AUTHENTICATED_OWNER_APPROVAL_IMPORT_UNAVAILABLE')

def import_fixture_event(run, panel, event):
    expected = fixture_event(panel)
    if event != expected: raise ValueError('EVENT_CONFLICT_OR_STALE')
    name = 'receipts/'+panel['panel_id']+'.json'
    path = safe(run, name)
    if path.exists():
        if read_json(run, name) != expected: raise ValueError('EXISTING_RECEIPT_CONFLICT')
        return 'replayed'
    write_json(run, name, expected)
    return 'imported'

def receipt_issues(run, panel):
    try:
        bound = current_binding(panel)
        record = read_json(run, 'receipts/'+panel['panel_id']+'.json')
        if any(record.get(k) != v for k,v in bound.items()): return ['APPROVAL_STALE']
        if record != fixture_event(panel): return ['INVALID_SYNTHETIC_RECEIPT']
        return []
    except FileNotFoundError: return ['APPROVAL_MISSING']
    except (ValueError, KeyError, TypeError) as exc: return [str(exc)]

def compose(run, final=False):
    # Final output never created: G3.5 provenance and authenticated G4 absent.
    if final: raise ValueError('AUTHENTICATED_G35_AND_G4_REQUIRED')
    panels = read_json(run, 'panels.json')
    if [p['panel_id'] for p in panels] != list(IDS): raise ValueError('PANEL_SET_MISMATCH')
    issues = {p['panel_id']:receipt_issues(run,p) for p in panels}
    if any(issues.values()): raise ValueError('MOCK_LAYOUT_BLOCKED:'+str(issues))
    # Validate all bindings before writing any preview. Embed the checked bytes.
    raw_images = [safe(ROOT,p['path']).read_bytes() for p in panels]
    for p, raw in zip(panels,raw_images):
        if hashlib.sha256(raw).hexdigest()!=current_binding(p)['image_sha256']:
            raise ValueError('IMAGE_CHANGED_DURING_COMPOSITION')
    from PIL import Image, ImageDraw
    canvas = Image.new('RGB',(520,760),'white'); draw = ImageDraw.Draw(canvas)
    draw.text((20,20),'SYNTHETIC TEST PREVIEW - NOT FINAL',fill='red')
    sections=[]
    for i,(p,raw) in enumerate(zip(panels,raw_images)):
        with Image.open(io.BytesIO(raw)) as im: canvas.paste(im.convert('RGB'),(20,70+i*330))
        draw.text((20,340+i*330),'MOCK ONLY / NO OWNER APPROVAL',fill='red')
        sections.append('<section><img alt="synthetic panel" src="data:image/png;base64,'+
            base64.b64encode(raw).decode()+'"><p>'+html.escape(p['dialogue']['dialogue'][0])+
            '</p><small>MOCK ONLY / NO OWNER APPROVAL</small></section>')
    preview = safe(run,'preview'); preview.mkdir(exist_ok=True)
    # Exclusive creation preserves prior output; rerun must use a fresh run.
    with safe(preview,'vertical.png').open('xb') as f: canvas.save(f,format='PNG')
    with safe(preview,'index.html').open('x') as f:
        f.write('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>SYNTHETIC TEST PREVIEW</title><style>body{max-width:520px;margin:auto;font-family:sans-serif}img{width:100%}section{margin:64px 20px}h1,small{color:#a00}</style>'
            '<h1>TEST ONLY · NOT FINAL</h1>'+''.join(sections))
    production_checks=[admission(p['path'],p['panel_id'],p['expected'],p['dialogue']) for p in panels]
    write_json(run,'composition-report.json',{'mock_only':True,'final_allowed':False,
        'dimensions':[520,760], 'bindings':[current_binding(p) for p in panels],
        'production_checks':production_checks,'g4':'not_authenticated'})
    return str(preview)

def demo():
    run=create_fixture(); panels=read_json(run,'panels.json')
    for panel in panels:
        event=fixture_event(panel)
        import_fixture_event(run,panel,event)
        assert import_fixture_event(run,panel,event)=='replayed'
    return {'run':str(run),'preview':compose(run),'mock_only':True,'final_allowed':False}
