import copy
import unittest
from biwoom_studio.core import ROOT,safe
from biwoom_studio.qa.offline import start,resume,state_of,checkpoint,check_asset,IDS

class P3(unittest.TestCase):
    def setup_run(self):
        name=start();return name,safe(ROOT,'output/p2-mock-runs/'+name)
    def test_targeted_repair_and_idempotent_complete(self):
        name,run=self.setup_run();s=state_of(run)
        self.assertEqual(s['reports'][1]['errors'],['HASH_MISMATCH'])
        originals={p:safe(run,s['records'][p]['image_path']).read_bytes() for p in IDS}
        result=resume(name);self.assertEqual(result['phase'],'complete');self.assertEqual(result['attempts'],1)
        self.assertEqual(resume(name),result)
        for p in IDS:self.assertEqual(safe(run,s['records'][p]['image_path']).read_bytes(),originals[p])
        for p in (IDS[0],IDS[2]):self.assertEqual(result['records'][p],s['records'][p])
    def test_bounded_failure_across_resume(self):
        name,run=self.setup_run()
        self.assertEqual(resume(name,fail=True)['phase'],'paused')
        s=resume(name,fail=True);self.assertEqual(s['phase'],'stalled');self.assertEqual(s['attempts'],2)
        self.assertEqual(resume(name),s)
    def test_interrupted_reservation_no_duplicate(self):
        name,run=self.setup_run();s=state_of(run);s['pending']={'panel_id':IDS[1],'revision':2};checkpoint(run,s)
        self.assertEqual(resume(name)['reason'],'INTERRUPTED_ATTEMPT_REQUIRES_REVIEW')
        self.assertFalse(safe(run,'candidates/'+IDS[1]+'/r002.svg').exists())
    def test_missing_asset(self):
        name,run=self.setup_run();r=state_of(run)['records'][IDS[0]];r['image_path']='missing.svg'
        self.assertIn('ASSET_MISSING',check_asset(run,r,IDS[0]))
    def test_wrong_id(self):
        name,run=self.setup_run();r=state_of(run)['records'][IDS[0]]
        self.assertIn('PANEL_ID_MISMATCH',check_asset(run,r,IDS[2]))
    def test_invalid_format_and_size(self):
        name,run=self.setup_run();r=state_of(run)['records'][IDS[0]]
        path=safe(run,'invalid.svg');path.write_text('<svg width="1" height="2"/>');r['image_path']='invalid.svg'
        errors=check_asset(run,r,IDS[0]);self.assertIn('SVG_FORMAT',errors);self.assertIn('DIMENSIONS',errors)
    def test_escape_guard(self):
        with self.assertRaisesRegex(ValueError,'INVALID_RUN_NAME'):resume('../outside')
