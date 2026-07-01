import unittest
import os
import sqlite3
from src.models.job import Job
from src.database.jobs import init_db, get_cached_ai, set_cached_ai

class TestCaching(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "data/test_jobs.db"
        
        # Ensure fresh start by deleting existing test db file
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass
                
        # Patch the database path for tests
        import src.database.jobs as db_jobs
        self.original_db_path = db_jobs.DB_PATH
        db_jobs.DB_PATH = self.test_db_path
        
        init_db()

    def tearDown(self):
        import src.database.jobs as db_jobs
        db_jobs.DB_PATH = self.original_db_path
        
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

    def test_ai_cache_operations(self):
        job_hash = "abc123hash"
        self.assertIsNone(get_cached_ai(job_hash))
        
        set_cached_ai(
            job_hash=job_hash,
            score=88,
            confidence="high",
            strengths=["Python", "SQL"],
            missing=["Docker"],
            summary="Strong Python backend engineer."
        )
        
        cached = get_cached_ai(job_hash)
        self.assertIsNotNone(cached)
        self.assertEqual(cached["score"], 88)
        self.assertEqual(cached["confidence"], "high")
        self.assertIn("Python", cached["strengths"])
        self.assertIn("Docker", cached["missing"])
        self.assertEqual(cached["summary"], "Strong Python backend engineer.")

if __name__ == "__main__":
    unittest.main()
