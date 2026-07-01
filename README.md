# 🤖 Job Finder Agent v2

> Scrapes **Greenhouse API**, **Lever API**, and **YC / HN Jobs** daily, scores listings against  
> your resume using a Python-First approach, and sends the top matches to **Telegram**.  
> Leverages LiteLLM for caching-aware AI explanations and weekly Sunday resume insights.

---

## How it works (v2 Architecture)

```
[GitHub Actions / Local Scheduler]
             ↓
[Greenhouse API]  +  [Lever API]  +  [HN/YC Firebase API]
             ↓
[Deduplication Filter]  →  Checks content hash in jobs.db
             ↓
[Deterministic Filters]  →  Filter by max experience, location, internships, department
             ↓
[Python Match Score]   →  Weighted scoring (Skills, Exp, Loc, Title, Remote, Education)
             ↓
[Shortlist Top 40]
             ↓
[AI Fit Explainer]      →  Explain top 20 ONLY (with SQLite caching by content hash)
             ↓
[Final Match Ranking]   →  0.7 * Python + 0.3 * AI Score
             ↓
[Telegram Bot & DB]     →  Renders HTML templates (dynamic length split), logs queryable stats to analytics.db
```

---

## Setup & First-Time Run Guide (~15 minutes)

### Step 1 — Clone and prepare environment

Clone your repository and prepare the python virtual environment:

```bash
git clone https://github.com/YOUR_USERNAME/job-finder-agent
cd job-finder-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2 — Configure Preferences and Credentials

1. **Environment Variables**: Copy `.env.example` to `.env` and fill in:
   - `LLM_API_KEY`: Groq API Key (default) or key for OpenAI/Gemini/Anthropic.
   - `TELEGRAM_BOT_TOKEN`: Token from [@BotFather](https://t.me/BotFather).
   - `TELEGRAM_CHAT_ID`: Numeric ID from [@userinfobot](https://t.me/userinfobot).
   - `RESUME_PATH`: Location of your resume (defaults to `data/resume.pdf`).
   - `TOP_N`: Max jobs to send (defaults to `25`).
   
2. **Filters & Weights**: Open `config/preferences.json` to edit your hard filters and Python match weights:
   - `experience`: Max years of experience allowed (e.g. `2`).
   - `remote` / `india`: Flags for matching remote or location-based openings.
   - `internships`: Boolean to allow/block internships.
   - `excluded_departments`: List of department words to reject.
   - `preferred_locations`: Cities/Locations you prefer to work in.
   - `preferred_roles`: Key titles representing your target roles.

3. **Greenhouse Slugs**: Customize the target companies you want to track using Greenhouse in `companies.txt`.

4. **Lever Slugs**: Customize the target companies you want to track using Lever in `companies_lever.txt`.

5. **Skills Taxonomy**: Add or modify skills in `data/skills.json` to define your target tech stack categories.

6. **Resume File**: Place your resume PDF, TXT, or MD file at the path specified in `.env` (e.g., `data/resume.pdf`).

---

## Testing & Execution

### 1. Run Unit Tests
Verify the entire scoring, filtering, and caching system is functioning:
```bash
python -m unittest discover -s tests
```

### 2. Verify Greenhouse Slugs (Optional)
Check if Greenhouse company slugs are valid:
```bash
python tests/verify_slugs.py
```
Remove any invalid company slugs from `companies.txt`.

### 3. Verify Telegram Credentials (Optional)
Send a quick test message to make sure your bot is configured properly:
```bash
python tests/verify_telegram.py
```

### 4. Run the Daily Pipeline
Start the scraper, matcher, and notifier:
```bash
python main.py
```
Job cards will begin arriving in your configured Telegram chat. Subsequent runs will use SQL caching to completely avoid making duplicate AI calls for identical jobs, keeping runtimes under 1 minute.

---

## Deploying on GitHub Actions (Runs Free Daily)

### Step 1 — Push to your repo
```bash
git add .
git commit -m "commit job finder files"
git push origin main
```

### Step 2 — Upload your Resume to Google Drive / Dropbox
To keep your resume private, you will load it from a secret link at runtime instead of committing it directly:
- **Google Drive**: Share the PDF as "Anyone with link can view", copy the link, and format it like: `https://drive.google.com/uc?export=download&id=YOUR_FILE_ID`.
- **Dropbox**: Copy the share link and change the `dl=0` at the end to `dl=1` (e.g., `https://www.dropbox.com/.../resume.pdf?dl=1`).

### Step 3 — Set up GitHub Repository Secrets & Permissions
1. Go to your repository **Settings → Actions → General**, scroll to **Workflow permissions**, select **Read and write permissions**, and click **Save** (needed to commit databases).
2. Go to **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `LLM_PROVIDER` (e.g. `groq` or `gemini`)
   - `LLM_MODEL` (e.g. `llama-3.1-8b-instant`)
   - `LLM_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `RESUME_URL` (Paste your direct download link from Step 2)

---

## Local Automation on Windows (Alternative to GitHub)

If you keep your project entirely local and offline, you can run the agent automatically once a day at 9:30 AM using **Windows Task Scheduler**:

1. Press the **Windows Key**, type **Task Scheduler**, and press **Enter**.
2. Click **Create Basic Task...** in the right panel.
3. Set Trigger to **Daily** $\rightarrow$ Start Time to `09:30:00 AM`.
4. Set Action to **Start a program**.
5. Browse and select your batch script: `D:\Coding\job-finder-agent\run_agent.bat`.
6. Set "Start in" to your folder: `D:\Coding\job-finder-agent`.
7. (Optional) Under the task's properties under the **Conditions** tab, check **"Wake the computer to run this task"** so it wakes up your PC if it's asleep.

---

## Project Structure

```
job-finder-agent/
├── config/
│   └── preferences.json        # Filters, role choices, and scoring weights
├── data/
│   ├── skills.json             # Taxonomy of skills for python matching
│   ├── discovered_greenhouse.json  # Auto-discovered hiring Greenhouse YC startups
│   ├── discovered_lever.json       # Auto-discovered hiring Lever YC startups
│   ├── jobs.db                 # SQLite: tracks seen jobs & AI cache (local only)
│   └── analytics.db            # SQLite: daily metrics & missing tech trends (local only)
├── templates/
│   ├── telegram_report_header.html
│   ├── telegram_job.html
│   └── telegram_weekly_report.html
├── src/
│   ├── pipeline/               # Deterministic pipeline stages & orchestrator
│   ├── ai/                     # LLM communication & career insights review
│   ├── extractors/             # Plaintext resume loader & regex skill engine
│   ├── cache/                  # Cache storage wrappers
│   ├── database/               # SQLite tables operations
│   ├── models/                 # Dataclasses representing jobs and profiles
│   ├── notifications/          # Telegram formatting & sending
│   ├── utils/                  # Shared configuration & LiteLLM loaders
│   └── scraper.py              # Greenhouse, Lever, and HN scraper API logic
├── tests/                      # Full suite of unit & integration tests
│   ├── verify_slugs.py         # greenhouse verify script
│   └── verify_telegram.py      # telegram credentials verify script
├── companies.txt               # Manual Greenhouse slugs
├── companies_lever.txt         # Manual Lever slugs
├── discover_slugs.py           # Concurrently scans YC hiring startups for Greenhouse/Lever slugs
├── run_agent.bat               # Windows Task Scheduler automation batch script
├── main.py                     # Entry point (runs pipeline)
├── requirements.txt
└── .env.example
```
