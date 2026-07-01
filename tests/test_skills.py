import unittest
from src.extractors.skills import extract_skills, init_extractor

class TestSkills(unittest.TestCase):
    def setUp(self):
        init_extractor("data/skills.json", force=True)

    def test_extract_skills(self):
        desc1 = "Looking for a C++ developer with python and MySQL experience."
        skills1 = extract_skills(desc1)
        self.assertIn("C++", skills1)
        self.assertIn("Python", skills1)
        self.assertIn("MySQL", skills1)
        
        desc2 = "Requirements: C, Docker, and C#"
        skills2 = extract_skills(desc2)
        self.assertIn("C", skills2)
        self.assertIn("Docker", skills2)
        self.assertIn("C#", skills2)
        self.assertNotIn("C++", skills2)
        
        desc3 = "Next.js frontend and Node.js backend"
        skills3 = extract_skills(desc3)
        self.assertIn("Next.js", skills3)
        self.assertIn("Node.js", skills3)

if __name__ == "__main__":
    unittest.main()
