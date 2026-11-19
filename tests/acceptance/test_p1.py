import unittest
from fixtures.p1 import bundle
from biwoom_studio.models.p1 import validate_bundle, validate_story

class P1(unittest.TestCase):
    def test_valid_ten_synthetic_panels_not_generation_ready(self):
        result=validate_bundle(bundle())
        self.assertTrue(result['schema_valid']); self.assertFalse(result['generation_ready'])
    def bad(self, change, code):
        b=bundle(); change(b)
        result=validate_bundle(b)
        self.assertFalse(result['schema_valid'])
        self.assertTrue(any(e.startswith(code) for e in result['errors']),result)
    def test_missing_panel(self): self.bad(lambda b:b['panels']['panels'].pop(),'PANEL_IDS')
    def test_duplicate_panel(self): self.bad(lambda b:b['panels']['panels'][1].update(id='ST-999-EP01-P001'),'PANEL_IDS')
    def test_unknown_source(self): self.bad(lambda b:b['panels']['panels'][0].update(source_ids=['missing']),'SOURCE_REF')
    def test_unknown_locator(self): self.bad(lambda b:b['panels']['panels'][0]['source_refs'][0].update(locator='missing'),'SOURCE_LOCATOR')
    def test_unverified_canonical(self): self.bad(lambda b:b['panels']['panels'][0].update(origin_type='canonical'),'CANONICAL_UNVERIFIED')
    def test_missing_character(self): self.bad(lambda b:b['panels']['panels'][0].update(characters=['missing']),'BIBLE_REF')
    def test_hash_changed(self): self.bad(lambda b:b['actual_hashes'].update(script='changed'),'HASH_MISMATCH')
    def test_false_approval(self): self.bad(lambda b:b['project']['approval_gates'].update(G1='approved'),'DRAFT_APPROVAL_GUARD')
    def test_reuse_enabled(self): self.bad(lambda b:b['sources']['sources'][0].update(text_reuse_allowed=True),'DRAFT_RIGHTS_GUARD')
    def test_ready_status_rejected(self): self.bad(lambda b:b['panels']['panels'][0].update(status='ready_for_generation'),'PANEL_DRAFT_GUARD')
    def test_malformed(self): self.assertFalse(validate_bundle({})['schema_valid'])
    def test_path_escape(self):
        with self.assertRaisesRegex(ValueError,'INVALID_STORY_ID'):validate_story('../outside')
