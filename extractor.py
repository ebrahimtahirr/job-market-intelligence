import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize the Anthropic client using the API key from .env
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# Send a job description to Claude and get back structured signals
def extract_signals(job_description):
    trimmed_description = job_description[:3000]

    prompt = f"""
Extract key information from this job posting. Return JSON only — no explanation, no markdown, no extra text.

Rules:
- "skills" means analytical or business abilities (e.g. data analysis, forecasting, stakeholder management)
- "tools" means specific named software, platforms, or programming languages only (e.g. Excel, Tableau, Python, SQL, Salesforce, AWS). Do NOT include general descriptions or industry jargon.
- If no specific tools are mentioned, return an empty list for tools.

{{
  "skills": ["max 6 skills"],
  "tools": ["max 6 specific software tools or languages only"],
  "experience_years": "number or null",
  "remote": true or false,
  "seniority": "entry, mid, senior, or null"
}}

Job description:
{trimmed_description}
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=256,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        
        return message.content[0].text 

    except Exception as error:
        print(f"Claude API call failed: {error}")
        return None


if __name__ == "__main__":
    test_description = """
    We are looking for a mid-level Data Analyst with 3+ years of experience.
    Must have strong SQL skills and experience with Python and Tableau.
    Familiarity with AWS and Excel is a plus. This is a remote position.
    """

    result = extract_signals(test_description)
    print(result)