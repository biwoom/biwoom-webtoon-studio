"""Synthetic review protocol only. No production authority or transport."""
import hashlib
import json
from dataclasses import dataclass

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

@dataclass(frozen=True)
class Offer:
    snapshot: str
    offer_id: str

def make_offer(target,image_bytes,dialogue,image_revision,dialogue_revision):
    if not target.startswith('ST-999-') or not image_revision or not dialogue_revision:
        raise ValueError('SYNTHETIC_TARGET_AND_VERSIONS_REQUIRED')
    body={'target':target,'image_sha256':hashlib.sha256(image_bytes).hexdigest(),
          'dialogue_sha256':digest(dialogue),'image_revision':image_revision,
          'dialogue_revision':dialogue_revision,'gate':'G3.5','test_only':True}
    snapshot=json.dumps(body,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    return Offer(snapshot,hashlib.sha256(snapshot.encode()).hexdigest())

class ProductionTransport:
    def receive(self,*args,**kwargs):
        raise ValueError('TRUSTED_PRODUCTION_TRANSPORT_UNAVAILABLE')

class SyntheticTransport:
    """In-memory fixture channel; explicitly cannot attest real-world identity."""
    def __init__(self,events):self.events=dict(events)
    def receive(self,event_id):
        if event_id not in self.events:raise ValueError('EVENT_NOT_IN_TEST_CHANNEL')
        return dict(self.events[event_id])

class TestReviewSession:
    def __init__(self,offer,expected_owner,transport):
        if type(transport) is not SyntheticTransport:raise ValueError('TEST_TRANSPORT_REQUIRED')
        if expected_owner!='SYNTHETIC_OWNER':raise ValueError('TEST_OWNER_REQUIRED')
        self.offer=offer;self.owner=expected_owner;self.transport=transport;self.receipts={}
    def receive(self,event_id,current_offer):
        offer=self.offer
        if hashlib.sha256(offer.snapshot.encode()).hexdigest()!=offer.offer_id:raise ValueError('OFFER_TAMPERED')
        if current_offer!=offer:raise ValueError('CURRENT_ARTIFACT_STALE')
        event=self.transport.receive(event_id)
        expected={'event_id':event_id,'author':'SYNTHETIC_OWNER','reply_to':offer.offer_id,
            'consent':{'decision':'approve','gate':'G3.5','offer_id':offer.offer_id,
                       'scope':'image_and_dialogue'},'test_only':True}
        if event!=expected:raise ValueError('EXACT_LINKED_CONSENT_REQUIRED')
        if event_id in self.receipts:
            if self.receipts[event_id]!=digest(event):raise ValueError('REPLAY_CONFLICT')
            return {'status':'replayed','test_only':True,'production_authority':False}
        self.receipts[event_id]=digest(event)
        return {'status':'accepted_test_only','offer_id':offer.offer_id,'test_only':True,'production_authority':False}
