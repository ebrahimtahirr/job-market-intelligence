# Job Market Intelligence Pipeline

An automated pipeline that pulls analyst job postings daily, extracts structured signals using Claude AI, and surfaces insights via a live interactive dashboard.

## Live Demo
[View Dashboard](https://job-market-intelligence-mingqywwbfrae7gkpxappfe.streamlit.app/)

## What it does
- Fetches Data Analyst and Business Analyst job postings from the Adzuna API
- Stores postings in a SQLite database with automatic deduplication
- Uses Claude (Anthropic) to extract skills, tools, seniority, and remote status from each job description
- Displays trends in an interactive Streamlit dashboard with filters by company, seniority, and work type
- Generates a plain English market briefing using Claude on every dashboard load

## Tech Stack
- Python 3.11
- Anthropic Claude API
- Adzuna Jobs API
- SQLite
- Pandas
- Plotly
- Streamlit

## Access
This project is currently available as a live dashboard only. Drop a comment if you're interested in the setup instructions.