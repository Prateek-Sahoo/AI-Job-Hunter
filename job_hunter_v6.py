import pandas as pd
import json
import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich import box

import ollama

# =============================================================================
# SETUP
# =============================================================================

console = Console()

# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET_ROLES = [
    # Core strength roles
    "Revenue Operations Manager",
    "Sales Operations Analyst",
    "Sales Operations Manager",
    "Revenue Operations Analyst",
    # Analytics & Reporting
    "Business Analytics Manager",
    "Reporting Analyst",
    "Commercial Analyst",
    # CRM focused
    "CRM Manager",
    "Salesforce Business Analyst",
    # Strategy & Consulting
    "Business Analyst",
    "Strategy Consultant",
    "GTM Analyst",
]

# LinkedIn precise location strings
LOCATIONS = [
    "Hyderabad, Telangana, India",
    "Bengaluru, Karnataka, India",
    "Dubai, United Arab Emirates",
    "London, England, United Kingdom",
    "Luxembourg",
]

MIN_SCORE         = 25
MAX_JOBS_TO_GRADE = 100
FETCH_WORKERS     = 5   # parallel description fetches

KEEP_KEYWORDS = [
    'operations', 'revenue ops', 'sales ops', 'revops',
    'analytics', 'analyst', 'reporting', 'crm', 'salesforce',
    'dynamics', 'power bi', 'data', 'strategy', 'commercial',
    'insights', 'gtm', 'go-to-market', 'forecasting',
    'consulting', 'pipeline', 'dashboard', 'kpi', 'manager'
]

REJECT_KEYWORDS = [
    'software engineer', 'developer', 'devops', 'clinical',
    'nurse', 'doctor', 'recruiter', 'driver', 'warehouse',
    'accountant', 'sdr', 'bdr', 'telesales', 'cold call',
    'field sales', 'hr manager', 'human resources', 'payroll',
    'tax', 'legal', 'compliance', 'supply chain', 'procurement',
    'network engineer', 'system admin', 'it support'
]

RUBRIC_PROMPT = """
You are an expert recruiter. Score this job title/company/location for the following candidate.
Since you only have the job title and company name, use your knowledge of typical role requirements
to infer what the job likely involves. Be realistic and fair.

CANDIDATE PROFILE — Prateek Kumar Sahoo:
- Total experience: ~5 years
- Current: Associate Manager – Research & Analytics at Concentrix (BPO/Consulting, 10 months)
  * Led analytics consulting for C-suite, built Power BI dashboards, Python sentiment analysis,
    Looker Studio ecosystem, Power Automate workflows, $100K cost savings
- Previous: Business Analyst – Sales Operations at Tech Mahindra (3+ years IT services)
  * Managed $200M revenue portfolio across 200 enterprise accounts
  * CRM optimization (Salesforce, MS Dynamics), 99% data accuracy
  * Sales forecasting, pipeline management, executive reporting to C-suite
  * Market analysis, account targeting, 18% conversion rate improvement
- Earlier: Management Trainee – Channel Sales at KENT RO (1 year)
  * Territory expansion, Tableau dashboards, team management
- Education: MBA Marketing & Operations, B.Tech EEE
- Certifications: Scrum Master, Six Sigma White Belt, McKinsey Forward, Data Analytics

TECHNICAL SKILLS:
- BI & Viz: Power BI, Tableau, Looker Studio, Qlik, Excel (Advanced)
- CRM: Salesforce, Microsoft Dynamics
- Programming: Python, SQL, R
- Automation: Power Automate, Power Apps
- Other: JIRA, Market Research, Forecasting

IDEAL ROLE CHARACTERISTICS:
- Revenue Operations, Sales Operations, Business Analytics, Commercial Analytics
- Involves dashboards, reporting, CRM, forecasting, or stakeholder management
- Seniority: Senior Analyst, Lead Analyst, Associate Manager, or Manager level
- Industries: IT services, SaaS, consulting, BPO, tech, FMCG, financial services

SCORING RUBRIC (start at 0, max 100):
+30  Role is Revenue Ops, Sales Ops, Commercial Analytics, or Business Analytics at a relevant company
+20  Company/role likely requires Power BI, Tableau, Salesforce, or SQL based on industry
+15  Role involves forecasting, pipeline management, CRM, or executive reporting
+15  Seniority matches: Senior Analyst, Lead, Associate Manager, Manager (3-7 yrs experience range)
+10  Company is in IT services, SaaS, consulting, BPO, or tech industry
+10  Role involves data automation, Python, Power Automate, or process optimization

PENALTIES:
-70  Role is clearly cold-calling, field sales, SDR/BDR, telesales, or pure door-to-door
-60  Role is software engineering, DevOps, clinical/medical, legal, or completely unrelated field
-30  Role requires 10+ years experience (too senior for candidate)
-20  Role is very junior / entry level (0-2 years) — candidate is overqualified
-10  Role is in an industry completely unrelated to candidate's background

IMPORTANT NOTES:
- If the company is a well-known tech/consulting firm (Deloitte, Accenture, Microsoft, Salesforce etc),
  give benefit of the doubt on tool requirements
- A "Business Analyst" at a tech company is likely a good match
- A "Business Analyst" at a hospital or construction firm is likely NOT a match
- Use company name and location context to inform your scoring

Output ONLY valid JSON — no explanation outside JSON:
{"score": integer_0_to_100, "reason": "one sentence: what matches and what doesn't"}
"""

