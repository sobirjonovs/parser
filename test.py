import requests
from bs4 import BeautifulSoup

page = requests.get('https://asaxiy.uz/uz/product/knigi')
soup = BeautifulSoup(page.content, "lxml")
for text in soup.select('.product__item > a'):
    print(text.get_text(strip=True))


# class dict(dict):
#     def hello(self):
#         print(self.items())
#
#
# hello = dict()
# hello.hello()