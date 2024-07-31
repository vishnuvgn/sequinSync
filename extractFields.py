import os, time, random, csv
from dotenv import load_dotenv
load_dotenv()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# additional imports needed for linux vm:
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# time.sleep(random.randint(a, b)) is called in some places so that suspicious activity is (hopefully!) not detected


def initiateLocal():
    driver = webdriver.Safari()
    return driver

def initiateRemote():
    download_directory = '/home/workmerk/sequinSync/csvs'

    options = FirefoxOptions()

    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", download_directory)
    options.set_preference("browser.download.manager.showWhenStarting", False)

    options.add_argument('--headless')  # Run in headless mode
    options.set_preference('dom.webdriver.enabled', False)
    gecko_path = '/snap/bin/geckodriver' # path to geckodriver on my linux
    driver = webdriver.Firefox(service=FirefoxService(gecko_path), options=options)
    return driver


def login(driver, url):
    
    print(driver)
    driver.get(url)

    try:

        email_field = driver.find_element(By.ID, "emailLogin")
        email_field.send_keys(os.getenv('AIRTABLE_LOGIN_EMAIL'))
        email_field.send_keys(Keys.RETURN)

        time.sleep(random.randint(3, 5))

        password_field = driver.find_element(By.ID, "passwordLogin")
        password_field.send_keys(os.getenv('AIRTABLE_LOGIN_PASSWORD')) 


        time.sleep(random.randint(3, 5))

        password_field.send_keys(Keys.RETURN)

        time.sleep(random.randint(3, 5))
        return driver
    
    except:
        return driver

def get_column_names(driver):
    
    fields = []

    header_row = driver.find_element(By.CSS_SELECTOR, 'div.headerRow.leftPane')
    
    # Find the span with class name within the headerRow leftPane
    name_span = header_row.find_element(By.CSS_SELECTOR, 'span.name')
    
    # Extract the text from the span
    pk_field = name_span.text
    fields.append(pk_field)
    
    print(f'The text inside the span with class "name" is: {pk_field}')

    header_row_right = driver.find_element(By.CSS_SELECTOR, 'div.headerRow.rightPane')
    
    # Find all spans with class name within the headerRow rightPane
    name_spans = header_row_right.find_elements(By.CSS_SELECTOR, 'span.name')

    # Extract the text from each span and print it
    for name_span in name_spans:
        name_text = name_span.text
        fields.append(name_text)
        print(f'The text inside the span with class "name" is: {name_text}')


    return fields

def download(driver):
    controlBar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.viewSwitcherContainer > div:nth-child(1)')))
    print("controlBar found")
    syncFieldsBtn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[4]/div[1]/div[2]/div[1]/div[1]/div/div[3]/div'))
    )
    print("syncFieldsBtn found")
    # # syncFieldsBtn = controlBar.find_element()
    syncFieldsBtn.click()

    print("syncFieldsBtn clicked")

    time.sleep(random.randint(3, 5))

    downloadBtn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[36]/ul/li[10]/span')))
    print("downloadBtn found")
    # downloadBtn.click()
    driver.execute_script("arguments[0].click();", downloadBtn)
    print("downloadBtn clicked")

def compileFieldList(table_urls, whichServer):
    table_fields = {}
    if whichServer == "Local" or whichServer == "local" or whichServer == "l":
        driver = initiateLocal()
        for table, url in table_urls.items():
            time.sleep(random.randint(3, 5))
            driver = login(driver, url)
            fields = get_column_names(driver)
            table_fields[table] = fields

    else:
        driver = initiateRemote()
        for table, url in table_urls.items():
            time.sleep(random.randint(3, 5))
            driver = login(driver, url)
            download(driver)
            fp = table + "-Sync Fields.csv" # FIXME: This is a temporary solution
            print(fp)
            fields = extract_header_from_csv(fp)
            print("Fields: ",fields)
            table_fields[table] = fields
        


    # print(table_fields)
    driver.quit()
    return table_fields

def extract_header_from_csv(file_path):
    file_path = os.path.join("/home/workmerk/sequinSync/csvs", file_path)
    with open(file_path, newline='') as file:
        reader = csv.reader(file)
        header_row = next(reader, [])  # Returns an empty list if file is empty or no header row
        clean_header_row = [column.strip().lstrip('\ufeff') for column in header_row]
    return clean_header_row