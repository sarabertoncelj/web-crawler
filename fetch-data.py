import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
from bs4 import BeautifulSoup
import urllib.robotparser
import datetime

import dbfunctions
import frontier

WEB_PAGE_ADDRESS = "https://computingforgeeks.com/"
WEB_DRIVER_LOCATION = "/usr/bin/chromedriver"
TIMEOUT = 5

WEB_PAGE_ADDRESS = frontier.get_new_url()

rp = urllib.robotparser.RobotFileParser()
rp.set_url(WEB_PAGE_ADDRESS + "/robots.txt")
rp.read()

robots = rp.can_fetch("*", WEB_PAGE_ADDRESS)
print(robots)

if robots:
    chrome_options = Options()
    # If you comment the following line, a browser will show ...
    chrome_options.add_argument("--headless")

    #Adding a specific user agent
    chrome_options.add_argument("user-agent=fri-ieps-TEST")

    #to get status code
    d = DesiredCapabilities.CHROME
    d["goog:loggingPrefs"] = {"performance": "ALL"}

    print(f"Retrieving web page URL '{WEB_PAGE_ADDRESS}'")
    driver = webdriver.Chrome(WEB_DRIVER_LOCATION, options=chrome_options, desired_capabilities=d)
    driver.get(WEB_PAGE_ADDRESS)

    #status code
    #print (driver.get_log('performance')[3])
    tmp = driver.get_log('performance')[3]['message']
    logs_json = json.loads(tmp)
    print("Status: " + logs_json["message"]["params"]["response"]["headers"]["status"])

    # Timeout needed for Web page to render (read more about it)
    time.sleep(TIMEOUT)

    html = driver.page_source
    driver.close()

    # iskanje vseh povezav z znacko a in tipa href
    extractedLinks = []
    soup = BeautifulSoup(html, features="html.parser")
    for link in soup.findAll('a'):
        href = link.get('href')
        extractedLinks.append(href)
    frontier.store_urls(extractedLinks)
    print("First 10 extracted links: " + str(extractedLinks[:min(len(extractedLinks), 10)]))
    print("Number of extracted links: " + str(len(extractedLinks)))

    #dodajanje vseh pridobljenih povezav v bazo
    testString = "test string"
    dbfunctions.clear_db()
    dbfunctions.create_new_site(WEB_PAGE_ADDRESS, testString, testString)
    siteid = dbfunctions.get_site_id(WEB_PAGE_ADDRESS)
    pagetype = "HTML"
    dbfunctions.create_new_page(siteid, pagetype, testString, testString, 200)
    #dbfunctions.create_new_image(1, testString, "content type", '0',)
    #dbfunctions.create_new_page_data(1, "data type code", '0')
    #dbfunctions.create_new_link(1, 2)
