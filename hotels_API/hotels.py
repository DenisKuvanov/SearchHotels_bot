import requests
from typing import List, Dict, Tuple
from telebot.types import Message
from loguru import logger

X_RAPIDAPI_KEY = "cfcdca8e7cmshdea121d9cb1595fp19d74cjsn19805112f7c8"


def get_hotels(message: Message, parameters: dict) -> [dict, None]:
    """

    :param message:
    :param parameters:
    :return:
    """
    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    location_id = parameters['destination_id']
    day_in, month_in, year_in = sep_date(parameters['date_in'])
    day_out, month_out, year_out = sep_date(parameters['date_out'])
    hotels_amount = int(parameters['number_of_hotels'])
    images_amount = int(parameters['number_of_photo'])
    min_price, max_price = 1, 900
    if parameters['order'] != 'PRICE':
        min_price, max_price = int(parameters['min_price']), int(parameters['max_price'])

    payload = {
        "currency": "USD",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "destination": {"regionId": location_id},
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
                "adults": 1,
                "children": []
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
        "X-RapidAPI-Key": X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    response = requests.post(url, json=payload, headers=headers).json()
    hotels_lst = []
    for i_hotel in response['data']['propertySearch']['properties']:
        hotel = {
            'id': i_hotel['id'],
            'name': i_hotel['name'],
            'distance_from_centre':
                i_hotel['destinationInfo']['distanceFromDestination']['value'],
            'price_per_night': i_hotel['price']['lead']['formatted'],
            'total_price':
                i_hotel['price']['displayMessages'][1]['lineItems'][0][
                    'value'].replace('total', ''),
            'url': 'https://www.hotels.com/h{}.Hotel-Information'.format(
                i_hotel['id']),
            'images': get_images(hotel_id=i_hotel['id'], images_amount=images_amount)

        }
        hotels_lst.append(hotel)

    return hotels_lst


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
        "locale": "ru_RU",
        "siteId": 300000001,
        "propertyId": hotel_id
    }
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": X_RAPIDAPI_KEY,
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


def sep_date(date: str) -> Tuple:
    day, month, year = list(map(lambda x: int(x), date.split('.')))
    return (day, month, year)