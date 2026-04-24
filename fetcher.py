import requests
import os
from dotenv import load_dotenv

# Load the variables from .env into the environment
load_dotenv()

# Read credentials from environment
APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")


# Fetch analyst job postings from Adzuna for a given location and page number
def fetch_jobs(keyword="data analyst", location="us", page=1, results_per_page=10):
    url = f"https://api.adzuna.com/v1/api/jobs/{location}/search/{page}"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": keyword,
        "results_per_page": results_per_page,
        "content-type": "application/json"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    except requests.exceptions.RequestException as error:
        print(f"API call failed: {error}")
        return []


# Print a summary of each job to the terminal
def display_jobs(jobs):
    if not jobs:
        print("No jobs returned.")
        return

    for job in jobs:
        print("---")
        print(f"Title:    {job.get('title')}")
        print(f"Company:  {job.get('company', {}).get('display_name')}")
        print(f"Location: {job.get('location', {}).get('display_name')}")
        print(f"Salary:   {job.get('salary_min')} - {job.get('salary_max')}")
        print(f"URL:      {job.get('redirect_url')}")


# Entry point — this runs when you execute the script directly
if __name__ == "__main__":
    jobs = fetch_jobs()
    display_jobs(jobs)
    