from analysis.matching import compare_requirements_with_retrieval
from db.chroma import create_collection
from models.job_schemas import JobRequirements

from analysis.fit import calculate_fit
from analysis.decision import should_apply
from analysis.fit import calculate_fit

requirements = JobRequirements(
    requirements=[
        {
            "requirement": "ME / MTech / BE / BTech in CSE with Data Science or an equivalent technical degree.",
            "category": "education",
            "importance": "required",
            "evidence": "ME / MTech / BE / BTech in CSE with Data Science or an equivalent technical degree.",
        },
        {
            "requirement": "Strong academic background with a minimum of 70% or CGPA 7.0+.",
            "category": "education",
            "importance": "required",
            "evidence": "Strong academic background with a minimum of 70% or CGPA 7.0+.",
        },
        {
            "requirement": "Strong knowledge of Python.",
            "category": "technical_skill",
            "importance": "required",
            "evidence": "Strong knowledge of Python.",
        },
        {
            "requirement": "Strong knowledge of data structures and algorithms.",
            "category": "technical_skill",
            "importance": "required",
            "evidence": "Strong knowledge of data structures and algorithms.",
        },
        {
            "requirement": "Strong understanding of SQL and relational data concepts.",
            "category": "technical_skill",
            "importance": "required",
            "evidence": "Strong understanding of SQL and relational data concepts.",
        },
        {
            "requirement": "Familiarity with Git.",
            "category": "technical_skill",
            "importance": "required",
            "evidence": "Familiarity with Git.",
        },
        {
            "requirement": "Eagerness to learn Databricks, Power BI, and related tools quickly.",
            "category": "competency",
            "importance": "preferred",
            "evidence": "Eagerness to learn Databricks, Power BI, and related tools quickly.",
        },
        {
            "requirement": "Interest in statistics, experimentation, feature engineering, or applied data science.",
            "category": "competency",
            "importance": "unspecified",
            "evidence": "Interest in statistics, experimentation, feature engineering, or applied data science.",
        },
        {
            "requirement": "Exposure to Azure Cloud services such as Azure Data Lake, Azure Databricks, Azure Functions, or Azure DevOps.",
            "category": "technical_skill",
            "importance": "preferred",
            "evidence": "Exposure to Azure Cloud services such as Azure Data Lake, Azure Databricks, Azure Functions, or Azure DevOps.",
        },
        {
            "requirement": "Exposure to Power BI, .NET APIs, or ReactJS for simple internal dashboards.",
            "category": "technical_skill",
            "importance": "preferred",
            "evidence": "Exposure to Power BI, .NET APIs, or ReactJS for simple internal dashboards.",
        },
        {
            "requirement": "Good communication and teamwork skills.",
            "category": "competency",
            "importance": "required",
            "evidence": "Good communication and teamwork skills.",
        },
        {
            "requirement": "Eagerness to learn and take responsibility.",
            "category": "competency",
            "importance": "required",
            "evidence": "Eagerness to learn and take responsibility.",
        },
        {
            "requirement": "Strong logical thinking and problem-solving attitude.",
            "category": "competency",
            "importance": "required",
            "evidence": "Strong logical thinking and problem-solving attitude.",
        },
        {
            "requirement": "Interest in automation, AI-assisted analysis, data engineering, or data science approaches for development and analysis.",
            "category": "competency",
            "importance": "unspecified",
            "evidence": "Interest in automation, AI-assisted analysis, data engineering, or data science approaches for development and analysis.",
        },
        {
            "requirement": "Self-taught developers with solid portfolios are also encouraged to apply.",
            "category": "application",
            "importance": "preferred",
            "evidence": "Self-taught developers with solid portfolios are also encouraged to apply.",
        },
        {
            "requirement": "Personal projects, dashboards, or a GitHub profile.",
            "category": "application",
            "importance": "preferred",
            "evidence": "Personal projects, dashboards, or a GitHub profile.",
        },
        {
            "requirement": "Internship duration: 6 months.",
            "category": "other",
            "importance": "unspecified",
            "evidence": "Duration: 6 months",
        },
        {
            "requirement": "Location: Onsite, Hyderabad.",
            "category": "other",
            "importance": "unspecified",
            "evidence": "Location: Onsite, Hyderabad",
        },
        {
            "requirement": "Type: Paid internship.",
            "category": "other",
            "importance": "unspecified",
            "evidence": "Type: Paid internship",
        },
    ]
)


collection = create_collection()

job_match = compare_requirements_with_retrieval(
    requirements=requirements,
    collection=collection,
)


print("\n" + "=" * 70)
print("JOBPILOT — WSAUDIOLOGY REQUIREMENT MATCHING")
print("=" * 70)

for index, match in enumerate(job_match.matches, start=1):
    print(f"\n{index}. {match.requirement}")
    print(f"   Category:   {match.category}")
    print(f"   Importance: {match.importance}")
    print(f"   Status:     {match.status}")
    print(f"   Evidence:")

    if match.evidence:
        for evidence in match.evidence:
            print(f"      - {evidence}")
    else:
        print("      - None")

    print(f"   Explanation: {match.explanation}")

print("\n" + "=" * 70)

fit = calculate_fit(job_match)

print("\n======================================================================")
print("JOBPILOT — FIT SUMMARY")
print("======================================================================")
print(f"Fit Score:         {fit['fit_score']}/100")
print(f"Strong Matches:    {fit['strong_matches']}")
print(f"Partial Matches:   {fit['partial_matches']}")
print(f"No Evidence:       {fit['no_evidence']}")
print(f"Total Requirements: {fit['total_requirements']}")

decision = should_apply(job_match, fit)

print("\n======================================================================")
print("JOBPILOT — APPLICATION DECISION")
print("======================================================================")
print(f"Recommendation: {decision['recommendation'].upper()}")
print(f"Fit Score:      {decision['fit_score']}/100")

if decision["required_missing"]:
    print("\nRequired requirements with no evidence:")
    for requirement in decision["required_missing"]:
        print(f"   - {requirement}")

if decision["required_partial"]:
    print("\nRequired requirements with partial evidence:")
    for requirement in decision["required_partial"]:
        print(f"   - {requirement}")