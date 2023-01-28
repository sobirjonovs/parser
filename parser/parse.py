import logging
import time

import requests
import random

from threading import Thread
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

logging.basicConfig(filename='parser.log', format='[%(asctime)s] %(levelname)s: %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')


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
            'TITLE': 'asaxiy div'
        },
        'https://olcha.uz': {
            'TITLE': 'olcha div'
        },
        'https://elmakon.uz': {
            'TITLE': 'elmakon div'
        },
        'https://texnomart.uz': {
            'TITLE': 'texnomart div'
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
        for store_link, parameters in self.STRATEGIES.items():
            self.__add_thread(name=store_link, parameters=parameters, callable_=self.__parse_store)

    def __parse_store(self, name, parameters):
        logging.info(f'started: {name}')
        print(parameters)
        time.sleep(5)
        logging.info(f'finished: {name}')

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

    def __add_thread(self, name, parameters, callable_):
        """
        Create a thread and start it
        :rtype: object
        """
        thread = Thread(target=callable_, args=[name, parameters])
        thread.start()
        self.threads.append(thread)

        return self

    def __join_threads(self):
        for thread in self.threads:
            thread.join()

    def __del__(self):
        self.__join_threads()
        self.threads = []


parser = Parser()
