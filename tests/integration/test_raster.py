import copy
import hashlib
import unittest
from pathlib import Path
from PIL import Image
from biwoom_studio.core import ROOT,safe
from biwoom_studio.qa.raster import demo,inspect_raster,admission,review_issues,text_hash
import json

class Raster(unittest.TestCase):
    def setUp(self):
        self.run=Path(demo()['run']);self.path=str((self.run/'fixture.png').relative_to(ROOT));self.e=json.loads((self.run/'expected.json').read_text());self.pid=self.e['panel_id'];self.d={'dialogue':['synthetic'],'captions':[]}
    def test_png_decode(self):self.assertTrue(inspect_raster(self.path,self.pid,self.e)['technical_pass'])
    def test_jpeg_decode(self):
        path=self.run/'fixture.jpg';Image.new('RGB',(320,200)).save(path)
        e=dict(self.e,format='JPEG',image_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertTrue(inspect_raster(str(path.relative_to(ROOT)),self.pid,e)['technical_pass'])
    def test_missing(self):self.assertFalse(inspect_raster(str((self.run/'missing.png').relative_to(ROOT)),self.pid,self.e)['technical_pass'])
    def test_stale_hash(self):
        e=dict(self.e,image_sha256='0'*64);self.assertIn('MISMATCH:image_sha256',inspect_raster(self.path,self.pid,e)['errors'])
    def test_metadata_wrong(self):
        self.assertIn('MISMATCH:width',inspect_raster(self.path,self.pid,dict(self.e,width=1))['errors'])
    def test_broken_raster(self):
        path=self.run/'broken.png';path.write_bytes(b'not an image')
        self.assertFalse(inspect_raster(str(path.relative_to(ROOT)),self.pid,self.e)['technical_pass'])
    def test_missing_review_blocks(self):
        r=admission(self.path,self.pid,self.e,self.d);self.assertIn('MANUAL_REVIEW_MISSING',r['reasons']);self.assertFalse(r['p4_admitted'])
    def review(self):return {'schema':'manual_review_v1','panel_id':self.pid,'image_sha256':self.e['image_sha256'],'dialogue_sha256':text_hash(self.d),'mock_only':False,'reviewed_by':'TEST_UNSIGNED','reviewed_at':'2026-11-18T00:00:00+00:00','visual':{'status':'pass','notes':'test only'},'doctrinal':{'status':'pass','notes':'test only'}}
    def test_altered_dialogue(self):self.assertIn('MANUAL_MISMATCH:dialogue_sha256',review_issues(self.review(),self.pid,self.e['image_sha256'],text_hash({'dialogue':['changed']})))
    def test_wrong_review_panel(self):self.assertIn('MANUAL_MISMATCH:panel_id',review_issues(self.review(),'ST-999-EP01-P002',self.e['image_sha256'],text_hash(self.d)))
    def test_unsigned_pass_still_not_approval(self):
        r=admission(self.path,self.pid,self.e,self.d,self.review());self.assertFalse(r['p4_admitted']);self.assertIn('APPROVAL_MISSING',r['reasons']);self.assertIn('AUTHENTICATED_OWNER_APPROVAL_IMPORT_UNAVAILABLE',r['reasons'])
    def test_synthetic_review_rejected(self):
        r=self.review();r['mock_only']=True;self.assertIn('SYNTHETIC_REVIEW_NOT_PRODUCTION',review_issues(r,self.pid,self.e['image_sha256'],text_hash(self.d)))
