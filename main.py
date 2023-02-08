import telebot
from telebot.types import Message, CallbackQuery, InputMediaPhoto
from redis_db import user_state_db, user_history_db
from requests.exceptions import RequestException

from utils.instruments import is_user_in_db, add_user, phrase, \
    make_message, is_input_correct, add_command_history, add_hotels_in_history, \
    make_history_message
from utils.logger_settings import logger
from hotels_API.locations import search_city, get_name_location
from hotels_API.hotels import get_hotels


TOKEN = '5813738796:AAHv8WA1vSu6M2cf7q9PgLOw9nlWqUSoaDE'
bot = telebot.TeleBot(token=TOKEN, parse_mode='HTML')

# Добавляем кнопку меню с командами бота
commands = []
commands.append(telebot.types.BotCommand('/start', 'запустить бота'))
commands.append(telebot.types.BotCommand('/help', 'список всех команд'))
commands.append(telebot.types.BotCommand('/lowprice', 'топ дешёвых отелей в городе'))
commands.append(telebot.types.BotCommand('/highprice', 'топ дорогих отелей в городе'))
commands.append(telebot.types.BotCommand('/bestdeal', 'лучшие предложения по цене и расположению'))
commands.append(telebot.types.BotCommand('/history', 'история поиска отелей'))
bot.set_my_commands(commands=commands)


@bot.message_handler(commands=['help', 'start'])
def start_help(message: Message) -> None:
    """
    Отлавливает команды 'help' и 'start'. Выводит информацию о боте и его
    доступные команды
    :param message: Message
    :return: None
    """
    if not is_user_in_db(message):
        add_user(message)
    if 'start' in message.text:
        logger.info('"start" command is called')
        bot.send_message(chat_id=message.chat.id, text=phrase('start'))
    else:
        logger.info('"help" command is called')
        bot.send_message(chat_id=message.chat.id, text=phrase('help'))


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal', 'history'])
def get_commands(message: Message) -> None:
    """
    Отслеживает команды '/lowprice', '/highprice', '/bestdeal', '/history',
    устанавливает сортировку и запрашивает параметры поиска у пользователя
    :param message: Message
    :return: None
    """
    logger.info("\n" + "*" * 100 + "\n")
    if not is_user_in_db(message=message):
        add_user(message=message)
    user_chat_id = message.chat.id
    user_state_db.hset(user_chat_id, 'state', 1)
    if 'lowprice' in message.text:
        user_state_db.hset(user_chat_id, 'order', 'PRICE_LOW_TO_HIGH')
        logger.info('"lowprice" command is called')
        add_command_history(message=message, command='lowprice')
    elif '/highprice' in message.text:
        user_state_db.hset(user_chat_id, 'order', 'RECOMMENDED')
        logger.info('"highprice" command is called')
        add_command_history(message=message, command='highprice')
    elif '/bestdeal' in message.text:
        user_state_db.hset(user_chat_id, 'order', 'DISTANCE')
        logger.info('"bestdeal" command is called')
        add_command_history(message=message, command='bestdeal')
    elif '/history' in message.text:
        user_state_db.hset(user_chat_id, 'order', 'HISTORY')
        logger.info('"HISTORY" command is called')
        user_state_db.hset(user_chat_id, 'state', 0)
        history = user_history_db.lrange(str(user_chat_id), 0, 9)
        if not history:
            bot.send_message(chat_id=user_chat_id, text='В данный момент история запросов пуста')
        for elem in history:
            text = make_history_message(elem)
            bot.send_message(chat_id=user_chat_id, text=text)

    logger.info(user_state_db.hget(user_chat_id, 'order'))
    state = user_state_db.hget(user_chat_id, 'state')
    logger.info(f"Current state: {state}")
    if not user_state_db.hget(user_chat_id, 'order') == "HISTORY":
        bot.send_message(chat_id=message.chat.id, text=make_message(message, 'question_'))


@bot.message_handler(content_types=['text'])
def get_text_message(message: Message) -> None:
    """
    Обрабатывает поступаемые текстовые сообщения
    :param message: Message
    :return: None
    """
    if not is_user_in_db(message=message):
        add_user(message=message)
    state = user_state_db.hget(message.chat.id, 'state')
    if state == '1':
        get_location(message)
    elif state in ['2', '3', '4', '5', '6']:
        get_search_parameters(message)
    else:
        bot.send_message(chat_id=message.chat.id, text=phrase('dontunderstanding'))


