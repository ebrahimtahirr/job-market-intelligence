import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import anthropic
import os
import json
from dotenv import load_dotenv
from scorer import score_all_jobs

load_dotenv()

DB_PATH = "jobs.db"
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Page config ---
st.set_page_config(
    page_title="JobLens — Analyst Market Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    /* Base */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #0A0A0F;
        color: #E8E8F0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main container */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #0D0D1A 0%, #111128 50%, #0A0A0F 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .hero-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }

    .hero-title {
        font-family: 'Syne', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FFFFFF 0%, #A5B4FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.1;
    }

    .hero-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: #6B7280;
        margin-top: 0.5rem;
        font-weight: 300;
        letter-spacing: 0.05em;
    }

    .hero-badge {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(99, 102, 241, 0.3);
        color: #A5B4FC;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #111128 0%, #0F0F20 100%);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: border-color 0.2s ease;
    }

    .metric-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
    }

    .metric-value {
        font-family: 'Syne', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1;
    }

    .metric-label {
        font-size: 0.8rem;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.4rem;
        font-weight: 500;
    }

    .metric-accent {
        color: #818CF8;
    }

    /* Section headers */
    .section-header {
        font-family: 'Syne', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(99, 102, 241, 0.2);
    }

    /* Briefing card */
    .briefing-card {
        background: linear-gradient(135deg, #111128 0%, #0F0F20 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-left: 3px solid #6366F1;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        font-size: 1rem;
        line-height: 1.8;
        color: #C4C4D4;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0D0D1A;
        border-right: 1px solid rgba(99, 102, 241, 0.15);
    }

    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.5rem;
    }

    .sidebar-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(99, 102, 241, 0.2);
    }

    /* H1B toggle */
    .h1b-toggle {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .h1b-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #10B981;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* Job score cards */
    .job-card {
        background: linear-gradient(135deg, #111128 0%, #0F0F20 100%);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s ease;
    }

    .job-card:hover {
        border-color: rgba(99, 102, 241, 0.35);
    }

    .job-title {
        font-family: 'Syne', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #FFFFFF;
    }

    .job-meta {
        font-size: 0.85rem;
        color: #6B7280;
        margin-top: 0.25rem;
    }

    .score-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .score-high { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
    .score-mid { background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); }
    .score-low { background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }

    .recency-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-left: 0.5rem;
    }

    .recency-hot { background: rgba(16, 185, 129, 0.1); color: #10B981; }
    .recency-warm { background: rgba(245, 158, 11, 0.1); color: #F59E0B; }
    .recency-cool { background: rgba(156, 163, 175, 0.1); color: #9CA3AF; }

    /* ATS keyword pills */
    .keyword-pill {
        display: inline-block;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.25);
        color: #A5B4FC;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.2rem;
    }

    .keyword-pill-secondary {
        display: inline-block;
        background: rgba(75, 85, 99, 0.2);
        border: 1px solid rgba(75, 85, 99, 0.3);
        color: #9CA3AF;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.2rem;
    }

    /* Divider */
    .custom-divider {
        border: none;
        border-top: 1px solid rgba(99, 102, 241, 0.12);
        margin: 2rem 0;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #111128;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #6B7280;
        border-radius: 8px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(99, 102, 241, 0.2);
        color: #A5B4FC;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        padding: 0.5rem 2rem;
        transition: opacity 0.2s ease;
    }

    .stButton > button:hover {
        opacity: 0.85;
    }
</style>
""", unsafe_allow_html=True)


# --- Data loading ---
def load_jobs():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    connection = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT title, company, location, salary_min, salary_max,
               skills, tools, experience_years, remote, seniority, h1b_sponsor
        FROM jobs
        WHERE signals_extracted = 1
    """, connection)
    connection.close()
    return df


def get_top_skills(df, top_n=10):
    skill_counts = {}
    for skill_list in df["skills"].dropna():
        for skill in skill_list.split(","):
            skill = skill.strip().lower()
            if skill:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
    return sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]


def get_top_tools(df, top_n=10):
    tool_counts = {}
    for tool_list in df["tools"].dropna():
        for tool in tool_list.split(","):
            tool = tool.strip().lower()
            if tool:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
    return sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]


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


