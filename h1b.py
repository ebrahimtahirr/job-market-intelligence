import pandas as pd
import sqlite3

DB_PATH = "jobs.db"
H1B_FILE = "h1b_datahubexport-2023.csv"


# Load H1B sponsors from USCIS data into a set of company names
def load_h1b_sponsors():
    df = pd.read_csv(H1B_FILE)

    # Keep only companies with at least 1 initial approval
    sponsors = df[df["Initial Approval"] > 0]["Employer"].dropna()

    # Normalize to lowercase for matching
    sponsor_set = set(sponsors.str.lower().str.strip())
    print(f"Loaded {len(sponsor_set)} H1B sponsors from USCIS data.")
    return sponsor_set


# Add h1b_sponsor column to jobs table if it doesn't exist
def add_h1b_column():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN h1b_sponsor INTEGER DEFAULT NULL")
        connection.commit()
        print("Added h1b_sponsor column.")
    except sqlite3.OperationalError:
        pass
    connection.close()


# Match each job's company against the H1B sponsor list and label it
def label_h1b_sponsors():
    sponsor_set = load_h1b_sponsors()
    add_h1b_column()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT job_id, company FROM jobs WHERE company IS NOT NULL")
    jobs = cursor.fetchall()

    matched = 0
    for job_id, company in jobs:
        company_normalized = company.lower().strip()
        is_sponsor = 1 if company_normalized in sponsor_set else 0
        cursor.execute(
            "UPDATE jobs SET h1b_sponsor = ? WHERE job_id = ?",
            (is_sponsor, job_id)
        )
        if is_sponsor:
            matched += 1

    connection.commit()
    connection.close()
    print(f"Labeled {matched} jobs as H1B sponsors out of {len(jobs)} total.")


if __name__ == "__main__":
    label_h1b_sponsors()