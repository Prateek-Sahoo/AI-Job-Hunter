# 🤖 AI Job Hunter — Automated Job Scraper & AI Evaluator

> **Part of the "Building with AI" series** — real tools built with AI assistance, shared openly.

An end-to-end AI-powered job hunting agent that scrapes LinkedIn across multiple cities and countries, reads every job description, and scores each role against your profile — using **Gemini 2.0 Flash** for fast, accurate AI evaluation.

No manual searching. No copy-pasting. Just a ranked Excel of your best matches every morning.

---

## 🎯 What It Does

```
Phase 1   →  Scrapes LinkedIn for 13 role types across 6 locations
Phase 1.5 →  Deduplicates and filters irrelevant titles instantly
Phase 2   →  Opens each job, reads the full description
Phase 3   →  Scores each job 0–100 using a personalised AI rubric
Phase 4   →  Exports a sorted Excel — best matches at the top
```

---

## 📊 Sample Output

| Title | Company | Location | Match Score | AI Reasoning |
|-------|---------|----------|-------------|--------------|
| Revenue Operations Analyst | Acme Corp | Dubai | 85/100 | Strong match — Power BI, Salesforce, forecasting required |
| Sales Operations Manager | TechCo | London | 78/100 | Good fit — SQL and CRM pipeline management mentioned |
| Business Analyst | StartupXYZ | Hyderabad | 62/100 | Partial match — analytics role but no CRM requirement |

---

## ⚙️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core scripting |
| Playwright | Headless browser — scrapes LinkedIn without detection |
| BeautifulSoup | HTML parsing |
| Gemini 2.0 Flash | AI model — scores each job (free, fast, cloud-based) |
| Pandas + OpenPyXL | Excel export |
| python-dotenv | Secure API key management |

---

## 🚀 Setup

### 1. Clone the repo

```bash
git clone https://github.com/Prateek-Sahoo/AI-Job-Hunter.git
cd AI-Job-Hunter
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Get your free Gemini API key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **"Get API Key"** → **"Create API key"**
4. Copy the key

### 4. Create a `.env` file in the project folder

```
GEMINI_API_KEY=your_api_key_here
```

> ⚠️ Never share this file or commit it to GitHub. It's already excluded by `.gitignore`.

---

## ▶️ How to Run

```bash
python job_hunter_v3.py
```

Or on Windows, double-click **`run.bat`**

The terminal shows live progress. When done, an Excel file appears in the same folder — sorted best matches first.

---

## 🎯 Scoring Rubric

The AI evaluates each job using this rubric, calibrated for a **mid-level Sales Ops / Revenue Ops / Analytics professional (3–6 years experience)**:

| Criteria | Points |
|----------|--------|
| Core role is Sales Ops, Revenue Ops, or Sales Analytics | +25 |
| Requires Power BI, Tableau, or SQL | +20 |
| Requires Salesforce or MS Dynamics CRM | +15 |
| Involves forecasting, pipeline management, or executive reporting | +15 |
| Mentions Python, Power Automate, or automation | +10 |
| Seniority fits (Analyst → Senior Analyst → Associate Manager) | +10 |
| Industry is IT services, consulting, SaaS, or tech | +5 |
| **Penalty:** Cold-calling, field sales, SDR/BDR | -60 |
| **Penalty:** Software engineering or clinical/medical | -50 |
| **Penalty:** Requires 8+ years (too senior) | -25 |
| **Penalty:** Requires 0–1 years (too junior) | -25 |

Only jobs scoring **45 or above** are saved to the output file.

---

## 🌍 Customising for Your Profile

### Change target locations

Open `job_hunter_v3.py` and edit `LOCATIONS`:

```python
LOCATIONS = [
    "Hyderabad, Telangana, India",
    "Bengaluru, Karnataka, India",
    "Dubai, United Arab Emirates",
    "London, England, United Kingdom",
    "Luxembourg",
    "Stockholm, Sweden",
]
```

### Change target roles

Edit `TARGET_ROLES` to add or remove job titles:

```python
TARGET_ROLES = [
    "Sales Operations",
    "Revenue Operations",
    "Business Analyst",
    "Data Analyst",
    # Add your own here
]
```

### Change the scoring rubric

Edit the `RUBRIC_PROMPT` section to match your own skills, tools, and experience level.

### Change minimum score threshold

```python
MIN_SCORE = 45  # Only jobs scoring 45+ will be saved
```

---

## 📁 Project Structure

```
AI-Job-Hunter/
├── job_hunter_v3.py     # ⭐ Main script — recommended
├── job_agent.py         # Earlier version using Gemini (Gemini 1.5 Flash)
├── evaluator.py         # Earlier version using local Ollama model
├── scraper.py           # Standalone scraper (no AI grading)
├── run.bat              # One-click Windows runner
├── requirements.txt     # Python dependencies
├── .env                 # Your API key (never commit this)
├── .env.example         # Template — safe to share
├── .gitignore           # Excludes .env and Excel output files
└── README.md
```

---

## 📦 requirements.txt

```
pandas
openpyxl
playwright
beautifulsoup4
google-generativeai
python-dotenv
```

---

## 💡 Tips

- Run it daily — LinkedIn posts most jobs in the morning
- Lower `MIN_SCORE` to 35 if you want a wider result set
- Add `"Mumbai, Maharashtra, India"` to locations to expand India search
- The free Gemini tier allows 1,500 requests/day — enough for any job search

---

## 🗺️ Roadmap

- [ ] Schedule daily runs automatically via Windows Task Scheduler
- [ ] Email digest of top matches sent every morning
- [ ] Support for Indeed and Naukri job boards
- [ ] Web UI dashboard to browse and filter results

---

## 🙋 About This Project

Built as part of **"Building with AI"** — a series documenting real tools I build using AI assistance.

Two years ago this would have taken weeks of YouTube tutorials and half-understood Stack Overflow answers. Today it took an hour.

Follow along on [LinkedIn](https://linkedin.com/in/prateeksahoo) for Day 2 and beyond.

---

## 📄 License

MIT — free to use, modify, and share.