# --- Plotly chart theme ---
CHART_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#9CA3AF", "family": "DM Sans"},
    "xaxis": {"gridcolor": "rgba(99,102,241,0.08)", "showline": False},
    "yaxis": {"gridcolor": "rgba(99,102,241,0.08)", "showline": False},
    "margin": {"l": 20, "r": 20, "t": 40, "b": 20}
}


# =====================
# SIDEBAR
# =====================
with st.sidebar:
    st.markdown('<div class="sidebar-title">🔍 JobLens</div>', unsafe_allow_html=True)

    st.markdown("**Filters**")

    df_full = load_jobs()

    all_companies = sorted(df_full["company"].dropna().unique().tolist())
    selected_companies = st.multiselect("Company", options=all_companies, default=[])

    all_seniority = sorted(df_full["seniority"].dropna().unique().tolist())
    selected_seniority = st.multiselect("Seniority Level", options=all_seniority, default=[])

    remote_option = st.radio("Work Type", options=["All", "Remote Only", "On-site Only"])

    st.markdown('<div class="h1b-toggle">', unsafe_allow_html=True)
    st.markdown('<div class="h1b-label">🟢 H1B Sponsorship</div>', unsafe_allow_html=True)
    h1b_only = st.toggle("Show H1B sponsors only", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<span style="font-size:0.75rem;color:#4B5563;">Data updated daily via Adzuna API<br>Signals extracted by Claude AI</span>', unsafe_allow_html=True)


# =====================
# MAIN CONTENT
# =====================

# Apply filters
df = df_full.copy()

if selected_companies:
    df = df[df["company"].isin(selected_companies)]
if selected_seniority:
    df = df[df["seniority"].isin(selected_seniority)]
if remote_option == "Remote Only":
    df = df[df["remote"] == 1]
elif remote_option == "On-site Only":
    df = df[df["remote"] == 0]
if h1b_only:
    df = df[df["h1b_sponsor"] == 1]

if df.empty:
    st.warning("No jobs match your current filters.")
    st.stop()

# --- Hero ---
st.markdown(f"""
<div class="hero-header">
    <div class="hero-badge">Live Market Intelligence</div>
    <div class="hero-title">Analyst Job Market<br>Intelligence</div>
    <div class="hero-subtitle">Powered by Adzuna API · Signals extracted by Claude AI · Updated daily</div>
</div>
""", unsafe_allow_html=True)

# --- Metrics ---
h1b_count = int(df["h1b_sponsor"].sum()) if "h1b_sponsor" in df.columns else 0
avg_salary = f"${df['salary_min'].mean():,.0f}" if df["salary_min"].notna().any() else "N/A"

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df)}</div><div class="metric-label">Total Jobs</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{int(df["remote"].sum())}</div><div class="metric-label">Remote Jobs</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-value">{df["company"].nunique()}</div><div class="metric-label">Companies</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-value metric-accent">{avg_salary}</div><div class="metric-label">Avg Salary</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#10B981">{h1b_count}</div><div class="metric-label">H1B Sponsors</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Charts Row 1: Skills + Tools ---
st.markdown('<div class="section-header">Market Signals</div>', unsafe_allow_html=True)
col_l, col_r = st.columns(2)

with col_l:
    top_skills = get_top_skills(df)
    if top_skills:
        skills_df = pd.DataFrame(top_skills, columns=["Skill", "Count"])
        fig = px.bar(skills_df, x="Count", y="Skill", orientation="h",
                     title="Top 10 In-Demand Skills",
                     color="Count", color_continuous_scale=["#1E1B4B", "#6366F1", "#A5B4FC"])
        fig.update_layout(**CHART_THEME, title_font={"size": 14, "color": "#E8E8F0"})
        fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    top_tools = get_top_tools(df)
    if top_tools:
        tools_df = pd.DataFrame(top_tools, columns=["Tool", "Count"])
        fig = px.bar(tools_df, x="Count", y="Tool", orientation="h",
                     title="Top 10 Tools & Platforms",
                     color="Count", color_continuous_scale=["#064E3B", "#10B981", "#6EE7B7"])
        fig.update_layout(**CHART_THEME, title_font={"size": 14, "color": "#E8E8F0"})
        fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# --- Charts Row 2: Salary + Seniority ---
