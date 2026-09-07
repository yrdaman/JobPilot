import unittest

from src.ingestion.chunker import (
    chunk_resume_hybrid,
    section_split,
)


class ChunkerTests(unittest.TestCase):
    def test_normal_resume_keeps_sections(self):
        text = """JOHN DOE
Hyderabad, India

PROFILE SUMMARY
Data analyst with Python experience.

TECHNICAL SKILLS
Python, SQL, GIS

WORK EXPERIENCE
Validated large datasets.
"""

        sections = section_split(text)

        self.assertEqual(
            [section["section_key"] for section in sections],
            ["general", "summary", "skills", "experience"],
        )
        self.assertEqual(chunk_resume_hybrid(text)[1].metadata["section_key"], "summary")

    def test_different_section_names_are_detected(self):
        text = """PROFESSIONAL SUMMARY
Short summary.

    WORK EXPERIENCE
Worked with data.

    ACADEMIC PROJECTS
Built a data pipeline.
"""

        self.assertEqual(
            [section["section"] for section in section_split(text)],
            ["PROFESSIONAL SUMMARY", "WORK EXPERIENCE", "ACADEMIC PROJECTS"],
        )

    def test_resume_without_headings_uses_general_section(self):
        text = "Candidate with Python and SQL experience.\nWorked on data validation."

        sections = section_split(text)

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["section_key"], "general")
        self.assertEqual(len(chunk_resume_hybrid(text)), 1)

    def test_long_section_uses_token_splitting(self):
        bullets = "\n".join(
            f"- Project evidence {index}: " + "SQL data validation " * 25
            for index in range(8)
        )
        chunks = chunk_resume_hybrid(
            "PROJECTS\n" + bullets,
            max_tokens=100,
            overlap_tokens=20,
        )

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.metadata["section_key"] == "projects" for chunk in chunks))
        self.assertTrue(all(chunk.metadata["strategy"] == "section+token" for chunk in chunks))
        self.assertTrue(all(chunk.metadata["chunk_id"] == index for index, chunk in enumerate(chunks)))

    def test_bullets_remain_in_their_section(self):
        text = """PROJECTS
Climate Analytics
- Used SQL for data validation.
- Processed a large dataset.
Resume Matcher
- Used PostgreSQL for matching.
- Built retrieval tests.
"""

        chunks = chunk_resume_hybrid(text)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].metadata["section_key"], "projects")
        self.assertIn("Climate Analytics", chunks[0].text)
        self.assertIn("PostgreSQL", chunks[0].text)

    def test_evidence_lines_are_not_false_headings(self):
        text = """Built experience with SQL and data validation
- Worked with PostgreSQL datasets.
Email: candidate@example.com
"""

        sections = section_split(text)

        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["section_key"], "general")


if __name__ == "__main__":
    unittest.main()
