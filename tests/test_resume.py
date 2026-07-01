import unittest
from unittest.mock import patch, MagicMock
from src.extractors.resume import load_resume_text

class TestResumeParser(unittest.TestCase):
    @patch("os.path.exists")
    @patch("zipfile.ZipFile")
    def test_docx_parser(self, mock_zip, mock_exists):
        mock_exists.return_value = True
        
        xml_data = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p><w:r><w:t>John Doe</w:t></w:r></w:p>
                <w:p><w:r><w:t>Python Developer</w:t></w:r></w:p>
            </w:body>
        </w:document>
        """
        
        mock_zip_instance = MagicMock()
        mock_zip_instance.read.return_value = xml_data
        mock_zip.return_value.__enter__.return_value = mock_zip_instance
        
        text = load_resume_text("data/resume.docx")
        
        self.assertIn("John Doe", text)
        self.assertIn("Python Developer", text)

if __name__ == "__main__":
    unittest.main()
