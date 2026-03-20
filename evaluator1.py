import pandas as pd
import json
import time
import ollama
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# --- TARGET CONFIGURATION ---
TARGET_ROLES = ["Sales Operations", "Revenue Operations", "Business Analyst", "Analytics Manager"]
# Keeping your preferred target regions
LOCATIONS = ["Hyderabad, India", "Dubai, UAE", "London, UK", "Luxembourg", "Sweden"]

def block_media(route):
    """Prevents images/styles from loading to maximize scraping speed."""
    if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
        route.abort()
    else:
        route.continue_()

def get_full_description(url, browser):
    """Navigates to the job link to grab the full text for Ollama to read."""
    try:
        page = browser.new_page()
        page.route("**/*", block_media)
        page.goto(url, timeout=12000)
        page.wait_for_timeout(1000)
        
        soup = BeautifulSoup(page.content(), 'html.parser')
        # LinkedIn's standard selector for job descriptions
        desc_div = soup.find('div', class_='show-more-less-html__markup')
        text = desc_div.get_text(separator=' ', strip=True) if desc_div else "Description not found."
        page.close()
        return text[:3500] # Sending the first 3500 chars is plenty for a 1B model
    except:
        return None

def grade_with_ollama(description):
    """Calls your custom 'job-evaluator' model built in Ollama."""
    try:
        # This calls the specific model you created with your Modelfile
        response = ollama.chat(
            model='job-evaluator', 
            messages=[{'role': 'user', 'content': f"Evaluate this job description:\n{description}"}],
            format='json'
        )
        result = json.loads(response['message']['content'])
        return result.get('score', 0), result.get('reason', 'Graded by Local AI')
    except Exception as e:
        return 0, f"Ollama Error: {str(e)}"

def run_pipeline():
    print("===========================================")
    print(f" LOGGING START: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("===========================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        raw_leads = []
        
        # --- PHASE 1: SEARCHING ---
        search_page = browser.new_page()
        search_page.route("**/*", block_media)
        
        for loc in LOCATIONS:
            for role in TARGET_ROLES:
                print(f" Scanning: {role} in {loc}...")
                url = f"https://www.linkedin.com/jobs/search?keywords={role}&location={loc}&f_TPR=r86400"
                search_page.goto(url)
                search_page.wait_for_timeout(2000) # Small wait for dynamic content
                
                soup = BeautifulSoup(search_page.content(), 'html.parser')
                cards = soup.find_all('div', class_='base-card')
                
                for c in cards:
                    try:
                        title = c.find('h3', class_='base-search-card__title').text.strip()
                        # Quick keyword pre-filter to save local AI processing time
                        if any(k in title.lower() for k in ['ops', 'analyst', 'revenue', 'data', 'sales']):
                            raw_leads.append({
                                'Title': title,
                                'Company': c.find('h4', class_='base-search-card__subtitle').text.strip(),
                                'Link': c.find('a', class_='base-card__full-link')['href'],
                                'Location': loc,
                                'Date_Found': datetime.now().strftime("%Y-%m-%d")
                            })
                    except: continue
        search_page.close()
        
        print(f"\n[PHASE 2] Found {len(raw_leads)} potential matches. Grading with Ollama...")
        
        # --- PHASE 2: LOCAL AI EVALUATION ---
        final_list = []
        for i, job in enumerate(raw_leads):
            print(f" [{i+1}/{len(raw_leads)}] Grading: {job['Title']} at {job['Company']}")
            
            desc = get_full_description(job['Link'], browser)
            if desc:
                score, reason = grade_with_ollama(desc)
                job['Match_Score'] = score
                job['AI_Reasoning'] = reason
                final_list.append(job)
        
        # --- PHASE 3: EXPORT ---
        if final_list:
            df = pd.DataFrame(final_list).sort_values(by='Match_Score', ascending=False)
            filename = f"Evaluated_Jobs_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
            df.to_excel(filename, index=False)
            print(f"\n[SUCCESS] Pipeline saved to: {filename}")
        else:
            print("\n[!] No relevant jobs found to evaluate today.")
            
        browser.close()

if __name__ == "__main__":
    run_pipeline()