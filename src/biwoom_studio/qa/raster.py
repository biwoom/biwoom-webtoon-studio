import hashlib
import io
import json
import re
import tempfile
import warnings
from datetime import datetime
from pathlib import Path
from ..core import ROOT,safe,write_json
from ..audit.preflight import approval_binding_issues

def text_hash(text):
    return hashlib.sha256(json.dumps(text,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def inspect_raster(relative_path,panel_id,expected):
    report={'panel_id':panel_id,'path':relative_path,'technical_pass':False,'errors':[]}
    if not re.fullmatch(r'ST-\d{3}-EP\d{2}-P\d{3}',panel_id):
        report['errors'].append('INVALID_PANEL_ID');return report
    try:
        from PIL import Image
        path=safe(ROOT,relative_path)
        if path.stat().st_size>20*1024*1024:raise ValueError('FILE_TOO_LARGE')
        raw=path.read_bytes();report['image_sha256']=hashlib.sha256(raw).hexdigest()
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as im:
                fmt=im.format;size=im.size;mode=im.mode
                if fmt not in ('PNG','JPEG') or size[0]*size[1]>16000000:raise ValueError('UNSUPPORTED_RASTER')
                im.verify()
            with Image.open(io.BytesIO(raw)) as im:im.load()
        report.update(format=fmt,width=size[0],height=size[1],mode=mode,bytes=len(raw))
        if not isinstance(expected,dict):raise ValueError('EXPECTED_METADATA_MISSING')
        for k,value in [('panel_id',panel_id),('image_sha256',report['image_sha256']),('format',fmt),('width',size[0]),('height',size[1])]:
            if expected.get(k)!=value:report['errors'].append('MISMATCH:'+k)
        if path.suffix.lower() not in ({'PNG':['.png'],'JPEG':['.jpg','.jpeg']}[fmt]):report['errors'].append('EXTENSION_MISMATCH')
    except (ImportError,OSError,ValueError,SyntaxError,Warning) as exc:
        report['errors'].append(type(exc).__name__+':'+str(exc))
    report['technical_pass']=not report['errors']
    return report

def review_issues(record,panel_id,image_hash,dialogue_hash):
    if not isinstance(record,dict):return ['MANUAL_REVIEW_MISSING']
    errors=[]
    for key,value in [('schema','manual_review_v1'),('panel_id',panel_id),('image_sha256',image_hash),('dialogue_sha256',dialogue_hash)]:
        if record.get(key)!=value:errors.append('MANUAL_MISMATCH:'+key)
    if record.get('mock_only') is not False:errors.append('SYNTHETIC_REVIEW_NOT_PRODUCTION')
    for field in ('reviewed_by','reviewed_at'):
        if not isinstance(record.get(field),str) or not record[field].strip():errors.append('MANUAL_MISSING:'+field)
    try:
        if datetime.fromisoformat(record.get('reviewed_at','')).tzinfo is None:raise ValueError()
    except (TypeError,ValueError):errors.append('MANUAL_TIME_INVALID')
    for dimension in ('visual','doctrinal'):
        part=record.get(dimension)
        if not isinstance(part,dict) or part.get('status')!='pass' or not isinstance(part.get('notes'),str) or not part['notes'].strip():errors.append('MANUAL_PENDING:'+dimension)
    return errors

def admission(relative_path,panel_id,expected,dialogue,review=None,approval=None):
    # Never trust a caller-supplied technical report; inspect current bytes every time.
    qa=inspect_raster(relative_path,panel_id,expected)
    reasons=list(qa['errors'])
    reasons+=review_issues(review,panel_id,qa.get('image_sha256'),text_hash(dialogue))
    if qa['technical_pass']:
        reasons+=approval_binding_issues(panel_id,safe(ROOT,relative_path).read_bytes(),dialogue,approval)
    else:reasons.append('TECHNICAL_QA_BLOCKED')
    # No authenticated owner-approval importer exists. Matching unsigned JSON cannot admit production.
    reasons.append('AUTHENTICATED_OWNER_APPROVAL_IMPORT_UNAVAILABLE')
    return {'technical':qa,'reasons':reasons,'p4_admitted':False,'final_allowed':False,'preview_only':True,'manual_review_is_not_approval':True}

def demo():
    from PIL import Image,ImageDraw
    base=safe(ROOT,'output/raster-qa-runs');base.mkdir(parents=True,exist_ok=True)
    run=Path(tempfile.mkdtemp(prefix='raster-',dir=base))
    image=Image.new('RGB',(320,200),'#dddddd');ImageDraw.Draw(image).text((12,30),'SYNTHETIC QA FIXTURE - NOT ART',fill='black')
    path=run/'fixture.png';image.save(path)
    pid='ST-999-EP01-P001';dialogue={'dialogue':['합성 검증 텍스트'],'captions':[]}
    expected={'panel_id':pid,'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'format':'PNG','width':320,'height':200}
    review={'schema':'manual_review_v1','panel_id':pid,'image_sha256':expected['image_sha256'],'dialogue_sha256':text_hash(dialogue),'mock_only':True,'reviewed_by':None,'reviewed_at':None,'visual':{'status':'pending','notes':'사람 검토 필요'},'doctrinal':{'status':'pending','notes':'교학 판단 수행하지 않음'}}
    result=admission(str(path.relative_to(ROOT)),pid,expected,dialogue,review)
    for name,obj in [('expected.json',expected),('dialogue.json',dialogue),('manual-review.json',review),('technical-qa.json',result['technical']),('p4-admission.json',result)]:write_json(run,name,obj)
    return {'run':str(run),'technical_pass':result['technical']['technical_pass'],'p4_admitted':result['p4_admitted'],'fixture_only':True}
