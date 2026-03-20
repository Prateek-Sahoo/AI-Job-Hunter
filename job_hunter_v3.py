import pandas as pd
import json
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

# =============================================================================
# CONFIGURATION
# =============================================================================

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    'gemini-2.0-flash',
    generation_config={"response_mime_type": "application/json"}
)

# Wide net — generic + specific titles to catch all relevant postings
TARGET_ROLES = [
    # Core RevOps / SalesOps
    "Sales Operations",
    "Revenue Operations",
    "Sales Operations Analyst",
    "Revenue Operations Analyst",
    # Analytics
    "Business Analyst",
    "Data Analyst",
    "Analytics Manager",
    "Reporting Analyst",
    # Consulting / Strategy
    "Strategy Analyst",
    "Go-To-Market Analyst",
    "Commercial Analyst",
    # CRM / Tools
    "Salesforce Analyst",
    "CRM Analyst",
]

# LinkedIn precise location strings
LOCATIONS = [
    "Hyderabad, Telangana, India",
    "Bengaluru, Karnataka, India",
    "Dubai, United Arab Emirates",
    "London, England, United Kingdom",
    "Luxembourg",
    "Stockholm, Sweden",
]

# Only save jobs scoring at or above this
MIN_SCORE = 45

# Title pre-filter — must contain at least one of these to proceed
KEEP_KEYWORDS = [
    'operations', 'revenue', 'sales', 'analytics', 'analyst',
    'reporting', 'crm', 'data', 'strategy', 'commercial',
    'insights', 'gtm', 'go-to-market', 'forecasting', 'consulting'
]

# Instant reject — skip immediately if title contains any of these
REJECT_KEYWORDS = [
    'engineer', 'developer', 'software', 'devops', 'clinical',
    'nurse', 'doctor', 'recruiter', 'driver', 'warehouse',
    'accountant', 'sdr', 'bdr', 'telesales', 'cold call',
    'field sales', 'hr ', 'human resources', 'payroll'
]

# =============================================================================
# SCORING PROMPT — Built from Prateek's CV, mid-level targeting
# =============================================================================

RUBRIC_PROMPT = """
You are a recruiter evaluating a job description for this candidate:

CANDIDATE:
- 5 years experience in Sales Ops, Revenue Ops, Business Analytics
- Current: Associate Manager – Research & Analytics at Concentrix
- Previous: Business Analyst – Sales Operations at Tech Mahindra (managed $200M+ revenue, 200+ enterprise accounts)
- Tools: Power BI, Tableau, Looker Studio, Salesforce, MS Dynamics, SQL, Python, Power Automate, Power Apps, Excel
- Strengths: CRM pipeline management, sales forecasting, KPI dashboards, executive reporting, data automation, sentiment analysis
- Seniority target: Mid-level to Senior Analyst, or early Manager roles (3-6 years experience range)
- Open to: Hyderabad, Bengaluru, Dubai, London, Luxembourg, Sweden

SCORING (start at 0):
+25  Core role is Sales Ops, Revenue Ops, or Sales Analytics
+20  Requires Power BI, Tableau, or SQL
+15  Requires Salesforce or MS Dynamics CRM experience
+15  Involves forecasting, pipeline management, or executive reporting
+10  Mentions Python, Power Automate, or data automation
+10  Seniority fits (Analyst, Senior Analyst, Associate Manager, early Manager — 2-6 years exp)
+5   Industry is IT services, consulting, SaaS, or tech

PENALTIES:
-60  Purely cold-calling, field sales, SDR/BDR, or telesales
-50  Software engineering, DevOps, or clinical/medical
-25  Requires 8+ years experience (too senior)
-25  Requires only 0-1 years experience (too junior)

Output ONLY valid JSON:
{"score": integer_0_to_100, "reason": "one sentence covering key matches and mismatches"}
"""

# =============================================================================
# FUNCTIONS
# =============================================================================

def block_media(route):
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        route.abort()
    else:
        route.continue_()

def is_relevant_title(title: str) -> bool:
    t = title.lower()
    if any(k in t for k in REJECT_KEYWORDS):
        return False
    if any(k in t for k in KEEP_KEYWORDS):
        return True
    return False

