import unittest
from unittest.mock import patch
from pathlib import Path
from biwoom_studio.composition import korean as k
class Korean(unittest.TestCase):
    def test_measured_wrap(self):
        f,_=k.load_font('한글 시험 문장');lines,errors=k.wrap('한글 시험 문장',f,100)
        self.assertGreater(len(lines),1);self.assertTrue(all(f.getlength(x)<=100 for x in lines))
    def test_overlap(self):
        r,_=k.layout([{'text':'시험','box':[10,100,200,100]},{'text':'한글','box':[20,120,200,100]}])
        self.assertTrue(any('OVERLAP' in e for e in r['errors']))
    def test_height_clipped(self):
        r,_=k.layout([{'text':'한글 시험 문장 '*12,'box':[10,100,150,80]}])
        self.assertTrue(any('TEXT_CLIPPED' in e for e in r['errors']))
    def test_canvas_clipped(self):
        r,_=k.layout([{'text':'시험','box':[-10,100,200,100]}]);self.assertIn('0:BALLOON_CLIPPED',r['errors'])
    def test_punctuation_break(self):
        f,_=k.load_font('가.');_,errors=k.wrap('가 .',f,f.getlength('가'))
        self.assertIn('PUNCTUATION_BREAK',errors)
    def test_missing_font(self):
        with patch.object(k,'FONT',Path('/nonexistent-font')):
            with self.assertRaisesRegex(ValueError,'FONT_UNAVAILABLE'):k.load_font('한글')
    def test_missing_glyph(self):
        with self.assertRaisesRegex(ValueError,'MISSING_GLYPH'):k.load_font(chr(0x10ffff))
    def test_archive_roundtrip(self):
        d=k.demo();m=k.verify_archive(Path(d['run'])/'private-test-only.zip')
        self.assertEqual(len(m['files']),2);self.assertFalse(m['final_allowed'])

    def test_unbreakable_word(self):
        f,_=k.load_font('가나다라마바사');lines,errors=k.wrap('가나다라마바사',f,40)
        self.assertEqual(lines,['가나다라마바사']);self.assertTrue(any('WORD_TOO_WIDE' in e for e in errors))
    def test_newlines_and_eojeol(self):
        f,_=k.load_font('한글 시험 문장');lines,errors=k.wrap('한글 시험\n\n문장',f,70)
        self.assertIn('',lines);self.assertEqual(''.join(lines),'한글 시험문장')
        self.assertTrue(all(x.strip() in ('한글','시험','문장','') for x in lines))
