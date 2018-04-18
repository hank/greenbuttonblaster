import re, io, csv, os, glob, time, configparser
from zipfile import ZipFile
from selenium.webdriver import Firefox, FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from apscheduler.schedulers.background import BackgroundScheduler


def processZips(output_dir):
    zips = glob.glob(os.path.join(output_dir, "*.zip"))
    for i in zips:
        print("Ripping from {}".format(i))
        with ZipFile(os.path.join(output_dir, i)) as my_z:
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
        # Remove the zip
        os.unlink(os.path.join(output_dir, i))

def buildDriver(output_dir):
    profile = FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", output_dir)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip,application/x-zip-compressed,application/octet-stream")
    profile.set_preference("browser.helperApps.alwaysAsk.force", False);
    options = Options()
    #options.set_headless(headless=True)
    driver = Firefox(firefox_options=options, firefox_profile=profile)
    return driver

def login(driver, username, password):
    driver.get("https://secure.bge.com/Pages/Login.aspx")
    username_element = driver.find_element_by_id("Username")

    driver.execute_script("arguments[0].scrollIntoView(true);", username_element)
    # Submit login form
    print("Filling Login Form...")
    elem = driver.find_element_by_css_selector("div.exc-form-inner.exc-tooltip > #Username")
    elem.click()
    actions = ActionChains(driver)
    actions.send_keys(username)
    actions.send_keys(Keys.TAB)
    actions.send_keys(Keys.TAB)
    actions.send_keys(password)
    actions.send_keys(Keys.RETURN)
    print("Logging in...")
    actions.perform()

def green_buttonize(driver):
    elem = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='widget-usage-export']/div/div[2]/form/div/div/div/div[3]/div/label"),
        )
    )
    # Scroll to view radio button and click it
    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
    elem.click()

    elem = driver.find_element_by_css_selector("input.button.primary")
    elem.click()

def slow_send_keys(elem, keys):
    for c in keys:
        elem.send_keys(c)
        time.sleep(1)

def initiateRequest(driver, username, password, tmp_output_dir):
    try:
        login(driver, username, password)

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

        green_buttonize(driver)

        print("Waiting for download to complete")
        time.sleep(5)
        # Deal with any downloads
        processZips(tmp_output_dir)
    except Exception as e:
        print("Exception encountered: {}".format(e))

def run():
    config = configparser.ConfigParser()
    config.read('settings.txt')
    tmp_output_dir = config['DEFAULT']['tmp_output_dir']
    username = config['DEFAULT']['username']
    password = config['DEFAULT']['password']

    print("Temporary directory: {}".format(tmp_output_dir))
    if not os.path.exists(tmp_output_dir):
        os.makedirs(tmp_output_dir)
    # Remove any stale downloads
    for f in glob.glob(os.path.join(tmp_output_dir, "*")):
        print("Removing {}".format(f))
        os.unlink(os.path.join(tmp_output_dir, f))

    driver = buildDriver(tmp_output_dir)

    scheduler = BackgroundScheduler()
    scheduler.add_job(initiateRequest, 'interval', minutes=20,
        args=(driver, username, password, tmp_output_dir))

    # Run the first job
    initiateRequest(driver, username, password, tmp_output_dir)

    print("Starting scheduler")
    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except:
        scheduler.shutdown(wait=False)

    print("Exiting driver")
    driver.quit()

if __name__ == "__main__":
    run()
