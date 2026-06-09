"""classifier.py — AI engine for B2B lead intelligence."""

import json
import pandas as pd
from google import genai
from google.genai import types

from validators import COL_B2B, COL_STATUS

# We define the model here as imported by ui.py
MODEL_NAME = "gemini-2.5-flash" 

# Public domains that bypass the API
PUBLIC_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", 
    "outlook.com", "icloud.com", "live.com"
}

def process_leads(emails_raw: str, api_key: str) -> pd.DataFrame | None:
    """Parses raw text, filters public domains, and calls Gemini for corporate ones."""
    
    if not emails_raw or not emails_raw.strip():
        return None

    # Clean and extract unique emails
    emails = [e.strip() for e in emails_raw.split("\n") if e.strip()]
    if not emails:
        return None

    results = []
    corporate_domains = set()

    # Step 1: Initial Validation
    for email in emails:
        if "@" not in email:
            results.append({
                "Email": email,
                COL_STATUS: "Invalid",
                COL_B2B: "-",
                "Company Insight (AI)": "Invalid email format."
            })
            continue

        domain = email.split("@")[1].lower()

        if domain in PUBLIC_DOMAINS:
            results.append({
                "Email": email,
                COL_STATUS: "Public Inbox",
                COL_B2B: "Low",
                "Company Insight (AI)": "Public email provider. B2B intent is low."
            })
        else:
            results.append({
                "Email": email,
                COL_STATUS: "Corporate Email",
                COL_B2B: "Pending",
                "Company Insight (AI)": "Pending..."
            })
            corporate_domains.add(domain)

    # Step 2: AI Analysis for Corporate Domains
    if corporate_domains and api_key:
        client = genai.Client(api_key=api_key)
        domain_insights = {}

        # Prompt engineering: Ask Gemini to evaluate all domains in one single batch
        prompt = f"""
        Analyze the following corporate domains for B2B lead generation. 
        For each domain, determine the likely 'fit' (High, Medium, or Low) based on if they look like a solid B2B target.
        Provide a 1-sentence 'insight' explaining what the company likely does and why they got that fit score.
        
        Domains: {', '.join(corporate_domains)}
        
        Return ONLY a JSON dictionary where the keys are the domains, and the values are objects containing 'fit' and 'insight'.
        """

        try:
            # Using the NEW Google GenAI SDK syntax with JSON enforcement
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            domain_insights = json.loads(response.text)
        except Exception as e:
            print(f"API Error: {e}")

        # Step 3: Map AI insights back to the rows
        for row in results:
            if row[COL_STATUS] == "Corporate Email":
                domain = row["Email"].split("@")[1].lower()
                insight_data = domain_insights.get(domain, {})
                
                row[COL_B2B] = insight_data.get("fit", "Medium").capitalize()
                row["Company Insight (AI)"] = insight_data.get("insight", "Corporate domain detected. No deep AI insight available.")
                
    elif corporate_domains and not api_key:
        # If user pasted corporate emails but forgot their API key
        for row in results:
            if row[COL_STATUS] == "Corporate Email":
                row[COL_B2B] = "-"
                row["Company Insight (AI)"] = "⚠️ Gemini API key required for insight."

    return pd.DataFrame(results)