def scrape_jobs(browser) -> list:
    seen_links = set()
    leads = []
    page = browser.new_page()
    page.route("**/*", block_media)

    total = len(LOCATIONS) * len(TARGET_ROLES)
    count = 0

    for loc in LOCATIONS:
        for role in TARGET_ROLES:
            count += 1
            print(f"  [{count}/{total}] '{role}' in '{loc}'")
            url = (
                f"https://www.linkedin.com/jobs/search"
                f"?keywords={role.replace(' ', '%20')}"
                f"&location={loc.replace(' ', '%20')}"
                f"&f_TPR=r86400"
                f"&sortBy=DD"
            )
            try:
                page.goto(url, timeout=10000)
                page.wait_for_timeout(1800)
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(600)
            except:
                continue

            soup = BeautifulSoup(page.content(), 'html.parser')
            for card in soup.find_all('div', class_='base-card'):
                try:
                    title = card.find('h3', class_='base-search-card__title').text.strip()
                    link = card.find('a', class_='base-card__full-link')['href'].split('?')[0]

                    if link in seen_links:
                        continue
                    seen_links.add(link)

                    if not is_relevant_title(title):
                        continue

                    leads.append({
                        'Title': title,
                        'Company': card.find('h4', class_='base-search-card__subtitle').text.strip(),
                        'Location': card.find('span', class_='job-search-card__location').text.strip(),
                        'Link': link,
                        'Search_Keyword': role,
                        'Date_Found': datetime.now().strftime("%Y-%m-%d"),
                        'Match_Score': 0,
                        'AI_Reasoning': ''
                    })
                except:
                    continue

    page.close()
    return leads

def get_description(url: str, browser) -> str | None:
    try:
        page = browser.new_page()
        page.route("**/*", block_media)
        page.goto(url, timeout=12000)
        page.wait_for_timeout(800)
        soup = BeautifulSoup(page.content(), 'html.parser')
        desc = soup.find('div', class_='show-more-less-html__markup')
        text = desc.get_text(separator=' ', strip=True)[:2500] if desc else None
        page.close()
        return text
    except:
        return None

def grade_job(description: str) -> tuple[int, str]:
    try:
        prompt = RUBRIC_PROMPT + f"\n\nJob Description:\n{description}"
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return int(result.get('score', 0)), result.get('reason', 'No reason.')
    except Exception as e:
        return 0, f"API Error: {str(e)}"

# =============================================================================
# MAIN
# =============================================================================

def run():
    start = datetime.now()
    print("=" * 55)
    print(f"  AI JOB HUNTER  |  {start.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Model: Gemini 2.0 Flash  |  Min Score: {MIN_SCORE}/100")
    print("=" * 55)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Phase 1: Scrape
        print(f"\n[PHASE 1] Scraping {len(TARGET_ROLES)} roles across {len(LOCATIONS)} locations...")
        leads = scrape_jobs(browser)
        print(f"\n  → {len(leads)} unique relevant jobs found.")

        if not leads:
            print("  No jobs found today. Try again later.")
            browser.close()
            return

        # Phase 2: Grade with Gemini
        print(f"\n[PHASE 2] Grading {len(leads)} jobs with Gemini 2.0 Flash...")
        saved = []

        for i, job in enumerate(leads):
            print(f"  [{i+1}/{len(leads)}] {job['Title']} at {job['Company']}", end=' ')
            desc = get_description(job['Link'], browser)

            if not desc:
                print("→ skipped (no description)")
                continue

            score, reason = grade_job(desc)
            job['Match_Score'] = score
            job['AI_Reasoning'] = reason

            if score >= MIN_SCORE:
                saved.append(job)
                print(f"→ ✓ {score}/100")
            else:
                print(f"→ ✗ {score}/100")

            # Respect Gemini free tier rate limit (15 req/min)
            time.sleep(1.5)

        browser.close()

        # Phase 3: Export
        elapsed = round((datetime.now() - start).seconds / 60, 1)
        print(f"\n[PHASE 3] Saving results...")

        if saved:
            df = pd.DataFrame(saved).sort_values(by='Match_Score', ascending=False)
            filename = f"Jobs_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
            df.to_excel(filename, index=False)

            print(f"\n{'=' * 55}")
            print(f"  ✓ {len(saved)} quality matches saved → '{filename}'")
            print(f"  ✓ Top match: {df.iloc[0]['Title']} at {df.iloc[0]['Company']}")
            print(f"  ✓ Top score: {df.iloc[0]['Match_Score']}/100")
            print(f"  ✓ Completed in {elapsed} minutes")
            print(f"{'=' * 55}")
        else:
            print(f"\n  No jobs scored above {MIN_SCORE} today.")
            print(f"  Completed in {elapsed} minutes")

if __name__ == "__main__":
    run()
