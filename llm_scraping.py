from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://llm-stats.com"
LLM_UPDATES_URL = f"{BASE_URL}/llm-updates"


def _fetch_model_lead(args: tuple) -> tuple:
    """Fetch the static lead text for a model detail page (runs in thread pool)."""
    title, url = args
    try:
        html = requests.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        lead_tag = soup.select_one("p.model-lead")
        return title, lead_tag.text if lead_tag else None
    except Exception as e:
        print(f"[WARNING] Could not fetch lead for {title}: {e}")
        return title, None


def _create_driver() -> webdriver.Chrome:
    """Create a single reusable headless Chrome driver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Resolve driver path once, outside the loop
    driver_path = ChromeDriverManager().install()
    return webdriver.Chrome(service=Service(driver_path), options=chrome_options)


def _get_description(driver: webdriver.Chrome, url: str):
    """Navigate to a model page, click the reveal button, and return the description.

    Retries up to 3 times to handle StaleElementReferenceException (DOM rebuild
    after page load) and uses a JS click to bypass ElementClickInterceptedException
    caused by overlapping elements.
    """
    from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException

    driver.get(url)
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Re-fetch the button on every attempt to avoid stale references
            button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.ml-1"))
            )
            # Scroll into view and use JS click to bypass intercepting overlays
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            driver.execute_script("arguments[0].click();", button)

            desc_elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.model-description"))
            )
            return desc_elem.text.removesuffix("less")

        except (StaleElementReferenceException, ElementClickInterceptedException) as e:
            if attempt < max_attempts - 1:
                continue  # retry
            print(f"[WARNING] Description not found for {url} after {max_attempts} attempts: {e}")
            return None
        except Exception as e:
            print(f"[WARNING] Description not found for {url}: {e}")
            return None


def get_latest_model_updates(BASE_URL=BASE_URL, LLM_UPDATES_URL=LLM_UPDATES_URL):
    # Step 1: Scrape the update cards
    llm_updates_html = requests.get(LLM_UPDATES_URL, timeout=10).text
    llm_updates_soup = BeautifulSoup(llm_updates_html, "html.parser")
    llm_updates_cards = llm_updates_soup.select("a.group.flex")

    # Collect (title, url) pairs, skipping cards without a title
    cards = []
    for card in llm_updates_cards:
        title_tag = card.select_one("h3")
        if not title_tag:
            continue
        href = card.get("href", "")
        cards.append((title_tag.text, f"{BASE_URL}{href}"))

    # Step 2: Fetch all lead texts in parallel (replaces sequential requests.get per card)
    leads = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_fetch_model_lead, card): card for card in cards}
        for future in as_completed(futures):
            title, lead = future.result()
            leads[title] = lead

    # Step 3: Use a single shared Selenium driver for all description reveals
    driver = _create_driver()
    parts = []
    try:
        for title, url in cards:
            entry = [f"\nModel: {title}"]
            lead = leads.get(title)
            if lead:
                entry.append(f"Lead: {lead}")
            description = _get_description(driver, url)
            if description:
                entry.append(f"Description: {description}")
            parts.append("\n".join(entry))
    finally:
        driver.quit()

    return "\n".join(parts)
