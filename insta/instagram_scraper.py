from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# Set up Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in background
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Initialize driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(10)

# Open BBC News Instagram page
driver.get("https://www.instagram.com/bbcnews/")

# Scroll down to load posts
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(3)

# Fetch the LAST post link
last_post = driver.find_element(By.XPATH, "(//a[contains(@href, '/p/')])[last()]").get_attribute("href")
driver.get(last_post)

# Extract Image URL and Caption
image_url = driver.find_element(By.XPATH, "//img[contains(@class, 'x5yr21d')]").get_attribute("src")
caption = driver.find_element(By.XPATH, "//h1").text

# Print results
print("Image URL:", image_url)
print("Caption:", caption)

# Close driver
driver.quit()
