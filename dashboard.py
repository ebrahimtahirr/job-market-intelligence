import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "jobs.db"
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# Load all enriched jobs from the database into a pandas DataFrame
def load_jobs():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()

    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT title, company, location, salary_min, salary_max,
               skills, tools, experience_years, remote, seniority
        FROM jobs
        WHERE signals_extracted = 1
    """, connection)
    connection.close()
    return df


# Count how often each skill appears across all jobs
def get_top_skills(df, top_n=10):
    skill_counts = {}
    for skill_list in df["skills"].dropna():
        for skill in skill_list.split(","):
            skill = skill.strip().lower()
            if skill:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_skills[:top_n]


# Count how often each tool appears across all jobs
def get_top_tools(df, top_n=10):
    tool_counts = {}
    for tool_list in df["tools"].dropna():
        for tool in tool_list.split(","):
            tool = tool.strip().lower()
            if tool:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
    sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_tools[:top_n]


# Ask Claude to generate a plain English briefing based on the job data
def generate_briefing(df):
    top_skills = get_top_skills(df, top_n=5)
    top_tools = get_top_tools(df, top_n=5)
    remote_count = int(df["remote"].sum())
    total = len(df)
    seniority_counts = df["seniority"].value_counts().to_dict()

    prompt = f"""
You are a job market analyst. Based on the following data from {total} analyst job postings,
write a concise 3-4 sentence market briefing in plain English. No bullet points, just prose.

Top skills: {top_skills}
Top tools: {top_tools}
Remote jobs: {remote_count} out of {total}
Seniority breakdown: {seniority_counts}
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as error:
        return f"Briefing unavailable: {error}"


# --- Dashboard layout ---
st.set_page_config(page_title="Job Market Intelligence", layout="wide")
st.title("Job Market Intelligence Dashboard")
st.caption("Analyst job postings powered by Adzuna + Claude")

df = load_jobs()

if df.empty:
    st.warning("No enriched jobs found. Run enricher.py first.")
else:
    # --- Sidebar filters ---
    st.sidebar.header("Filters")

    all_companies = sorted(df["company"].dropna().unique().tolist())
    selected_companies = st.sidebar.multiselect(
        "Company",
        options=all_companies,
        default=[]
    )

    all_seniority = sorted(df["seniority"].dropna().unique().tolist())
    selected_seniority = st.sidebar.multiselect(
        "Seniority",
        options=all_seniority,
        default=[]
    )

    remote_option = st.sidebar.radio(
        "Work Type",
        options=["All", "Remote Only", "On-site Only"]
    )

    # Apply filters
    filtered_df = df.copy()

    if selected_companies:
        filtered_df = filtered_df[filtered_df["company"].isin(selected_companies)]

    if selected_seniority:
        filtered_df = filtered_df[filtered_df["seniority"].isin(selected_seniority)]

    if remote_option == "Remote Only":
        filtered_df = filtered_df[filtered_df["remote"] == 1]
    elif remote_option == "On-site Only":
        filtered_df = filtered_df[filtered_df["remote"] == 0]

    # --- Key metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jobs", len(filtered_df))
    col2.metric("Remote Jobs", int(filtered_df["remote"].sum()))
    col3.metric("Companies", filtered_df["company"].nunique())

    st.divider()

    # --- Top Skills chart ---
    top_skills = get_top_skills(filtered_df)
    if top_skills:
        skills_df = pd.DataFrame(top_skills, columns=["Skill", "Count"])
        fig_skills = px.bar(skills_df, x="Count", y="Skill", orientation="h",
                            title="Top 10 In-Demand Skills",
                            color="Count", color_continuous_scale="blues")
        fig_skills.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_skills, use_container_width=True)

    # --- Top Tools chart ---
    top_tools = get_top_tools(filtered_df)
    if top_tools:
        tools_df = pd.DataFrame(top_tools, columns=["Tool", "Count"])
        fig_tools = px.bar(tools_df, x="Count", y="Tool", orientation="h",
                           title="Top 10 Tools & Platforms",
                           color="Count", color_continuous_scale="greens")
        fig_tools.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_tools, use_container_width=True)

    # --- Seniority breakdown ---
    seniority_df = filtered_df["seniority"].value_counts().reset_index()
    seniority_df.columns = ["Seniority", "Count"]
    if not seniority_df.empty:
        fig_seniority = px.pie(seniority_df, names="Seniority", values="Count",
                               title="Seniority Breakdown")
        st.plotly_chart(fig_seniority, use_container_width=True)

    st.divider()

    # --- Claude briefing ---
    st.subheader("Daily Market Briefing")
    with st.spinner("Generating briefing..."):
        briefing = generate_briefing(filtered_df)
    st.write(briefing)

    st.divider()

    # --- Raw data table ---
    st.subheader("Job Listings")
    st.dataframe(
        filtered_df[["title", "company", "location", "seniority", "remote", "skills"]],
        use_container_width=True
    )