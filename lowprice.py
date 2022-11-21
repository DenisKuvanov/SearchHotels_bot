import requests
from typing import List


def search_city() -> str:
    """
    Данная функция служит для поиска города в базе сайта hotels.com по
    введённому запросу пользователя. Возвращает id города. В случае неудачного
    поиска возвращает пустую строку

    :return: city_id - id города
    :rtype: str
    """

    url = "https://hotels4.p.rapidapi.com/locations/v3/search"

    headers = {
        "X-RapidAPI-Key": "cfcdca8e7cmshdea121d9cb1595fp19d74cjsn19805112f7c8",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    city = input('\nВведите название города латиницей: ')
    querystring = {"q": city, "locale": "en_US", "langid": "1033",
                   "siteid": "300000001"}


    response = requests.get(url, headers=headers, params=querystring).json()

    city_id = ''
    if response['sr']:
        for i_elem in response['sr']:
            if i_elem['type'] == 'CITY':
                answer = input(
                    f"{i_elem['regionNames']['fullName']} - город выбран верно? (да/нет) ")
                if answer.lower() == 'да':
                    city_id = i_elem['gaiaId']
                    break

    return city_id


def get_images(hotel_id: str, images_amount: int) -> List[str]:
    """
    Данная функция получает на вход id отеля и количество фотографий, которые
    нужно получить. После чего возвращает список из этих фото

    :param hotel_id (str): значение id отеля
    :param images_amount (int): количество фотографий для вывода
    :return images_lst - список из ссылок на фото отеля
    :rtype List[str]
    """
    url = "https://hotels4.p.rapidapi.com/properties/v2/detail"

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "propertyId": hotel_id
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "cfcdca8e7cmshdea121d9cb1595fp19d74cjsn19805112f7c8",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.request("POST", url, json=payload, headers=headers).json()
    images_lst = []

    if len(response['data']['propertyInfo']['propertyGallery']['images']) < images_amount:  # Проверка количества фотографий отеля,
        images_amount = len(response['data']['propertyInfo']['propertyGallery']['images'])  # на случай, если их меньше указанного значения

    for _ in range(images_amount):
        images_lst.append(
            response['data']['propertyInfo']['propertyGallery']['images'][_]['image']['url']
        )

    return images_lst


def search_hotels(city_id: str):

    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    day_in, month_in, year_in = list(map(lambda x: int(x), (
        input('Укажите дату заезда в формате "дд.мм.гггг": ').split('.'))))
    day_out, month_out, year_out = list(map(lambda x: int(x), (
        input('Укажите дату выезда в формате "дд.мм.гггг": ').split('.'))))
    adults = int(input('Укажите количество взрослых в номере: '))
    children_amount = int(input('Укажите количество детей: '))
    children = [{'age': int(input(f'Возраст {i}-го ребёнка'))} for i in range(1, children_amount + 1)]
    hotels_amount = int(input('Введите количество отелей, которые нужно '
                              'вывести (не больше 20): '))
    images_amount = int(input('Введите количество фото для каждого отеля (если выводить не нужно, то введите 0): '))
    min_price, max_price = list(map(lambda x: int(x), input('Укажите диапазон цены за сутки в формате "100-200": ').split('-')))

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "destination": {"regionId": city_id},
        "checkInDate": {
            "day": day_in,
            "month": month_in,
            "year": year_in
        },
        "checkOutDate": {
            "day": day_out,
            "month": month_out,
            "year": year_out
        },
        "rooms": [
            {
                "adults": adults,
                "children": children
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": hotels_amount,
        "sort": "PRICE_LOW_TO_HIGH",
        "filters": {"price": {
            "max": max_price,
            "min": min_price
        }}
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "cfcdca8e7cmshdea121d9cb1595fp19d74cjsn19805112f7c8",
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.post(url, json=payload, headers=headers).json()
    hotels_lst = []
    for i_hotel in response['data']['propertySearch']['properties']:
        hotel = {
            'id': i_hotel['id'],
            'name': i_hotel['name'],
            'distance_from_centre': i_hotel['destinationInfo']['distanceFromDestination']['value'],
            'price_per_night': i_hotel['price']['lead']['formatted'],
            'total_price': i_hotel['price']['displayMessages'][1]['lineItems'][0]['value'].replace('total', ''),
            'url': 'https://www.hotels.com/h{}.Hotel-Information'.format(i_hotel['id']),
            'images': get_images(hotel_id=i_hotel['id'], images_amount=images_amount)

        }
        hotels_lst.append(hotel)

    return hotels_lst


def print_hotels_info(hotels_lst):
    for hotel in hotels_lst:
        print(f"\nName: {hotel['name']}")
        print(f"Distance from centre: {hotel['distance_from_centre']}")
        print(f"Price per night: {hotel['price_per_night']}")
        print(f"Total price: {hotel['total_price']}")
        print(f"URL: {hotel['url']}")
        if hotel['images']:
            print("Photo: ")
            for image in hotel['images']:
                print('\t', image)
