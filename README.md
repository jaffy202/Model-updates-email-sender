# LLM Updates Web Scraper & Email Alert System

A hybrid web scraping and alert pipeline designed to extract the latest Large Language Model (LLM) release announcements, summaries, and detailed descriptions from [llm-stats.com](https://llm-stats.com/llm-updates), detect new model releases against previous runs, and automatically dispatch email notifications.

This module demonstrates a dual-strategy scraping architecture: combining fast HTTP-based parsing with headless browser automation to handle both static content and JavaScript-rendered interactive UI elements, paired with an automated change-detection and email alerting workflow.

---

## Table of Contents

- [Architecture & Workflow](#architecture--workflow)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [1. Running the Automated Alert Pipeline (`main.py`)](#1-running-the-automated-alert-pipeline-mainpy)
  - [2. Direct Module Invocation / Import](#2-direct-module-invocation--import)
- [Code Breakdown & Reference](#code-breakdown--reference)
  - [`main.py` — Pipeline & Notification Manager](#mainpy--pipeline--notification-manager)
  - [`llm_scraping.py` — Core Scraper Engine](#llm_scrapingpy--core-scraper-engine)
- [DOM Selectors Reference](#dom-selectors-reference)
- [Senior Engineer Insights & Optimization Recommendations](#senior-engineer-insights--optimization-recommendations)

---

## Architecture & Workflow

Modern web applications frequently mix server-rendered markup with client-side interactive widgets. The system executes a coordinated scraping, comparison, and dispatch pipeline:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Trigger Pipeline (`main.py`)                             │
│ - Invokes `get_latest_model_updates()`                      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Scrape & Aggregate Updates (`llm_scraping.py`)           │
│ - Discover cards statically via `requests` + `BeautifulSoup` │
│ - Expand interactive descriptions via `selenium`            │
│ - Return formatted updates text                             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Change Detection Check                                   │
│ - Compare new output with `last_output.txt`                 │
│ - Check if file exists or text has changed                  │
└───────────────┬─────────────────────────────┬───────────────┘
                │ (Different / Initial)       │ (Identical)
                ▼                             ▼
┌───────────────────────────────┐ ┌───────────────────────────┐
│ 4. Update & Dispatch          │ │ 4. No-Op                  │
│ - Overwrite `last_output.txt` │ │ - Log "[NO CHANGE]"       │
│ - Send email via SMTP         │ │ - Terminate cleanly       │
└───────────────────────────────┘ └───────────────────────────┘
```

---

## Features

- **Automated Change Detection**: Tracks previously scraped model updates in `last_output.txt` and only triggers notifications when new releases or modified details are detected.
- **Integrated Email Alerts**: Automatically formats and delivers update summaries to designated recipients via SMTP (e.g. Gmail).
- **Hybrid Scraping Engine**: Uses lightweight HTTP requests where possible and delegates to Selenium only when interactive UI rendering is required.
- **Automated Driver Management**: Leverages `webdriver-manager` to automatically download and configure matching ChromeDriver binaries.
- **Explicit Synchronization**: Employs `WebDriverWait` with `expected_conditions` to prevent race conditions during DOM re-renders.
- **Resilient Exception Handling**: Wraps UI clicks and email operations in structured `try/except` blocks to ensure robust execution.

---

## Directory Structure

```text
llm_engineering/week1/web_scraping/
├── __init__.py           # Package marker
├── llm_scraping.py       # Core scraper implementation
├── main.py               # Orchestrator: change-detection & email dispatch
├── last_output.txt       # Cache of the latest scraped output (generated)
├── requirements.txt      # Python dependencies
└── README.md             # Module documentation
```

---

## Prerequisites

- **Python**: 3.9 or higher
- **Google Chrome**: Installed on the host operating system
- **Network Access**: Outbound HTTPS connectivity to `https://llm-stats.com` and SMTP access to `smtp.gmail.com`
- **Email Credentials**: A Gmail account with a generated **16-character App Password** (required by Google for SMTP authentication)

---

## Installation

1. **Navigate to the module directory**:
   ```bash
   cd llm_engineering/week1/web_scraping
   ```

2. **(Optional) Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Dependencies Overview

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `requests` | `2.34.2` | Fast HTTP requests for static page fetching |
| `beautifulsoup4` | `4.15.0` | High-level HTML DOM parsing and CSS selector querying |
| `selenium` | `4.49.0` | Browser automation to execute JavaScript and trigger clicks |
| `webdriver_manager` | `4.1.2` | Automated ChromeDriver binary acquisition and path resolution |

---

## Usage

### 1. Running the Automated Alert Pipeline (`main.py`)

Execute `main.py` directly from the terminal:

```bash
python main.py
```

**Pipeline Workflow**:
1. Calls `get_latest_model_updates()` to fetch current LLM release details.
2. Reads `last_output.txt` (if present) and checks for content changes.
3. If new updates are found or if running for the first time:
   - Saves the fresh updates to `last_output.txt`.
   - Sends an email alert to the configured recipient.
4. If no changes are detected, prints `[NO CHANGE]` and exits without sending duplicate emails.

### Sample Output Format

```text
Model: GPT-6.1 Sol
Lead: GPT-6.1 Sol is a language model from OpenAI, released in September 2026, with multimodal input, a 1.1M-token context window...
Description: GPT-6.1 Sol is OpenAI's GPT-6.1 model delivering near-Astra performance for complex coding, computer use, and professional work...

Model: Claude Sonnet 5.5
Lead: Claude Sonnet 5.5 is a language model from Anthropic, released in September 2026, with multimodal input, a 1M-token context window...
Description: Claude Sonnet 5.5 is the second model in Anthropic's Claude 5.5 family and a faster, lower-cost complement to Claude Opus 5.5...
```

---

## Code Breakdown & Reference

### `main.py` — Pipeline & Notification Manager

#### Key Configurations
- `OUTPUT_FILE`: `Path` — Path to `last_output.txt` storing historical run outputs.
- `RECIPIENT_EMAIL`: `str` — Target inbox for alert emails.
- `SENDER_EMAIL`: `str` — Sender Google email account.
- `SENDER_PASSWORD`: `str` — 16-character Google App Password for SMTP authentication.
- `SMTP_SERVER`: `str` — Hostname of the email server (`smtp.gmail.com`).
- `SMTP_PORT`: `int` — SMTP port (`587` for STARTTLS / `465` for SSL).

#### Functions
- **`send_email(subject: str, body: str, recipient: str) -> bool`**:
  Constructs a `MIMEMultipart` email with plain-text UTF-8 encoding, establishes an authenticated SMTP connection, and transmits the message.
- **`main()`**:
  Coordinates scraping, performs string diffing against `OUTPUT_FILE`, updates local storage, and triggers email notifications upon difference detection.

---

### `llm_scraping.py` — Core Scraper Engine

#### Constants
- **`BASE_URL`**: `str` = `"https://llm-stats.com"` — Base domain used to resolve relative hyperlinks.
- **`LLM_UPDATES_URL`**: `str` = `f"{BASE_URL}/llm-updates"` — Target listing endpoint.

#### `get_latest_model_updates(BASE_URL, LLM_UPDATES_URL) -> str`
Orchestrates the multi-stage extraction:
1. **Index Parsing**: Queries `LLM_UPDATES_URL` via `requests` and locates all update cards (`a.group.flex`).
2. **Card Iteration & Model Extraction**: Extracts model name from `<h3>` and builds detail URL.
3. **Lead Extraction**: Fetches static HTML and reads summary lead (`p.model-lead`).
4. **Dynamic Description Expansion**: Opens Chrome WebDriver, clicks `button.ml-1`, waits for `p.model-description`, and cleans UI artifacts.
5. **Returns**: Formatted newline-separated string containing aggregated model entries.

---

## DOM Selectors Reference

| Selector | Tool | Purpose |
| :--- | :--- | :--- |
| `a.group.flex` | BeautifulSoup | Selects individual update cards on the index page |
| `h3` | BeautifulSoup | Extracts the model title from an update card |
| `p.model-lead` | BeautifulSoup | Extracts the initial lead / summary text on detail page |
| `button.ml-1` | Selenium | Locates the interactive "more/expand" button |
| `p.model-description` | Selenium | Locates the fully rendered model description after expansion |

---

