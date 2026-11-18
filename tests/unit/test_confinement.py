import unittest
from pathlib import Path
from biwoom_studio.core import ROOT, safe

class Confinement(unittest.TestCase):
    def test_repository_root_resolved_after_src_move(self):
        self.assertEqual(ROOT, Path(__file__).resolve().parents[2])
    def test_external_root_rejected_without_read(self):
        with self.assertRaisesRegex(ValueError, 'ROOT_OUTSIDE_STUDIO'):
            safe(ROOT.parent, 'not-read-or-created')
    def test_absolute_path_rejected(self):
        with self.assertRaisesRegex(ValueError, 'PATH_ESCAPE'):
            safe(ROOT, ROOT / 'not-created')
