url_queue = ["https://askubuntu.com/"]
def store_urls(urls):
    for url in urls:
        if not url in url_queue:
            url_queue.append(url)
def get_new_url():
    new_url = "no more urls in queue"
    if len(url_queue) > 0:
        new_url = url_queue[0]
        url_queue.remove(new_url)
    print(new_url)
    return new_url
# print(url_queue)
# store_urls(["url1", "url2", "url3"])
# print(url_queue)
# get_new_url()
# print(url_queue)
# store_urls(["url2", "url4", "url3"])
# print(url_queue)
