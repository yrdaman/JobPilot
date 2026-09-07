import unittest

from pydantic import ValidationError

from models.schemas import CandidateProfile
from ingestion.parser import _candidate_profile_response_format, parse_resume_text


class FakeResumeLLMClient:
    def __init__(self, profile: CandidateProfile):
        self.profile = profile
        self.received_text = None

    def parse_resume(self, resume_text: str) -> CandidateProfile:
        self.received_text = resume_text
        return self.profile


class ResumeParserTests(unittest.TestCase):
    def test_groq_schema_requires_all_declared_properties(self):
        schema = _candidate_profile_response_format()["json_schema"]["schema"]

        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        self.assertEqual(
            set(schema["$defs"]["Certification"]["required"]),
            set(schema["$defs"]["Certification"]["properties"]),
        )

    def test_parser_returns_validated_profile_without_api_call(self):
        expected = CandidateProfile(
            summary="Data analyst with Python and SQL experience.",
            skills=["Python", "SQL"],
            additional_information=[],
        )
        client = FakeResumeLLMClient(expected)

        result = parse_resume_text("PROFILE\nData analyst with Python and SQL experience.", client)

        self.assertEqual(result, expected)
        self.assertEqual(client.received_text, "PROFILE\nData analyst with Python and SQL experience.")

    def test_skills_are_concise_and_evidence_preserves_metrics(self):
        expected = CandidateProfile(
            skills=["Data validation", "SQL", "PostgreSQL", "HTML5", "CSS3"],
            experience=[
                {
                    "title": "Data Intern",
                    "company": "Example Company",
                    "evidence": ["Validated 70,000+ patient records using SQL."],
                }
            ],
            projects=[
                {
                    "name": "Document Intelligence",
                    "evidence": ["Converted 350+ documents into structured datasets."],
                }
            ],
        )

        result = parse_resume_text("Resume evidence", FakeResumeLLMClient(expected))

        self.assertEqual(
            result.skills,
            ["Data validation", "SQL", "PostgreSQL", "HTML5", "CSS3"],
        )
        self.assertEqual(len(result.experience[0].evidence), 1)
        self.assertIn("70,000+", result.experience[0].evidence[0])
        self.assertEqual(len(result.projects[0].evidence), 1)
        self.assertIn("350+", result.projects[0].evidence[0])

    def test_evidence_statement_is_rejected_as_a_skill(self):
        with self.assertRaises(ValidationError):
            CandidateProfile(
                skills=[
                    "Data accuracy and validation on 70,000+ row healthcare dataset"
                ]
            )

    def test_missing_information_is_not_invented(self):
        result = parse_resume_text(
            "Only a summary is present",
            FakeResumeLLMClient(CandidateProfile(summary="Only a summary is present")),
        )

        self.assertEqual(result.summary, "Only a summary is present")
        self.assertEqual(result.skills, [])
        self.assertEqual(result.experience, [])
        self.assertEqual(result.projects, [])

    def test_project_and_experience_evidence_keep_separate_points(self):
        profile = CandidateProfile(
            experience=[
                {
                    "evidence": [
                        "Executed SQL queries on PostgreSQL datasets.",
                        "Verified backend reports.",
                    ]
                }
            ],
            projects=[
                {
                    "name": "ML Pipeline",
                    "evidence": [
                        "Engineered a Python ML pipeline on 70,000+ records.",
                        "Improved recall from 0.71 to 0.84.",
                    ],
                }
            ],
        )

        self.assertEqual(len(profile.experience[0].evidence), 2)
        self.assertEqual(len(profile.projects[0].evidence), 2)
        self.assertIn("0.71", profile.projects[0].evidence[1])
        self.assertIn("0.84", profile.projects[0].evidence[1])

    def test_missing_evidence_defaults_to_empty_lists(self):
        profile = CandidateProfile(
            experience=[{"title": "Data Intern"}],
            projects=[{"name": "Unspecified Project"}],
        )

        self.assertEqual(profile.experience[0].evidence, [])
        self.assertEqual(profile.projects[0].evidence, [])

    def test_empty_resume_is_rejected_before_provider_call(self):
        client = FakeResumeLLMClient(CandidateProfile())

        with self.assertRaises(ValueError):
            parse_resume_text("  ", client)

        self.assertIsNone(client.received_text)


if __name__ == "__main__":
    unittest.main()