import schedule
import time
from pipeline import run_pipeline
from enricher import enrich_jobs


# Run the full pipeline — fetch new jobs and enrich them with Claude
def run_daily_job():
    print("Starting daily pipeline run...")
    run_pipeline()
    enrich_jobs()
    print("Daily run complete.")


# Schedule the job to run once every 24 hours
schedule.every(24).hours.do(run_daily_job)

print("Scheduler started. Pipeline will run every 24 hours.")
print("Running pipeline now for the first time...")

# Run immediately on startup so you don't wait 24 hours for the first result
run_daily_job()

# Keep the script running and check every minute if a job is due
while True:
    schedule.run_pending()
    time.sleep(60)