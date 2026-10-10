# Daily Undervalued Online Business Acquisition Radar

An intelligent, automated acquisition research system that finds **undervalued digital businesses and online assets under $1,000 USD** (with a strictly qualified exception lane up to $5,000).

Rather than acting as a generic scraper, this system operates as a hybrid **digital-business acquisition analyst**, **Google SEO specialist**, **micro-SaaS investor**, and **financial due-diligence engine**. It searches trusted marketplaces daily, normalizes and deduplicates listings, analyzes organic search moat and algorithm risk, calculates conservative traffic replacement and monetization value, scores opportunities out of 100, and generates daily actionable dossiers.

---

## 1. Acquisition Strategy & Investment Thesis

### Primary Strategy: The Under-$1,000 Sweet Spot
- **Maximum Budget:** **$1,000 USD total**, inclusive of all escrow fees (Escrow.com min ~$30 or 3.25%) and registrar domain transfer fees (~$15).
- **Target Asset Classes:**
  - **Niche Utilities & Developer Tools:** Calculators, converters, formatters, and browser extensions with steady organic traffic that currently have zero monetization or merely a donation link.
  - **Organic Content & Review Sites:** Established content sites (1.5+ years old) monetized solely with low-yield affiliate programs (e.g. Amazon Associates 1-3%) that can be upgraded with direct brand sponsorships or ad networks.
  - **Micro-SaaS & Lightweight Software:** Early-stage software with active registered users and proven product utility ($10–$100 MRR) where the founder seeks a quick exit.
  - **Curated Newsletters & Digital Media:** Newsletters with engaged subscribers (open rate > 35%) and no sponsor monetization.
  - **Neglected Digital Assets with Authority:** Aged domains with indexed pages and quality referring backlinks that bypass Google's 6-month indexing sandbox.

### Exclusions & Red Flags
- Assets dependent on fake traffic or bot networks.
- Misleading revenue claims without third-party proof (Stripe, PayPal, AdSense).
- Copyright or scraping liabilities (e.g. unofficial TikTok/Instagram scrapers).
- Single customer or single traffic source concentration (>80%).
- Founder personal brand dependency (where the business cannot transfer).

---

## 2. Marketplace Coverage & Source Integrity

| Marketplace | Primary Inventory | Budget Fit (&le; $1k) | Buyer Protection | Access Method & Compliance |
|---|---|---|---|---|
| **Little Exits** *(formerly TinyAcquisitions)* | Micro-SaaS, tools, extensions, newsletters | **Highest** ($100–$5,000 focus) | Founder-to-founder; Escrow recommended | Public directory & project pages |
| **Motion Invest** | Vetted content sites, blogs, affiliate assets | **Moderate** (Starter sites $500–$2,000) | **High** (Vetted by team; assisted transfer) | Public catalog & sitemaps |
| **SideProjectors** | Side projects, developer tools, SaaS concepts | **High** ($100–$1,500 concentration) | Peer-to-peer (Escrow.com required) | Public explore & search directory |
| **Microns.io** | Curated micro-startups, SaaS, newsletters | **High** ($500–$3,000 sweet spot) | Curated by founder (Ilya Novohatskyi) | Public directory & digest feed |
| **Flippa** | Starter websites, domains, ecommerce, SaaS | **High** (Thousands under $1k) | Flippa Escrow / Escrow.com | Public search; Official API supported (`FLIPPA_API_KEY`) |
| **Acquire.com** *(MicroAcquire)* | B2B SaaS, micro-SaaS, ecommerce | **Low for &le; $1k; High for &le; $5k** | **High** (APA contracts, Escrow.com) | Public teasers; CSV/JSON export ingestion |
| **Investors Club** | Established cash-flowing blogs ($10k+) | **Low** ($10,000+ minimum) | **Highest** (24-point diligence reports) | Catalog monitor (for distressed liquidation) |

