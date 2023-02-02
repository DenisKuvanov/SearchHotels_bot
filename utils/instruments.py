import datetime
import re
import json
from typing import List

from telebot.types import Message
from loguru import logger
from redis_db import redis_db

from utils.bot_messages import vocabulary

steps = {
    '1': 'destination_id',
    '2': 'date_in_out',
    '3min': 'min_price',
    '3max': 'max_price',
    '4': 'distance',
    '5': 'number_of_hotels',
    '6': 'number_of_photo'
}

logger_config = {
    "handlers": [
        {
            "sink": "logs/bot.log",
            "format": "{time:YYYY-MM-DD at HH:mm:ss Z} | {level} | {message}",
            "encoding": "utf-8",
            "level": "DEBUG",
            "rotation": "10 MB",
            "compression": "zip"
        },
    ],
}


def add_user(message: Message) -> None:
    """
    Добавляет пользователя в базу данных
    :param message:
    :return: None
    """
    logger.info(f'function "{add_user.__name__}" called')
    user_chat_id = str(message.chat.id)
    redis_db.hset(user_chat_id, 'state', 0)
    redis_db.hset(user_chat_id, 'username', message.chat.username)


def is_input_correct(message: Message) -> bool:
    """
    Проверяет корректность ввода параметров
    :param message: Message
    :return: True, если параметр введён корректно
    """
    chat_id = message.chat.id
    state = redis_db.hget(chat_id, 'state')
    msg = message.text.strip()
    logger.info(f'function {is_input_correct.__name__} called')
    if state == '6' and msg.strip().isdigit() and 0 <= int(msg.strip()) <= 10:
        return True
    elif state == '5' and msg.strip().isdigit() and 0 < int(msg.strip()) <= 10:
        return True
    elif state == '4' and msg.strip().isdigit() and int(msg.strip()) > 0:
        return True
    elif state == '3' and is_price_correct(msg):
        return True
    elif state == '2' and is_date_correct(msg):
        return True
    elif state == '1' and msg.replace(' ', '').replace('-', '').isalpha():
        return True


def is_price_correct(price: str) -> bool:
    """
    Проверяет корректность введёной максимальной и минимальной суммы
    :param price:
    :return: bool
    """
    if not price.replace(' ', '').replace('-', '').isdigit():
        return False
    if '-' not in price:
        return False
    min_price, max_price = list(map(lambda elem: int(elem), price.replace(' ', '').split('-')))
    if min_price < 1 or max_price < 1:
        return False
    if min_price >= max_price:
        return False
    return True


def is_date_correct(date: str) -> bool:
    """
    Проверяет корректность даты заезда и выезда
    :param date:
    :return:
    """
    if not date.replace(' ', '').replace('-', '').replace('.', '').isdigit():
        return False
    date_in, date_out = date.replace(' ', '').split('-')
    pattern = r'(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[12])\.(202[2-3])'
    if not re.fullmatch(pattern, date_in) or not re.fullmatch(pattern, date_out):
        return False
    day_in, month_in, year_in = list(map(lambda d: int(d), date_in.split('.')))
    day_out, month_out, year_out = list(map(lambda d: int(d), date_out.split('.')))
    if datetime.date(year_in, month_in, day_in) < datetime.date.today():
        return False
    if not datetime.date(year_in, month_in, day_in) < datetime.date(year_out, month_out, day_out):
        return False
    return True


def is_user_in_db(message: Message) -> bool:
    """
    Проверяет, есть ли пользователь в базе данных
    :param message: Message
    :return: True, если пользователь есть в базе данных
    """
    logger.info(f'function "{is_user_in_db.__name__}" called')
    user_chat_id = str(message.chat.id)
    if redis_db.hget(user_chat_id, 'state'):
        return True
    return False


def make_message(message: Message, prefix: str) -> str:
    """
    Формирует и возвращает сообщение с информацией о неправильном вводе или
    вопрос в соответсвии с префиксом и состоянием
    :param message: Message
    :param prefix: префикс для поиска нужного сообщения в словаре
    :return: str
    """
    state = redis_db.hget(message.chat.id, 'state')
    msg = phrase(prefix + state)

    return msg


def add_command_history(message: Message, command: str) -> None:
    """
    Добавляет в историю поиска введённую пользователем команду и дату её ввода
    :param message: Message
    :param command: команда, введённая пользователем
    :return: None
    """
    logger.info(f'function "{add_command_history.__name__}" called')
    user_chat_id = str(message.chat.id)
    if redis_db.llen('u_' + user_chat_id) >= 10:
        redis_db.lpop('u_' + user_chat_id)
    redis_db.rpush('u_' + user_chat_id,
                   json.dumps({
                       'command': command,
                       'date': datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'),
                       'destination_name': '',
                       'hotels_lst': []
                   }))


def add_hotels_in_history(message: Message, all_hotels_lst: List) -> None:
    """
    Добавляет список найденных отелей в историю поиска пользователя
    :param message: Message
    :param all_hotels_lst: список найденныйх отелей
    :return: None
    """
    logger.info(f'function "{add_hotels_in_history.__name__}" called')
    user_chat_id = str(message.chat.id)
    last_elem = json.loads(redis_db.rpop('u_' + user_chat_id))
    last_elem['destination_name'] = redis_db.hget(user_chat_id, 'destination_name')
    hotels_lst = [hotel_name['name'] for hotel_name in all_hotels_lst]
    last_elem['hotels_lst'] = hotels_lst
    redis_db.rpush('u_' + user_chat_id, json.dumps(last_elem))


def make_history_message(elem: bytes) -> str:
    """
    Формирует сообщение, содержащие историю запросов пользователя
    :param elem:
    :return:
    """
    elem_history = json.loads(elem)
    hotels_name = ''
    for hotel in elem_history['hotels_lst']:
        hotels_name += '\n- ' + hotel
    text = f"Введённая команда: <b>{elem_history['command']}</b>\nВведённый " \
           f"город: <b>{elem_history['destination_name']}</b>\nДата вво" \
           f"да: <b>{elem_history['date']}</b>\nНайденные отели: <b>" \
           f"{hotels_name}</b> "
    return text


def phrase(key: str) -> str:
    """
    Возвращает подходящую фразу для отправки ботом
    :param key: str
    :param message: Message
    :return: Возвращает фразу
    :rtype: str
    """
    return vocabulary[key]
