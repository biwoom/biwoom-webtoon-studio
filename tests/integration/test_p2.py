import unittest
from biwoom_studio.generation.mock import candidate, create_run, safe, read_json, digest

class P2(unittest.TestCase):
    def panel(self,pid='ST-999-EP01-P006'):return {'id':pid,'status':'draft','dialogue':[{'text':'synthetic'}]}
    def test_candidate_record_current_bytes(self):
        run=create_run(); r=candidate(run,self.panel())
        self.assertEqual(digest(safe(run,r['image_path']).read_bytes()),r['image_sha256'])
        self.assertEqual(r['approval'],'not_approved');self.assertEqual(r['live_calls'],0)
    def test_target_revision_keeps_sibling_and_prior(self):
        run=create_run(); a=candidate(run,self.panel()); b=candidate(run,self.panel('ST-999-EP01-P007'))
        before=[safe(run,r['image_path']).read_bytes() for r in (a,b)]
        c=candidate(run,self.panel('ST-999-EP01-P007'),2)
        self.assertEqual(before,[safe(run,r['image_path']).read_bytes() for r in (a,b)])
        self.assertNotEqual(c['image_sha256'],b['image_sha256'])
    def test_duplicate_revision_refused(self):
        run=create_run();candidate(run,self.panel())
        with self.assertRaises(FileExistsError):candidate(run,self.panel())
    def test_live_guard_before_any_file_access(self):
        with self.assertRaisesRegex(ValueError,'LIVE_PROVIDER_DISABLED'):candidate(None,self.panel(),live=True)
    def test_unknown_provider_guard(self):
        with self.assertRaisesRegex(ValueError,'LIVE_PROVIDER_DISABLED'):candidate(None,self.panel(),provider='external')
    def test_non_draft_not_approved_by_test(self):
        p=self.panel();p['status']='approved'
        with self.assertRaisesRegex(ValueError,'DRAFT_TEST_ONLY'):candidate(None,p)
    def test_bad_id_no_files(self):
        with self.assertRaisesRegex(ValueError,'INVALID_PANEL_ID'):candidate(None,self.panel('../escape'))
    def test_reference_tamper_blocked(self):
        run=create_run();safe(run,'reference.svg').write_bytes(b'changed fixture')
        with self.assertRaisesRegex(ValueError,'REFERENCE_CHANGED'):candidate(run,self.panel())
        self.assertFalse(safe(run,'candidates').exists())
    def test_failure_logged_no_candidate(self):
        run=create_run()
        with self.assertRaisesRegex(RuntimeError,'SIMULATED_PROVIDER_FAILURE'):candidate(run,self.panel(),fail=True)
        stem='candidates/ST-999-EP01-P006/r001'
        self.assertFalse(safe(run,stem+'.svg').exists());self.assertFalse(safe(run,stem+'.json').exists())
        self.assertFalse(read_json(run,stem+'.failure.json')['candidate_created'])
