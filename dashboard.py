import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import anthropic
import os
import json
from dotenv import load_dotenv
from scorer import score_all_jobs

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
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Jobs", len(filtered_df))
    col2.metric("Remote Jobs", int(filtered_df["remote"].sum()))
    col3.metric("Companies", filtered_df["company"].nunique())
    col4.metric("Avg Salary", f"${filtered_df['salary_min'].mean():,.0f}"
                if filtered_df["salary_min"].notna().any() else "N/A")

    st.divider()

    # --- Row 1: Skills and Tools side by side ---
    col_left, col_right = st.columns(2)

    with col_left:
        top_skills = get_top_skills(filtered_df)
        if top_skills:
            skills_df = pd.DataFrame(top_skills, columns=["Skill", "Count"])
            fig_skills = px.bar(skills_df, x="Count", y="Skill", orientation="h",
                                title="Top 10 In-Demand Skills",
                                color="Count", color_continuous_scale="blues")
            fig_skills.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_skills, use_container_width=True)

    with col_right:
        top_tools = get_top_tools(filtered_df)
        if top_tools:
            tools_df = pd.DataFrame(top_tools, columns=["Tool", "Count"])
            fig_tools = px.bar(tools_df, x="Count", y="Tool", orientation="h",
                               title="Top 10 Tools & Platforms",
                               color="Count", color_continuous_scale="greens")
            fig_tools.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_tools, use_container_width=True)

    st.divider()

    # --- Row 2: Salary by seniority and seniority breakdown side by side ---
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        salary_df = filtered_df[
            (filtered_df["salary_min"].notna()) &
            (filtered_df["salary_min"] > 0) &
            (filtered_df["seniority"].notna())
        ].copy()

        if not salary_df.empty:
            salary_grouped = salary_df.groupby("seniority").agg(
                avg_salary_min=("salary_min", "mean"),
                avg_salary_max=("salary_max", "mean")
            ).reset_index()

            fig_salary = px.bar(
                salary_grouped,
                x="seniority",
                y=["avg_salary_min", "avg_salary_max"],
                title="Average Salary Range by Seniority",
                barmode="group",
                labels={"value": "Salary (USD)", "seniority": "Seniority"},
                color_discrete_sequence=["#636EFA", "#EF553B"]
            )
            st.plotly_chart(fig_salary, use_container_width=True)
        else:
            st.info("Not enough salary data to display this chart.")

    with col_right2:
        seniority_df = filtered_df["seniority"].value_counts().reset_index()
        seniority_df.columns = ["Seniority", "Count"]
        if not seniority_df.empty:
            fig_seniority = px.pie(seniority_df, names="Seniority", values="Count",
                                   title="Seniority Breakdown")
            st.plotly_chart(fig_seniority, use_container_width=True)

    st.divider()

    # --- Top hiring locations ---
    bad_locations = ["us", "uk", "canada", "remote", "united states"]
    location_df = filtered_df[
        ~filtered_df["location"].str.lower().isin(bad_locations)
    ]["location"].value_counts().reset_index().head(10)
    location_df.columns = ["Location", "Count"]
    if not location_df.empty:
        fig_location = px.bar(location_df, x="Count", y="Location", orientation="h",
                              title="Top 10 Hiring Locations",
                              color="Count", color_continuous_scale="oranges")
        fig_location.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_location, use_container_width=True)

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

    st.divider()

    # --- Job Fit Scorer ---
    st.subheader("Job Fit Scorer")

    scorer_tab1, scorer_tab2 = st.tabs(["Match Against Database", "Match Against Custom Job"])

    # --- Tab 1: Match against database ---
    with scorer_tab1:
        st.caption("Upload your resume and Claude will score the top 5 matching jobs from the database, prioritizing recent postings.")

        uploaded_resume = st.file_uploader("Upload your resume (PDF)", type=["pdf"], key="resume_db")

        if uploaded_resume is not None:
            if st.button("Score Jobs", key="score_db"):
                with st.spinner("Reading your resume..."):
                    try:
                        import PyPDF2
                        pdf_reader = PyPDF2.PdfReader(uploaded_resume)
                        resume_text = ""
                        for page in pdf_reader.pages:
                            resume_text += page.extract_text()

                        if not resume_text.strip():
                            st.error("Could not extract text from your resume. Make sure it is not a scanned image.")
                            st.stop()

                    except Exception as error:
                        st.error(f"Failed to read PDF: {error}")
                        st.stop()

                with st.spinner("Claude is reading your resume..."):
                    try:
                        profile_prompt = f"""
Read this resume and extract a candidate profile. Return JSON only — no explanation, no markdown:

{{
  "years_experience": "number or null",
  "skills": ["list of analytical and business skills"],
  "tools": ["list of software tools and platforms"],
  "industry": "industry background in a few words",
  "seniority": "entry, mid, or senior"
}}

Resume:
{resume_text[:3000]}
"""
                        profile_message = client.messages.create(
                            model="claude-sonnet-4-5",
                            max_tokens=512,
                            messages=[{"role": "user", "content": profile_prompt}]
                        )
                        raw_profile = profile_message.content[0].text
                        cleaned_profile = raw_profile.strip()
                        if cleaned_profile.startswith("```"):
                            cleaned_profile = cleaned_profile.split("\n", 1)[1]
                        if cleaned_profile.endswith("```"):
                            cleaned_profile = cleaned_profile.rsplit("\n", 1)[0]

                        candidate = json.loads(cleaned_profile)

                        st.success("Resume read successfully.")
                        st.markdown(f"**Detected profile:** {candidate.get('seniority')} level | {candidate.get('years_experience')} years | {candidate.get('industry')}")
                        st.markdown(f"**Skills found:** {', '.join(candidate.get('skills', []))}")
                        st.markdown(f"**Tools found:** {', '.join(candidate.get('tools', []))}")

                    except Exception as error:
                        st.error(f"Failed to extract profile from resume: {error}")
                        st.stop()

                candidate_profile = f"""
Years of experience: {candidate.get('years_experience')}
Seniority: {candidate.get('seniority')}
Industry: {candidate.get('industry')}
Skills: {', '.join(candidate.get('skills', []))}
Tools: {', '.join(candidate.get('tools', []))}
"""
                with st.spinner("Scoring all jobs against your profile..."):
                    scored_jobs = score_all_jobs(candidate_profile)

                top_5 = scored_jobs[:5]
                st.success(f"Top 5 matches out of {len(scored_jobs)} jobs.")

                for job in top_5:
                    score = job["final_score"]
                    relevance = job["relevance_score"]
                    hours_ago = job["hours_ago"]
                    color = "green" if score >= 70 else "orange" if score >= 50 else "red"

                    if hours_ago <= 24:
                        recency_label = "🟢 Posted in last 24 hours"
                    elif hours_ago <= 72:
                        recency_label = "🟡 Posted in last 3 days"
                    elif hours_ago <= 168:
                        recency_label = "🟠 Posted in last week"
                    else:
                        recency_label = "⚪ Posted over a week ago"

                    st.markdown(f"**{job['title']}** — {job.get('company', 'Unknown')} — {job.get('location', 'Unknown')}")
                    st.markdown(f":{color}[Score: {score}/100] (Relevance: {relevance}/100) | {recency_label}")
                    st.markdown(f"✅ {' | '.join(job['match_reasons'])}")
                    st.markdown(f"⚠️ {' | '.join(job['gap_reasons'])}")
                    st.divider()

                st.subheader("ATS Keywords & Resume Tips")
                with st.spinner("Generating ATS keywords..."):
                    top_5_summary = "\n".join([
                        f"Job: {j['title']} | Matches: {j['match_reasons']} | Gaps: {j['gap_reasons']}"
                        for j in top_5
                    ])
                    ats_prompt = f"""
You are a resume expert. Based on these top 5 job matches for a candidate with these skills: {', '.join(candidate.get('skills', []))}, return JSON only:

{{
  "must_have_keywords": ["top 8 keywords to add to resume immediately"],
  "nice_to_have_keywords": ["5 keywords that would strengthen the resume"],
  "resume_tips": ["3 specific actionable tips to improve the resume for these roles"]
}}

Job match data:
{top_5_summary}
"""
                    try:
                        ats_message = client.messages.create(
                            model="claude-sonnet-4-5",
                            max_tokens=512,
                            messages=[{"role": "user", "content": ats_prompt}]
                        )
                        raw_ats = ats_message.content[0].text
                        cleaned_ats = raw_ats.strip()
                        if cleaned_ats.startswith("```"):
                            cleaned_ats = cleaned_ats.split("\n", 1)[1]
                        if cleaned_ats.endswith("```"):
                            cleaned_ats = cleaned_ats.rsplit("\n", 1)[0]

                        ats_data = json.loads(cleaned_ats)
                        col_ats1, col_ats2 = st.columns(2)

                        with col_ats1:
                            st.markdown("**Must-Have Keywords**")
                            for kw in ats_data.get("must_have_keywords", []):
                                st.markdown(f"- {kw}")
                            st.markdown("**Nice-to-Have Keywords**")
                            for kw in ats_data.get("nice_to_have_keywords", []):
                                st.markdown(f"- {kw}")

                        with col_ats2:
                            st.markdown("**Resume Tips**")
                            for tip in ats_data.get("resume_tips", []):
                                st.markdown(f"- {tip}")

                    except Exception as error:
                        st.error(f"ATS generation failed: {error}")

    # --- Tab 2: Match against custom job ---
    with scorer_tab2:
        st.caption("Upload your resume and paste any job description to get a match score and ATS keywords.")

        uploaded_resume_custom = st.file_uploader("Upload your resume (PDF)", type=["pdf"], key="resume_custom")
        custom_job = st.text_area("Paste the job description here", height=200,
                                  placeholder="Copy and paste the full job description from LinkedIn, a company website, or anywhere else...")

        if uploaded_resume_custom is not None and custom_job.strip():
            if st.button("Score This Job", key="score_custom"):
                with st.spinner("Reading your resume..."):
                    try:
                        import PyPDF2
                        pdf_reader = PyPDF2.PdfReader(uploaded_resume_custom)
                        resume_text_custom = ""
                        for page in pdf_reader.pages:
                            resume_text_custom += page.extract_text()

                        if not resume_text_custom.strip():
                            st.error("Could not extract text from your resume.")
                            st.stop()

                    except Exception as error:
                        st.error(f"Failed to read PDF: {error}")
                        st.stop()

                with st.spinner("Claude is analyzing your resume and the job description..."):
                    try:
                        custom_score_prompt = f"""
You are a recruiting analyst. Score how well this candidate matches this specific job posting.

Resume:
{resume_text_custom[:2000]}

Job description:
{custom_job[:2000]}

Return JSON only — no explanation, no markdown:
{{
  "score": <integer from 0 to 100>,
  "match_reasons": ["up to 3 specific reasons they are a good match"],
  "gap_reasons": ["up to 3 specific gaps or weaknesses"],
  "must_have_keywords": ["top 8 keywords from this job to add to the resume"],
  "nice_to_have_keywords": ["5 keywords that would strengthen the resume for this role"],
  "resume_tips": ["3 specific actionable tips to tailor the resume for this exact job"]
}}
"""
                        custom_message = client.messages.create(
                            model="claude-sonnet-4-5",
                            max_tokens=512,
                            messages=[{"role": "user", "content": custom_score_prompt}]
                        )
                        raw_custom = custom_message.content[0].text
                        cleaned_custom = raw_custom.strip()
                        if cleaned_custom.startswith("```"):
                            cleaned_custom = cleaned_custom.split("\n", 1)[1]
                        if cleaned_custom.endswith("```"):
                            cleaned_custom = cleaned_custom.rsplit("\n", 1)[0]

                        custom_result = json.loads(cleaned_custom)

                        score = custom_result.get("score", 0)
                        color = "green" if score >= 70 else "orange" if score >= 50 else "red"

                        st.markdown(f"### Match Score: :{color}[{score}/100]")
                        st.markdown(f"✅ {' | '.join(custom_result.get('match_reasons', []))}")
                        st.markdown(f"⚠️ {' | '.join(custom_result.get('gap_reasons', []))}")

                        st.divider()
                        st.subheader("ATS Keywords & Resume Tips")

                        col_c1, col_c2 = st.columns(2)

                        with col_c1:
                            st.markdown("**Must-Have Keywords**")
                            for kw in custom_result.get("must_have_keywords", []):
                                st.markdown(f"- {kw}")
                            st.markdown("**Nice-to-Have Keywords**")
                            for kw in custom_result.get("nice_to_have_keywords", []):
                                st.markdown(f"- {kw}")

                        with col_c2:
                            st.markdown("**Resume Tips**")
                            for tip in custom_result.get("resume_tips", []):
                                st.markdown(f"- {tip}")

                    except Exception as error:
                        st.error(f"Analysis failed: {error}")