col_l2, col_r2 = st.columns(2)

with col_l2:
    salary_df = df[
        (df["salary_min"].notna()) &
        (df["salary_min"] > 0) &
        (df["seniority"].notna())
    ].copy()

    if not salary_df.empty:
        salary_grouped = salary_df.groupby("seniority").agg(
            avg_salary_min=("salary_min", "mean"),
            avg_salary_max=("salary_max", "mean")
        ).reset_index()

        fig = px.bar(salary_grouped, x="seniority",
                     y=["avg_salary_min", "avg_salary_max"],
                     title="Salary Range by Seniority",
                     barmode="group",
                     labels={"value": "Salary (USD)", "seniority": "Level"},
                     color_discrete_sequence=["#4F46E5", "#818CF8"])
        fig.update_layout(**CHART_THEME, title_font={"size": 14, "color": "#E8E8F0"})
        st.plotly_chart(fig, use_container_width=True)

with col_r2:
    seniority_df = df["seniority"].value_counts().reset_index()
    seniority_df.columns = ["Seniority", "Count"]
    if not seniority_df.empty:
        fig = px.pie(seniority_df, names="Seniority", values="Count",
                     title="Seniority Breakdown",
                     color_discrete_sequence=["#4F46E5", "#818CF8", "#C7D2FE", "#E0E7FF"])
        fig.update_layout(**CHART_THEME, title_font={"size": 14, "color": "#E8E8F0"})
        fig.update_traces(textfont_color="white")
        st.plotly_chart(fig, use_container_width=True)

# --- Locations ---
bad_locations = ["us", "uk", "canada", "remote", "united states"]
location_df = df[
    ~df["location"].str.lower().isin(bad_locations)
]["location"].value_counts().reset_index().head(10)
location_df.columns = ["Location", "Count"]

if not location_df.empty:
    fig = px.bar(location_df, x="Count", y="Location", orientation="h",
                 title="Top 10 Hiring Locations",
                 color="Count", color_continuous_scale=["#431407", "#F97316", "#FED7AA"])
    fig.update_layout(**CHART_THEME, title_font={"size": 14, "color": "#E8E8F0"})
    fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# --- Briefing ---
st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
st.markdown('<div class="section-header">Daily Market Briefing</div>', unsafe_allow_html=True)

with st.spinner("Generating briefing..."):
    briefing = generate_briefing(df)

st.markdown(f'<div class="briefing-card">{briefing}</div>', unsafe_allow_html=True)

# --- Job Fit Scorer ---
st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
st.markdown('<div class="section-header">Job Fit Scorer</div>', unsafe_allow_html=True)

scorer_tab1, scorer_tab2 = st.tabs(["Match Against Database", "Match Against Custom Job"])

