import sqlite3
import json
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "jobs.db"
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# Score a single job against a candidate profile using Claude
def score_job(job_title, job_description, candidate_profile):
    prompt = f"""
You are a recruiting analyst. Score how well this candidate matches the job posting.

Candidate profile:
{candidate_profile}

Job title: {job_title}
Job description (first 1500 characters): {job_description[:1500]}

Return JSON only — no explanation, no markdown, no extra text:
{{
  "score": <integer from 0 to 100>,
  "match_reasons": ["up to 3 reasons why they are a good match"],
  "gap_reasons": ["up to 3 skills or experience gaps"]
}}
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("\n", 1)[0]
        return json.loads(cleaned)

    except Exception as error:
        print(f"Scoring failed for {job_title}: {error}")
        return None


# Score all jobs in the database against a candidate profile
def score_all_jobs(candidate_profile):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT job_id, title, description
        FROM jobs
        WHERE signals_extracted = 1
        AND description IS NOT NULL
    """)

    jobs = cursor.fetchall()
    connection.close()

    results = []
    for job_id, title, description in jobs:
        result = score_job(title, description, candidate_profile)
        if result:
            results.append({
                "job_id": job_id,
                "title": title,
                "score": result.get("score", 0),
                "match_reasons": result.get("match_reasons", []),
                "gap_reasons": result.get("gap_reasons", [])
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


if __name__ == "__main__":
    test_profile = """
    3 years of experience as a data analyst.
    Strong SQL skills, experienced with Excel and Power BI.
    Some Python experience. Background in fintech.
    Looking for mid-level roles, open to remote work.
    """

    results = score_all_jobs(test_profile)
    for r in results[:5]:
        print(f"Score: {r['score']} | {r['title']}")
        print(f"  Match: {r['match_reasons']}")
        print(f"  Gaps:  {r['gap_reasons']}")
        print("---")