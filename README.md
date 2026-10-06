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
  - [`main.py` — Pipeline Orchestrator](#mainpy--pipeline-orchestrator)
  - [`email_formatter.py` — Email Formatter](#email_formatterpy--email-formatter)
  - [`email_sender.py` — SMTP Dispatcher](#email_senderpy--smtp-dispatcher)
  - [`llm_scraping.py` — Core Scraper Engine](#llm_scrapingpy--core-scraper-engine)
- [DOM Selectors Reference](#dom-selectors-reference)

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
│ - Return raw formatted text                                 │
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
│ 4. Format & Dispatch          │ │ 4. No-Op                  │
│ - Overwrite `last_output.txt` │ │ - Log "[NO CHANGE]"       │
│ - Parse models into structs   │ │ - Terminate cleanly       │
│   (`email_formatter.py`)      │ └───────────────────────────┘
│ - Build HTML + plain-text     │
│   email bodies                │
│ - Send multipart email        │
│   via SMTP (`email_sender.py`)│
└───────────────────────────────┘
```

---

## Features

- **Automated Change Detection**: Tracks previously scraped model updates in `last_output.txt` and only triggers notifications when new releases or modified details are detected.
- **Styled HTML Emails**: Produces rich, provider colour-coded HTML emails with a dark header banner, per-model cards, and a plain-text fallback — all via `email_formatter.py`.
- **Multipart Email Dispatch**: Sends `multipart/alternative` messages so every email client (Gmail, Outlook, plain-text) renders the best version it supports.
- **Hybrid Scraping Engine**: Uses lightweight HTTP requests where possible and delegates to Selenium only when interactive UI rendering is required.
- **Parallel Lead Fetching**: Concurrent `ThreadPoolExecutor` fetches static lead text across all model cards simultaneously, significantly reducing total scrape time.
- **Automated Driver Management**: Leverages `webdriver-manager` to automatically download and configure matching ChromeDriver binaries.
- **Explicit Synchronization**: Employs `WebDriverWait` with `expected_conditions` to prevent race conditions during DOM re-renders.
- **JS-Based Click with Retry**: Uses `execute_script("arguments[0].click()")` to bypass overlapping UI overlays (`ElementClickInterceptedException`) and retries up to 3 times on stale DOM references (`StaleElementReferenceException`), ensuring reliable description expansion even on dynamic pages.
- **Resilient Exception Handling**: Wraps UI clicks and email operations in structured `try/except` blocks to ensure robust execution.

---

## Directory Structure

```text
Model-updates-email-sender/
├── llm_scraping.py       # Core scraper: static + headless browser extraction
├── email_formatter.py    # Parses raw output; builds HTML & plain-text email bodies
├── email_sender.py       # SMTP dispatcher — sends multipart/alternative email
├── main.py               # Orchestrator: change-detection, formatting & dispatch
├── last_output.txt       # Cache of the latest scraped output (generated)
├── requirements.txt      # Python dependencies
├── .gitignore            # Git ignore rules
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
   cd Model-updates-email-sender
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

### `main.py` — Pipeline Orchestrator

#### Key Configurations
- `OUTPUT_FILE`: `Path` — Path to `last_output.txt` storing historical run outputs.
- `RECIPIENT_EMAIL`: `str` — Target inbox for alert emails (read from env var).
- `SENDER_EMAIL`: `str` — Sender Google email account (read from env var).
- `SENDER_PASSWORD`: `str` — 16-character Google App Password for SMTP authentication (read from env var).

#### Functions
- **`main()`**:
  Coordinates scraping, performs string diffing against `OUTPUT_FILE`, updates local storage, calls `email_formatter` to build HTML and plain-text bodies, then dispatches the email via `email_sender`.

---

### `email_formatter.py` — Email Formatter

Parses the raw scraper string into structured data and renders the email bodies.

#### Functions
- **`parse_models(raw_text: str) -> list[dict]`**:
  Splits the raw text on `Model:` boundaries and extracts `name`, `lead`, `description`, `provider`, and `colors` (provider-matched colour palette) for each entry.
- **`build_html_email(models: list[dict], date_str: str) -> str`**:
  Returns a complete HTML document using table-based layout with inline CSS (compatible with Gmail and Outlook). Each model is rendered as a card with a colour-coded provider header, a bold lead row, and a description row. Includes a dark header banner and a footer.
- **`build_plain_text_email(models: list[dict], date_str: str) -> str`**:
  Returns a clean, human-readable plain-text alternative with `━━━` section dividers and clearly labelled `SUMMARY` / `DETAILS` blocks.

---

### `email_sender.py` — SMTP Dispatcher

Handles all SMTP connection and message transmission logic.

#### Constants
- `SMTP_SERVER`: `str` — `"smtp.gmail.com"`
- `SMTP_PORT`: `int` — `587` (STARTTLS); set to `465` to switch to SMTP_SSL.

#### Functions
- **`send_email(subject, html_body, plain_body, sender_email, sender_password, recipient) -> bool`**:
  Constructs a `MIMEMultipart("alternative")` message, attaches the plain-text part first and the HTML part second (email clients render the last matching part they support), establishes an authenticated STARTTLS/SSL SMTP connection, and transmits the message.

---

### `llm_scraping.py` — Core Scraper Engine

#### Constants
- **`BASE_URL`**: `str` = `"https://llm-stats.com"` — Base domain used to resolve relative hyperlinks.
- **`LLM_UPDATES_URL`**: `str` = `f"{BASE_URL}/llm-updates"` — Target listing endpoint.

#### Private Helpers

- **`_fetch_model_lead(args: tuple) -> tuple`**:
  Fetches the static `p.model-lead` text for a single model detail page using `requests` + `BeautifulSoup`. Designed to run inside a `ThreadPoolExecutor` for concurrent execution across all cards.

- **`_create_driver() -> webdriver.Chrome`**:
  Instantiates a headless Chrome `webdriver.Chrome` instance with `--no-sandbox` and `--disable-dev-shm-usage` flags. Resolves the ChromeDriver binary once via `ChromeDriverManager().install()` so the path lookup is not repeated per-page.

- **`_get_description(driver, url) -> str | None`**:
  Navigates to a model detail page and expands its full description. Uses a **JS-based click** (`execute_script("arguments[0].click()")`) to bypass `ElementClickInterceptedException` caused by floating UI overlays, and scrolls the button into view before clicking. Implements a **retry loop (up to 3 attempts)** that re-fetches the button element on each attempt to recover from `StaleElementReferenceException` triggered by post-navigation DOM rebuilds.

#### `get_latest_model_updates(BASE_URL, LLM_UPDATES_URL) -> str`
Orchestrates the multi-stage extraction:
1. **Index Parsing**: Queries `LLM_UPDATES_URL` via `requests` and locates all update cards (`a.group.flex`).
2. **Card Iteration & Model Extraction**: Extracts model name from `<h3>` and builds detail URL.
3. **Parallel Lead Extraction**: Dispatches `_fetch_model_lead` across all cards concurrently using `ThreadPoolExecutor(max_workers=8)`.
4. **Dynamic Description Expansion**: Reuses a single shared `webdriver.Chrome` instance (created by `_create_driver`) to sequentially call `_get_description` per card — clicks `button.ml-1`, waits for `p.model-description`, and strips trailing `"less"` UI text.
5. **Returns**: Formatted newline-separated string containing aggregated model entries.

---

## DOM Selectors Reference

| Selector | Tool | Interaction | Purpose |
| :--- | :--- | :--- | :--- |
| `a.group.flex` | BeautifulSoup | Static parse | Selects individual update cards on the index page |
| `h3` | BeautifulSoup | Static parse | Extracts the model title from an update card |
| `p.model-lead` | BeautifulSoup | Static parse | Extracts the initial lead / summary text on detail page |
| `button.ml-1` | Selenium | JS click + retry | Locates the interactive "more/expand" button; clicked via `execute_script` to bypass overlay intercepts |
| `p.model-description` | Selenium | `WebDriverWait` | Locates the fully rendered model description after expansion |

---

