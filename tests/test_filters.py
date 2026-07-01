import unittest
from unittest.mock import patch
from src.models.job import Job
from src.pipeline.filters import apply_hard_filters, extract_experience

class TestFilters(unittest.TestCase):
    def test_extract_experience(self):
        self.assertEqual(extract_experience("Software Engineer", "Requires 3+ years of experience"), 3)
        self.assertEqual(extract_experience("Software Engineer", "0-2 years of experience required"), 2)
        self.assertEqual(extract_experience("Software Engineer (5 years exp)", "Looking for someone with 5 years experience"), 5)
        self.assertEqual(extract_experience("Junior Developer", "No experience needed"), 0)

    @patch("src.pipeline.filters.load_preferences")
    def test_apply_hard_filters(self, mock_prefs):
        mock_prefs.return_value = {
            "experience": 2,
            "remote": True,
            "india": True,
            "internships": False,
            "require_salary": False,
            "excluded_departments": ["sales", "hr"],
            "preferred_locations": ["bangalore", "remote"]
        }
        
        job1 = Job("1", "Google", "SWE", "Bangalore", "url1", "date", "Greenhouse", "Requires 1 year experience")
        job2 = Job("2", "Google", "SWE Intern", "Remote", "url2", "date", "Greenhouse", "Internship role")
        job3 = Job("3", "Google", "Senior SWE", "Hyderabad", "url3", "date", "Greenhouse", "Requires 5+ years of experience")
        job4 = Job("4", "Google", "HR Specialist", "Bangalore", "url4", "date", "Greenhouse", "HR role", department="HR")
        job5 = Job("5", "Google", "SWE", "Remote", "url5", "date", "Greenhouse", "1 year experience required")
        job6 = Job("6", "Google", "SWE", "Seattle", "url6", "date", "Greenhouse", "No experience")
        
        jobs = [job1, job2, job3, job4, job5, job6]
        filtered = apply_hard_filters(jobs)
        
        filtered_ids = [j.id for j in filtered]
        self.assertIn("1", filtered_ids)
        self.assertNotIn("2", filtered_ids)
        self.assertNotIn("3", filtered_ids)
        self.assertNotIn("4", filtered_ids)
        self.assertIn("5", filtered_ids)
        self.assertNotIn("6", filtered_ids)

if __name__ == "__main__":
    unittest.main()