*Note: All adapters respect robots.txt crawl delays, public visibility rules, and avoid bypassing paywalls or anti-bot protections.*

---

## 3. SEO Intelligence & Traffic Valuation Engine

### Google Search Central Alignment
- **Zero-Click & AI Overviews Vulnerability:** Interactive utilities, micro-SaaS, and multi-step tools are classified as **Low Vulnerability** because AI Overviews cannot replace an interactive session. Generic definitional content sites are penalized as **High Vulnerability**.
- **Helpful Content & Algorithm Stability:** Trajectory tracking monitors 6-month traffic. Any asset suffering >30% drop is flagged with a **-15 point penalty** for search engine penalty risk.
- **Search Intent Analysis:** Computes commercial search intent ratio based on transactional keywords (e.g. *best*, *pricing*, *calculator*, *generator*, *vs*).

### Traffic & Audience Valuation Methodology
We maintain strict distinctions between theoretical traffic value, current revenue, and actual profit:
1. **Ad-Equivalent Traffic Value:** What an advertiser would pay Google Ads for equivalent search volume at prevailing niche CPC benchmarks. *(Formula: `Monthly Visits × Commercial Intent × 0.12 × Niche CPC`)*.
2. **Achievable Monetization Potential:** Realistic monthly cash flow across display ads (niche RPMs), high-paying affiliate programs, and micro-subscriptions.
3. **Rebuild Replacement Cost:** Capital and time required to build an equivalent asset from zero (developer build hours + Google sandbox domain aging).

---

## 4. 100-Point Scoring Rubric & Classifications

Every candidate is objectively evaluated across 6 categories:

| Category | Max Points | Evaluation Factors |
|---|:---:|---|
| **1. Existing Audience & Traffic Quality** | **25 pts** | Monthly visits, pageviews, subscribers, GA4/GSC verification status |
| **2. SEO Strength & Organic Growth** | **20 pts** | Domain age, referring domains, search intent, AI Overview resilience |
| **3. Revenue Quality & Financial Evidence** | **20 pts** | Proven cash flow, Stripe/payment proof, recurring business model |
| **4. Price Attractiveness & Payback** | **15 pts** | Asking price &le; $1,000, payback period, rebuild cost discount |
| **5. Ease of Transfer & Simplicity** | **10 pts** | Weekly operating hours (&le; 3 hrs/wk = max pts), clean tech stack |
| **6. Risk Profile & Data Confidence** | **10 pts** | Absence of red flags, data completeness |
| **Penalties** | **Deductions** | Declining traffic >30% (-15), Unverified claims (-10), Personal brand (-15) |

### Classifications
- **BUYER SHORTLIST:** Score &ge; 70 and asking price &le; $1,000. High-conviction candidates.
- **WATCHLIST:** Score 50–69, or assets needing price negotiation or metrics recheck.
- **REJECTED:** Score < 50 or fatal disqualifiers (copyright risk, platform ban). Stored with explicit reasons.

### Exceptional Section (Up to $5,000 USD)
Relaxes the normal $1,000 budget up to $5,000 **only** when an opportunity satisfies 6 strict criteria:
1. Proven, defensible positive cash flow or rare owned distribution channel.
2. Verified financial evidence (Stripe/PayPal connect).
3. Compelling valuation multiple (e.g. ~1x annual profit vs industry typical 2.5x–4.0x).
4. Full downside risk disclosure.
5. Specific pre-purchase verification protocol.
6. Explicit proof of why it is materially superior to sub-$1,000 alternatives.
*If nothing qualifies, the report explicitly states: "No exceptional opportunities justified exceeding the $1,000 budget today."*

---

## 5. System Architecture

