import json
import threading
import time
from urllib import request
from urllib.request import urlopen

from bs4 import BeautifulSoup


def parse_store_categories() -> dict:
    code = urlopen("https://asaxiy.uz").read()
    soup = BeautifulSoup(code, "lxml")

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

        sub_categories = urlopen(f"https://asaxiy.uz{request.quote(menu.get('href'))}").read()
        sub_soup = BeautifulSoup(sub_categories, "lxml")
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
            types = urlopen(f"https://asaxiy.uz{request.quote(sub_category.get('href'))}").read()
            types = BeautifulSoup(types, "lxml")
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
                code = urlopen(f"https://asaxiy.uz{request.quote(url)}").read()
                soup = BeautifulSoup(code, "lxml")
                product = soup.find(class_="product__item")

                if not product:
                    continue

                product = product.find("a")

                product_url = product.get('href')
                code_product = urlopen(f"https://asaxiy.uz{request.quote(product_url)}").read()
                soup_product = BeautifulSoup(code_product, "lxml")
                img = soup_product.find(class_="img-fluid")
                price = soup_product.find(class_="price-box_new-price")

                type_product['products'].append({
                    product_url: {
                        'title': soup_product.find("h1").getText(),
                        'description': soup_product.find(class_="description__item").getText(),
                        'characteristics': soup_product.find(class_='characteristics').prettify(),
                        'images': [img.get("src")],
                        'price': price.getText() if price else 0,
                        'availability': soup_product.find(class_='text__content d-flex align-items-center mb-3').find(
                            class_="text__content-name").getText(),
                        'installment': True if soup_product.find('a', {'data-target': '#installment'}) else False,
                    }
                })

    return categories


thread1 = threading.Thread(target=parse_store, args=['asaxiy'])
# thread2 = threading.Thread(target=parse_store, args=['olcha'])
# thread3 = threading.Thread(target=parse_store, args=['elmakon'])
# thread4 = threading.Thread(target=parse_store, args=['texnomart'])
# thread5 = threading.Thread(target=parse_store, args=['prom'])

thread1.start() #, thread2.start(), thread3.start(), thread4.start(), thread5.start()
