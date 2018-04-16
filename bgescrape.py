import re
import io
import csv
from zipfile import ZipFile
import os
import glob
import time
import configparser
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TMP_OUTPUT_DIR = r'c:\windows\temp\bge'

config = configparser.ConfigParser()
config.read('settings.txt')
TMP_OUTPUT_DIR = config['DEFAULT']['tmp_output_dir']
USERNAME = config['DEFAULT']['username']
PASSWORD = config['DEFAULT']['password']

print("Temporary directory: {}".format(TMP_OUTPUT_DIR))
if not os.path.exists(TMP_OUTPUT_DIR):
    os.makedirs(TMP_OUTPUT_DIR)
# Remove any stale downloads
for f in glob.glob(os.path.join(TMP_OUTPUT_DIR, "*")):
    print("Removing {}".format(f))
    os.unlink(os.path.join(TMP_OUTPUT_DIR, f))

profile = FirefoxProfile()
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.download.dir", TMP_OUTPUT_DIR)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip,application/x-zip-compressed,application/octet-stream")
profile.set_preference("browser.helperApps.alwaysAsk.force", False);
options = Options()
#options.set_headless(headless=True)
driver = Firefox(firefox_options=options, firefox_profile=profile)
actions = ActionChains(driver)

driver.get("https://secure.bge.com/Pages/Login.aspx")
username_element = driver.find_element_by_id("Username")

driver.execute_script("arguments[0].scrollIntoView(true);", username_element)

# Submit login form
print("Filling Login Form...")
elem = driver.find_element_by_css_selector("div.exc-form-inner.exc-tooltip > #Username")
elem.click()
actions.send_keys(USERNAME)
actions.send_keys(Keys.TAB)
actions.send_keys(Keys.TAB)
actions.send_keys(PASSWORD)
actions.send_keys(Keys.RETURN)
print("Logging in...")
actions.perform()

# Wait for page to load
print("Waiting for clickability on sidebar...")
WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, '.exc-sidebar-left'),
    )
)
print("Going to Green Button Connect...")
driver.get("https://secure.bge.com/MyAccount/MyBillUsage/pages/secure/GreenButtonConnectDownloadMyData.aspx")

print("Switching to inner frame...")
frame = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "#uiOpowerIFrame iframe")
    )
)
driver.switch_to.frame(frame)
elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, ".green-button")
    )
)

time.sleep(5)
print("Clicking Green Button...")
elem = driver.find_element_by_css_selector(".green-button")
driver.execute_script("arguments[0].scrollIntoView(true);", elem)
elem.click()

elem = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@id='widget-usage-export']/div/div[2]/form/div/div/div/div[3]/div/label"),
    )
)
driver.execute_script("arguments[0].scrollIntoView(true);", elem)
elem.click()
elem = driver.find_element_by_id("date-picker-from")
elem.click()
elem.send_keys(Keys.SHIFT+Keys.TAB)
elem.send_keys(Keys.SHIFT+Keys.TAB)
for c in "04102018":
    elem.send_keys(c)
    time.sleep(1)
elem = driver.find_element_by_id("date-picker-to")
elem.click()
elem.send_keys(Keys.SHIFT+Keys.TAB)
elem.send_keys(Keys.SHIFT+Keys.TAB)
for c in "04142018":
    elem.send_keys(c)
    time.sleep(1)
elem = driver.find_element_by_css_selector("input.button.primary")
elem.click()

time.sleep(8)

driver.quit()

# Deal with any downloads
zips = glob.glob(os.path.join(TMP_OUTPUT_DIR, "*.zip"))
for i in zips:
    print("Ripping from {}".format(i))
    with ZipFile(os.path.join(TMP_OUTPUT_DIR, i)) as my_z:
        for zi in my_z.infolist():
            if not zi.is_dir():
                print("Opening {}".format(zi.filename))
                with my_z.open(zi.filename, 'r') as f:
                    s = f.read()
                    powerreader = csv.reader(s.decode("utf-8").splitlines())
                    for row in powerreader:
                        if (len(row) == 8 and
                           re.search(r'Electric|Gas', row[0], re.I) is not None):
                            print(" | ".join(row))

