from fetcher import fetch_jobs
from database import initialize_database, insert_jobs


# Run the full pipeline: fetch jobs from Adzuna and save them to the database
def run_pipeline(keyword="data analyst OR business analyst", location="us", pages=3):
    initialize_database()

    total_jobs = []

    for page in range(1, pages + 1):
        print(f"Fetching page {page}...")
        jobs = fetch_jobs(keyword=keyword, location=location, page=page)
        total_jobs.extend(jobs)

    print(f"Total jobs fetched: {len(total_jobs)}")
    insert_jobs(total_jobs)
    print("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()