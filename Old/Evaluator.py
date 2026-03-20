import pandas as pd
import ollama
import json
import re
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def extract_url_from_hyperlink(formula):
    # Extracts the raw URL from the Excel =HYPERLINK formula
    if pd.isna(formula) or not isinstance(formula, str):
        return None
    match = re.search(r'\"(http.*?)\"', formula)
    return match.group(1) if match else None

def get_job_description(url, browser):
    # Quickly grabs the text from the job page
    if not url or url == 'N/A':
        return None
    
    try:
        page = browser.new_page()
        page.goto(url, timeout=10000) # 10 second timeout
        page.wait_for_timeout(1500)
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # LinkedIn usually keeps the description in this class, but we grab all text as a fallback
        desc_div = soup.find('div', class_='show-more-less-html__markup')
        text = desc_div.get_text(separator=' ', strip=True) if desc_div else soup.get_text(separator=' ', strip=True)
        
        page.close()
        return text
    except Exception as e:
        print(f"      [!] Could not load page: {e}")
        return None

def evaluate_job(description):
    # The strict prompt customized to your professional background
    system_prompt = """
    You are an expert technical recruiter and career coach.
    Evaluate the provided job description for a candidate with the following profile:
    - 5+ years of experience in Sales Operations, Revenue Operations, and Business Analytics.
    - Strong technical expertise in Power BI, Salesforce, SQL, Python, and Tableau.
    - Experience managing CRM pipelines, sales forecasting, and enterprise accounts.
    - Familiarity with data automation (Power Automate, Power Apps).

    Rate this job from 0 to 100 based on how well it matches this exact profile.
    Be highly critical. If the job requires completely different core skills (e.g., heavy software engineering, pure marketing, or clinical research), give it a low score (< 40). 
    If it aligns perfectly with revenue operations and analytics, score it highly (> 80).

    You MUST output your response strictly in valid JSON format with two keys: "score" (integer) and "reason" (a 1-sentence explanation).
    Example: {"score": 85, "reason": "Strong match for Power BI and Sales Ops experience, though it requires slightly more focus on marketing automation."}
    """

    try:
        response = ollama.chat(model='llama3.2', messages=[
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': f"Evaluate this job description:\n\n{description}"
            }
        ], format='json')

        # Parse the JSON response
        result = json.loads(response['message']['content'])
        return result.get('score', 0), result.get('reason', 'Failed to parse reason.')
    except Exception as e:
        print(f"      [!] AI Evaluation failed: {e}")
        return 0, "Evaluation error."

if __name__ == "__main__":
    # --- UPDATE THIS TO YOUR RECENT EXCEL FILE NAME ---
    input_filename = "job_leads_20260320_0115.xlsx"
    output_filename = "graded_" + input_filename

    try:
        df = pd.read_excel(input_filename)
        print(f"Loaded {len(df)} jobs from {input_filename}. Starting AI evaluation...")
    except FileNotFoundError:
        print(f"Error: Could not find '{input_filename}'. Please update the filename in the script.")
        exit()

    # Create new columns for our AI grades
    df['Match_Score'] = 0
    df['AI_Reasoning'] = ""

    with sync_playwright() as p:
        # We use headless=True to keep the browser invisible
        browser = p.chromium.launch(headless=True)
        
        for index, row in df.iterrows():
            title = row.get('Title', 'Unknown')
            company = row.get('Company', 'Unknown')
            print(f"\n[{index + 1}/{len(df)}] Analyzing: {title} at {company}")
            
            raw_url = extract_url_from_hyperlink(row.get('Link', ''))
            
            if not raw_url:
                print("      -> Skipping: No valid URL found.")
                continue

            # Step 1: Read the description
            description = get_job_description(raw_url, browser)
            
            # Step 2: Grade the description
            if description and len(description) > 100:
                score, reason = evaluate_job(description)
                df.at[index, 'Match_Score'] = score
                df.at[index, 'AI_Reasoning'] = reason
                print(f"      -> Score: {score}/100")
                print(f"      -> Reason: {reason}")
            else:
                print("      -> Skipping: Could not extract enough text to evaluate.")

        browser.close()

    # Save the graded data, sorting the best matches to the top
    df = df.sort_values(by='Match_Score', ascending=False)
    df.to_excel(output_filename, index=False)
    print(f"\nFinished! Evaluated jobs saved to '{output_filename}'")