def get_location(message: Message) -> None:
    """
    Получает название города, ищет через API hotels совпадения и отправляет их в
    чат
    :param message: Message
    :return: None
    """
    if not is_input_correct(message=message):
        bot.send_message(chat_id=message.chat.id, text=make_message(message, 'mistake_'))
    else:
        wait_msg = bot.send_message(chat_id=message.chat.id, text=phrase('wait'))
        locations = search_city(message=message)
        bot.delete_message(message.chat.id, wait_msg.id)
        if not locations or len(locations) < 1:
            bot.send_message(message.chat.id, str(message.text) + phrase(key='locations_not_found'))
        else:
            menu = telebot.types.InlineKeyboardMarkup()
            for city_name, city_id in locations.items():
                menu.add(telebot.types.InlineKeyboardButton(
                    text=city_name,
                    callback_data='code' + city_id
                ))
            menu.add(telebot.types.InlineKeyboardButton(
                text='Отмена',
                callback_data='cancel'
            ))
            bot.send_message(message.chat.id, phrase('loc_choose'), reply_markup=menu)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call: CallbackQuery) -> None:
    """
    Отслеживает кнопки, нажатые пользователем
    :param call: CallbackQuery
    :return: None
    """

    logger.info(f'Function {callback_worker.__name__} called with argument: {call}')
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id)

    if call.data.startswith('code'):
        if user_state_db.hget(chat_id, 'state') != '1':
            bot.send_message(call.message.chat.id, text=phrase('enter_command'))
            user_state_db.hset(chat_id, 'state', 0)
        else:
            city_name = get_name_location(call.message.json, call.data)
            user_state_db.hset(chat_id, mapping={
                'destination_id': call.data[4:],
                'destination_name': city_name
            })
            logger.info(f"{city_name} selected")
            bot.send_message(
                chat_id=chat_id,
                text=f'{phrase(key="loc_selected")}: <b>{city_name}</b>'
            )
            user_state_db.hincrby(chat_id, 'state', 1)
            bot.send_message(chat_id=chat_id, text=make_message(call.message, 'question_'))

    if call.data == 'cancel':
        logger.info(f'Canceled by user')
        user_state_db.hset(chat_id, 'state', 0)
        bot.send_message(chat_id, 'Отменено')


def get_search_parameters(message: Message) -> None:
    """
    Получает и сохраняет параметры поиска от пользователя в базу данных
    :param message: Message
    :return: None
    """
    logger.info(f'Function {get_search_parameters.__name__} called with argument: {message}')
    chat_id = message.chat.id
    state = user_state_db.hget(chat_id, 'state')
    if not is_input_correct(message=message):
        bot.send_message(chat_id=chat_id, text=make_message(message, 'mistake_'))
    else:
        user_state_db.hincrby(chat_id, 'state', 1)
        if state == '2':
            date_in, date_out = message.text.replace(' ', '').split('-')
            user_state_db.hset(chat_id, mapping={
                'date_in': date_in,
                'date_out': date_out
            })
            logger.info(f'set date_in={date_in}, date_out={date_out}')
            if user_state_db.hget(chat_id, 'order') == 'PRICE_LOW_TO_HIGH':
                user_state_db.hincrby(chat_id, 'state', 2)
            elif user_state_db.hget(chat_id, 'order') == 'RECOMMENDED':
                user_state_db.hincrby(chat_id, 'state', 1)
            bot.send_message(chat_id=chat_id, text=make_message(message, 'question_'))
        elif state == '3':
            min_price, max_price = message.text.replace(' ', '').split('-')
            user_state_db.hset(chat_id, mapping={
                'min_price': min_price,
                'max_price': max_price
            })
            logger.info(f'set min_price={min_price}, max_price={max_price}')
            user_state_db.hincrby(chat_id, 'state', 1)
            bot.send_message(chat_id=chat_id, text=make_message(message, 'question_'))
        elif state == '4':
            min_price = message.text.strip()
            user_state_db.hset(chat_id, 'min_price', min_price)
            logger.info(f'set min_price={min_price}')
            bot.send_message(chat_id=chat_id,
                             text=make_message(message, 'question_'))
        elif state == '5':
            number_of_hotels = message.text.strip()
            user_state_db.hset(chat_id, 'number_of_hotels', number_of_hotels)
            logger.info(f'set number_of_hotels={number_of_hotels}')
            bot.send_message(chat_id=chat_id, text=make_message(message, 'question_'))
        elif state == '6':
            number_of_photo = message.text.strip()
            user_state_db.hset(chat_id, mapping={
                'number_of_photo': number_of_photo,
                'state': 0
            })
            logger.info(f'set number_of_photo={number_of_photo}, state=0')
            search_hotels(message=message)


def search_hotels(message: Message):
    chat_id = message.chat.id
    wait_msg = bot.send_message(chat_id=message.chat.id, text=phrase('wait'))
    parameters = user_state_db.hgetall(message.chat.id)
    try:
        hotels = get_hotels(message=message, parameters=parameters)
        logger.info(f'Function {get_hotels.__name__} returned: {hotels}')
        add_hotels_in_history(message=message, all_hotels_lst=hotels)
        bot.delete_message(chat_id=chat_id, message_id=wait_msg.id)
        if not hotels or len(hotels) < 1:
            bot.send_message(chat_id=chat_id, text=phrase(key='hotels_not_found'))
        else:
            for hotel in hotels:
                text = f"Название отеля: {hotel['name']}\nРасстояние до центра: {hotel['distance_from_centre']}\nЦена за сутки: ${hotel['price_per_night']}\n" \
                       f"Общая сумма: {hotel['total_price']}\nURL адрес отеля: {hotel['url']}"
                bot.send_message(message.from_user.id, text)
                photos = []
                for photo in hotel['images']:
                    photos.append(InputMediaPhoto(photo))
                if photos:
                    bot.send_media_group(chat_id=message.from_user.id, media=photos)
    except RequestException as ex:
        logger.error(f'Server error: {ex}')
        bot.send_message(chat_id=chat_id, text=phrase(key='hotels_not_found'))




try:
    bot.infinity_polling()
except Exception as e:
    logger.opt(exception=True).error(f'Unexpected error: {e}')