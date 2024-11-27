import requests
import json

HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
}

COOKIES = {
    'city_slug': 'ekb',
}

URL = "https://api-ecomm.sdvor.com/occ/v2/sd/products/search?fields=algorithmsForAddingRelatedProducts%2CcategoryCode%2Cproducts(code%2Cbonus%2Cslug%2CdealType%2Cname%2Cunit%2Cunits(FULL)%2CunitPrices(FULL)%2CavailableInStores(FULL)%2Cbadges(DEFAULT)%2Cmultiunit%2Cprice(FULL)%2CcrossedPrice(FULL)%2CtransitPrice(FULL)%2CpersonalPrice(FULL)%2Cimages(DEFAULT)%2Cstock(FULL)%2CmarketingAttributes%2CisArchive%2Ccategories(FULL)%2CcategoryNamesForAnalytics)%2Cfacets%2Cbreadcrumbs%2Cpagination(DEFAULT)%2Csorts(DEFAULT)%2Cbanners(FULL)%2CfreeTextSearch%2CcurrentQuery%2CkeywordRedirectUrl&currentPage=0&pageSize=99999&facets=allCategories%3Anapolnye-pokrytija-5448&lang=ru&curr=RUB&deviceType=mobile&baseStore=ekb"

def get_products(url):
    all_products = []
    response = requests.get(url, headers=HEADERS, cookies=COOKIES)
    if response.status_code != 200:
        print(f"Ошибка: статус код {response.status_code}")
        return all_products
    data = response.json()


    if "products" in data:
        for product in data["products"]:
            name = product.get("name", "Нет названия")
            price_data = product.get("price", {})
            price = price_data.get("formattedValue", "Нет цены")
            all_products.append({"name": name, "price": price})
    return all_products

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    products = get_products(URL)
    filename = f"json_parser.json"
    save_to_json(products, filename)
    print(f"Всего собрано товаров: {len(products)}")
    print(f"Данные сохранены в файл {filename}")