import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
from bs4 import BeautifulSoup
from queue import Queue
import urllib.request
import urllib.robotparser
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import dbfunctions
import requests
import psycopg2

WEB_PAGE_ADDRESS = "https://www.gov.si/"
#WEB_PAGE_ADDRESS = "https://www.amazon.de/?language=en_GB"
WEB_DRIVER_LOCATION = "/usr/bin/chromedriver"
TIMEOUT = 5
data_types = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'csv', 'ods', 'xlsx']
img_types = ['jpg', 'png', 'ico', 'jpeg', 'gif']
percent_encoding = {"%20":" ", '"':"%22", "%25":"%", "%2d":"-", "%2e":".", "%3c":"<", "%3e":">", "%5c":r"\\", "%5e":"^", "%5f":"_", "%60":"`", "%7b":"{", "%7c":"|", "%7d":"}", "%7e":"~"}

class MultiThreadScraper:
    def __init__(self, base_url_1, base_url_2, base_url_3, base_url_4):
        self.crawl_history = set([])
        self.frontier = Queue()
        # self.frontier.put(base_url_1)
        # self.frontier.put(base_url_2)
        # self.frontier.put(base_url_3)
        # self.frontier.put(base_url_4)

        conn = psycopg2.connect(host="localhost", user="user", password="SecretPassword")
        conn.autocommit = True
        frontier_logs = dbfunctions.get_300(conn)
        for url in frontier_logs:
            self.frontier.put(url[0])
            #print(url[0])

        history_logs = dbfunctions.get_everything_else(conn)
        for url in history_logs:
            self.crawl_history.add(url[0])
            #print(url[0])

        # dbfunctions.create_new_frontier_page(conn, base_url_1)
        # dbfunctions.create_new_frontier_page(conn, base_url_2)
        # dbfunctions.create_new_frontier_page(conn, base_url_3)
        # dbfunctions.create_new_frontier_page(conn, base_url_4)

        self.pool = ThreadPoolExecutor(max_workers=10)
        self.current_time = datetime.datetime.now()

        conn.close()

    def get_current_time(slef):
        return datetime.datetime.now()

    # pregled robots.txt
    def check_robots(self, url):
        rp = urllib.robotparser.RobotFileParser()
        domain = self.get_domain_url(url)
        rp.set_url( domain + "robots.txt")
        rp.read()
        robots = rp.can_fetch("*", url)
        return robots

    # pregled, ce lahko obiscemo url
    def check_url (self, url):
        if ".gov.si" in url:
            if self.check_robots(url):
                return True
        return False;

    #sidemap ne pustimo redirecta
    def get_sitemap(self, url):
        try:
            get_url = requests.get(url, allow_redirects=False)
            if get_url.status_code in [200, 301, 302, 307]:
                return get_url.text
            else:
                return None
        except:
            return None

    def get_robot(self, url):
        try:
            get_url = requests.get(url, allow_redirects=False)
            if get_url.status_code in [200, 301, 302, 307]:
                return get_url.text
            else:
                return None
        except:
            return None

    # iksanje loc
    def process_sitemap(self, text):
        soup = BeautifulSoup(text, features="html.parser" )
        result = []
        for loc in soup.findAll('loc'):
            result.append(loc.text)
        return result
    #pogledmo vse sitemape: avtor iz https://gist.github.com/vpetersson/f20efe6194460cc28d49
    def if_sitemap_sub(self, sites):
        if sites.endswith('.xml') and 'sitemap' in sites:
            return True
        else:
            return False

    def parse_sitemap(self, text):
        sitemap = self.process_sitemap(text)
        if sitemap is None:
            return
        result = []
        while sitemap:
            candidate = sitemap.pop()
            if self.if_sitemap_sub(candidate):
                sub_sitemap = self.get_sitemap(candidate)
                for i in self.process_sitemap(sub_sitemap):
                    sitemap.append(i)
            else:
                result.append(candidate)
        return result
    # olepsamo link
    def adjust_link(self, url, html):
    #    if url.startswith('/') or url.startswith(self.root_url):
        soup = BeautifulSoup(html, features="html.parser")

        base = soup.find(['base', 'link'], href=True)
        try:
            base_url = base.get('href')
        except:
            base_url = None
    # pogledamo ce je tag base v htmlju
        if base_url is None:
            url_join = urljoin(self.get_domain_url(url), url)
            #print("V htmlju ni taga <base>")
        else:
            url_join = urljoin(base_url, url)
        return url_join

    def scrape_page (self, url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("user-agent=fri-ieps-TEST")

        # statusna koda
        d = DesiredCapabilities.CHROME
        d["goog:loggingPrefs"] = {"performance": "ALL"}
        # print(f"Retrieving web page URL '{url}'")

        driver = webdriver.Chrome(WEB_DRIVER_LOCATION, options=chrome_options, desired_capabilities=d)
        driver.get(url)
        self.current_time = self.get_current_time();
        #status code
        #print (driver.get_log('performance')[3])
        tmp = driver.get_log('performance')[3]['message']
        logs_json = json.loads(tmp)
        #print("aaaaaaaaaaaa")
        try:
            status = logs_json["message"]["params"]["response"]["headersText"]
            status = status.split("\n")[0].split()[1]
            #print("status 1 " + str(status))
        except:
            try:
                status = logs_json["message"]["params"]["response"]["headers"]["status"]
                status = status.split("\n")[0]
                #print("status 2 " + str(status))
            except:
                try:
                    status = logs_json['message']['params']['redirectResponse']['headersText']
                    status = status.split("\n")[0].split()[1]
                    #print("status 3 " + str(status))
                except:
                    try:
                        status = logs_json["message"]["params"]["redirectResponse"]["headers"]["status"]
                        #print("status 4 " + str(status))
                    except:
                        try:
                            status = logs_json["message"]["params"]["response"]['status']
                            #print("status 5 " + str(status))
                        except:
                            print("Ce pride do napake poslji spodnji izpis Gaji prosim hvala")
                            print(logs_json["message"]["params"])
                            status = 200

        #rint("koncni status " + str(status))
        # Timeout needed for Web page to render (read more about it)
        time.sleep(TIMEOUT)
        response = driver.page_source
        redirect_url = driver.current_url
        driver.close()
        return response, url, status, redirect_url

    # check if page has canonical url
    def is_canonical(self, html, url):
        soup = BeautifulSoup(html, features="html.parser")
        # PARSIN LINKS
        for link in soup.findAll('link', rel=True):
            if link.get('rel') == ['canonical']:
                return (link.get('href') != url)
        return False

    def url_normalization(self, url):
        #remove default port number
        url = url.split(":")[0] + ":" + url.split(":")[1]

        #remove fragment
        url = url.split("#")[0]

        #add trailing slash
        if url[-1] != "/":
            url = url + "/"

        #resolve path
        dirs = []
        urlbase = url.split("/")[0] + "/" + url.split("/")[1] + "/" + url.split("/")[2] + "/"
        for dir in url.split("/")[3:-1]:
            if (dir in dirs):
                dirs = []
            dirs.append(dir)

        url = urlbase
        for dir in dirs:
            url = url + dir + "/"


        #remove default filename
        if url.split("/")[-2].split(".")[0] == "index":
            url = url.split("index")[0]

        #decode needlesly encoded characters
        if ("%" in url):
            triplet = "%" + url.split("%")[1][:2]
            if triplet.lower() in percent_encoding.keys():
                url = url.split("%")[0] + percent_encoding[triplet.lower()] + url.split("%")[1][2:]

        #encode disallowed characters
        url = url.replace(" ", "%")

        #lower case host names
        newurl = ""
        for i, part in enumerate(url.split("/")[:-1]):
            if i == 2:
                newurl = newurl + part.lower() + "/"
            else:
                newurl = newurl + part + "/"

        return newurl

    def compare_hash(self, conn, html):
        hashHtml = hash(html)
        duplicateUrl = dbfunctions.get_page_by_hash(conn, hashHtml)
        # if duplicateUrl != -1:
        #     print(hash)
        #     print("Hash compare duplicate of: " + duplicateUrl)
        return duplicateUrl

    def get_domain_url (self, url):
# from urlparse import urlparse  # Python 2
        parsed_uri = urlparse(url)
        result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

        #print("url " + url + "  " + "parsed url " + result)
        return result

    def get_domain (self, url):
# from urlparse import urlparse  # Python 2
        domain_url = self.get_domain_url(url)
        result = domain_url.split("://")[1].split("/")[0].replace("www.", "")
        #print("url " + url + "  " + "parsed url " + result)
        return result

    def scrape_callback(self, response):
        # create database connection
        conn = psycopg2.connect(host="localhost", user="user", password="SecretPassword")
        conn.autocommit = True

        html, target_url, http_status_code, redirect_url = response.result()
        # SSprint (target_url)
        if redirect_url in self.crawl_history:
            domain = self.get_domain(target_url)
            site_id = dbfunctions.get_site_id(conn, domain)
            accessed_time = self.current_time;
            #print(site_id)
            if site_id == -1:
                #print("Creating new site")
                self.parse_site(conn, domain, redirect_url)
            domain = self.get_domain(domain)
            site_id = dbfunctions.get_site_id(conn, domain)
            page_type_code = "DUPLICATE"
            html_content_hash = None
            id = dbfunctions.create_new_page(conn, site_id, page_type_code, target_url, 'NULL', html_content_hash, http_status_code, accessed_time, target_url)
        elif response.result() and (http_status_code == "200" or http_status_code == "307" or http_status_code == "301" or http_status_code == "302"):
            self.parse_site(conn, target_url, redirect_url)
            self.parse_page(conn, html, target_url, http_status_code, redirect_url)
        elif http_status_code == "400":
            domain = self.get_domain(target_url)
            # site_id = dbfunctions.get_site_id(domain)
            site_id = None
            html_content_hash = None
            dbfunctions.create_new_page(conn, site_id, 'NULL', target_url, 'NULL', html_content_hash, http_status_code, accessed_time, redirect_url)
        else:
            #print(http_status_code)
            domain = self.get_domain(target_url)
            site_id = dbfunctions.get_site_id(conn, domain)
            #print(site_id)
            if site_id == -1:
                #print("Creating new site")
                self.parse_site(conn, domain, redirect_url)
            domain = self.get_domain(domain)
            site_id = dbfunctions.get_site_id(conn, domain)
            #print("New site id: " + str(site_id))
            accessed_time = self.current_time;
            html_content_hash = None
            dbfunctions.create_new_page(conn, site_id, 'NULL', target_url, 'NULL', html_content_hash, http_status_code, accessed_time, redirect_url)

        conn.close()

    #parsing site: domain, robots_content, sitemap_content

    def parse_site (self, conn, url, redirect_url):
        #print("PARSE SITE")
        domain = self.get_domain(redirect_url)
        if dbfunctions.get_site_id(conn, domain) == -1 :
            robots_url  = self.get_domain_url(redirect_url) + "robots.txt"

            robots = self.get_robot(robots_url)
            #robots_html, target_url, http_status_code = self.scrape_page(robots_url)

            if robots is  None:
                robots_content = None
            else:
                soup = BeautifulSoup(robots, features="html.parser")
                robots_content = soup.get_text()

            sitemap_url = self.get_domain_url(redirect_url) + "sitemap.xml"
            sitemap = self.get_sitemap(sitemap_url)
            if sitemap is  None:
                sitemap_content = None
            else:
                sitemap_content = ('\n'.join(self.parse_sitemap(sitemap)))

            #sitemap_html, target_url, http_status_code = self.scrape_page(sitemap_url)
        #    if http_status_code != "200":
        #        sidemap_content = None
        #    else:
        #        soup = BeautifulSoup(sitemap_html, features="html.parser")
        #        sidemap_content = soup.get_text(separator='')


        #CE SITE NI V BAZI
        if dbfunctions.get_site_id(conn, domain) == -1 :
            dbfunctions.create_new_site(conn, domain, robots_content, sitemap_content)
        # else:
        #     print("Site ze v bazi id: " + str(dbfunctions.get_site_id(conn, domain)))

    def parse_page (self, conn, html_content, url, http_status_code, redirect_url):
        #print("PARSE PAGE")
        domain = self.get_domain(redirect_url)
        site_id = dbfunctions.get_site_id(conn, domain)
        if site_id == -1:
            self.parse_site(conn, domain, url)
        accessed_time = self.current_time;
        same_hash = self.compare_hash(conn, html_content)

        if self.is_canonical(html_content, redirect_url) or same_hash != -1:
            #print("Canonical URL")
            page_type_code = "DUPLICATE"
            html_content_hash = None
            id = dbfunctions.create_new_page(conn, site_id, page_type_code, url, 'NULL', html_content_hash, http_status_code, accessed_time, redirect_url)

        else:
            #print("Not canonical URL")
            #http_status_code = db.
            page_type_code = "HTML"
            #print (site_id, page_type_code, url, http_status_code, accessed_time)
            html_content_hash = hash(html_content)
            id = dbfunctions.create_new_page(conn, site_id, page_type_code, url, html_content, html_content_hash, http_status_code, accessed_time, redirect_url)

            self.parse_image(conn, id, html_content)
            self.parse_links(conn, id, html_content)
            #dbfunctions.create_new_page(site_id, page_type_code, url, html_content, http_status_code)

            #rp.set_url( domain + "/robots.txt")

    def parse_image(self, conn, pageid, html):
        # iskanje vseh povezav z znacko a in tipa href

        extractedLinks = []
        soup = BeautifulSoup(html, features="html.parser")
        # PARSIN LINKS
        for image in soup.findAll('img'):

            filename = image.get("src")
            if (filename):
                filename = filename.split("/")[-1]
                time = self.current_time;
                type = filename.split(".")

            #    dbfunctions.create_new_image(pageid, filename, type[len(type)-1].upper())

                if len(type[-1])>5:
                	dbfunctions.create_new_image(conn, pageid, filename, None)
                else:
                	dbfunctions.create_new_image(conn, pageid, filename, type[-1].upper())

    def parse_links(self, conn, pageid, html):
        # iskanje vseh povezav z znacko a in tipa href
        #print("PARSE LINKS")
        data_types = ['pdf', 'doc', 'docx', 'ppt', 'pptx']
        extractedLinks = []
        soup = BeautifulSoup(html, features="html.parser")
        # PARSIN LINKS
        for link in soup.findAll(['a', 'link'], href=True):
            href = link.get('href')
            #če je potrebno pretvorimo relative url v ustrezno obliko
            url = self.adjust_link (href, html)
            #če je ustrezen url ga damo v vrsto
            #print ("ALI BO DODAN URL " + url + ": " + str(self.check_url(url)))
            type = href.split(".")[-1]
            if type in data_types:
                # shrani
                data_type = type
                # print(data_type, ": ", url)
                dbfunctions.create_new_page_data(conn, pageid, data_type)
            elif type in img_types:
                # shrani
                data_type = type.upper()
                filename = href.split("/")[-1]
                # print(data_type, ": ", url)
                dbfunctions.create_new_image(conn, pageid, filename, data_type)
            elif self.check_url(url):
                originalURL = url
                url = self.url_normalization(url)
                #check if url already in database or frontier
                pageType = dbfunctions.get_page_type(conn, url)
                self.frontier.put(url)
                extractedLinks.append(url)
                id = dbfunctions.create_new_frontier_page(conn, url)
                if (id != -1): dbfunctions.create_new_link(conn, pageid, id)


    #    print("First 10 extracted links: " + str(extractedLinks[:min(len(extractedLinks), 10)]))
    #    print("Number of extracted links: " + str(len(extractedLinks)))


    def run_scraper(self):
        while True:
            try:
                target_url = self.frontier.get(timeout=60)
                #print ("target_url: " + target_url)
                if target_url not in self.crawl_history:
                    #print("Scraping URL: {}".format(target_url))
                    self.root_url = self.get_domain_url(target_url)
                    self.crawl_history.add(target_url)
                    worker = self.pool.submit(self.scrape_page, target_url)
                    worker.add_done_callback(self.scrape_callback) # a lah damo target_url sm not?


            except Exception as e:
                print(e)
                continue


if __name__ == '__main__':
    #dbfunctions.clear_db();
    s = MultiThreadScraper("https://www.e-prostor.gov.si/", "https://e-uprava.gov.si/", "https://www.gov.si/", "http://evem.gov.si/")
    s.run_scraper()
