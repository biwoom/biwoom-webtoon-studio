import json
import unittest
from biwoom_studio.core import (create_fixture, approve_fixture_only, preview, layout, validate, safe)

class Gates(unittest.TestCase):
    def setUp(self):
        self.run = create_fixture()  # All runs remain under local ignored output/mock-runs; no cleanup deletion.
    def change(self, fn):
        path = self.run/'source/storyboard.json'
        data = json.loads(path.read_text())
        fn(data['panels'])
        path.write_text(json.dumps(data, ensure_ascii=False))
    def blocked(self, code, pid):
        self.assertEqual(layout(self.run), [{'code':code,'panel_id':pid}])
        self.assertFalse((self.run/'export/mock-layout.json').exists())
    def test_positive(self):
        approve_fixture_only(self.run)
        self.assertEqual(layout(self.run), [])
        result = json.loads((self.run/'export/mock-layout.json').read_text())
        self.assertTrue(result['mock_only'])
        self.assertFalse(result['production_release'])
        self.assertEqual([p['id'] for p in result['panels']], ['P01','P02'])
    def test_missing_approval_preview_not_final(self):
        issues = preview(self.run)
        self.assertEqual(len(issues),2)
        self.assertFalse(json.loads((self.run/'preview/review.json').read_text())['final'])
        self.assertEqual(layout(self.run), issues)
        self.assertFalse((self.run/'export/mock-layout.json').exists())
    def test_stale_dialogue_unchanged_panel_valid(self):
        approve_fixture_only(self.run)
        original_image = (self.run/'candidates/P02.marker').read_bytes()
        self.change(lambda p:p[1].update(dialogue='수정된 합성 대사'))
        self.blocked('APPROVAL_STALE','P02')
        self.assertEqual((self.run/'candidates/P02.marker').read_bytes(), original_image)
        self.assertNotIn('P01', [e['panel_id'] for e in validate(self.run)[1]])
    def test_stale_image(self):
        approve_fixture_only(self.run)
        (self.run/'candidates/P02.marker').write_bytes(b'CHANGED MOCK MARKER')
        self.blocked('APPROVAL_STALE','P02')
    def test_missing_panel(self):
        approve_fixture_only(self.run)
        self.change(lambda p:p.pop())
        self.blocked('MISSING_PANEL','P02')
    def test_source_mislabel(self):
        approve_fixture_only(self.run)
        self.change(lambda p:p[0].update(source_roles={'S01':'canon'}))
        self.blocked('SOURCE_ROLE_MISMATCH','P01')
    def test_real_data_cannot_auto_approve(self):
        self.change(lambda p:p[0].update(dialogue='Not the fixed synthetic fixture'))
        with self.assertRaisesRegex(ValueError,'NOT_SYNTHETIC_FIXTURE'):
            approve_fixture_only(self.run)
        self.assertEqual(list((self.run/'approvals').iterdir()), [])
    def test_path_escape(self):
        with self.assertRaisesRegex(ValueError,'PATH_ESCAPE'): safe(self.run, '../outside')
        self.assertFalse((self.run/'export/mock-layout.json').exists())
    def test_symlink_image_rejected(self):
        approve_fixture_only(self.run)
        (self.run/'candidates/link.marker').symlink_to(self.run/'candidates/P01.marker')
        self.change(lambda p:p[0].update(image='candidates/link.marker'))
        with self.assertRaisesRegex(ValueError,'SYMLINK_REJECTED'): layout(self.run)
        self.assertFalse((self.run/'export/mock-layout.json').exists())
