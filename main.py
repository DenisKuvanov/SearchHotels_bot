import telebot
from telebot.types import Message, CallbackQuery, InputMediaPhoto
from loguru import logger
from utils.instruments import is_user_in_db, logger_config, add_user, phrase, \
    get_user_info, set_user_info, make_message, is_input_correct
from hotels_API.locations import search_city, get_name_location
from hotels_API.hotels import get_hotels


logger.configure(**logger_config)
TOKEN = '5813738796:AAHv8WA1vSu6M2cf7q9PgLOw9nlWqUSoaDE'
bot = telebot.TeleBot(token=TOKEN, parse_mode='HTML')


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
    set_user_info(key='state', value='1', message=message)
    if 'lowprice' in message.text:
        set_user_info(key='order', value='PRICE', message=message)
        logger.info('"lowprice" command is called')
    elif '/highprice' in message.text:
        bot.send_message(chat_id=message.chat.id,
                         text='Команда highprice пока в разработке')
        #дорабоать
        # set_user_info(key='order', value='PRICE_HIGHT_TO_LOW', message=message)
        # logger.info('"highprice" command is called')
    elif '/bestdeal' in message.text:
        bot.send_message(chat_id=message.chat.id,
                         text='Команда bestdeal пока в разработке')
        #дорабоать
        # set_user_info(key='order', value='DISTANCE_FROM_CENTRE', message=message)
        # logger.info('"bestdeal" command is called')
    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Команда history пока в разработке')
        #дорабоать
        # set_user_info(key='order', value='HISTORY', message=message)
        # logger.info('"history" command is called')

    logger.info(get_user_info(key='order', message=message))
    state = get_user_info(key='state', message=message)
    logger.info(f"Current state: {state}")
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
    state = get_user_info(key='state', message=message)
    if state == '1':
        get_location(message)
    elif state in ['2', '3', '4', '5', '6']:
        get_search_parameters(message)
    else:
        bot.send_message(chat_id=message.chat.id, text=phrase('dontunderstanding'))


def get_location(message: Message) -> None:
    """
    Получает название города, ищет чере API hotels совпадения и отправляет их в
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
        if get_user_info(key='state', message=call.message) != '1':
            bot.send_message(call.message.chat.id, text=phrase('enter_command'))
            set_user_info(key='state', value='0', message=call.message)
        else:
            city_name = get_name_location(call.message.json, call.data)
            set_user_info(key='destination_id', value=call.data[4:], message=call.message)
            set_user_info(key='destination_name', value=city_name, message=call.message)
            logger.info(f"{city_name} selected")
            bot.send_message(
                chat_id=chat_id,
                text=f'{phrase(key="loc_selected")}: <b>{city_name}</b>'
            )
            # if get_user_info(key='order', message=call.message) == 'DISTANCE_FROM_CENTRE':
            #     set_user_info(key='state', value='1', message=call.message, increase=True)
            # else:
            #     set_user_info(key='state', value='2', message=call.message, increase=True)
            set_user_info(key='state', value='1', message=call.message,
                          increase=True)
            bot.send_message(chat_id=chat_id, text=make_message(call.message, 'question_'))

    if call.data == 'cancel':
        logger.info(f'Canceled by user')
        set_user_info(key='state', value='0', message=call.message)
        bot.send_message(chat_id, 'Отменено')


def get_search_parameters(message: Message) -> None:
    """
    Получает и запоминает параметры поиска от пользователя
    :param message: Message
    :return: None
    """
    logger.info(f'Function {get_search_parameters.__name__} called with argument: {message}')
    chat_id = message.chat.id
    state = get_user_info(key='state', message=message)
    if not is_input_correct(message=message):
        bot.send_message(chat_id=chat_id, text=make_message(message, 'mistake_'))
    else:
        set_user_info(key='state', value='1', increase=True, message=message)
        if state == '2':
            date_in, date_out = message.text.replace(' ', '').split('-')
            set_user_info(key='date_in', value=date_in, message=message)
            set_user_info(key='date_out', value=date_out, message=message)
            if get_user_info(key='order', message=message) == 'PRICE':
                set_user_info(key='state', value='2', message=message, increase=True)
            bot.send_message(chat_id=chat_id, text=make_message(message, 'question_'))
        elif state == '5':
            number_of_hotels = message.text.strip()
            set_user_info(key='number_of_hotels', value=number_of_hotels, message=message)
            bot.send_message(chat_id=chat_id, text=make_message(message, 'question_'))
        elif state == '6':
            number_of_photo = message.text.strip()
            set_user_info(key='number_of_photo', value=number_of_photo, message=message)
            set_user_info(key='state', value='0', message=message)
            search_hotels(message=message)


def search_hotels(message: Message):
    chat_id = message.chat.id
    wait_msg = bot.send_message(chat_id=message.chat.id, text=phrase('wait'))
    parameters = get_user_info(message=message, all=True)
    hotels = get_hotels(message=message, parameters=parameters)
    logger.info(f'Function {get_hotels.__name__} returned: {hotels}')
    bot.delete_message(chat_id=chat_id, message_id=wait_msg.id)
    if not hotels or len(hotels) < 1:
        bot.send_message(chat_id=chat_id, text=phrase(key='hotels_not_found'))
    else:
        for hotel in hotels:
            text = f"Название отеля: {hotel['name']}\nРасстояние до центра: {hotel['distance_from_centre']}\nЦена за сутки: {hotel['price_per_night']}\n" \
                   f"Общая сумма: {hotel['total_price']}\nURL адрес отеля: {hotel['url']}"
            msg = bot.send_message(message.from_user.id, text)
            photos = []
            for photo in hotel['images']:
                photos.append(InputMediaPhoto(photo))
            if photos:
                bot.send_media_group(chat_id=message.from_user.id, media=photos)





try:
    bot.infinity_polling()
except Exception as e:
    logger.opt(exception=True).error(f'Unexpected error: {e}')