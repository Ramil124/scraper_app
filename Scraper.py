from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time

app = FastAPI()

class URLRequest(BaseModel):
    url: str

def scrape_visible_main_text(url: str) -> str:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        time.sleep(5)  # wait for rendering


        # Wait until at least the main content or table appears
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Scroll to bottom to trigger lazy content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        js_script = """
        function getVisibleText(el) {
            var text = '';
            function hasExcludedClass(node) {
                while (node && node !== document.body) {
                    if (node.classList && (node.classList.contains('menu') || node.classList.contains('for_link_con'))) {
                        return true;
                    }
                    node = node.parentElement;
                }
                return false;
            }
            function isVisible(node) {
                var style = window.getComputedStyle(node);
                var rect = node.getBoundingClientRect();
                return (
                    style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    rect.width > 0 &&
                    rect.height > 0
                );
            }
            function walk(node) {
                if (node.nodeType === Node.TEXT_NODE) {
                    if (isVisible(node.parentElement) && !hasExcludedClass(node.parentElement)) {
                        var trimmed = node.textContent.trim();
                        if (trimmed) {
                            text += trimmed + "\\n";
                        }
                    }
                } else if (node.nodeType === Node.ELEMENT_NODE && isVisible(node) && !hasExcludedClass(node)) {
                    for (var i = 0; i < node.childNodes.length; i++) {
                        walk(node.childNodes[i]);
                    }
                }
            }
            walk(el);
            return text;
        }
        return getVisibleText(document.querySelector('main') || document.body);
        """

        visible_text = driver.execute_script(js_script)
        clean_text = "\n".join([line.strip() for line in visible_text.splitlines() if line.strip()])
        return clean_text if clean_text else "No visible main content found."

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

    finally:
        driver.quit()


@app.post("/scrape")
def scrape_handler(req: URLRequest):
    text = scrape_visible_main_text(req.url)
    return {"text": text}
