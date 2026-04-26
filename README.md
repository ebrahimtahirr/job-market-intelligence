# Job Market Intelligence Pipeline

An automated AI pipeline that fetches analyst job postings daily, extracts structured signals using Claude, and surfaces actionable insights via a live interactive dashboard.

## Live Demo
[View Dashboard](https://job-market-intelligence-mingqywwbfrae7gkpxappfe.streamlit.app/)

## What it does
- Fetches Data Analyst and Business Analyst job postings daily from the Adzuna API
- Uses Claude (Anthropic) to extract skills, tools, seniority, and remote status from each job description
- Displays trends in an interactive dashboard with filters by company, seniority, and work type
- Generates a plain English market briefing using Claude on every dashboard load
- Scores your resume against all jobs in the database and returns your top 5 matches with ATS keywords
- Lets you paste any job description and get an instant match score and resume tips

## Tech Stack
Python · Claude API · Adzuna API · SQLite · Pandas · Plotly · Streamlit

## Access
Live dashboard available above. Drop a comment if you're interested in how it was built.