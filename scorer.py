import sqlite3
import json
import anthropic
import os
from datetime import datetime, timezone
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


# Calculate how many hours ago a job was posted
def hours_since_posted(date_string):
    if not date_string:
        return 9999
    try:
        posted = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - posted
        return delta.total_seconds() / 3600
    except Exception:
        return 9999


# Calculate a combined score that weighs both relevance and recency
def combined_score(relevance_score, hours_ago):
    # Recency bonus: full bonus if posted within 24 hours, drops off after that
    if hours_ago <= 24:
        recency_bonus = 20
    elif hours_ago <= 72:
        recency_bonus = 10
    elif hours_ago <= 168:
        recency_bonus = 5
    else:
        recency_bonus = 0

    return relevance_score + recency_bonus


# Score all jobs in the database against a candidate profile
def score_all_jobs(candidate_profile):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT job_id, title, description, date_fetched, company, location
        FROM jobs
        WHERE signals_extracted = 1
        AND description IS NOT NULL
    """)

    jobs = cursor.fetchall()
    connection.close()

    results = []
    for job_id, title, description, date_fetched, company, location in jobs:
        result = score_job(title, description, candidate_profile)
        if result:
            hours_ago = hours_since_posted(date_fetched)
            final_score = combined_score(result.get("score", 0), hours_ago)

            results.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "relevance_score": result.get("score", 0),
                "hours_ago": round(hours_ago),
                "final_score": final_score,
                "match_reasons": result.get("match_reasons", []),
                "gap_reasons": result.get("gap_reasons", [])
            })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results