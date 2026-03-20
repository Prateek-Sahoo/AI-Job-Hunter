# 🤖 AI Job Hunter — Automated Job Scraper & AI Evaluator

> **Part of the "Building with AI" series** — real tools built with AI assistance, shared openly.

An end-to-end AI-powered job hunting agent that scrapes LinkedIn job listings, reads each full job description, and scores them against your profile using a **free, local AI model** — no API keys, no subscriptions, runs entirely on your PC.

---

## 💡 What It Does

| Phase | Script | What happens |
|-------|--------|--------------|
| Phase 1 | `scraper.py` | Scrapes LinkedIn for job listings → saves titles + links to Excel |
| Phase 2 | `evaluator.py` | Opens each link, reads the full description, scores it with local AI |

The final output is a **ranked Excel file** — best matching jobs sorted to the top, each with a score out of 100 and a one-line AI reasoning.

---

## 🖥️ Demo Output

![Graded Output](assets/graded-output.png)

---

## ⚙️ Tech Stack

- **Python** — core scripting
- **Playwright** — headless browser for scraping job pages
- **BeautifulSoup** — HTML parsing
- **Ollama** — runs a local LLM on your machine (free, private, no API key needed)
- **Llama 3.2** — the AI model used for job evaluation
- **Pandas + OpenPyXL** — Excel read/write

---

## 🚀 Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/ai-job-hunter.git
cd ai-job-hunter
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Install and set up Ollama

Download Ollama from [ollama.com](https://ollama.com) and install it.

Then pull the model:

```bash
ollama run llama3.2
```

Once it downloads and gives you a `>>>` prompt, type `/bye` to exit. The model is now saved on your machine.

> Make sure Ollama is running in the background before running the evaluator script.

---

## ▶️ How to Run

### Step 1 — Scrape job listings

```bash
python scraper.py
```

This will generate a file like `job_leads_YYYYMMDD_HHMM.xlsx` in your folder.

### Step 2 — Run the AI evaluator

Open `evaluator.py` and update the filename variable near the bottom to match your generated file:

```python
input_filename = "job_leads_YYYYMMDD_HHMM.xlsx"
```

Then run:

```bash
python evaluator.py
```

The terminal will show live progress as each job is scored. When complete, a new file called `graded_job_leads_YYYYMMDD_HHMM.xlsx` will be created — sorted by best match.

### One-click run (Windows)

Alternatively, just double-click `run.bat` to run both scripts in sequence.

---

## 🎯 Customising for Your Profile

The AI prompt inside `evaluator.py` is pre-configured for a **Sales Operations / Revenue Operations** profile with skills in Power BI, Salesforce, SQL, Python, and Tableau.

To tailor it to your background, edit the `system_prompt` inside the `evaluate_job()` function:

```python
system_prompt = """
You are an expert technical recruiter and career coach.
Evaluate the provided job description for a candidate with the following profile:
- [YOUR YEARS] of experience in [YOUR FIELD]
- Strong technical expertise in [YOUR SKILLS]
...
"""
```

---

## 📁 Project Structure

```
ai-job-hunter/
├── scraper.py          # Phase 1: LinkedIn scraper
├── evaluator.py        # Phase 2: AI job evaluator
├── run.bat             # One-click runner (Windows)
├── requirements.txt    # Python dependencies
├── .gitignore          # Excludes Excel output files
├── assets/             # Screenshots and images
└── README.md
```

---

## 📦 requirements.txt

```
pandas
openpyxl
ollama
playwright
beautifulsoup4
```

---

## ⚠️ Known Limitations

- LinkedIn may block scraping if too many requests are made quickly — add delays if needed
- Works best with public job listings; login-gated listings may not load
- AI scoring accuracy depends on how well you customise the prompt to your profile

---

## 🗺️ Roadmap

- [ ] Fix Ollama API error handling
- [ ] Add support for other job boards (Indeed, Naukri)
- [ ] Build a simple web UI for non-technical users
- [ ] Add email digest of top-scored jobs

---

## 🙋 About This Project

This was built as **Day 1 of "Building with AI"** — a personal series documenting real tools I build using AI assistance.

Two years ago this would have taken weeks. Today it took an hour.

Follow along on [LinkedIn](https://linkedin.com/in/YOUR_PROFILE) for updates.

---

## 📄 License

MIT — free to use, modify, and share.