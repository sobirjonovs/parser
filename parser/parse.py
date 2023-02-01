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
            'PAGE': '?page=',
            'PRODUCT_URL': '.product__item > a[href]',
            'PRODUCT_IMAGE': '.item__main-img > img',
            'PRODUCT_TITLE': 'h1.product-title',
            'PRODUCT_PRICE': '.price-box_new-price',
            'PRODUCT_CHARACTERISTICS': '.characteristics table',
            'PRODUCT_DESCRIPTION': '.description__item',
            'PRODUCT_INSTALLMENT': 'a[data-target="#installment"]',
            'PRODUCT_AVAILABILITY': 'a#add_to_cart'
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

    def _parse_categories(self, parameters):
        categories = self._soup(self.link).select(parameters['CATEGORY_TITLE'])
        data = dict()

        for category in categories:
            category_url = category.get('href')
            category_title = category.get_text(strip=True)

            data.set(
                key=category_url,
                title=category_title,
                categories=self._parse_sub_categories(link=category_url, category_title=category_title,
                                                      parameters=parameters)
            )

            categories_ = data[category_url]

            if not categories_['categories']:
                categories_['categories'].set(
                    key=category_url,
                    title=category_title,
                    types=dict().set(
                        key=category_url,
                        title=category_title,
                        products=self._parse_products(link=category_url, parameters=parameters))
                )

        return data

    def _parse_sub_categories(self, link, category_title, parameters):
        result = dict()

        sub_categories = self._soup(f"{self.link}{link}").select(parameters['SUB_CATEGORY_TITLE'])

        for sub_category in sub_categories:
            sub_category_title = sub_category.get_text(strip=True)
            sub_category_url = sub_category.get('href')

            result.set(
                key=sub_category_url,
                title=sub_category_title,
                types=self._parse_types(link=sub_category_url, sub_category_title=sub_category_title,
                                        parameters=parameters)
            )

            types_ = result[sub_category_url]

            if not types_['types']:
                types_['types'].set(
                    key=sub_category_url,
                    title=sub_category_title,
                    products=self._parse_products(link=sub_category_url, parameters=parameters)
                )

        if not result:
            result.set(
                key=link,
                title=category_title,
                types=dict().set(
                    key=link,
                    title=category_title,
                    products=self._parse_products(link=link, parameters=parameters))
            )

        return result

    def _parse_types(self, link, sub_category_title, parameters):
        result = dict()

        types = self._soup(f"{self.link}{link}").select(parameters['TYPE_TITLE'])

        for type_ in types:
            type_title = type_.get_text(strip=True)
            type_url = type_.get('href')

            result.set(
                key=type_url,
                title=type_title,
                products=self._parse_products(link=type_url, parameters=parameters)
            )

        if not result:
            result.set(
                key=link,
                title=sub_category_title,
                products=self._parse_products(link=link, parameters=parameters)
            )

        return result

    def _parse_products(self, link, parameters, page=1, result=dict()):
        products = self._soup(f"{self.link}{link}{parameters['PAGE']}{page}").select(parameters['PRODUCT_URL'])

        if not products:
            return result

        for product in products:
            product_link = product.get('href')

            if product_link in result:
                _product = result[product_link]
                _product['duplicates'] += 1

                if _product['duplicates'] < 3:
                    continue

                return result

            try:
                product_page = self._soup(f"{self.link}{product_link}")
            except requests.exceptions.TooManyRedirects:
                logging.info(f'redirected: {product_link} | page: {page}')
                continue

            product_image = self._select_one(product_page, parameters['PRODUCT_IMAGE'], image=True)
            product_title = self._select_one(product_page, parameters['PRODUCT_TITLE'])
            product_price = self._select_one(product_page, parameters['PRODUCT_PRICE'], numeric=True)
            product_characteristics = self._select_one(product_page, parameters['PRODUCT_CHARACTERISTICS'], pretty=True)
            product_description = self._select_one(product_page, parameters['PRODUCT_DESCRIPTION'], pretty=True)
            product_availability = self._select_one(product_page, parameters['PRODUCT_AVAILABILITY'], boolean=True)
            product_installment = self._select_one(product_page, parameters['PRODUCT_INSTALLMENT'], boolean=True)

            result.set(
                key=product_link,
                title=product_title,
                description=product_description,
                characteristics=product_characteristics,
                images=[product_image],
                price=product_price,
                availability=product_availability,
                installment=product_installment,
                duplicates=0
            )

        return self._parse_products(link, parameters, page + 1, result)

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

    @staticmethod
    def _select_one(soup, selector, boolean: False, pretty=False, image=False, numeric=False):
        element = soup.select_one(selector)

        if pretty:
            return element.prettify() if element else None

        if boolean:
            return True if element else False

        if image:
            return element.get('src') if element else None

        if numeric:
            return element.get_text(strip=True) if element else 0

        return element.get_text(strip=True) if element else None

    def __parse(self, name, parameters):
        self.link = name
        logging.info(f'started: {name}')
        print(self._parse_categories(parameters))
        logging.info(f'finished: {name}')

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
