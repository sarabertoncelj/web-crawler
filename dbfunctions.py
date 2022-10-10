import concurrent.futures
import threading
import psycopg2

# ??? wat is this
lock = threading.Lock()

def clear_db():
    conn = psycopg2.connect(host="localhost", user="user", password="SecretPassword")
    conn.autocommit = True

    cur = conn.cursor()

    # get all table names
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='crawldb'")
    allTablesStr = ""
    for value in cur.fetchall():
        allTablesStr = allTablesStr + ("crawldb." + value[0] + ", ")

    # delete all entries in all tables
    #print("TRUNCATE " + allTablesStr[:-2])
    cur.execute("TRUNCATE " + allTablesStr[:-2])

    #cur.execute("INSERT INTO crawldb.page_type VALUES ('FRONTIER')  ON CONFLICT DO NOTHING")
    cur.execute("INSERT INTO crawldb.data_type VALUES ('PDF'), ('DOC'), ('DOCX'), ('PPT'), ('PPTX');")
    cur.execute("INSERT INTO crawldb.page_type VALUES ('HTML'), ('BINARY'), ('DUPLICATE'), ('FRONTIER');")

    cur.close()
    conn.close()

def create_new_site(conn, domain, robots_content, sitemap_content):

    cur = conn.cursor()
    #print(domain)
    query = f"INSERT INTO crawldb.site VALUES (DEFAULT, %s, %s, %s)"
    cur.execute(query, (domain, robots_content, sitemap_content))

    cur.close()
def create_new_frontier_page(conn, url):

    cur = conn.cursor()
    #cur.execute("INSERT INTO crawldb.page_type VALUES (%s)", page_type_code)

    #cur.execute("INSERT INTO crawldb.page VALUES (DEFAULT, %s, %s, '" + url + "', %s, %s, %s) ON CONFLICT DO UPDATE RETURNING crawldb.page.id", (site_id, page_type_code, html_content, http_status_code, accessed_time))

    query = f"INSERT INTO crawldb.page VALUES (DEFAULT, null, 'FRONTIER', %s, null, -1, null, null) ON CONFLICT DO NOTHING RETURNING crawldb.page.id"
    # query = f"UPDATE crawldb.page SET crawldb.page.site_id = {site_id}, crawldb.page.page_type_code = {page_type_code}, crawldb.page.html_content = {html_content}, crawldb.page.http_status_code = {http_status_code}, crawldb.page.accessed_time = current_timestamp WHERE crawldb.page.url = {url} RETURNING crawldb.page.id"
    cur.execute(query, (url, ))
    id_of_new_row = cur.fetchone()
    id = -1
    if id_of_new_row:
        id = id_of_new_row[0]

    cur.close()
    return id

def create_new_page(conn, site_id, page_type_code, url, html_content, html_content_hash, http_status_code, accessed_time, redirect_url):

    cur = conn.cursor()
    #cur.execute("INSERT INTO crawldb.page_type VALUES ('" + page_type_code + "') ON CONFLICT DO NOTHING")
    query = f"INSERT INTO crawldb.page_type VALUES (%s) ON CONFLICT DO NOTHING"
    cur.execute(query, (page_type_code, ))
    query = f"UPDATE crawldb.page SET site_id = %s, page_type_code = %s, url = %s, html_content = %s, html_content_hash = %s, http_status_code = %s, accessed_time = current_timestamp WHERE url = %s RETURNING crawldb.page.id"
    cur.execute(query, (site_id, page_type_code, redirect_url, html_content, html_content_hash, http_status_code, url))
    id_of_new_row = cur.fetchone()[0]
    # print("id ", id_of_new_row)

    cur.close()
    return id_of_new_row

def create_new_image(conn, page_id, filename, content_type):

    cur = conn.cursor()
    # query = f"INSERT INTO crawldb.image VALUES (DEFAULT, {page_id}, '{filename}', '{content_type}', null, current_timestamp)"
    query = f"INSERT INTO crawldb.image VALUES (DEFAULT, %s, %s, %s, null, current_timestamp)"
    cur.execute(query, (page_id, filename, content_type))

    cur.close()

