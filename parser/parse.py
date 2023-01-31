import logging
import random
from threading import Thread

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

from builtins import *

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
            'CATEGORY_TITLE': '.mega__menu-list .tab-open',
            'SUB_CATEGORY_TITLE': '.a__aside-data > h6',
            'TYPE_TITLE': '.a__aside-data > h6',
            'PRODUCT_URL': '.product__item > a'
        }
    }

    def __init__(self):
        """
        Initialize a request object using session
        to prevent "Maximum Request Exceeds" exception
        :rtype: object
        """
        self.threads = list()
        self.session = requests.session()

        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)

        # mount http/https for url
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def parse(self):
        for store_link, parameters in self.STRATEGIES.items():
            self.__add_thread(name=store_link, parameters=parameters, callable_=self.__parse)

    def __parse(self, name, parameters):
        self.link = name
        logging.info(f'started: {name}')
        print(self._parse_categories(parameters))
        logging.info(f'finished: {name}')

    def _parse_categories(self, parameters):
        categories = self._soup(self.link).select(parameters['CATEGORY_TITLE'])
        data = dict()

        for category in categories:
            category_url = category.get('href')
            category_title = category.get_text(strip=True)

            data.set(
                key=category_url,
                title=category_title,
                categories=self._parse_sub_categories(link=category_url, parameters=parameters)
            )

            if not data['categories']:
                data['categories'].set(
                    key=category_url,
                    title=category_title,
                    types=dict().set(
                        key=category_url,
                        title=category_title,
                        products=self._parse_products(link=category_url, parameters=parameters))
                )

        return data

    def _parse_sub_categories(self, link, parameters):
        result = dict()

        sub_categories = self._soup(f"{self.link}{link}").select(parameters['SUB_CATEGORY_TITLE'])

        for sub_category in sub_categories:
            title = sub_category.get_text(strip=True)

        return result

    def _parse_products(self, link, parameters):
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

    def _soup(self, url: str, type_: str = 'lxml'):
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

    def __del__(self):
        self.threads = []
        self.session = None


parser = Parser()
