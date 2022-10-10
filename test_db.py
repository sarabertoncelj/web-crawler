import dbfunctions
import time
from bs4 import BeautifulSoup
from datetime import datetime
#dbfunctions.create_new_site("test1", "robots_content", "sitemap_content")
# time.sleep(5)
# print(dbfunctions.get_site_id("tealdsldst1"))


def parse_image(pageid, html):
    # iskanje vseh povezav z znacko a in tipa href

    extractedLinks = []
    soup = BeautifulSoup(html, features="html.parser")
    # PARSIN LINKS
    for image in soup.findAll('img'):
        filename = image.get('src')
        type = filename.split(".")
        dbfunctions.create_new_image(pageid, filename, type[len(type)-1], "stop", "stop")

def parse_page_data(pageid, html):
    # iskanje vseh povezav z znacko a in tipa href

    extractedLinks = []
    soup = BeautifulSoup(html, features="html.parser")
    # PARSIN LINKS
    for image in soup.findAll('img'):
        filename = image.get('src')
        time = datetime.now()
        type = filename.split(".")
        print("INSERT INTO crawldb.image VALUES (DEFAULT, %s, '" + filename + "', '" + type[len(type)-1] + "', %s, %s)", (pageid, None, time))
        # dbfunctions.create_new_image(pageid, filename, type[len(type)-1], None, time)

parse_image(100, '<div class="w3-card-4">   <img src="img_avatar.png" alt="Person" </div>')
