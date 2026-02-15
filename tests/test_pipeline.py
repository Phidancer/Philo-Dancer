from pathlib import Path
import tempfile
import unittest

from music_teaching_system.pdf_ingest import classify_page, parse_pdf
from music_teaching_system.pipeline import convert_pdf_to_teaching_system
from music_teaching_system.webapp import _html_page


class PipelineTests(unittest.TestCase):
    def test_convert_text_backed_material(self):
        content = "SHEET staff measure 1 | C D E F\fHarmony analysis chart form"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "lesson.txt"
            out = Path(tmp) / "out"
            source.write_text(content, encoding="utf-8")

            bundle = convert_pdf_to_teaching_system(source, out)

            self.assertGreaterEqual(len(bundle.sections), 2)
            self.assertTrue((out / "bundle.json").exists())
            self.assertTrue((out / "index.html").exists())
            self.assertTrue(any("classified_as=sheetmusic" in x for x in bundle.audit_log))
            self.assertTrue(any("classified_as=analysis" in x for x in bundle.audit_log))

    def test_parse_pdf_text_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "mock.pdf"
            source.write_text("Page 1\fPage 2", encoding="utf-8")
            parsed = parse_pdf(source)
            self.assertEqual(parsed.title, "mock")
            self.assertEqual(len(parsed.pages), 2)

    def test_classify_hybrid_page(self):
        text = "SHEET staff measure 1 with harmony analysis chart"
        self.assertEqual(classify_page(text), "hybrid")


    def test_binary_pdf_fallback_has_ocr_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "scan.pdf"
            out = Path(tmp) / "out"
            source.write_bytes(b"%PDF-1.7\x00\x01\x02\x03\xff\xfe")
            bundle = convert_pdf_to_teaching_system(source, out)
            self.assertTrue(any("no readable text" in x for x in bundle.audit_log))
            self.assertIn("OCR", bundle.sections[0].objective)


    def test_html_escapes_script_end_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "lesson.txt"
            out = Path(tmp) / "out"
            source.write_text("analysis </script> chart", encoding="utf-8")
            convert_pdf_to_teaching_system(source, out)
            html = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("<script id='bundle-data' type='application/json'>", html)
            self.assertIn(r"<\/script>", html)

    def test_web_html_wrapper(self):
        page = _html_page("<h1>ok</h1>").decode("utf-8")
        self.assertIn("Schenker 教材转换器", page)
        self.assertIn("<h1>ok</h1>", page)
        self.assertIn("<title>Schenker 教材转换器</title>", page)


if __name__ == "__main__":
    unittest.main()
