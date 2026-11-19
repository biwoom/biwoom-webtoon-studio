import json
import os
import subprocess
import sys
import unittest
from biwoom_studio.core import ROOT,safe,read_json
from biwoom_studio.composition import vertical
from biwoom_studio.audit.review_offer import make_offer,digest
from biwoom_studio.audit.durable import TestLedger
from biwoom_studio.audit.pipeline import event_for,demo
class Durable(unittest.TestCase):
    def setUp(self):
        self.run=vertical.create_fixture();self.offer=make_offer('ST-999-EP01-P001',b'fixture',{},'r1','d1');self.event=event_for(self.offer,1);self.root={self.event['event_id']:digest(self.event)}
    def test_restart_actual_process(self):
        TestLedger(self.run,self.root).accept(self.offer,self.offer,self.event)
        code="from biwoom_studio.audit.durable import TestLedger;from biwoom_studio.audit.review_offer import Offer;from pathlib import Path;import json,sys;d=json.loads(sys.argv[1]);o=Offer(**d['offer']);print(TestLedger(Path(d['run']),d['root']).accept(o,o,d['event'])['status'])"
        d={'run':str(self.run),'root':self.root,'event':self.event,'offer':self.offer.__dict__}
        result=subprocess.run([sys.executable,'-c',code,json.dumps(d)],cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(result.stdout.strip(),'replayed')
    def test_atomic_rollback(self):
        ledger=TestLedger(self.run,self.root)
        with self.assertRaises(RuntimeError):ledger.accept(self.offer,self.offer,self.event,fail_before_commit=True)
        self.assertEqual(TestLedger(self.run,self.root).accept(self.offer,self.offer,self.event)['status'],'accepted_test_only')
    def test_same_offer_different_event_collision(self):
        ledger=TestLedger(self.run,self.root);ledger.accept(self.offer,self.offer,self.event)
        other=event_for(self.offer,2)
        with self.assertRaisesRegex(ValueError,'COLLISION'):TestLedger(self.run,{other['event_id']:digest(other)}).accept(self.offer,self.offer,other)
    def test_same_event_other_offer_collision(self):
        TestLedger(self.run,self.root).accept(self.offer,self.offer,self.event)
        other=make_offer('ST-999-EP01-P002',b'other',{},'r1','d1');event=event_for(other,1)
        with self.assertRaisesRegex(ValueError,'COLLISION'):TestLedger(self.run,{event['event_id']:digest(event)}).accept(other,other,event)
    def test_untrusted_source(self):
        with self.assertRaisesRegex(ValueError,'TRUST_ROOT'):TestLedger(self.run,{}).accept(self.offer,self.offer,self.event)
    def test_stale(self):
        other=make_offer('ST-999-EP01-P001',b'changed',{},'r2','d1')
        with self.assertRaisesRegex(ValueError,'STALE'):TestLedger(self.run,self.root).accept(self.offer,other,self.event)
    def test_pipeline(self):
        r=demo();self.assertFalse(r['measurements']['final_allowed']);self.assertEqual(r['measurements']['external_requests'],0)
        self.assertTrue(safe(r['run'],'pipeline-test-only.zip').exists())

    def test_process_crash_uncommitted_row(self):
        ledger=TestLedger(self.run,self.root)
        code="import sqlite3,sys,os;d=sqlite3.connect(sys.argv[1]);d.execute('BEGIN IMMEDIATE');d.execute('INSERT INTO receipts VALUES(?,?,?,?)',('unfinished','offer','hash','{}'));os._exit(23)"
        r=subprocess.run([sys.executable,'-c',code,str(ledger.path)],cwd=ROOT)
        self.assertEqual(r.returncode,23)
        import sqlite3
        with sqlite3.connect(ledger.path) as db:self.assertEqual(db.execute('SELECT count(*) FROM receipts').fetchone()[0],0)
        self.assertEqual(ledger.accept(self.offer,self.offer,self.event)['status'],'accepted_test_only')
    def test_concurrent_process_replay(self):
        TestLedger(self.run,self.root)
        d={'run':str(self.run),'root':self.root,'event':self.event,'offer':self.offer.__dict__}
        code="from biwoom_studio.audit.durable import TestLedger;from biwoom_studio.audit.review_offer import Offer;from pathlib import Path;import json,sys;d=json.loads(sys.argv[1]);o=Offer(**d['offer']);print(TestLedger(Path(d['run']),d['root']).accept(o,o,d['event'])['status'])"
        processes=[subprocess.Popen([sys.executable,'-c',code,json.dumps(d)],cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for _ in range(3)]
        results=[p.communicate() for p in processes]
        self.assertTrue(all(p.returncode==0 for p in processes),results)
        self.assertEqual(sorted(x[0].strip() for x in results),['accepted_test_only','replayed','replayed'])