# =============================================================================
# HELPERS
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
    return any(k in t for k in KEEP_KEYWORDS)

def score_color(score: int) -> str:
    if score >= 75: return "bold green"
    if score >= 55: return "bold yellow"
    return "bold red"

# =============================================================================
# PHASE 1 — SCRAPE LINKEDIN (OPTIMIZED)
# =============================================================================

def scrape_jobs(progress, task) -> list:
    seen_links = set()
    leads = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.route("**/*", block_media)

        # Randomise user agent to reduce bot detection
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        })

        for loc in LOCATIONS:
            for role in TARGET_ROLES:
                progress.update(task, description=f"[cyan]Scanning:[/cyan] {role[:20]} in {loc[:18]}...")

                url = (
                    f"https://www.linkedin.com/jobs/search"
                    f"?keywords={role.replace(' ', '%20')}"
                    f"&location={loc.replace(' ', '%20')}"
                    f"&f_TPR=r86400"   # last 24 hours
                    f"&sortBy=DD"      # newest first
                    f"&position=1&pageNum=0"
                )

                try:
                    # Reduced timeout + wait — sweet spot between speed and reliability
                    page.goto(url, timeout=12000, wait_until="domcontentloaded")
                    page.wait_for_timeout(1000)
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(500)

                    soup = BeautifulSoup(page.content(), 'html.parser')
                    cards = soup.find_all('div', class_='base-card')

                    for card in cards:
                        try:
                            title   = card.find('h3', class_='base-search-card__title').text.strip()
                            link    = card.find('a', class_='base-card__full-link')['href'].split('?')[0]
                            company = card.find('h4', class_='base-search-card__subtitle').text.strip()
                            loc_tag = card.find('span', class_='job-search-card__location')
                            location = loc_tag.text.strip() if loc_tag else loc

                            if link in seen_links:
                                continue
                            seen_links.add(link)

                            if not is_relevant_title(title):
                                continue

                            leads.append({
                                'Title':          title,
                                'Company':        company,
                                'Location':       location,
                                'Link':           link,
                                'Search_Keyword': role,
                                'Date_Found':     datetime.now().strftime("%Y-%m-%d"),
                                'Match_Score':    0,
                                'AI_Reasoning':   ''
                            })
                        except:
                            continue

                except Exception as e:
                    console.print(f"  [red]! Skipped {role} / {loc}: timeout[/red]")

                progress.advance(task)

        page.close()
        browser.close()

    return leads

# =============================================================================
# PHASE 2 — FETCH DESCRIPTIONS IN PARALLEL
# =============================================================================

def fetch_one_description(job: dict) -> tuple[dict, str | None]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.route("**/*", block_media)
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            page.goto(job['Link'], timeout=12000, wait_until="domcontentloaded")
            page.wait_for_timeout(600)

            soup = BeautifulSoup(page.content(), 'html.parser')
            desc = soup.find('div', class_='show-more-less-html__markup')
            text = desc.get_text(separator=' ', strip=True)[:2500] if desc else None
            page.close()
            return job, text
        except:
            return job, None
        finally:
            browser.close()

# =============================================================================
# PHASE 3 — GRADE WITH OLLAMA (local, free, no limits)
# =============================================================================

def grade_job(description: str) -> tuple[int, str]:
    try:
        response = ollama.chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': RUBRIC_PROMPT},
                {'role': 'user', 'content': f"Job Description:\n{description}"}
            ],
            format='json'
        )
        result = json.loads(response['message']['content'])
        return int(result.get('score', 0)), result.get('reason', 'No reason.')
    except Exception as e:
        return 0, f"Ollama Error: {str(e)}"

# =============================================================================
# MAIN
# =============================================================================

