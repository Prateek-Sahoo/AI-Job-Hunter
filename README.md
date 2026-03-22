# 🤖 AI Job Hunter — Automated Job Scraper & AI Evaluator

> **Part of the "Building with AI" series** — real tools built with AI assistance, shared openly.

An end-to-end AI-powered job hunting agent that scrapes LinkedIn across multiple cities, reads every relevant listing, and scores each role against your profile — using a **free local AI model via Ollama**. No API keys. No subscriptions. No data leaving your machine. Runs entirely on your PC.

---

## 💡 What It Does

```
Phase 1  →  Scrapes LinkedIn for your target roles across 5 locations
Phase 1.5→  Deduplicates and filters irrelevant titles instantly
Phase 2  →  Builds job summaries from scraped data
Phase 3  →  Scores each job 0–100 using a personalised AI rubric (Ollama)
Phase 4  →  Exports a sorted Excel — best matches at the top
```

---

## ✨ Features

- **100% Free & Local** — powered by Ollama, no API key needed
- **Rich terminal UI** — live progress bars, spinners, and a colour-coded results table
- **Smart pre-filtering** — rejects irrelevant titles instantly before AI processing
- **Deduplication** — same job never scored twice across searches
- **CV-tailored scoring** — rubric built around your actual skills and experience level
- **Experience matching** — penalises roles requiring 8+ years so you only see relevant seniority

---

## 🖥️ Terminal Preview

```
╔══════════════════════════════════════════════════════╗
║  🤖  AI JOB HUNTER  v6                               ║
║  Source: LinkedIn  •  Model: Ollama llama3.2         ║
║  Min Score: 25/100  •  Max Jobs: 100  •  Last 24hrs  ║
╚══════════════════════════════════════════════════════╝

● PHASE 1  LinkedIn — 60 searches across 5 locations...
  Scanning: Revenue Operations Manager in Dubai...  ████████  100%  0:02:10
  ✓ Found 119 unique relevant jobs.

● PHASE 2  Building summaries from scraped data...
  ✓ Summaries ready for all 100 jobs.

● PHASE 3  Grading with Ollama llama3.2...
  Grading: Sales Operations Analyst...  ████░░░░  42%  0:00:45

● RESULTS  Top 10 matches:
┌────┬───────┬────────────────────────┬──────────────┬──────────────┐
│ #  │ Score │ Title                  │ Company      │ Location     │
│ 1  │  85   │ Revenue Ops Analyst    │ Accenture    │ Dubai        │
│ 2  │  78   │ Sales Operations Lead  │ Infosys      │ Hyderabad    │
└────┴───────┴────────────────────────┴──────────────┴──────────────┘
```

---

## ⚙️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core scripting |
| Playwright | Headless browser — scrapes LinkedIn |
| BeautifulSoup | HTML parsing |
| Ollama + Llama 3.2 | Local AI model — scores jobs (free, private) |
| Rich | Beautiful terminal UI with progress bars and tables |
| Pandas + OpenPyXL | Excel export |

---

## 🚀 Setup

### 1. Clone the repo

```bash
git clone https://github.com/Prateek-Sahoo/AI-Job-Hunter.git
cd AI-Job-Hunter
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Install Ollama and pull the model

Download Ollama from [ollama.com](https://ollama.com), install it, then run:

```bash
ollama run llama3.2
```

Once it downloads, type `/bye` to exit. The model is now saved on your machine.

> Make sure the Ollama app is running in your system tray before running the script.

---

## ▶️ How to Run

```bash
python job_hunter_v6.py
```

Or on Windows, double-click **`run.bat`**

The terminal shows live progress across all phases. When done, an Excel file appears in the same folder — sorted by best match score.

---

## 🎯 Scoring Rubric

Built around a **Sales Ops / Revenue Ops / Business Analytics professional with ~5 years experience**:

| Criteria | Points |
|----------|--------|
| Core role is Sales Ops, Revenue Ops, or Business Analytics | +30 |
| Company/role likely requires Power BI, Tableau, or SQL | +20 |
| Involves forecasting, pipeline, CRM, or executive reporting | +15 |
| Seniority fits (Senior Analyst, Lead, Associate Manager) | +15 |
| Company is IT services, SaaS, consulting, or tech | +10 |
| Mentions Python, Power Automate, or process automation | +10 |
| **Penalty:** Cold-calling, field sales, SDR/BDR | -60 |
| **Penalty:** Software engineering or clinical/medical | -60 |
| **Penalty:** Requires 8+ years experience | -50 |
| **Penalty:** Requires 10+ years experience | -45 |
| **Penalty:** Entry level 0–2 years | -20 |

Only jobs scoring **25 or above** are saved. Everything is visible in the Excel for manual review.

---

## 🌍 Customising for Your Profile

### Change target roles

```python
TARGET_ROLES = [
    "Revenue Operations Manager",
    "Sales Operations Analyst",
    "Business Analyst",
    # Add your own here
]
```

### Change locations

```python
LOCATIONS = [
    "Hyderabad, Telangana, India",
    "Dubai, United Arab Emirates",
    "London, England, United Kingdom",
    # Add your own here
]
```

### Update the scoring rubric

Edit the `RUBRIC_PROMPT` section in `job_hunter_v6.py` to match your own skills, tools, and experience level.

### Change minimum score threshold

```python
MIN_SCORE = 25  # Lower to see more results, raise to filter aggressively
```

---

## 📁 Project Structure

```
AI-Job-Hunter/
├── job_hunter_v6.py     # ⭐ Main script — latest version
├── job_agent.py         # Earlier version (Gemini API)
├── evaluator1.py        # Earlier version (Ollama, two-step)
├── Modelfile            # Custom Ollama model configuration
├── run.bat              # One-click Windows runner
├── requirements.txt     # Python dependencies
└── README.md
```

---

## 📦 requirements.txt

```
pandas
openpyxl
playwright
beautifulsoup4
ollama
rich
python-dotenv
```

---

## 💡 Tips

- Run it daily — LinkedIn posts most jobs in the morning (8–10am local time)
- Lower `MIN_SCORE` to 10 if you want to see the full picture of what's being scored
- Add more cities to `LOCATIONS` to expand your search
- The `job-evaluator` custom Modelfile in the repo is a fine-tuned version — try it by changing `model='llama3.2'` to `model='job-evaluator'`

---

## 🗺️ Roadmap

- [ ] Schedule daily runs via Windows Task Scheduler
- [ ] Email digest of top matches every morning
- [ ] Support for Indeed and Naukri job boards
- [ ] Web UI dashboard to browse results

---

## 🙋 About This Project

Built as part of **"Building with AI"** — a series documenting real tools I build using AI assistance.

Two years ago this would have taken weeks. Today it took an afternoon.

Follow along on [LinkedIn](https://linkedin.com/in/prateeksahoo) for Day 2 and beyond.

---

## 📄 License

MIT — free to use, modify, and share.
