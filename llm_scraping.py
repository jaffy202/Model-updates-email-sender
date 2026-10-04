from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://llm-stats.com"
LLM_UPDATES_URL = f"{BASE_URL}/llm-updates"

def get_latest_model_updates(BASE_URL=BASE_URL, LLM_UPDATES_URL=LLM_UPDATES_URL):
    llm_updates = ''
    llm_updates_html = requests.get(LLM_UPDATES_URL).text
    llm_updates_soup = BeautifulSoup(llm_updates_html, "html.parser")

    llm_updates_cards = llm_updates_soup.select("a.group.flex")

    # Step 2: Loop through each card
    for llm_updates_card in llm_updates_cards:
        title = llm_updates_card.select_one("h3")
        if not title:
            continue
        
        llm_updates += f'\nModel: {title.text}'

        href = llm_updates_card['href']
        model_detail_url = f"{BASE_URL}{href}"

        # Step 3: Get static lead text with requests
        model_details_html = requests.get(model_detail_url).text
        model_details_soup = BeautifulSoup(model_details_html, "html.parser")
        model_lead = model_details_soup.select_one("p.model-lead")
        if model_lead:
            llm_updates += f'\nLead: {model_lead.text}'

        # Step 4: Use Selenium to click and reveal description
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")              # run without GUI
        options.add_argument("--no-sandbox")            # required in CI
        options.add_argument("--disable-dev-shm-usage") # avoid shared memory issues

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.get(model_detail_url)

        # Halting the execution for 1 second
        time.sleep(1)

        try:
            # Click the button
            button = driver.find_element(By.CSS_SELECTOR, "button.ml-1")
            button.click()

            # Wait until description appears
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p.model-description"))
            )

            # Extract updated description
            model_description = driver.find_element(By.CSS_SELECTOR, "p.model-description").text.removesuffix('less')
            llm_updates += f'\nDescription: {model_description}'

        except Exception as e:
            print("Description not found:", e)

        driver.quit()
    
    return llm_updates
