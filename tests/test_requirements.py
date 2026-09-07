import unittest

from pydantic import ValidationError

from analysis.job_requirements import (
    _job_requirements_response_format,
    extract_job_requirements,
)
from models.job_schemas import JobRequirements


class FakeJobRequirementsClient:
    def __init__(self, result: JobRequirements):
        self.result = result
        self.received_text = None

    def extract_requirements(self, jd_text: str) -> JobRequirements:
        self.received_text = jd_text
        return self.result


class JobRequirementsTests(unittest.TestCase):
    def test_explicit_technologies_are_extracted(self):
        jd_text = "Requirements:\n- Python\n- PostgreSQL\n- AWS"
        result = JobRequirements(
            requirements=[
                {"requirement": "Python", "category": "technical_skill", "importance": "unspecified", "evidence": "- Python"},
                {"requirement": "PostgreSQL", "category": "technical_skill", "importance": "unspecified", "evidence": "- PostgreSQL"},
                {"requirement": "AWS", "category": "technical_skill", "importance": "unspecified", "evidence": "- AWS"},
            ]
        )

        parsed = extract_job_requirements(jd_text, FakeJobRequirementsClient(result))

        self.assertEqual(
            [item.requirement for item in parsed.requirements],
            ["Python", "PostgreSQL", "AWS"],
        )

    def test_required_and_preferred_importance_is_preserved(self):
        result = JobRequirements(
            requirements=[
                {
                    "requirement": "Python",
                    "category": "technical_skill",
                    "importance": "required",
                    "evidence": "Required: Python experience.",
                },
                {
                    "requirement": "AWS",
                    "category": "technical_skill",
                    "importance": "preferred",
                    "evidence": "AWS experience is preferred.",
                },
            ]
        )

        parsed = extract_job_requirements("JD text", FakeJobRequirementsClient(result))

        self.assertEqual(parsed.requirements[0].importance, "required")
        self.assertEqual(parsed.requirements[1].importance, "preferred")

    def test_unmentioned_technology_is_not_invented(self):
        result = JobRequirements(
            requirements=[
                {
                    "requirement": "Python",
                    "category": "technical_skill",
                    "importance": "unspecified",
                    "evidence": "Experience with Python.",
                }
            ]
        )

        parsed = extract_job_requirements("Experience with Python.", FakeJobRequirementsClient(result))

        self.assertNotIn("AWS", [item.requirement for item in parsed.requirements])

    def test_evidence_is_original_jd_wording(self):
        result = JobRequirements(
            requirements=[
                {
                    "requirement": "2+ years of experience",
                    "category": "experience",
                    "importance": "required",
                    "evidence": "Required: 2+ years of experience with Python.",
                }
            ]
        )

        parsed = extract_job_requirements(
            "Required: 2+ years of experience with Python.",
            FakeJobRequirementsClient(result),
        )

        self.assertIn("2+ years", parsed.requirements[0].evidence)

    def test_empty_jd_is_rejected(self):
        with self.assertRaises(ValueError):
            extract_job_requirements("   ", FakeJobRequirementsClient(JobRequirements()))

    def test_importance_rejects_unknown_values(self):
        with self.assertRaises(ValidationError):
            JobRequirements(
                requirements=[
                    {
                        "requirement": "Python",
                        "category": "technical_skill",
                        "importance": "mandatory-ish",
                        "evidence": "Python",
                    }
                ]
            )

    def test_groq_schema_requires_all_declared_properties(self):
        schema = _job_requirements_response_format()["json_schema"]["schema"]

        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        self.assertEqual(
            set(schema["$defs"]["JobRequirement"]["required"]),
            set(schema["$defs"]["JobRequirement"]["properties"]),
        )

    def test_wsa_jd_examples_use_the_correct_categories(self):
        result = JobRequirements(
            requirements=[
                {
                    "requirement": "BTech in CSE with Data Science",
                    "category": "education",
                    "importance": "unspecified",
                    "evidence": "ME / MTech / BE / BTech in CSE with Data Science or an equivalent technical degree.",
                },
                {
                    "requirement": "Python",
                    "category": "technical_skill",
                    "importance": "required",
                    "evidence": "Strong knowledge of Python.",
                },
                {
                    "requirement": "SQL",
                    "category": "technical_skill",
                    "importance": "required",
                    "evidence": "Strong understanding of SQL and relational data concepts.",
                },
                {
                    "requirement": "Git",
                    "category": "technical_skill",
                    "importance": "unspecified",
                    "evidence": "Familiarity with Git.",
                },
                {
                    "requirement": "communication and teamwork",
                    "category": "competency",
                    "importance": "unspecified",
                    "evidence": "Good communication and teamwork skills.",
                },
                {
                    "requirement": "Self-taught developers with solid portfolios",
                    "category": "application",
                    "importance": "preferred",
                    "evidence": "Self-taught developers with solid portfolios are also encouraged to apply.",
                },
                {
                    "requirement": "Onsite, Hyderabad",
                    "category": "other",
                    "importance": "unspecified",
                    "evidence": "Location: Onsite, Hyderabad",
                },
                {
                    "requirement": "6 months",
                    "category": "other",
                    "importance": "unspecified",
                    "evidence": "Duration: 6 months",
                },
            ]
        )
        parsed = extract_job_requirements("WSA JD", FakeJobRequirementsClient(result))

        categories = {item.requirement: item.category for item in parsed.requirements}
        self.assertEqual(categories["BTech in CSE with Data Science"], "education")
        self.assertEqual(categories["Python"], "technical_skill")
        self.assertEqual(categories["SQL"], "technical_skill")
        self.assertEqual(categories["Git"], "technical_skill")
        self.assertEqual(categories["communication and teamwork"], "competency")
        self.assertEqual(categories["Self-taught developers with solid portfolios"], "application")
        self.assertEqual(categories["Onsite, Hyderabad"], "other")
        self.assertEqual(categories["6 months"], "other")
        self.assertIn("encouraged to apply", parsed.requirements[5].evidence)

    def test_category_rejects_unknown_values(self):
        with self.assertRaises(ValidationError):
            JobRequirements(
                requirements=[
                    {
                        "requirement": "Python",
                        "category": "technology",
                        "importance": "unspecified",
                        "evidence": "Python",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()