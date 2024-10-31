from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


COOKIES = {
    '_ymab_param': 'MEww6EBWnRaB2NB61cPScLUZI6SHm-lddqXm2uathZDsvt78xnhAm-yvzzQen2lrfTB27MAir6GUuaHtURAUGgBtzNY',
    'rrpvid': '668238209843822',
    'instance-uid': '20200183-e472-4741-b17e-2193a46c673e',
    'rcuid': '6525633cfe0a4d45a9715eb3',
    '_ga': 'GA1.1.521162159.1730370100',
    '_ym_uid': '1730370100546318385',
    '_ym_d': '1730370100',
    '_ym_isad': '1',
    '_userGUID': '0:m2x5oidr:oM2klJu~4uNinTYJB2m4Xa6Oo3DgWyDh',
    'first_visit': '2024-10-31T15:21:40.734+05:00',
    '_userGUID': '0:m2x5oidr:oM2klJu~4uNinTYJB2m4Xa6Oo3DgWyDh',
    'rrlevt': '1730370285143',
    'days_from_first_visit': '0',
    'auth_user_id': 'current',
    '_ym_visorc': 'b',
    'dSesn': 'aebf927c-2957-bec5-8d5f-a508bc9ae194',
    '_dvs': '0:m2xbjcod:Uve4pnW617MPU8VFYjQVTzvgezq9oFj5',
    'digi_uc': '|v:173037:599843|c:173037:440102!173038:479518',
    'city_slug': 'ekb',
    '_ga_EXGRJB28H8': 'GS1.1.1730379934.3.1.1730381552.26.0.0',
}

HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    # 'cookie': '_ymab_param=MEww6EBWnRaB2NB61cPScLUZI6SHm-lddqXm2uathZDsvt78xnhAm-yvzzQen2lrfTB27MAir6GUuaHtURAUGgBtzNY; rrpvid=668238209843822; instance-uid=20200183-e472-4741-b17e-2193a46c673e; rcuid=6525633cfe0a4d45a9715eb3; _ga=GA1.1.521162159.1730370100; _ym_uid=1730370100546318385; _ym_d=1730370100; _ym_isad=1; _userGUID=0:m2x5oidr:oM2klJu~4uNinTYJB2m4Xa6Oo3DgWyDh; first_visit=2024-10-31T15:21:40.734+05:00; _userGUID=0:m2x5oidr:oM2klJu~4uNinTYJB2m4Xa6Oo3DgWyDh; rrlevt=1730370285143; days_from_first_visit=0; auth_user_id=current; _ym_visorc=b; dSesn=aebf927c-2957-bec5-8d5f-a508bc9ae194; _dvs=0:m2xbjcod:Uve4pnW617MPU8VFYjQVTzvgezq9oFj5; digi_uc=|v:173037:599843|c:173037:440102!173038:479518; city_slug=ekb; _ga_EXGRJB28H8=GS1.1.1730379934.3.1.1730381552.26.0.0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
}


def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def get_products(url):
    all_products = []

    driver = webdriver.Chrome()
    driver.get(url)

    try:
        scroll_to_bottom(driver)

        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-grid-item")))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        products = soup.find_all("div", class_="product")

        if not products:
            print("Товары не найдены на странице.")
            return all_products

        for product in products:
            name_elem = product.find("a", class_="product-name")
            price_elem = product.find("span", class_="main")

            name = name_elem.text.strip() if name_elem else 'Нет названия'
            price = price_elem.text.strip() if price_elem else 'Нет цены'

            all_products.append({"name": name, "price": price})

    finally:
        driver.quit()

    return all_products


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    URL = "https://www.sdvor.com/ekb/category/napolnye-pokrytija-5448"
    products = get_products(URL)
    filename = "products.json"
    save_to_json(products, filename)
    print(f"Всего собрано товаров: {len(products)}")
    print(f"Данные сохранены в файл {filename}")



















