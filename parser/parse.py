import random
from threading import Thread

import requests
from bs4 import BeautifulSoup

from requests.adapters import HTTPAdapter, Retry


class Parser:
    # request timeout in seconds
    REQUEST_TIMEOUT = 300
    HEADERS = {'User-Agent': 'Mozilla/5.0'}
    PROXIES = [
        '154.16.180.182:3128',
        '213.230.71.33:443',
        '139.59.228.95:8118'
    ]

    # Stores keyed with store link and within places to parse
    STRATEGIES = {
        'https://asaxiy.uz': {
            'TITLE': 'div'
        },
        'https://olcha.uz': {
            'TITLE': 'div'
        },
        'https://elmakon.uz': {
            'TITLE': 'div'
        },
        'https://texnomart.uz': {
            'TITLE': 'div'
        }
    }

    def __init__(self):
        """
        Initialize a request object using session
        to prevent "Maximum Request Exceeds" exception
        :rtype: object
        """
        self.threads = []
        self.session = requests.session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)

        # mount http/https for url
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def parse(self):
        print('parsing')
        for store_link, parameters in self.STRATEGIES.items():
            pass

    def _get(self, url: str, **kwargs):
        """
        Type: Protected method
        Sends get request using session object and close it quickly
        :return: Response
        """
        session = self.session.get(url=url, timeout=self.REQUEST_TIMEOUT, headers=self.HEADERS,
                                   proxies=self.__generate_proxy(), **kwargs)

        session.close()

        return session

    def _soup(self, url: str, type_: str = 'lxm'):
        return BeautifulSoup(self._get(url).content, type_)

    def __generate_proxy(self):
        """
        Type: Private method
        Gets random proxy from the list
        :return: dict
        """
        return {'http': random.choice(self.PROXIES)}

    def __add_thread(self, name, callable_):
        """
        Create a thread and start it
        :rtype: object
        """
        thread = Thread(target=callable_, args=[name])
        thread.start()
        self.threads.append(thread)

        return self

    def __join_threads(self):
        for thread in self.threads:
            thread.join()


parser = Parser()