def run():
    start = datetime.now()
    total_searches = len(TARGET_ROLES) * len(LOCATIONS)

    console.print(Panel.fit(
        f"[bold cyan]🤖  AI JOB HUNTER  v6[/bold cyan]\n"
        f"[dim]Source: LinkedIn  •  Model: Ollama llama3.2 (local, free, no limits)[/dim]\n"
        f"[dim]Min Score: {MIN_SCORE}/100  •  Max Jobs: {MAX_JOBS_TO_GRADE}  •  Last 24hrs[/dim]\n"
        f"[dim]{start.strftime('%A, %d %B %Y  %H:%M')}[/dim]",
        box=box.DOUBLE_EDGE,
        border_style="cyan"
    ))

    # ── Phase 1: Scrape ──────────────────────────────────────────────────────
    console.print(f"\n[bold cyan]● PHASE 1[/bold cyan]  LinkedIn — {total_searches} searches across {len(LOCATIONS)} locations...\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(bar_width=35),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Starting...", total=total_searches)
        leads = scrape_jobs(progress, task)

    console.print(f"\n  [green]✓[/green] Found [bold]{len(leads)}[/bold] unique relevant jobs.\n")

    if not leads:
        console.print(Panel.fit(
            "[yellow]No jobs found today.\nLinkedIn may be rate-limiting. Try again in 30 minutes.[/yellow]",
            border_style="yellow"
        ))
        return

    leads = leads[:MAX_JOBS_TO_GRADE]
    console.print(f"  [dim]→ Grading top {len(leads)} jobs.[/dim]\n")

    # Phase 2: Build descriptions from scraped card data
    # LinkedIn blocks individual job page loads so we grade using
    # title + company + location already scraped in Phase 1.
    console.print(f"[bold cyan]● PHASE 2[/bold cyan]  Building summaries from scraped data...\n")
    for job in leads:
        job['_desc'] = (
            f"Job Title: {job['Title']}\n"
            f"Company: {job['Company']}\n"
            f"Location: {job['Location']}\n"
            f"Search Category: {job['Search_Keyword']}"
        )
    console.print(f"  [green]✓[/green] Summaries ready for all {len(leads)} jobs.\n")

    # Phase 3: Grade with Gemini
    console.print(f"[bold cyan]● PHASE 3[/bold cyan]  Grading with Gemini 2.0 Flash...\n")

    saved = []
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(bar_width=35),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Grading...", total=len(leads))
        for job in leads:
            desc = job.get('_desc', '')
            progress.update(task, description=f"[cyan]Grading:[/cyan] {job['Title'][:28]}...")
            score, reason = grade_job(desc)
            job['Match_Score']  = score
            job['AI_Reasoning'] = reason
            saved.append(job)  # save all — filter by MIN_SCORE in Excel
            progress.advance(task)


    # ── Phase 4: Export + Results table ─────────────────────────────────────
    elapsed = round((datetime.now() - start).seconds / 60, 1)

    if saved:
        df = pd.DataFrame(saved).sort_values(by='Match_Score', ascending=False)
        filename = f"Jobs_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
        df.to_excel(filename, index=False)

        console.print(f"\n[bold cyan]● RESULTS[/bold cyan]  Top {min(10, len(saved))} matches:\n")

        table = Table(box=box.ROUNDED, border_style="cyan", show_lines=True)
        table.add_column("#",        style="dim",        width=4)
        table.add_column("Score",    justify="center",   width=7)
        table.add_column("Title",    style="bold white", width=26)
        table.add_column("Company",  style="cyan",       width=20)
        table.add_column("Location", style="dim",        width=18)
        table.add_column("Why",      style="dim",        width=38)

        for rank, (_, row) in enumerate(df.head(10).iterrows(), 1):
            score = row['Match_Score']
            table.add_row(
                str(rank),
                f"[{score_color(score)}]{score}[/{score_color(score)}]",
                str(row['Title'])[:26],
                str(row['Company'])[:20],
                str(row['Location'])[:18],
                str(row['AI_Reasoning'])[:38]
            )

        console.print(table)
        # Show score distribution
        bands = {
            "🟢 70-100 (Strong match)":  len(df[df['Match_Score'] >= 70]),
            "🟡 50-69  (Good match)":    len(df[(df['Match_Score'] >= 50) & (df['Match_Score'] < 70)]),
            "🟠 30-49  (Possible)":      len(df[(df['Match_Score'] >= 30) & (df['Match_Score'] < 50)]),
            "🔴 0-29   (Weak/reject)":   len(df[df['Match_Score'] < 30]),
        }
        dist = "  ".join([f"{k}: {v}" for k, v in bands.items()])
        console.print(Panel.fit(
            f"[bold green]✓  {len(saved)} jobs graded → {filename}[/bold green]\n"
            f"[dim]{dist}[/dim]\n"
            f"[dim]Completed in {elapsed} minutes[/dim]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[yellow]No jobs scored above {MIN_SCORE} today.\nTry lowering MIN_SCORE in the config.[/yellow]\n"
            f"[dim]Completed in {elapsed} minutes[/dim]",
            border_style="yellow"
        ))

if __name__ == "__main__":
    run()