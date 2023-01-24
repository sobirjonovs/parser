import json
import random
import threading
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

REQUEST_TIMEOUT = 300  # seconds
HEADERS = {'User-Agent': 'Mozilla/5.0'}
PROXIES = [
    '154.16.180.182:3128',
    '213.230.71.33:443',
    '139.59.228.95:8118'
]

session = requests.session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


def generate_proxy():
    return {'http': random.choice(PROXIES)}


def get(url: str, **kwargs):
    return session.get(url, **kwargs)


def parse_store_categories() -> dict:
    code = get("https://asaxiy.uz", timeout=REQUEST_TIMEOUT, headers=HEADERS, proxies=generate_proxy())
    code.close()
    soup = BeautifulSoup(code.content, "lxml")
    menus = soup.find(class_="mega__menu-list").findAll(class_="tab-open")

    categories = {}

    for menu in menus:
        categories.update({
            menu.get('href'): {
                'title': menu.getText().strip(),
                'sub_categories': {}
            }
        })

        c_temp = categories[menu.get('href')]

        sub_categories = get(f"https://asaxiy.uz{menu.get('href')}", timeout=REQUEST_TIMEOUT, headers=HEADERS,
                             proxies=generate_proxy())
        sub_categories.close()
        sub_soup = BeautifulSoup(sub_categories.content, "lxml")
        sub_categories = sub_soup.findAll(class_='a__aside-data')

        for sub_category in sub_categories:
            sub_title = sub_category.find('h6').getText()

            c_temp['sub_categories'].update({
                sub_category.get('href'): {
                    'title': sub_title,
                    'types': {}
                }
            })

            sc_temp = c_temp['sub_categories'][sub_category.get('href')]
            types = get(f"https://asaxiy.uz{sub_category.get('href')}", timeout=REQUEST_TIMEOUT, headers=HEADERS,
                        proxies=generate_proxy())
            types.close()
            types = BeautifulSoup(types.content, "lxml")
            types = types.findAll(class_='a__aside-data')

            for type_category in types:
                sc_temp['types'].update({
                    type_category.get('href'): {
                        'title': type_category.find('h6').getText(),
                        'products': []
                    }
                })

            if not sc_temp['types']:
                sc_temp['types'].update({
                    sub_category.get('href'): {
                        'title': sub_title,
                        'products': []
                    }
                })

        if not c_temp['sub_categories']:
            c_temp['sub_categories'].update({
                menu.get('href'): {
                    'title': menu.getText(),
                    'types': {
                        menu.get('href'): {
                            'title': menu.getText(),
                            'products': []
                        }
                    }
                }
            })

    return categories


def parse_store(name):
    print(f"start: {name} - {time.strftime('%-d %B %Y, %I:%M:%S%p')}")
    categories = parse_store_products(parse_store_categories())

    with open('categories.json', 'w') as file:
        file.write(json.dumps(categories))

    with open('categories_indent.json', 'w') as file:
        file.write(json.dumps(categories, indent=2, ensure_ascii=False))

    print(f"finish: {name} - {time.strftime('%-d %B %Y, %I:%M:%S%p')}")


def parse_store_products(categories):
    for category in categories.values():
        for sub_category in category['sub_categories'].values():
            for url, type_product in sub_category['types'].items():
                type_product['products'] = get_products(url)

        print('finished - ', category['title'])

    return categories


def get_products(product_url=None, page=1, foreign_products={}):
    products_page = get(f"https://asaxiy.uz{product_url}?page={page}", timeout=REQUEST_TIMEOUT, headers=HEADERS,
                        proxies=generate_proxy())
    products_page.close()
    products_page = BeautifulSoup(products_page.content, "lxml")
    products_a = products_page.select('div.product__item > a[href]')
    products = foreign_products

    if not products_a:
        return products

    for product_a in products_a:
        product_link = product_a.get('href')

        if product_link in products:
            clone_product = products[product_link]
            clone_product['duplicates'] += 1

            if clone_product['duplicates'] == 1:
                continue

            return products

        product_single_page = get(f"https://asaxiy.uz{product_link}", timeout=REQUEST_TIMEOUT, headers=HEADERS,
                                  proxies=generate_proxy())
        product_single_page.close()
        product_page = BeautifulSoup(product_single_page.content, "lxml")

        img = product_page.find(class_="item__main-img")
        img = img.findChild('img') if img else None
        price = product_page.find(class_="price-box_new-price")
        characteristics = product_page.select('.characteristics table')
        description = product_page.find(class_="description__item")

        products.update({
            product_link: {
                'title': product_page.find("h1").getText(),
                'description': description.getText() if description else None,
                'characteristics': characteristics[0].prettify() if characteristics else None,
                'images': [img.get("src") if img else None],
                'price': price.getText() if price else 0,
                'availability': True if product_page.select('#add_to_cart') else False,
                'installment': True if product_page.find('a', {'data-target': '#installment'}) else False,
                'duplicates': 0
            }
        })

    return get_products(product_url, page + 1, products)


thread1 = threading.Thread(target=parse_store, args=['asaxiy'])
# thread2 = threading.Thread(target=parse_store, args=['olcha'])
# thread3 = threading.Thread(target=parse_store, args=['elmakon'])
# thread4 = threading.Thread(target=parse_store, args=['texnomart'])
# thread5 = threading.Thread(target=parse_store, args=['prom'])

thread1.start()

# , thread2.start(), thread3.start(), thread4.start(), thread5.start()
