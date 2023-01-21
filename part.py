import json

import requests
from bs4 import BeautifulSoup


def get_products(page=1, product_url=None, foreign_products={}):
    code_product = requests.get(f"https://asaxiy.uz{product_url}?page={page}", timeout=200)
    products_page = BeautifulSoup(code_product.content, "lxml")
    products_a = products_page.select('div.product__item > a[href]')
    products = foreign_products

    for product_a in products_a:
        product_link = product_a.get('href')

        if product_link in products:
            return products

        product_request = requests.get(f"https://asaxiy.uz{product_link}")
        product_page = BeautifulSoup(product_request.content, "lxml")

        print(product_link)

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

    return get_products(page + 1, product_url, products)


products = get_products()
print(json.dumps(products, ensure_ascii=False, indent=2))
