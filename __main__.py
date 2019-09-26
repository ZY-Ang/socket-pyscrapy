import os
import json
from socket import socket, AF_INET, SOCK_STREAM
import ssl
import firebase_admin
from firebase_admin import credentials, db
from urllib.parse import urlparse
import time
import timeit
from random import randrange
import re


class Scraper:
    @staticmethod
    def get_hostname(url_string):
        """
        Gets hostname or netloc part of a url string
        """
        print("get_hostname(" + str(url_string) + ")")
        parsed_url = urlparse(url_string)
        return parsed_url.hostname or parsed_url.netloc

    @staticmethod
    def get_site(url_string):
        """
        :param url_string: A url to be accessed
        :return: site data for a given urlString. Performs all necessary low level socket-http stuff
        Format: {
            response_time: <float>seconds,
            response: <string>httpResponse
        }
        """
        print("get_site(" + str(url_string) + ")")
        url = urlparse(url_string)
        server_address = (url.hostname, 443) if url.scheme == 'https' else (url.hostname, 80)
        # Create http request
        http_request = 'GET /' + url_string \
            .replace(url.scheme + '://', '') \
            .replace(url.netloc + '/', '', 1) \
            .replace(url.netloc, '', 1) + ' HTTP/1.1\r\n'
        http_request += 'Host: ' + url.hostname + ':' + str(80) + '\r\n'
        http_request += 'Connection: close\r\n'
        http_request += '\r\n'

        # Socket and timing stuff here
        sock = None
        if url.scheme == 'https':
            context = ssl.create_default_context()
            sock = context.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname=url.hostname)
        else:
            sock = socket(AF_INET, SOCK_STREAM)
        sock.connect(server_address)
        start = timeit.default_timer()
        sock.sendall(http_request.encode())  # Send utf-8 up
        response = b''
        while True:
            buf = sock.recv(1024)
            if not buf:
                break
            response += buf
        end = timeit.default_timer()
        sock.close()
        decoded_response = None
        encodings = ['utf-8', 'latin-1']  # Apparently if you visit a chinese website utf-8 won't work
        for encoding in encodings:
            try:
                decoded_response = response.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if decoded_response is None:
            print("Unable to decode response at " + url_string)
            raise Exception("Unable to decode response!")

        return {
            "response_time": end - start,
            "response": decoded_response,
            "url": url_string
        }

    @staticmethod
    def add_site_to_firebase(site_data):
        """
        :param site_data: to be added to firebase
        """
        print("add_to_firebase(" + json.dumps({
            "response_time": site_data['response_time'],
            "response": '...',
            "url": site_data['url'],
        }) + ")")
        db.reference('data').push({
            "response_time": site_data['response_time'],
            "date_accessed": time.time(),
            "url": site_data['url'],
        })

    @staticmethod
    def get_urls(site_data):
        """
        :param site_data: {response_time: <float>seconds, response: <string>httpResponse}
        :return: list of URLs inside a given site_data response. Performs all necessary html, http parsing actions.
        """
        print("get_urls(" + json.dumps({
            "response_time": site_data['response_time'],
            "response": '...',
            "url": site_data['url'],
        }) + ")")
        current_scheme_prefix = urlparse(site_data['url']).scheme + "://"
        split_response = site_data['response'].split('\r\n\r\n')

        if len(split_response) >= 2:
            # Regex from:
            #   https://stackoverflow.com/questions/6038061/regular-expression-to-find-urls-within-a-string/54086404
            all_web_or_relative_urls_regex = r'(?:(?:http|https):\/\/|www\.|ftp\.)(?:\([-A-Z0-9+&@#\/%=~_|$?!:,' \
                                             r'.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#\/%=~_|$?!:,' \
                                             r'.]*\)|[A-Z0-9+&@#\/%=~_|$])'
            urls_on_page = re.findall(all_web_or_relative_urls_regex, split_response[1], re.IGNORECASE | re.MULTILINE)
            for index, url in enumerate(urls_on_page):
                if not (url.startswith('http://') or url.startswith('https://')):
                    urls_on_page[index] = current_scheme_prefix + url
            return urls_on_page

        return []

    @staticmethod
    def add_urls_to_queue_firebase(urls_to_add):
        """
        Pushes a url into the queue on firebase database
        """
        print("add_url_to_queue_firebase([...len = " + str(len(urls_to_add)) + "...])")
        queue_ref = db.reference('queue')
        for url in urls_to_add:
            existing_url = db.reference('data').order_by_child('url').equal_to(url).get()
            if len(existing_url.keys()) == 0:
                queue_ref.push(url)

    def start(self):
        has_next_url = True
        while has_next_url:
            next_element_snapshot = db.reference('queue').order_by_key().limit_to_first(1).get()
            if len(next_element_snapshot.keys()) != 1:
                has_next_url = False
            else:
                key, url = [(k, v) for k, v in next_element_snapshot.items()][0]
                existing_url = db.reference('data').order_by_child('url').equal_to(url).get()
                # Similar to queue 'pop' but follows eventual consistency model for multi-threading.
                db.reference('queue/' + key).delete()
                # Only perform request if unvisited
                if len(existing_url.keys()) == 0:
                    print("=========================== " + url + " ===========================")
                    try:
                        site_data = Scraper.get_site(url)
                        Scraper.add_site_to_firebase(site_data)
                        urls_to_add = Scraper.get_urls(site_data)
                        Scraper.add_urls_to_queue_firebase(urls_to_add)
                    except Exception as e:
                        print("Failed: ", e, flush=True)
            # Wait 5 to 30 seconds before getting the next link (so the server can't tell I'm a bot)
            time.sleep(randrange(5, 31))

        print("No more pages to scrape. Probably need to seed")
        return 0


# To multi-thread, just run more times e.g. python3 __main__.py & python3 __main__.py & python3 __main__.py & ...
def main():
    # Just use firebase to store results.
    cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.environ['FIREBASE_DATABASE_URL']  # Or whatever your database URL is
    })
    scraper = Scraper()
    scraper.start()


if __name__ == '__main__':
    main()
