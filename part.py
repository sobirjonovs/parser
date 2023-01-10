import json
from urllib import request
from urllib.request import urlopen

from bs4 import BeautifulSoup


code_product = urlopen(f"https://asaxiy.uz/product/komod-detskii-4-h-yarusnyi-elif").read()
soup_product = BeautifulSoup(code_product, "lxml")

with open('test.json', 'w') as file:
    file.write(json.dumps({'asdfdasf': 'asdfasdf'}))