with scorer_tab1:
    st.caption("Upload your resume — Claude reads it, scores every job in the database, and returns your top 5 matches prioritized by recency and relevance.")

    uploaded_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"], key="resume_db")

    if uploaded_resume is not None:
        if st.button("Find My Top Matches", key="score_db"):
            with st.spinner("Reading your resume..."):
                try:
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(uploaded_resume)
                    resume_text = ""
                    for page in pdf_reader.pages:
                        resume_text += page.extract_text()
                    if not resume_text.strip():
                        st.error("Could not extract text. Make sure your resume is not a scanned image.")
                        st.stop()
                except Exception as e:
                    st.error(f"Failed to read PDF: {e}")
                    st.stop()

            with st.spinner("Claude is reading your resume..."):
                try:
                    profile_message = client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=512,
                        messages=[{"role": "user", "content": f"""
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
"""}]
                    )
                    raw = profile_message.content[0].text.strip()
                    if raw.startswith("```"): raw = raw.split("\n", 1)[1]
                    if raw.endswith("```"): raw = raw.rsplit("\n", 1)[0]
                    candidate = json.loads(raw)

                    st.success("Resume read successfully.")
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Seniority", candidate.get('seniority', 'N/A').title())
                    col_b.metric("Experience", f"{candidate.get('years_experience', 'N/A')} years")
                    col_c.metric("Industry", candidate.get('industry', 'N/A'))

                    with st.expander("Detected Skills & Tools"):
                        st.markdown(f"**Skills:** {', '.join(candidate.get('skills', []))}")
                        st.markdown(f"**Tools:** {', '.join(candidate.get('tools', []))}")

                except Exception as e:
                    st.error(f"Failed to extract profile: {e}")
                    st.stop()

            candidate_profile = f"""
Years of experience: {candidate.get('years_experience')}
Seniority: {candidate.get('seniority')}
Industry: {candidate.get('industry')}
Skills: {', '.join(candidate.get('skills', []))}
Tools: {', '.join(candidate.get('tools', []))}
"""
            with st.spinner("Scoring all jobs..."):
                scored_jobs = score_all_jobs(candidate_profile)

            top_5 = scored_jobs[:5]
            st.success(f"Top 5 matches from {len(scored_jobs)} jobs")

            for job in top_5:
                score = job["final_score"]
                relevance = job["relevance_score"]
                hours_ago = job["hours_ago"]

                score_class = "score-high" if score >= 70 else "score-mid" if score >= 50 else "score-low"

                if hours_ago <= 24:
                    recency_html = '<span class="recency-badge recency-hot">🟢 Last 24h</span>'
                elif hours_ago <= 72:
                    recency_html = '<span class="recency-badge recency-warm">🟡 Last 3 days</span>'
                elif hours_ago <= 168:
                    recency_html = '<span class="recency-badge recency-warm">🟠 Last week</span>'
                else:
                    recency_html = '<span class="recency-badge recency-cool">⚪ Older</span>'

                st.markdown(f"""
<div class="job-card">
    <div class="job-title">{job['title']}</div>
    <div class="job-meta">{job.get('company', 'Unknown')} · {job.get('location', 'Unknown')}</div>
    <div style="margin-top:0.75rem;">
        <span class="score-badge {score_class}">Score: {score}/100</span>
        <span style="font-size:0.75rem;color:#6B7280;margin-left:0.5rem;">Relevance: {relevance}/100</span>
        {recency_html}
    </div>
    <div style="margin-top:0.75rem;font-size:0.85rem;color:#10B981;">✅ {' | '.join(job['match_reasons'])}</div>
    <div style="margin-top:0.4rem;font-size:0.85rem;color:#F59E0B;">⚠️ {' | '.join(job['gap_reasons'])}</div>
</div>
""", unsafe_allow_html=True)

            # ATS Keywords
            st.markdown('<div class="section-header" style="margin-top:2rem;">ATS Keywords & Resume Tips</div>', unsafe_allow_html=True)
            with st.spinner("Generating ATS keywords..."):
                top_5_summary = "\n".join([
                    f"Job: {j['title']} | Matches: {j['match_reasons']} | Gaps: {j['gap_reasons']}"
                    for j in top_5
                ])
                try:
                    ats_message = client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=512,
                        messages=[{"role": "user", "content": f"""
You are a resume expert. Return JSON only:

{{
  "must_have_keywords": ["top 8 keywords to add to resume immediately"],
  "nice_to_have_keywords": ["5 keywords that would strengthen the resume"],
  "resume_tips": ["3 specific actionable tips"]
}}

Candidate skills: {', '.join(candidate.get('skills', []))}
Job matches: {top_5_summary}
"""}]
                    )
                    raw_ats = ats_message.content[0].text.strip()
                    if raw_ats.startswith("```"): raw_ats = raw_ats.split("\n", 1)[1]
                    if raw_ats.endswith("```"): raw_ats = raw_ats.rsplit("\n", 1)[0]
                    ats_data = json.loads(raw_ats)

                    col_k1, col_k2 = st.columns(2)
                    with col_k1:
                        st.markdown("**Must-Have Keywords**")
                        keywords_html = "".join([f'<span class="keyword-pill">{kw}</span>' for kw in ats_data.get("must_have_keywords", [])])
                        st.markdown(keywords_html, unsafe_allow_html=True)

                        st.markdown("<br>**Nice-to-Have Keywords**", unsafe_allow_html=True)
                        secondary_html = "".join([f'<span class="keyword-pill-secondary">{kw}</span>' for kw in ats_data.get("nice_to_have_keywords", [])])
                        st.markdown(secondary_html, unsafe_allow_html=True)

                    with col_k2:
                        st.markdown("**Resume Tips**")
                        for i, tip in enumerate(ats_data.get("resume_tips", []), 1):
                            st.markdown(f"""
<div style="background:rgba(99,102,241,0.08);border-left:2px solid #6366F1;padding:0.75rem 1rem;border-radius:0 8px 8px 0;margin-bottom:0.5rem;font-size:0.85rem;color:#C4C4D4;">
{i}. {tip}
</div>""", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"ATS generation failed: {e}")

