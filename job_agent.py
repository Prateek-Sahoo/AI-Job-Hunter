import pandas as pd
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- YOUR GEMINI API KEY ---
genai.configure(api_key="AIzaSyCZrKTNjcNMZFddmEX6QROLtNzhS5_q7jY")
model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})

def scrape_linkedin_jobs(keywords, locations, browser):
    jobs_data = []
    page = browser.new_page()
    total_searches = len(locations) * len(keywords)
    current_search = 1
    
    for location in locations:
        for keyword in keywords:
            print(f"  -> Search {current_search}/{total_searches}: '{keyword}' in '{location}'...")
            current_search += 1
            
            search_url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}&f_TPR=r86400&trk=public_jobs_jobs-search-bar_search-submit"
            page.goto(search_url)
            
            page.wait_for_timeout(3000) 
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(2000)

            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            job_cards = soup.find_all('div', class_='base-card')
            
            for card in job_cards:
                try:
                    title_elem = card.find('h3', class_='base-search-card__title')
                    company_elem = card.find('h4', class_='base-search-card__subtitle')
                    location_elem = card.find('span', class_='job-search-card__location')
                    link_elem = card.find('a', class_='base-card__full-link')
                    time_elem = card.find('time')
                    
                    raw_link = link_elem['href'] if link_elem else 'N/A'
                    
                    jobs_data.append({
                        'Date_Scraped': datetime.now().strftime("%Y-%m-%d"),
                        'Keyword': keyword,
                        'Title': title_elem.text.strip() if title_elem else 'N/A',
                        'Company': company_elem.text.strip() if company_elem else 'N/A',
                        'Location': location_elem.text.strip() if location_elem else 'N/A',
                        'Posted': time_elem.text.strip() if time_elem else 'Recent',
                        'Link': raw_link,
                        'Match_Score': 0,      
                        'AI_Reasoning': ""     
                    })
                except Exception:
                    continue
                    
    page.close()
    return jobs_data

def get_job_description(url, browser):
    if not url or url == 'N/A' or url.strip() == '':
        return None
    try:
        page = browser.new_page()
        page.goto(url, timeout=10000)
        page.wait_for_timeout(1500)
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        desc_div = soup.find('div', class_='show-more-less-html__markup')
        text = desc_div.get_text(separator=' ', strip=True) if desc_div else soup.get_text(separator=' ', strip=True)
        
        page.close()
        return text
    except Exception:
        return None

def evaluate_job(description):
    # Rewritten using safe string concatenation to avoid Notepad Syntax Errors
    rubric_prompt = (
        "You are an expert technical recruiter. Evaluate the following job description against a candidate with 5+ years of experience.\n"
        "Calculate a final score from 0 to 100 using EXACTLY this strict rubric:\n"
        "Start at 0 points.\n"
        "+30 points if the core role is Revenue Operations, Sales Operations, or Sales Analytics.\n"
        "+20 points if the job requires Power BI, Tableau, or SQL.\n"
        "+20 points for experience managing CRM pipelines (Salesforce).\n"
        "+15 points for executive stakeholder management and forecasting.\n"
        "+15 points for data automation (Python, Power Automate).\n"
        "-50 points (Penalty) if it is purely cold-calling sales, heavy software engineering, or clinical research.\n\n"
        "Output ONLY valid JSON with two keys: \"score\" (integer) and \"reason\" (a 1-sentence explanation of the math).\n"
        "Example: {\"score\": 85, \"reason\": \"Starts at 0, +30 for Sales Ops, +20 for Power BI, +20 for Salesforce, +15 for forecasting.\"}\n\n"
        "Job Description:\n" + description
    )

    try:
        response = model.generate_content(rubric_prompt)
        result = json.loads(response.text)
        return result.get('score', 0), result.get('reason', 'Failed to parse reason.')
    except Exception as e:
        return 0, "API Error."

if __name__ == "__main__":
    target_roles = ["Sales Operations", "Revenue Operations", "Business Analyst", "Analytics Manager"]
    target_locations = [
        "Hyderabad, India", "Bengaluru, Karnataka, India", 
        "London, United Kingdom", "Dubai, United Arab Emirates", 
        "Sweden", "Luxembourg"
    ]
    
    print("===========================================")
    print(" STARTING CLOUD-POWERED JOB AGENT (GEMINI)")
    print("===========================================")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # --- PHASE 1: SOURCING ---
        print("\n[PHASE 1] Sourcing new job leads...")
        jobs = scrape_linkedin_jobs(target_roles, target_locations, browser)
        print(f" Found {len(jobs)} total jobs across all locations.")
        
        # --- PHASE 1.5: HIGH-SPEED PRE-FILTER ---
        if jobs:
            print("\n[PHASE 1.5] Filtering out irrelevant job titles...")
            allowed_keywords = ['operations', 'revenue', 'analytics', 'consulting', 'analyst', 'sales', 'strategy', 'data']
            
            filtered_jobs = []
            for job in jobs:
                title_lower = job['Title'].lower()
                if any(keyword in title_lower for keyword in allowed_keywords):
                    filtered_jobs.append(job)
            
            print(f" Reduced to {len(filtered_jobs)} highly relevant roles for AI grading.")
            jobs = filtered_jobs

        # --- PHASE 2: CLOUD EVALUATION ---
        if jobs:
            print("\n[PHASE 2] Evaluating jobs with Gemini API...")
            for i, job in enumerate(jobs):
                print(f"  -> [{i+1}/{len(jobs)}] Analyzing: {job['Title']} at {job['Company']}")
                
                desc = get_job_description(job['Link'], browser)
                if desc and len(desc) > 100:
                    score, reason = evaluate_job(desc)
                    job['Match_Score'] = score
                    job['AI_Reasoning'] = reason
                    # Quick sleep to respect free API rate limits
                    time.sleep(2) 
                else:
                    print("     [!] Skipping: Could not read description.")
                    
            # --- PHASE 3: EXPORT ---
            print("\n[PHASE 3] Saving results...")
            df = pd.DataFrame(jobs)
            df = df.sort_values(by='Match_Score', ascending=False) 
            filename = f'master_job_pipeline_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
            df.to_excel(filename, index=False)
            print(f" Success! Fully graded pipeline saved to '{filename}'")
            
        else:
            print("\nNo relevant jobs found to evaluate today.")
            
        browser.close()