import copy
import json
import unittest
from PIL import Image
from biwoom_studio.core import safe, read_json
from biwoom_studio.composition import vertical as v

class P4Tests(unittest.TestCase):
    def setUp(self):
        self.run=v.create_fixture(); self.panels=read_json(self.run,'panels.json')
    def approve(self):
        for p in self.panels: v.import_fixture_event(self.run,p,v.fixture_event(p))
    def test_visible_preview(self):
        self.approve(); target=v.compose(self.run)
        with Image.open(safe(self.run,'preview/vertical.png')) as im:
            im.load(); self.assertEqual(im.size,(520,760))
        self.assertIn('NOT FINAL',safe(self.run,'preview/index.html').read_text())
        self.assertFalse(read_json(self.run,'composition-report.json')['final_allowed'])
    def test_replay_preserves_bytes(self):
        self.approve(); p=self.panels[0]; path=safe(self.run,'receipts/'+p['panel_id']+'.json')
        before=(path.read_bytes(),path.stat().st_mtime_ns)
        self.assertEqual(v.import_fixture_event(self.run,p,v.fixture_event(p)),'replayed')
        self.assertEqual(before,(path.read_bytes(),path.stat().st_mtime_ns))
    def test_conflicting_event(self):
        p=self.panels[0]; e=v.fixture_event(p); e['decision']='approved'
        with self.assertRaisesRegex(ValueError,'CONFLICT'): v.import_fixture_event(self.run,p,e)
    def test_changed_dialogue_only_affected(self):
        self.approve(); self.panels[0]['dialogue']['dialogue'][0]='altered'
        self.assertIn('APPROVAL_STALE',v.receipt_issues(self.run,self.panels[0]))
        self.assertEqual(v.receipt_issues(self.run,self.panels[1]),[])
    def test_changed_image_rejected(self):
        self.approve(); p=self.panels[0]; safe(v.ROOT,p['path']).write_bytes(v.fixture_bytes(1))
        self.assertTrue(v.receipt_issues(self.run,p))
        self.assertEqual(v.receipt_issues(self.run,self.panels[1]),[])
    def test_missing_receipt_no_output(self):
        with self.assertRaisesRegex(ValueError,'BLOCKED'):v.compose(self.run)
        self.assertFalse(safe(self.run,'preview').exists())
    def test_final_blocked_with_fake_g4(self):
        self.approve()
        with self.assertRaisesRegex(ValueError,'G4'):v.compose(self.run,final=True)
        self.assertFalse(safe(self.run,'preview').exists())
        self.assertFalse(safe(self.run,'export').exists())
    def test_owner_json_is_not_authentication(self):
        with self.assertRaisesRegex(ValueError,'UNAVAILABLE'):
            v.import_owner_approval({'authenticated':True,'g4':True,'approved_by':'owner'})
    def test_nonfixture_cannot_mock_approve(self):
        p=self.panels[0]; p['dialogue']['dialogue'][0]='real dialogue'
        with self.assertRaisesRegex(ValueError,'NOT_SYNTHETIC'):v.fixture_event(p)
    def test_existing_conflict_preserved(self):
        self.approve();p=self.panels[0];path=safe(self.run,'receipts/'+p['panel_id']+'.json')
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError,'CONFLICT'):v.import_fixture_event(self.run,p,v.fixture_event(p))
        self.assertEqual(path.read_text(),'{}')
    def test_path_escape(self):
        p=self.panels[0];p['path']='../escape.png'
        with self.assertRaises(ValueError):v.current_binding(p)
