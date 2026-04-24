import sqlite3
import json
from database import save_signals
from extractor import extract_signals

DB_PATH = "jobs.db"


# Fetch all jobs from the database that haven't been enriched yet
def get_unenriched_jobs():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT job_id, description
        FROM jobs
        WHERE signals_extracted = 0
        AND description IS NOT NULL
    """)

    jobs = cursor.fetchall()
    connection.close()
    return jobs


# Run Claude extraction on all unenriched jobs and save results
def enrich_jobs():
    jobs = get_unenriched_jobs()
    print(f"Found {len(jobs)} jobs to enrich.")

    for index, (job_id, description) in enumerate(jobs):
        print(f"Enriching job {index + 1} of {len(jobs)}...")

        raw_response = extract_signals(description)

        if raw_response is None:
            print(f"Skipping job {job_id} — no response from Claude.")
            continue

        try:
            # Strip markdown code fences if Claude included them
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.split("\n", 1)[1]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response.rsplit("\n", 1)[0]

            signals = json.loads(cleaned_response)
            save_signals(job_id, signals)

        except json.JSONDecodeError:
            print(f"Skipping job {job_id} — Claude returned invalid JSON.")
            continue
        
            
            

        
            
            

    print("Enrichment complete.")


if __name__ == "__main__":
    enrich_jobs()