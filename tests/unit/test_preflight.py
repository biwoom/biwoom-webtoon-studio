import copy
import hashlib
import json
import unittest
from biwoom_studio.audit.preflight import approval_binding_issues, affected_panels, preflight

class Preflight(unittest.TestCase):
    def record(self):
        return {'panel_id':'P01','gate':'G3.5','approval_scope':'image_and_dialogue','decision':'approved','mock_only':False,'image_revision':'r1','dialogue_revision':'d1','approved_by':'TEST_PRINCIPAL','approved_at':'2026-11-18T00:00:00+00:00','image_sha256':hashlib.sha256(b'image').hexdigest(),'dialogue_sha256':hashlib.sha256(json.dumps({'dialogue':['text'],'captions':[]},sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    def test_matching_binding_only(self):self.assertEqual(approval_binding_issues('P01',b'image',{'dialogue':['text'],'captions':[]},self.record()),[])
    def test_changed_image(self):self.assertIn('IMAGE_CHANGED',approval_binding_issues('P01',b'changed',{},self.record()))
    def test_changed_dialogue(self):self.assertIn('DIALOGUE_CHANGED',approval_binding_issues('P01',b'image',{'dialogue':['changed']},self.record()))
    def test_missing_record(self):self.assertEqual(approval_binding_issues('P01',b'image',{},None),['APPROVAL_MISSING'])
    def test_mock_cannot_pass(self):
        r=self.record();r['mock_only']=True
        self.assertIn('NONPRODUCTION_RECORD',approval_binding_issues('P01',b'image',{},r))
    def test_identity_fields_required(self):
        r=self.record();r.pop('approved_by')
        self.assertIn('MISSING_APPROVED_BY',approval_binding_issues('P01',b'image',{},r))
    def test_wrong_panel(self):self.assertIn('PANEL_ID_MISMATCH',approval_binding_issues('P02',b'image',{},self.record()))
    def test_affected_cuts_no_mutation(self):
        c={'rules':[{'id':'R1','affected_panel_ids':['P02','P01','P02']}]};old=copy.deepcopy(c)
        self.assertEqual(affected_panels(c,'R1'),['P01','P02']);self.assertEqual(c,old)
    def test_unknown_rule(self):
        with self.assertRaises(ValueError):affected_panels({'rules':[]},'missing')
    def test_escape_rejected(self):
        with self.assertRaisesRegex(ValueError,'INVALID_STORY_ID'):preflight('../outside')

    def test_image_only_not_full_acceptance(self):
        r=self.record();r['approval_scope']='image_only'
        self.assertIn('IMAGE_ONLY_OR_UNSPECIFIED_SCOPE',approval_binding_issues('P01',b'image',{},r))
