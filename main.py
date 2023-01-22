import json
import threading
import time
from requests import get
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 200 # seconds
HEADERS = {'User-Agent': 'Mozilla/5.0'}
PROXY = {'http': '139.59.228.95:8118'}


def parse_store_categories() -> dict:
    code = get("https://asaxiy.uz", timeout=REQUEST_TIMEOUT, headers=HEADERS, proxies=PROXY)
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

        sub_categories = get(f"https://asaxiy.uz{menu.get('href')}", timeout=REQUEST_TIMEOUT, headers=HEADERS, proxies=PROXY)
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
            types = get(f"https://asaxiy.uz{sub_category.get('href')}", timeout=REQUEST_TIMEOUT, headers=HEADERS, proxies=PROXY)
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
                code = get(f"https://asaxiy.uz{url}", timeout=REQUEST_TIMEOUT, headers=HEADERS, proxies=PROXY)
                soup = BeautifulSoup(code.content, "lxml")
                product = soup.find(class_="product__item")

                if not product:
                    continue

                product = product.find("a")
                product_url = product.get('href')
                type_product['products'] = get_products(product_url)

    return categories


def get_products(product_url=None, page=1, foreign_products={}):
    print(page, product_url)
    code_product = get(f"https://asaxiy.uz{product_url}?page={page}", timeout=REQUEST_TIMEOUT, headers=HEADERS, proxies=PROXY)
    products_page = BeautifulSoup(code_product.content, "lxml")
    products_a = products_page.select('div.product__item > a[href]')
    print(products_a)
    products = foreign_products


    for product_a in products_a:
        product_link = product_a.get('href')

        print(product_link)

        if product_link in products:
            print(product_link, ' - ended')
            return products

        product_request = get(f"https://asaxiy.uz{product_link}", timeout=REQUEST_TIMEOUT, headers=HEADERS, proxies=PROXY)
        product_page = BeautifulSoup(product_request.content, "lxml")

        img = product_page.find(class_="img-fluid")
        price = product_page.find(class_="price-box_new-price")
        characteristics = product_page.select('.characteristics table')
        description = product_page.find(class_="description__item")

        products.update({
            product_link: {
                'title': product_page.find("h1").getText(),
                'description': description.getText() if description else None,
                'characteristics': characteristics[0].prettify() if characteristics else None,
                'images': [img.get("src")],
                'price': price.getText() if price else 0,
                'availability': True if product_page.select('#add_to_cart') else False,
                'installment': True if product_page.find('a', {'data-target': '#installment'}) else False,
            }
        })

    return get_products(product_url, page + 1, products)


thread1 = threading.Thread(target=parse_store, args=['asaxiy'])
# thread2 = threading.Thread(target=parse_store, args=['olcha'])
# thread3 = threading.Thread(target=parse_store, args=['elmakon'])
# thread4 = threading.Thread(target=parse_store, args=['texnomart'])
# thread5 = threading.Thread(target=parse_store, args=['prom'])

thread1.start()  # , thread2.start(), thread3.start(), thread4.start(), thread5.start()
