import unittest
from unittest.mock import patch
from src.models.job import Job
from src.models.resume import ResumeProfile
from src.pipeline.scoring import calculate_python_score

class TestScoring(unittest.TestCase):
    @patch("src.pipeline.scoring.extract_skills")
    def test_calculate_python_score(self, mock_extract):
        mock_extract.return_value = ["Python", "Docker"]
        
        resume = ResumeProfile(
            name="Rohit",
            skills=["Python", "Java", "SQL"],
            education="BCA",
            experience="Fresher",
            preferred_roles=["Software Engineer"],
            preferred_locations=["Bangalore"],
            skill_categories={}
        )
        
        job = Job(
            id="1",
            company="Google",
            title="Software Engineer",
            location="Bangalore",
            url="url",
            posted_at="date",
            source="Greenhouse",
            requirements="Python developer role"
        )
        
        score = calculate_python_score(job, resume)
        self.assertAlmostEqual(score, 68.0)

if __name__ == "__main__":
    unittest.main()
