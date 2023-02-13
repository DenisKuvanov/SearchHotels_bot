import requests
from typing import Dict
from telebot.types import Message
from utils.logger_settings import logger

X_RAPIDAPI_KEY = "e32598b809mshaacc28f4e9bf7ccp19a25ejsn955e64105d2e"


def get_name_location(data: dict, loc_id: str) -> str:
    """
     Получает id города и возвращает его точное название

    :param data: данные CallbackQuery
    :param loc_id: id города
    :return: location name
    """
    for loc in data['reply_markup']['inline_keyboard']:
        if loc[0]['callback_data'] == loc_id:
            return loc[0]['text']


def search_city(message: Message) -> Dict[str, str]:
    """
    Данная функция служит для поиска города в базе сайта hotels.com по
    введённому запросу пользователя. Возвращает словарь с названием города и
    его id. В случае неудачного поиска возвращает пустой словарь

    :return: Dict[regionNames - id]
    """

    url = "https://hotels4.p.rapidapi.com/locations/v3/search"

    headers = {
        "X-RapidAPI-Key": X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": "hotels4.p.rapidapi.com"
    }

    city = message.text.strip()
    querystring = {
        "q": city,
        "locale": "ru_RU"
    }
    logger.info(f'function {search_city.__name__} called with parameters {city}')
    cities_id = dict()
    try:
        response = requests.get(url, headers=headers, params=querystring).json()
        logger.info(f'Hotels api(locations) response received: {response}')

        if response.get('message'):
            logger.error(f'Problems with subscription to hotels api {response}')
            raise requests.exceptions.RequestException

        if response['sr']:
            for i_elem in response['sr']:
                if i_elem['type'] in ('CITY', 'NEIGHBORHOOD'):
                    cities_id[i_elem['regionNames']['fullName']] = i_elem['gaiaId']

    except requests.exceptions.RequestException as ex:
        logger.error(f'Server error: {ex}')
    except Exception as ex:
        logger.error(f'Error: {ex}')
    finally:
        return cities_id