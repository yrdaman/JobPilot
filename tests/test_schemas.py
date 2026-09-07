import unittest

from pydantic import ValidationError

from src.models.schemas import CandidateProfile


class CandidateProfileTests(unittest.TestCase):
    def test_realistic_candidate_profile_is_valid(self):
        profile = CandidateProfile(
            summary="Data Science graduate with experience in data validation and reporting.",
            skills=["Python", "SQL", "PostgreSQL"],
            experience=[
                {
                    "title": "Machine Learning Intern",
                    "company": "Sure Trust",
                    "dates": "2025-2026",
                    "evidence": [
                        "Executed SQL queries on PostgreSQL datasets for data verification."
                    ],
                }
            ],
            projects=[
                {
                    "name": "Climate Analytics",
                    "evidence": [
                        "Cleaned and validated a large geo-tagged dataset."
                    ],
                }
            ],
            education=[
                {
                    "degree": "B.Tech in Data Science",
                    "institution": "Example Institute",
                    "dates": "2022-2025",
                    "details": "CGPA: 7.29/10",
                }
            ],
            certifications=[
                {
                    "name": "Data Analytics Essentials",
                    "issuer": "Cisco",
                    "date": "2026",
                }
            ],
            additional_information=["Available for full-time roles"],
        )

        self.assertTrue(profile.experience[0].evidence[0].startswith("Executed SQL"))
        self.assertEqual(profile.projects[0].name, "Climate Analytics")

    def test_missing_sections_default_to_empty_collections(self):
        profile = CandidateProfile(summary="A short profile")
        another_profile = CandidateProfile()

        self.assertEqual(profile.skills, [])
        self.assertEqual(profile.experience, [])
        self.assertEqual(profile.projects, [])
        self.assertIsNot(profile.skills, another_profile.skills)
        self.assertIsNot(profile.experience, another_profile.experience)

    def test_skill_validation_only_checks_shape(self):
        profile = CandidateProfile(skills=["HTML5", "70,000+ records"])

        self.assertEqual(profile.skills, ["HTML5", "70,000+ records"])

        with self.assertRaises(ValidationError):
            CandidateProfile(skills=[""])

        with self.assertRaises(ValidationError):
            CandidateProfile(skills=["A skill name with too many words for this field"])

        with self.assertRaises(ValidationError):
            CandidateProfile(skills=["Python: scripting"])


if __name__ == "__main__":
    unittest.main()