```
side hustle/
├── .env                  # Configuration (budgets, scheduler, credentials)
├── radar.db              # SQLite database (listings, price history, scores)
├── main.py               # CLI entrypoint
├── radar/
│   ├── config.py         # App configuration & budget thresholds
│   ├── models.py         # Domain models (Listing, SEOMetrics, Valuation, Score)
│   ├── database.py       # SQLite persistence, migrations, and price tracking
│   ├── core/             # Normalization and cross-marketplace deduplication
│   ├── seo/              # Google SEO analyzer & niche CPC/RPM benchmarks
│   ├── valuation/        # All-in costs, payback periods, and 30-day playbooks
│   ├── scoring/          # 100-point rubric evaluator and classifier
│   ├── adapters/         # Modular marketplace source adapters
│   ├── reporting/        # Markdown and responsive HTML report generators
│   ├── scheduler/        # Daily runner and 08:00 Africa/Casablanca daemon
│   └── ui/               # Lightweight web server & interactive dashboard
├── data/fixtures/        # Calibrated acquisition test data
├── reports/              # Generated daily Markdown and HTML reports
└── tests/                # Automated unit and integration test suite
```

---

## 6. Quickstart & Usage

### 1. Setup Environment
```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies (already pinned in requirements.txt)
python -m pip install -r requirements.txt
```

### 2. Configure Settings
Copy `.env.example` to `.env` and adjust your preferences:
```ini
RADAR_MAX_NORMAL_BUDGET=1000.0
RADAR_MAX_EXCEPTIONAL_BUDGET=5000.0
RADAR_SCHEDULE_TIME=08:00
RADAR_TIMEZONE=Africa/Casablanca

# Optional email delivery
RADAR_ENABLE_EMAIL=false
RADAR_SMTP_HOST=smtp.gmail.com
RADAR_SMTP_USER=your_email@gmail.com
RADAR_SMTP_PASSWORD=your_app_password
RADAR_EMAIL_RECIPIENT=you@example.com

# Optional Telegram delivery
RADAR_ENABLE_TELEGRAM=false
RADAR_TELEGRAM_BOT_TOKEN=
RADAR_TELEGRAM_CHAT_ID=
```

### 3. CLI Commands

```bash
# Run a discovery and valuation cycle right now
python main.py run

# View current Buyer Shortlist (ranked deals under $1,000)
python main.py shortlist

# View Exceptional Candidates up to $5,000
python main.py exceptional

# Audit marketplace adapters, health, and access terms
python main.py sources

# Launch the interactive web dashboard
python main.py serve --port 8080
# Open http://localhost:8080 in your browser

# Run the background daily scheduler (08:00 Africa/Casablanca time)
python main.py daemon
```

### 4. Running Automated Tests
```bash
python -m pytest tests/
```

---

## 7. Scheduling Automation

### Option A: Built-In Python Daemon
Run as a background service:
```bash
python main.py daemon
```
Monitors the local clock and triggers the discovery and reporting pipeline daily at `08:00 Africa/Casablanca` time.

### Option B: Windows Task Scheduler
Create a scheduled task in PowerShell:
```powershell
$Action = New-ScheduledTaskAction -Execute "$PWD\.venv\Scripts\python.exe" -Argument "main.py run" -WorkingDirectory "$PWD"
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
Register-ScheduledTask -TaskName "DailyAcquisitionRadar" -Action $Action -Trigger $Trigger -Description "Daily Undervalued Business Acquisition Radar"
```

### Option C: Linux Cron (if deployed on VPS)
```bash
0 8 * * * cd /path/to/project && .venv/bin/python main.py run >> /var/log/radar.log 2>&1
```

---

## 8. Operating Costs & Credentials Summary

- **Core System Cost:** **$0 / month** (Runs entirely locally using SQLite, Python built-in server, and open search heuristics).
- **Optional Marketplace API Keys:**
  - `FLIPPA_API_KEY`: Free upon request from Flippa Developer portal.
  - `ACQUIRE_API_KEY`: Free upon registration on Acquire.com.
- **Optional Notification Integrations:**
  - SMTP: Works with any standard Gmail App Password or SendGrid free tier.
  - Telegram: Free via Telegram BotFather.
