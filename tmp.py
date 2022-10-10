import psycopg2
import dbfunctions

conn = psycopg2.connect(host="localhost", user="user", password="SecretPassword")
conn.autocommit = True

frontier = dbfunctions.get_frontier(conn)
print(len(frontier))
# for url in frontier:
#     print(url[0])

history = dbfunctions.get_history(conn)
print(len(history))
# for url in history:
#     print(url[0])

conn.close()
