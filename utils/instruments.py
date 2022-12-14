import datetime
from os import path
import re
import json

from telebot.types import Message
from loguru import logger

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

path_to_database = path.join(path.abspath(''), 'database', 'users_db.json')


def add_user(message: Message) -> None:
    """
    Добавляет пользователя в базу данных
    :param message:
    :return: None
    """
    logger.info(f'function "{add_user.__name__}" called')
    user_chat_id = str(message.chat.id)
    datebase = dict()

    if path.exists(path=path_to_database):
        with open(path_to_database, 'r', encoding='utf-8') as db:
            datebase = json.load(db)
    datebase[user_chat_id] = {
        'state': '0',
        'username': message.chat.username
    }
    with open(path_to_database, 'w', encoding='utf-8') as db:
        json.dump(datebase, db, indent=4, ensure_ascii=False)


def is_input_correct(message: Message) -> bool:
    """
    Проверяет корректность ввода параметров
    :param message: Message
    :return: True, если параметр введён корректно
    """
    state = get_user_info(key='state', message=message)
    msg = message.text.strip()
    if state in ['5', '6'] and msg.strip().isdigit() and 0 < int(msg.strip()) <= 10:
        return True
    elif state == '2' and is_date_correct(msg):
        return True
    elif state == '1' and msg.replace(' ', '').replace('-', '').isalpha():
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
    try:
        with open(path_to_database, 'r', encoding='utf-8') as db:
            datebase = json.load(db)
            if user_chat_id in datebase:
                return True
            return False
    except Exception as ex:
        return False


def get_user_info(message: Message, key: str = None, all: bool = None) -> str:
    """
    Возвращает  информацию о пользователе из базы данных по ключу key
    :param all: bool
    :param key: str
    :param message: Message
    :return: str
    """
    logger.info(f'function "{is_user_in_db.__name__}" called with parameter {key}')
    if not is_user_in_db(message):
        add_user(message)
    user_chat_id = str(message.chat.id)
    try:
        with open(path_to_database, 'r', encoding='utf-8') as db:
            datebase = json.load(db)
            if all:
                return datebase[user_chat_id]
            else:
                return datebase[user_chat_id][key]
    except Exception as ex:
        if key == 'state':
            return '0'
        elif key == 'order':
            return ''


def set_user_info(key:str, value: str, message: Message, increase: bool = False) -> None:
    """
    Устанавливает для пользователя переданное значение состояния
    :param key: str
    :param value: str
    :param message: Message
    :return: None
    """
    logger.info(f'function "{is_user_in_db.__name__}"called with parameter {key}')
    if not is_user_in_db(message):
        add_user(message)
    user_chat_id = str(message.chat.id)
    with open(path_to_database, 'r', encoding='utf-8') as db:
        datebase = json.load(db)
    if increase and key=='state':
        datebase[user_chat_id][key] = str(int(datebase[user_chat_id][key]) + int(value))
    else:
        datebase[user_chat_id][key] = value
    with open(path_to_database, 'w', encoding='utf-8') as db:
        json.dump(datebase, db, indent=4, ensure_ascii=False)


def make_message(message: Message, prefix: str) -> str:
    """
    Формирует и возвращает сообщение с информацией о неправильном вводе или
    вопрос в соответсвии с префиксом и состоянием
    :param message: Message
    :param prefix: префикс для поиска нужного сообщения в словаре
    :return: str
    """
    state = get_user_info(key='state', message=message)
    msg = phrase(prefix + state)

    return msg



def phrase(key: str) -> str:
    """
    Возвращает подходящую фразу для отправки ботом
    :param key: str
    :param message: Message
    :return: Возвращает фразу
    :rtype: str
    """
    return vocabulary[key]
