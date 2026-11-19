import unittest
from biwoom_studio.audit.review_offer import *
class ReviewOffer(unittest.TestCase):
    def setUp(self):
        self.offer=make_offer('ST-999-EP01-P001',b'synthetic',{'dialogue':'시험'},'r1','d1')
        self.event={'event_id':'e1','author':'SYNTHETIC_OWNER','reply_to':self.offer.offer_id,'consent':{'decision':'approve','gate':'G3.5','offer_id':self.offer.offer_id,'scope':'image_and_dialogue'},'test_only':True}
    def session(self,event=None):return TestReviewSession(self.offer,'SYNTHETIC_OWNER',SyntheticTransport({'e1':event or self.event}))
    def test_exact_and_replay(self):
        s=self.session();self.assertEqual(s.receive('e1',self.offer)['status'],'accepted_test_only');self.assertEqual(s.receive('e1',self.offer)['status'],'replayed')
    def test_generic_continue(self):
        e=dict(self.event,consent='계속 진행해줘')
        with self.assertRaises(ValueError):self.session(e).receive('e1',self.offer)
    def test_wrong_or_null_reply(self):
        for reply in [None,'another']:
            with self.assertRaises(ValueError):self.session(dict(self.event,reply_to=reply)).receive('e1',self.offer)
    def test_wrong_owner(self):
        with self.assertRaises(ValueError):self.session(dict(self.event,author='other')).receive('e1',self.offer)
    def test_stale_image_and_dialogue(self):
        for image,text in [(b'changed',{'dialogue':'시험'}),(b'synthetic',{'dialogue':'변경'})]:
            with self.assertRaisesRegex(ValueError,'STALE'):self.session().receive('e1',make_offer('ST-999-EP01-P001',image,text,'r1','d1'))
    def test_missing_version(self):
        with self.assertRaises(ValueError):make_offer('ST-999-EP01-P001',b'x',{},'', 'd1')
    def test_other_scope(self):
        e=dict(self.event);e['consent']=dict(e['consent'],scope='image_only')
        with self.assertRaises(ValueError):self.session(e).receive('e1',self.offer)
    def test_production_blocked(self):
        with self.assertRaisesRegex(ValueError,'UNAVAILABLE'):ProductionTransport().receive({'authenticated':True})
