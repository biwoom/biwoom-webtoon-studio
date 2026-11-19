"""Durable synthetic receipt ledger. Never authenticates production approval."""
import json
import sqlite3
from ..core import safe
from .review_offer import digest,TestReviewSession,SyntheticTransport

class TestLedger:
    def __init__(self,run,trust_root):
        self.path=safe(run,'test-receipts.sqlite3')
        # Explicit fixture event digests: not a production key or identity service.
        self.trust_root=dict(trust_root)
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('CREATE TABLE IF NOT EXISTS receipts(event_id TEXT PRIMARY KEY, offer_id TEXT UNIQUE NOT NULL, event_digest TEXT NOT NULL, receipt TEXT NOT NULL)')
    def accept(self,offer,current_offer,event,fail_before_commit=False):
        eid=event.get('event_id')
        if not isinstance(eid,str) or self.trust_root.get(eid)!=digest(event):
            raise ValueError('TEST_TRUST_ROOT_MISMATCH')
        TestReviewSession(offer,'SYNTHETIC_OWNER',SyntheticTransport({eid:event})).receive(eid,current_offer)
        receipt={'event_id':eid,'offer_id':offer.offer_id,'snapshot':json.loads(offer.snapshot),
                 'test_only':True,'production_authority':False,'gate':'MOCK_G3.5'}
        serialized=json.dumps(receipt,sort_keys=True,ensure_ascii=False)
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT event_id,offer_id,event_digest,receipt FROM receipts WHERE event_id=? OR offer_id=?',(eid,offer.offer_id)).fetchone()
            if row:
                if row!=(eid,offer.offer_id,digest(event),serialized):raise ValueError('REPLAY_OR_OFFER_COLLISION')
                return {'status':'replayed','receipt':json.loads(row[3])}
            # Intent and resulting receipt live in ONE atomic row/transaction.
            db.execute('INSERT INTO receipts VALUES(?,?,?,?)',(eid,offer.offer_id,digest(event),serialized))
            if fail_before_commit:raise RuntimeError('SIMULATED_INTERRUPTION_BEFORE_COMMIT')
        return {'status':'accepted_test_only','receipt':receipt}
