"""Measured local synthetic pipeline; no real approvals or external calls."""
import hashlib
import json
import time
import zipfile
from ..core import ROOT,safe,read_json,write_json
from ..composition import vertical
from ..composition.korean import verify_archive
from .review_offer import make_offer,digest
from .durable import TestLedger

def event_for(offer,index):
    return {'event_id':'synthetic-event-'+str(index),'author':'SYNTHETIC_OWNER','reply_to':offer.offer_id,
        'consent':{'decision':'approve','gate':'G3.5','offer_id':offer.offer_id,'scope':'image_and_dialogue'},'test_only':True}

def demo():
    start=time.perf_counter();run=vertical.create_fixture();panels=read_json(run,'panels.json')
    jobs=[]
    for i,p in enumerate(panels):
        offer=make_offer(p['panel_id'],safe(ROOT,p['path']).read_bytes(),p['dialogue'],'fixture-r1','fixture-d1')
        jobs.append((p,offer,event_for(offer,i)))
    ledger=TestLedger(run,{e['event_id']:digest(e) for _,_,e in jobs})
    for p,offer,event in jobs:
        ledger.accept(offer,offer,event)
        # Compatibility bridge permits ONLY the preexisting exact fixed fixture.
        vertical.import_fixture_event(run,p,vertical.fixture_event(p))
    preview=vertical.compose(run)
    manifest={'test_only':True,'final_allowed':False,'g4':'not_authenticated','files':{}}
    for name in ['preview/vertical.png','preview/index.html','composition-report.json']:
        manifest['files'][name]=hashlib.sha256(safe(run,name).read_bytes()).hexdigest()
    write_json(run,'manifest.json',manifest)
    with zipfile.ZipFile(safe(run,'pipeline-test-only.zip'),'x',zipfile.ZIP_DEFLATED) as z:
        for name in list(manifest['files'])+['manifest.json']:z.write(safe(run,name),name)
    verify_archive(safe(run,'pipeline-test-only.zip'))
    measurements={'test_only':True,'panel_count':len(panels),'elapsed_seconds':time.perf_counter()-start,
        'external_requests':0,'api_cost_usd':0,'human_art_review_performed':False,
        'production_quality_score':None,'total_labor_cost':None,'final_allowed':False,
        'archive_bytes':safe(run,'pipeline-test-only.zip').stat().st_size}
    write_json(run,'synthetic-measurements.json',measurements)
    return {'run':str(run),'preview':preview,'measurements':measurements}
