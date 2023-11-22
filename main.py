import sys
import requests
import json
import threading
from bs4 import BeautifulSoup

def fetch_data_list(url, store_id):
    # Создаем сессию, чтобы сохранить cookies
    session = requests.Session()

    # Устанавливаем cookies с идентификатором магазина и категорией, если это необходимо
    session.cookies.set('metroStoreId', store_id)

    # Тут может быть дополнительная логика для установки cookies или заголовков, если это требуется
    # ...

    # Отправляем HTTP GET запрос
    response = session.get(url)
    # Проверяем, получен ли успешный ответ
    if response.ok:
        # Создаем объект BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    else:
        print("Ошибка при запросе к странице:", response.status_code)
        return None
    

def parse_data(soup, url, store_id, price_data):

    data = []

    products_link = soup.find_all('a', class_='product-card-photo__link reset-link')

    for p_link, p_data in zip(products_link, price_data):
        
           
        product_url = url + p_link['href']
        product_soup = fetch_data_list(product_url, store_id)
        
        name_meta_tag = product_soup.find('h1', 
                        class_='product-page-content__product-name catalog-heading heading__h2')
        product_name = name_meta_tag.find('span').text.strip()

        product_data = {
            'id': int(product_soup.find('p', 
                class_='product-page-content__article').text.strip().replace('Артикул: ', '')),
            'name': product_name,
            'link': product_url,
            'new_price': p_data['new_price'], 
            'old_price': p_data['old_price'],
            'brand': product_soup.find('a', 
        class_='product-attributes__list-item-link reset-link active-blue-text').text.strip(),
        }
        data.append(product_data)
        print(product_data)

        if not p_data['new_price']:
            return data
        
    return data


def parse_price(soup):

    product_data = []

    price_divs = soup.find_all('div', class_='product-card__content')

    # Проходим по каждой карточке товара
    for price_div in price_divs:
        # Проверка на наличие товара
        availability = price_div.find('p', attrs={'is-out-of-stock': True})

        if not availability:

            new_price_div = price_div.find('div', class_='product-unit-prices__actual-wrapper')
            new_price = new_price_div.find('span', 
                            class_='product-price__sum-rubles').text.strip().replace('\xa0', '')
            
            old_price_div = price_div.find('div', class_='product-unit-prices__old-wrapper')
            old_price = old_price_div.find('span', class_='product-price__sum-rubles')

            
            if not old_price:
                old_price = None
            else:
                old_price = int(old_price.text.strip().replace('\xa0', ''))
            

            price_data = {
                'new_price': int(new_price),
                'old_price': old_price
            }
            product_data.append(price_data)

        else:
            price_data = {
                'new_price': None,
                'old_price': None
            }
            product_data.append(price_data)
            return product_data


    return product_data
        

if __name__ == '__main__':

    data = []

    # store_id = input('Введите ID магазина: ')
    # category = input('Введите наименование категории товаров: ')
    # pod_category = input('Введите наименование под категории товаров: ')
    
    store_id = '15'
    category = 'chaj-kofe-kakao'
    subcategory = 'kofe'
    file_path = f'store_id_{store_id}_category_{category}_subcategory_{subcategory}.json'

    base_url = 'https://online.metro-cc.ru'
    url = f'{base_url}/category/{category}/{subcategory}'

    soup = fetch_data_list(url, store_id)

    if soup:
        
        count = 2
        products = soup.find_all('div', class_='product-card__content')
        
        price_data = parse_price(soup)
        data.append(parse_data(soup, base_url, store_id, price_data))
        if data:
            if not data[-1][-1]['new_price']:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            sys.exit()
        page_url = url + '?page=' + str(count)
        print(page_url)
        page_soup = fetch_data_list(page_url, store_id)

        while page_soup:
            price_data = parse_price(page_soup)
            data.append(parse_data(page_soup, base_url, store_id, price_data))
            if not data[-1][-1]['new_price']:
                break
            print(count)
            count += 1
            page_url = url + '?page=' + str(count)
            print(page_url)
            page_soup = fetch_data_list(page_url, store_id)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data[:-1], f, ensure_ascii=False, indent=4)


        