def create_new_page_data(conn, page_id, data_type_code):

    cur = conn.cursor()
    # cur.execute("INSERT INTO crawldb.data_type VALUES ('" + data_type_code + "') ON CONFLICT DO NOTHING")
    query = f"INSERT INTO crawldb.data_type VALUES (%s) ON CONFLICT DO NOTHING"
    cur.execute(query, (data_type_code, ))

    # query = f"INSERT INTO crawldb.page_data VALUES (DEFAULT, {page_id}, '{data_type_code}', null)"
    query = f"INSERT INTO crawldb.page_data VALUES (DEFAULT, %s, %s, null)"
    cur.execute(query, (page_id, data_type_code))

    cur.close()

def create_new_link(conn, from_page, to_page):

    cur = conn.cursor()
    # query = f"INSERT INTO crawldb.link VALUES ({from_page}, {to_page})"
    query = f"INSERT INTO crawldb.link VALUES (%s, %s)"
    cur.execute(query, (from_page, to_page))

    cur.close()

def update_link(conn, from_page, to_page):

    cur = conn.cursor()
    # query = f"INSERT INTO crawldb.link VALUES ({from_page}, {to_page})"
    query = f"UPDATE crawldb.link SET from_page = %s WHERE to_page = %s"
    cur.execute(query, (from_page, to_page))

    cur.close()

def get_site_id(conn, site_url):
    cur = conn.cursor()
    query = f"SELECT id FROM crawldb.site WHERE  crawldb.site.domain = %s"
    # query = f"SELECT id FROM crawldb.site WHERE  crawldb.site.domain = '{site_url}'"
    cur.execute(query, (site_url, ))
    site = cur.fetchone()
    cur.close()
    if site:
        return site[0]
    else:
        return -1

def get_page_id(conn, page_url):
    cur = conn.cursor()
    query = f"SELECT id FROM crawldb.page WHERE  crawldb.page.url = %s"
    # query = f"SELECT id FROM crawldb.site WHERE  crawldb.site.domain = '{site_url}'"
    cur.execute(query, (page_url, ))
    page = cur.fetchone()
    cur.close()
    if site:
        return page[0]
    else:
        return -1

def get_page_type(conn, site_url):
    cur = conn.cursor()
    query = f"SELECT page_type_code FROM crawldb.page WHERE  crawldb.page.url = %s"
    # query = f"SELECT id FROM crawldb.site WHERE  crawldb.site.domain = '{site_url}'"
    cur.execute(query, (site_url, ))
    site = cur.fetchone()
    cur.close()
    if site:
        return site[0]
    else:
        return -1

def get_page_by_hash(conn, hash):
    cur = conn.cursor()
    query = f"SELECT id FROM crawldb.page WHERE  crawldb.page.html_content_hash = %s"
    # query = f"SELECT id FROM crawldb.site WHERE  crawldb.site.domain = '{site_url}'"
    cur.execute(query, (hash, ))
    site = cur.fetchone()
    cur.close()
    if site:
        return site[0]
    else:
        return -1

def get_frontier(conn):
    cur = conn.cursor()
    query = f"SELECT url FROM crawldb.page WHERE  crawldb.page.page_type_code = 'FRONTIER'"
    # query = f"SELECT id FROM crawldb.site WHERE  crawldb.site.domain = '{site_url}'"
    cur.execute(query)
    frontier = cur.fetchall()
    cur.close()
    return frontier

def get_history(conn):
    cur = conn.cursor()
    query = f"SELECT url FROM crawldb.page WHERE  crawldb.page.page_type_code != 'FRONTIER'"
    # query = f"SELECT id FROM crawldb.site WHERE  crawldb.site.domain = '{site_url}'"
    cur.execute(query)
    history = cur.fetchall()
    cur.close()
    return history

def get_300(conn):
    cur = conn.cursor()
    query = f"SELECT url FROM crawldb.page WHERE http_status_code = 307 OR http_status_code = 301 OR http_status_code = 302;"
    # query = f"SELECT id FROM crawldb.site WHERE  crawldb.site.domain = '{site_url}'"
    cur.execute(query)
    site = cur.fetchall()
    cur.close()
    return site

def get_everything_else(conn):
    cur = conn.cursor()
    query = f"SELECT url FROM crawldb.page WHERE http_status_code != 307 AND http_status_code != 301 AND http_status_code != 302;"
    # query = f"SELECT id FROM crawldb.site WHERE  crawldb.site.domain = '{site_url}'"
    cur.execute(query)
    site = cur.fetchall()
    cur.close()
    return site
