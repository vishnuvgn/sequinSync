import os, time, random
from dotenv import load_dotenv
load_dotenv()
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# additional imports needed for linux vm:
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# time.sleep(random.randint(a, b)) is called in some places so that suspicious activity is (hopefully!) not detected

def initiateRemote():
    options = FirefoxOptions()
    options.add_argument('--headless')  # Run in headless mode
    gecko_path = '/snap/bin/geckodriver'
    driver = webdriver.Firefox(service=FirefoxService(gecko_path), options=options)
    return driver

def initiateLocal():
    driver = webdriver.Safari()
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

def compileFieldList(table_urls):
    table_fields = {}
    
    
    d = initiateLocal()
    # d = initiateRemote()
    
    
    for table, url in table_urls.items():
        time.sleep(random.randint(3, 5))
        d = login(d, url)
        fields = get_column_names(d)
        table_fields[table] = fields

    # print(table_fields)
    return table_fields

compileFieldList({"Members" : "https://airtable.com/app03GWdFHFCFlo9u/tblyIeCi2GxlIAG49/viwRpq5VEnQboWjJV?blocks=hide"})