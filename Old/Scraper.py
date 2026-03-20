from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def scrape_linkedin_jobs(keywords, locations):
    jobs_data = []
    
    with sync_playwright() as p:
        # Invisible browser
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        
        total_searches = len(locations) * len(keywords)
        current_search = 1
        
        for location in locations:
            for keyword in keywords:
                print(f"Search {current_search}/{total_searches}: '{keyword}' in '{location}'...")
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
                        
                        title = title_elem.text.strip() if title_elem else 'N/A'
                        company = company_elem.text.strip() if company_elem else 'N/A'
                        job_location = location_elem.text.strip() if location_elem else 'N/A'
                        time_posted = time_elem.text.strip() if time_elem else 'Recent'
                        
                        # Keeping the raw link so Pandas and Ollama can read it easily
                        raw_link = link_elem['href'] if link_elem else 'N/A'
                        
                        jobs_data.append({
                            'Date_Scraped': datetime.now().strftime("%Y-%m-%d"),
                            'Keyword': keyword,
                            'Title': title,
                            'Company': company,
                            'Location': job_location,
                            'Posted': time_posted,
                            'Link': raw_link
                        })
                    except Exception:
                        continue
                        
        browser.close()
        
    return jobs_data

if __name__ == "__main__":
    target_roles = ["Sales Operations", "Revenue Operations", "Business Analyst", "Analytics Manager"]
    target_locations = [
        "Hyderabad, India", 
        "Bengaluru, Karnataka, India", 
        "London, United Kingdom", 
        "Dubai, United Arab Emirates", 
        "Sweden", 
        "Luxembourg"
    ]
    
    print("Starting the FAST invisible job scraper...")
    scraped_jobs = scrape_linkedin_jobs(target_roles, target_locations)
    
    if scraped_jobs:
        df = pd.DataFrame(scraped_jobs)
        filename = f'job_leads_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        df.to_excel(filename, index=False)
        print(f"\nSuccess! Found {len(scraped_jobs)} jobs.")
        print(f"Saved to '{filename}'.")
    else:
        print("\nNo jobs found.")