with scorer_tab2:
    st.caption("Paste any job description from LinkedIn or any company website and get an instant match score tailored to your resume.")

    uploaded_resume_custom = st.file_uploader("Upload Resume (PDF)", type=["pdf"], key="resume_custom")
    custom_job = st.text_area("Paste Job Description", height=200,
                              placeholder="Copy and paste the full job description here...")

    if uploaded_resume_custom is not None and custom_job.strip():
        if st.button("Analyze This Job", key="score_custom"):
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
                except Exception as e:
                    st.error(f"Failed to read PDF: {e}")
                    st.stop()

            with st.spinner("Analyzing match..."):
                try:
                    custom_message = client.messages.create(
                        model="claude-sonnet-4-5",
                        max_tokens=512,
                        messages=[{"role": "user", "content": f"""
You are a recruiting analyst. Score how well this candidate matches this job.

Resume:
{resume_text_custom[:2000]}

Job description:
{custom_job[:2000]}

Return JSON only:
{{
  "score": <0-100>,
  "match_reasons": ["up to 3 match reasons"],
  "gap_reasons": ["up to 3 gaps"],
  "must_have_keywords": ["top 8 keywords to add"],
  "nice_to_have_keywords": ["5 secondary keywords"],
  "resume_tips": ["3 specific tips for this exact job"]
}}
"""}]
                    )
                    raw = custom_message.content[0].text.strip()
                    if raw.startswith("```"): raw = raw.split("\n", 1)[1]
                    if raw.endswith("```"): raw = raw.rsplit("\n", 1)[0]
                    result = json.loads(raw)

                    score = result.get("score", 0)
                    score_class = "score-high" if score >= 70 else "score-mid" if score >= 50 else "score-low"

                    st.markdown(f"""
<div class="job-card">
    <div style="font-size:1.5rem;font-family:'Syne',sans-serif;font-weight:700;color:#fff;">Match Score</div>
    <div style="margin-top:0.5rem;">
        <span class="score-badge {score_class}" style="font-size:1.2rem;padding:0.4rem 1rem;">{score}/100</span>
    </div>
    <div style="margin-top:1rem;font-size:0.85rem;color:#10B981;">✅ {' | '.join(result.get('match_reasons', []))}</div>
    <div style="margin-top:0.4rem;font-size:0.85rem;color:#F59E0B;">⚠️ {' | '.join(result.get('gap_reasons', []))}</div>
</div>
""", unsafe_allow_html=True)

                    st.markdown('<div class="section-header" style="margin-top:1.5rem;">ATS Keywords & Resume Tips</div>', unsafe_allow_html=True)

                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.markdown("**Must-Have Keywords**")
                        kw_html = "".join([f'<span class="keyword-pill">{kw}</span>' for kw in result.get("must_have_keywords", [])])
                        st.markdown(kw_html, unsafe_allow_html=True)

                        st.markdown("<br>**Nice-to-Have Keywords**", unsafe_allow_html=True)
                        sec_html = "".join([f'<span class="keyword-pill-secondary">{kw}</span>' for kw in result.get("nice_to_have_keywords", [])])
                        st.markdown(sec_html, unsafe_allow_html=True)

                    with col_c2:
                        st.markdown("**Resume Tips**")
                        for i, tip in enumerate(result.get("resume_tips", []), 1):
                            st.markdown(f"""
<div style="background:rgba(99,102,241,0.08);border-left:2px solid #6366F1;padding:0.75rem 1rem;border-radius:0 8px 8px 0;margin-bottom:0.5rem;font-size:0.85rem;color:#C4C4D4;">
{i}. {tip}
</div>""", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Analysis failed: {e}")