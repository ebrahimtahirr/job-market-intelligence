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
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("\n", 1)[0]
        return json.loads(raw)

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
        return (now - posted).total_seconds() / 3600
    except Exception:
        return 9999


# Calculate combined score weighing relevance and recency
def combined_score(relevance_score, hours_ago):
    if hours_ago <= 24:
        recency_bonus = 20
    elif hours_ago <= 72:
        recency_bonus = 10
    elif hours_ago <= 168:
        recency_bonus = 5
    else:
        recency_bonus = 0
    return relevance_score + recency_bonus


# Fast keyword pre-filter — no Claude involved, pure Python
# Returns a relevance score based on how many candidate keywords appear in the job
def keyword_match_score(candidate_keywords, job_text):
    if not job_text:
        return 0
    job_text_lower = job_text.lower()
    matches = sum(1 for keyword in candidate_keywords if keyword.lower() in job_text_lower)
    return matches


# Extract keywords from candidate profile string
def extract_keywords(candidate_profile):
    keywords = []
    for line in candidate_profile.split("\n"):
        if "skills:" in line.lower() or "tools:" in line.lower():
            parts = line.split(":", 1)
            if len(parts) > 1:
                items = [k.strip() for k in parts[1].split(",") if k.strip()]
                keywords.extend(items)
    return keywords


# Score all jobs — pre-filter with keywords, then send top 200 to Claude
def score_all_jobs(candidate_profile, max_claude_calls=200):
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

    # Step 1 — keyword pre-filter in Python (free, instant)
    candidate_keywords = extract_keywords(candidate_profile)
    print(f"Extracted {len(candidate_keywords)} keywords from profile.")
    print(f"Pre-filtering {len(jobs)} jobs...")

    scored_by_keywords = []
    for job_id, title, description, date_fetched, company, location in jobs:
        kw_score = keyword_match_score(candidate_keywords, f"{title} {description}")
        scored_by_keywords.append((kw_score, job_id, title, description, date_fetched, company, location))

    # Sort by keyword score and take top 200
    scored_by_keywords.sort(key=lambda x: x[0], reverse=True)
    top_candidates = scored_by_keywords[:max_claude_calls]
    print(f"Sending top {len(top_candidates)} jobs to Claude for scoring.")

    # Step 2 — Claude scoring on top candidates only
    results = []
    for kw_score, job_id, title, description, date_fetched, company, location in top_candidates:
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