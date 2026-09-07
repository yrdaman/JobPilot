import argparse
from pathlib import Path

from analysis.job_requirements import extract_job_requirements


def main() -> None:
    argument_parser = argparse.ArgumentParser(
        description="Extract structured requirements from a job description."
    )
    argument_parser.add_argument("txt_path", type=Path)
    arguments = argument_parser.parse_args()

    jd_text = arguments.txt_path.read_text(encoding="utf-8")
    requirements = extract_job_requirements(jd_text)
    print(requirements.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
