import sqlite3
import os

DB_PATH = "jobs.db"


# Create the database and jobs table if they don't already exist
def initialize_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE,
            title TEXT,
            company TEXT,
            location TEXT,
            salary_min REAL,
            salary_max REAL,
            description TEXT,
            url TEXT,
            date_fetched TEXT,
            skills TEXT,
            tools TEXT,
            experience_years TEXT,
            remote INTEGER,
            seniority TEXT,
            signals_extracted INTEGER DEFAULT 0
        )
    """)

    connection.commit()
    connection.close()
    print("Database initialized.")


# Add new columns to an existing database that was created without them
def migrate_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    new_columns = [
        ("skills", "TEXT"),
        ("tools", "TEXT"),
        ("experience_years", "TEXT"),
        ("remote", "INTEGER"),
        ("seniority", "TEXT"),
        ("signals_extracted", "INTEGER DEFAULT 0")
    ]

    for column_name, column_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} {column_type}")
            print(f"Added column: {column_name}")
        except sqlite3.OperationalError:
            pass

    connection.commit()
    connection.close()
    print("Migration complete.")


# Insert a single job into the database, skip it if it already exists
def insert_job(job):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO jobs (
                job_id, title, company, location,
                salary_min, salary_max, description, url, date_fetched
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("id"),
            job.get("title"),
            job.get("company", {}).get("display_name"),
            job.get("location", {}).get("display_name"),
            job.get("salary_min"),
            job.get("salary_max"),
            job.get("description"),
            job.get("redirect_url"),
            job.get("created")
        ))

        connection.commit()

    except sqlite3.Error as error:
        print(f"Failed to insert job: {error}")

    finally:
        connection.close()


# Insert a list of jobs into the database
def insert_jobs(jobs):
    for job in jobs:
        insert_job(job)
    print(f"{len(jobs)} jobs processed.")


# Save extracted signals back to the correct job row
def save_signals(job_id, signals):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE jobs
            SET skills = ?,
                tools = ?,
                experience_years = ?,
                remote = ?,
                seniority = ?,
                signals_extracted = 1
            WHERE job_id = ?
        """, (
            ", ".join(signals.get("skills", [])),
            ", ".join(signals.get("tools", [])),
            str(signals.get("experience_years")),
            1 if signals.get("remote") else 0,
            signals.get("seniority"),
            job_id
        ))

        connection.commit()

    except sqlite3.Error as error:
        print(f"Failed to save signals: {error}")

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    migrate_database()