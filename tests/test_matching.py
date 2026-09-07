import unittest

from analysis.matching import compare_requirements
from models.job_schemas import JobRequirements
from models.schemas import CandidateProfile


def requirement(name: str, category: str = "technical_skill") -> dict:
    return {
        "requirement": name,
        "category": category,
        "importance": "unspecified",
        "evidence": name,
    }


class RequirementMatchingTests(unittest.TestCase):
    def test_explicit_python_evidence_is_strong_and_preserved(self):
        profile = CandidateProfile(
            skills=["Python"],
            projects=[{"name": "Pipeline", "evidence": ["Built a Python pipeline."]}],
        )
        result = compare_requirements(
            profile,
            JobRequirements(requirements=[requirement("Python")]),
        )

        self.assertEqual(result.matches[0].status, "strong")
        self.assertEqual(result.matches[0].evidence, ["Python", "Built a Python pipeline."])

    def test_postgresql_evidence_is_strong(self):
        profile = CandidateProfile(
            experience=[{"evidence": ["Executed queries on PostgreSQL datasets."]}]
        )

        result = compare_requirements(
            profile,
            JobRequirements(requirements=[requirement("PostgreSQL")]),
        )

        self.assertEqual(result.matches[0].status, "strong")

    def test_missing_aws_is_no_evidence_without_claim(self):
        profile = CandidateProfile(skills=["Python", "SQL"])

        result = compare_requirements(
            profile,
            JobRequirements(requirements=[requirement("AWS")]),
        )

        self.assertEqual(result.matches[0].status, "no_evidence")
        self.assertEqual(result.matches[0].evidence, [])
        self.assertNotIn("AWS", result.matches[0].explanation)

    def test_azure_related_evidence_is_never_strong_for_specific_service(self):
        profile = CandidateProfile(
            projects=[{"evidence": ["Tested Azure AI workflow implementations."]}]
        )

        result = compare_requirements(
            profile,
            JobRequirements(requirements=[requirement("Azure Data Lake")]),
        )

        self.assertEqual(result.matches[0].status, "partial")
        self.assertNotEqual(result.matches[0].status, "strong")
        self.assertEqual(
            result.matches[0].evidence,
            ["Tested Azure AI workflow implementations."],
        )

    def test_every_requirement_is_evaluated(self):
        profile = CandidateProfile(skills=["Python", "SQL"])
        requirements = JobRequirements(
            requirements=[
                requirement("Python"),
                requirement("SQL"),
                requirement("PostgreSQL"),
                requirement("AWS"),
                requirement("Power BI"),
            ]
        )

        result = compare_requirements(profile, requirements)

        self.assertEqual(len(result.matches), 5)
        self.assertEqual(
            [match.requirement for match in result.matches],
            ["Python", "SQL", "PostgreSQL", "AWS", "Power BI"],
        )

    def test_unrelated_evidence_is_not_returned(self):
        profile = CandidateProfile(
            projects=[{"evidence": ["Built a Python dashboard.", "Used Git for version control."]}]
        )

        result = compare_requirements(
            profile,
            JobRequirements(requirements=[requirement("Power BI")]),
        )

        self.assertEqual(result.matches[0].status, "no_evidence")
        self.assertEqual(result.matches[0].evidence, [])


if __name__ == "__main__":
    unittest.main()