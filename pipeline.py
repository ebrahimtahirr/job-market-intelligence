from fetcher import fetch_jobs
from database import initialize_database, insert_jobs

# Job titles to search for
KEYWORDS = [
    "data analyst",
    "business analyst",
    "market insights analyst",
    "strategy analyst",
    "reporting analyst",
    "operations analyst",
    "financial analyst",
    "product analyst"
]


# Run the full pipeline — fetch jobs for all keywords and save to database
def run_pipeline(location="us", pages=5, results_per_page=50):
    initialize_database()

    total_jobs = []

    for keyword in KEYWORDS:
        print(f"Fetching jobs for: {keyword}")
        for page in range(1, pages + 1):
            print(f"  Page {page}...")
            jobs = fetch_jobs(
                keyword=keyword,
                location=location,
                page=page,
                results_per_page=results_per_page
            )
            total_jobs.extend(jobs)

    print(f"Total jobs fetched: {len(total_jobs)}")
    insert_jobs(total_jobs)
    print("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()